from unittest.mock import Mock, patch

import requests
from django.test import Client, SimpleTestCase, override_settings

from .client import REQUEST_TIMEOUT


@override_settings(
    ALLOWED_HOSTS=["testserver"], CORS_ALLOWED_ORIGINS=["http://localhost:5173"]
)
class CameraAPITests(SimpleTestCase):
    start = "2026-09-29T00:00:00Z"
    end = "2026-09-30T00:00:00Z"

    def setUp(self):
        patcher = patch("cameras.client.requests.get")
        self.get = patcher.start()
        self.addCleanup(patcher.stop)
        self.get.return_value = Mock(status_code=200)
        self.get.return_value.json.return_value = {}
        self.auth = {"HTTP_AUTHORIZATION": "Bearer fake-token"}

    def test_login(self):
        for token in ("", "  ", "fake token", "fake\ntoken"):
            with self.subTest(token=repr(token)):
                self.assertEqual(
                    self.client.post("/api/login/", {"token": token}).status_code, 400
                )
        self.get.assert_not_called()

        self.get.return_value.json.return_value = {"email": "test@example.invalid"}
        response = Client(enforce_csrf_checks=True).post(
            "/api/login/", {"token": "fake-token"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["email"], "test@example.invalid")
        self.assertNotIn("sessionid", response.cookies)

    def test_auth(self):
        for scheme in ("Bearer", "PersonalAccessToken"):
            with self.subTest(scheme=scheme):
                response = self.client.get(
                    "/api/cameras/", HTTP_AUTHORIZATION=f"{scheme} fake-token"
                )
                self.assertEqual(response.status_code, 200)
                self.assertEqual(
                    self.get.call_args.kwargs["headers"],
                    {"Authorization": "PersonalAccessToken fake-token"},
                )
        self.assertEqual(self.get.call_args.kwargs["timeout"], REQUEST_TIMEOUT)
        self.assertFalse(self.get.call_args.kwargs["allow_redirects"])

    def test_auth_errors(self):
        for header in ("", "fake-token", "Basic fake-token", "Bearer", "Bearer a b"):
            with self.subTest(header=header):
                response = self.client.get("/api/cameras/", HTTP_AUTHORIZATION=header)
                self.assertEqual(response.status_code, 401)
                self.assertIn("WWW-Authenticate", response)
        self.get.assert_not_called()

    def test_methods(self):
        for route in ("recording-stream/1/", "recording-timeline/1/"):
            with self.subTest(route=route):
                response = self.client.post(f"/api/{route}", **self.auth)
                self.assertEqual(response.status_code, 405)
                self.assertEqual(response["Allow"], "GET")
        self.assertEqual(self.client.get("/api/login/").status_code, 405)
        self.get.assert_not_called()

    def test_streams(self):
        valid = {"url": "https://example.invalid/live.mp4", "format": "mp4"}
        cases = (
            ([None, "bad", {}, valid], 200, [valid]),
            ([], 200, []),
            (None, 502, None),
        )
        for streams, status, expected in cases:
            with self.subTest(streams=streams):
                self.get.return_value.json.return_value = {"streams": streams}
                response = self.client.get("/api/stream/1/", **self.auth)
                self.assertEqual(response.status_code, status)
                if status == 200:
                    self.assertEqual(response.json(), {"stream_details": expected})

    def test_dates(self):
        cases = (
            {},
            {"start": self.start},
            {"start": "bad", "end": self.end},
            {"start": "2026-09-29T00:00:00", "end": self.end},
            {"start": "2026-02-30T00:00:00Z", "end": self.end},
            {"start": self.end, "end": self.start},
            {"start": self.start, "end": self.start},
            {"start": "2026-09-29T02:00:00+02:00", "end": self.start},
        )
        for params in cases:
            with self.subTest(params=params):
                self.assertEqual(
                    self.client.get(
                        "/api/recording-timeline/1/", params, **self.auth
                    ).status_code,
                    400,
                )
        self.get.assert_not_called()

    def test_ranges(self):
        cases = (
            (
                "recording-timeline/1/",
                {"start": "2026-09-29T00:00:00-05:00", "end": self.end},
            ),
            ("recording-stream/1/", {"start": self.start}),
        )
        for route, params in cases:
            with self.subTest(route=route):
                response = self.client.get(f"/api/{route}", params, **self.auth)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(self.get.call_args.kwargs["params"], params)

    def test_network(self):
        for exception, status in (
            (requests.Timeout(), 504),
            (requests.ConnectionError(), 502),
        ):
            with self.subTest(exception=type(exception).__name__):
                self.get.side_effect = exception
                self.assertEqual(
                    self.client.get("/api/cameras/", **self.auth).status_code, status
                )

    def test_upstream_errors(self):
        self.get.return_value.json.return_value = {"sensitive": "private upstream data"}
        for upstream, expected in (
            (400, 400),
            (401, 401),
            (403, 403),
            (404, 404),
            (429, 429),
            (503, 502),
            (302, 502),
        ):
            with self.subTest(upstream=upstream):
                self.get.return_value.status_code = upstream
                response = self.client.get("/api/cameras/", **self.auth)
                self.assertEqual(response.status_code, expected)
                self.assertNotIn("private upstream data", response.content.decode())
                self.assertEqual(response["Cache-Control"], "no-store")
        self.get.return_value.json.assert_not_called()

    def test_json(self):
        self.get.return_value.json.side_effect = ValueError("HTML instead of JSON")
        self.assertEqual(self.client.get("/api/cameras/", **self.auth).status_code, 502)
        self.get.return_value.json.side_effect = None
        for payload in (None, [], "unexpected"):
            with self.subTest(payload=payload):
                self.get.return_value.json.return_value = payload
                self.assertEqual(
                    self.client.get("/api/cameras/", **self.auth).status_code, 502
                )

    def test_cors(self):
        response = self.client.options(
            "/api/cameras/",
            HTTP_ORIGIN="http://localhost:5173",
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="GET",
            HTTP_ACCESS_CONTROL_REQUEST_HEADERS="authorization",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Access-Control-Allow-Origin"], "http://localhost:5173"
        )
        response = self.client.get("/api/cameras/", HTTP_ORIGIN="http://localhost:5173")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response["Access-Control-Allow-Origin"], "http://localhost:5173"
        )
        response = self.client.get(
            "/api/cameras/", HTTP_ORIGIN="https://untrusted.example"
        )
        self.assertNotIn("Access-Control-Allow-Origin", response)
