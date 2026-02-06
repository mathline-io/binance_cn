import asyncio
from inspect import signature
from typing import Dict, Optional, Sequence, Tuple

import websockets
from django.conf import settings
from websockets.exceptions import ConnectionClosed

import appSite.globalvar as gv


UPSTREAM_CLOSE_CODE = 1011


def _decode_header_items(headers: Sequence[Tuple[bytes, bytes]]) -> Dict[str, str]:
    decoded = {}
    for key, value in headers:
        decoded[key.decode("latin1")] = value.decode("latin1")
    return decoded


def _extract_scope_ip(scope) -> str:
    headers = _decode_header_items(scope.get("headers", []))
    forwarded_for = headers.get("x-forwarded-for", "")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    client = scope.get("client")
    if isinstance(client, tuple) and client:
        return str(client[0])
    return ""


def _resolve_target_url(path: str, query_string: bytes) -> Optional[str]:
    route_path = path.lstrip("/")
    chunks = route_path.split("/", 2)
    if len(chunks) < 2 or chunks[0] != "ws":
        return None

    route_key = chunks[1]
    upstream_base = settings.BINANCE_WS_ENDPOINTS.get(route_key, "")
    if not upstream_base:
        return None

    upstream_path = chunks[2] if len(chunks) > 2 else ""
    if not upstream_path:
        return None

    target_url = f"{upstream_base.rstrip('/')}/{upstream_path.lstrip('/')}"
    if query_string:
        target_url = f"{target_url}?{query_string.decode('latin1')}"
    return target_url


def _build_upstream_headers(scope) -> Dict[str, str]:
    request_headers = _decode_header_items(scope.get("headers", []))
    blocked = {
        "host",
        "connection",
        "upgrade",
        "sec-websocket-key",
        "sec-websocket-version",
        "sec-websocket-extensions",
        "sec-websocket-protocol",
    }
    return {
        key: value for key, value in request_headers.items() if key.lower() not in blocked
    }


async def _client_to_upstream(receive, upstream_ws):
    while True:
        event = await receive()
        event_type = event.get("type")
        if event_type == "websocket.receive":
            if event.get("text") is not None:
                await upstream_ws.send(event["text"])
            elif event.get("bytes") is not None:
                await upstream_ws.send(event["bytes"])
        elif event_type == "websocket.disconnect":
            break


async def _upstream_to_client(send, upstream_ws):
    while True:
        message = await upstream_ws.recv()
        if isinstance(message, bytes):
            await send({"type": "websocket.send", "bytes": message})
        else:
            await send({"type": "websocket.send", "text": message})


class BinanceWebSocketProxy:
    def __init__(self):
        connect_sig = signature(websockets.connect)
        if "additional_headers" in connect_sig.parameters:
            self._header_arg_name = "additional_headers"
        else:
            self._header_arg_name = "extra_headers"

    async def __call__(self, scope, receive, send):
        event = await receive()
        if event.get("type") != "websocket.connect":
            return

        ip = _extract_scope_ip(scope)
        if ip not in gv.get("allowed_ips", []):
            await send({"type": "websocket.close", "code": 4403})
            return

        target_url = _resolve_target_url(
            path=scope.get("path", ""),
            query_string=scope.get("query_string", b""),
        )
        if not target_url:
            await send({"type": "websocket.close", "code": 4404})
            return

        ws_kwargs = {
            "subprotocols": scope.get("subprotocols") or None,
            "open_timeout": 15,
            "close_timeout": 10,
            self._header_arg_name: _build_upstream_headers(scope),
        }

        try:
            async with websockets.connect(target_url, **ws_kwargs) as upstream_ws:
                await send({"type": "websocket.accept"})
                to_upstream_task = asyncio.create_task(_client_to_upstream(receive, upstream_ws))
                to_client_task = asyncio.create_task(_upstream_to_client(send, upstream_ws))
                done, pending = await asyncio.wait(
                    [to_upstream_task, to_client_task],
                    return_when=asyncio.FIRST_EXCEPTION,
                )
                for task in pending:
                    task.cancel()
                for task in done:
                    exc = task.exception()
                    if exc and not isinstance(exc, ConnectionClosed):
                        raise exc
        except Exception:
            await send({"type": "websocket.close", "code": UPSTREAM_CLOSE_CODE})
