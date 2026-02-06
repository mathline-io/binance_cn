import traceback
from typing import Dict

import requests
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

import appSite.globalvar as gv
from appSite.models import SenderLogModel


KNOWN_BINANCE_PREFIXES = ("api", "sapi", "dapi", "eapi", "fapi", "papi", "vapi", "wapi")
REQUEST_HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
    "host",
    "content-length",
}
RESPONSE_EXCLUDED_HEADERS = REQUEST_HOP_BY_HOP_HEADERS | {"content-encoding"}


def index_handler(request):
    return render(request, 'index.html', {})


def _extract_ip(request) -> str:
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


def _build_target_path(path: str, default_prefix: str) -> str:
    clean_path = path.lstrip("/")
    for prefix in KNOWN_BINANCE_PREFIXES:
        if clean_path == prefix or clean_path.startswith(f"{prefix}/"):
            return f"/{clean_path}"
    return f"/{default_prefix}/{clean_path}"


def _build_forward_headers(request) -> Dict[str, str]:
    headers = {}
    for key, value in request.headers.items():
        if key.lower() in REQUEST_HOP_BY_HOP_HEADERS:
            continue
        headers[key] = value
    return headers


def _resolve_endpoint(name: str, fallback: str = "") -> str:
    endpoint_map = getattr(settings, "BINANCE_ENDPOINTS", {})
    endpoint = endpoint_map.get(name, "")
    if endpoint:
        return endpoint
    if fallback:
        return endpoint_map.get(fallback, "")
    return ""


def resender(request, path: str, api_url: str, default_prefix: str) -> requests.Response:
    request_path = _build_target_path(path=path, default_prefix=default_prefix)
    query_string = request.META.get("QUERY_STRING", "")
    target_url = f"{api_url}{request_path}"
    if query_string:
        target_url = f"{target_url}?{query_string}"

    method = request.method.upper()
    body = request.body if method in {"POST", "PUT", "PATCH", "DELETE"} else None
    return requests.request(
        method=method,
        url=target_url,
        data=body,
        headers=_build_forward_headers(request),
        timeout=(5, 30),
        allow_redirects=False,
    )


def base_api_handler(request, path, endpoint_name: str, default_prefix: str, fallback_endpoint: str = ""):
    ip = _extract_ip(request)
    if ip not in gv.get('allowed_ips', []):
        error_msg = 'Forbidden IP:' + ip
        if gv.get('use_log'):
            if not ip:
                ip = 'UnKnow'
            SenderLogModel(
                ip=ip,
                status=0,
                error_msg='Forbidden IP ' + ip
            ).save()
        error_data = {'code': '-1', 'data': {}, 'msg': error_msg}
        return JsonResponse(error_data, status=403)

    api_url = _resolve_endpoint(name=endpoint_name, fallback=fallback_endpoint)
    if not api_url:
        error_msg = f'Missing endpoint setting: {endpoint_name}'
        error_data = {'code': '-3', 'data': {}, 'msg': error_msg}
        return JsonResponse(error_data, status=500)

    try:
        upstream_response = resender(request, path, api_url=api_url, default_prefix=default_prefix)
        status = 1 if upstream_response.status_code < 400 else 0
        if gv.get('use_log'):
            SenderLogModel(
                ip=ip,
                status=status,
                error_msg='' if status else upstream_response.text[:2000],
            ).save()
        response = HttpResponse(
            content=upstream_response.content,
            status=upstream_response.status_code,
        )
        for key, value in upstream_response.headers.items():
            if key.lower() in RESPONSE_EXCLUDED_HEADERS:
                continue
            response[key] = value
        return response
    except requests.RequestException:
        error_msg = 'Error Binance Resender ' + traceback.format_exc()
        error_data = {'code': '-2', 'data': {}, 'msg': error_msg}
        if gv.get('use_log'):
            SenderLogModel(
                ip=ip,
                status=0,
                error_msg=error_msg,
            ).save()
        return JsonResponse(error_data, status=500)


@csrf_exempt
def api_handler(request, path):
    return base_api_handler(request, path, endpoint_name='api', default_prefix='api')


@csrf_exempt
def sapi_handler(request, path):
    return base_api_handler(request, path, endpoint_name='sapi', default_prefix='sapi', fallback_endpoint='api')


@csrf_exempt
def dapi_handler(request, path):
    return base_api_handler(request, path, endpoint_name='dapi', default_prefix='dapi')


@csrf_exempt
def eapi_handler(request, path):
    return base_api_handler(request, path, endpoint_name='eapi', default_prefix='eapi')


@csrf_exempt
def vapi_handler(request, path):
    return base_api_handler(request, path, endpoint_name='vapi', default_prefix='vapi', fallback_endpoint='eapi')


@csrf_exempt
def fapi_handler(request, path):
    return base_api_handler(request, path, endpoint_name='fapi', default_prefix='fapi')


@csrf_exempt
def papi_handler(request, path):
    return base_api_handler(request, path, endpoint_name='papi', default_prefix='papi')
