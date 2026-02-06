from binance_resender.ws_proxy import BinanceWebSocketProxy


class BinanceProtocolRouter:
    def __init__(self, http_app):
        self.http_app = http_app
        self.websocket_proxy = BinanceWebSocketProxy()

    async def __call__(self, scope, receive, send):
        if scope.get("type") == "websocket" and scope.get("path", "").startswith("/ws/"):
            await self.websocket_proxy(scope, receive, send)
            return
        await self.http_app(scope, receive, send)
