from unittest.mock import patch

from django.test import Client, TestCase

import appSite.globalvar as gv


class DummyUpstreamResponse:
    def __init__(self, status_code=200, content=b"{}", headers=None, text="{}"):
        self.status_code = status_code
        self.content = content
        self.headers = headers or {"Content-Type": "application/json"}
        self.text = text


class ResenderViewTests(TestCase):
    def setUp(self):
        gv.set("allowed_ips", ["127.0.0.1"])
        gv.set("use_log", 0)
        self.client = Client(REMOTE_ADDR="127.0.0.1")

    @patch("appSender.views.requests.request")
    def test_api_path_auto_prefix(self, request_mock):
        request_mock.return_value = DummyUpstreamResponse()

        response = self.client.get("/api/v3/time?recvWindow=5000&timestamp=1")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            request_mock.call_args.kwargs["url"],
            "https://api.binance.com/api/v3/time?recvWindow=5000&timestamp=1",
        )

    @patch("appSender.views.requests.request")
    def test_api_path_keep_existing_prefix(self, request_mock):
        request_mock.return_value = DummyUpstreamResponse()

        response = self.client.get("/api/api/v3/time")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            request_mock.call_args.kwargs["url"],
            "https://api.binance.com/api/v3/time",
        )

    @patch("appSender.views.requests.request")
    def test_sapi_route_forward_to_api_host(self, request_mock):
        request_mock.return_value = DummyUpstreamResponse()

        response = self.client.get("/sapi/v1/account/status?timestamp=1")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            request_mock.call_args.kwargs["url"],
            "https://api.binance.com/sapi/v1/account/status?timestamp=1",
        )

    @patch("appSender.views.requests.request")
    def test_post_keeps_raw_body_and_query(self, request_mock):
        request_mock.return_value = DummyUpstreamResponse()
        raw_body = b"symbol=BTCUSDT&side=BUY&quantity=0.01"

        response = self.client.generic(
            "POST",
            "/fapi/v1/order?timestamp=1&signature=abc",
            raw_body,
            content_type="application/x-www-form-urlencoded",
            HTTP_X_MBX_APIKEY="test-key",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            request_mock.call_args.kwargs["url"],
            "https://fapi.binance.com/fapi/v1/order?timestamp=1&signature=abc",
        )
        self.assertEqual(request_mock.call_args.kwargs["data"], raw_body)
        forwarded_headers = {
            key.lower(): value for key, value in request_mock.call_args.kwargs["headers"].items()
        }
        self.assertEqual(forwarded_headers["x-mbx-apikey"], "test-key")

    @patch("appSender.views.requests.request")
    def test_upstream_status_and_headers_passthrough(self, request_mock):
        request_mock.return_value = DummyUpstreamResponse(
            status_code=429,
            content=b'{"code":-1003,"msg":"Too many requests"}',
            headers={
                "Content-Type": "application/json",
                "Retry-After": "2",
                "Connection": "close",
            },
        )

        response = self.client.get("/api/v3/time")

        self.assertEqual(response.status_code, 429)
        self.assertEqual(response["Retry-After"], "2")
        self.assertNotIn("Connection", response)

    @patch("appSender.views.requests.request")
    def test_forbidden_ip(self, request_mock):
        gv.set("allowed_ips", ["10.1.1.1"])

        response = self.client.get("/api/v3/time")

        self.assertEqual(response.status_code, 403)
        request_mock.assert_not_called()
