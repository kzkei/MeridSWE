"""Unit tests for ApiClient class and health_check func"""

import json
from typing import Optional
import unittest
from unittest.mock import MagicMock, patch
import requests
from src.utils.client import ApiClient, health_check


def _mock_response(
    *,
    status_code: int = 200,
    text: str = "{}",
    headers: Optional[dict]  = None,
) -> MagicMock:
    response = MagicMock()
    response.status_code = status_code
    response.text = text
    response.headers = headers or {}
    response.json.return_value = json.loads(text)
    return response


class TestApiClientRequest(unittest.TestCase):
    @patch("src.utils.client.requests.Session.request")
    def test_request_sends_authorization_in_headers(self, mock_request: MagicMock) -> None:
        mock_request.return_value = _mock_response()

        client = ApiClient("https://example.com", "sa_test_key")
        client.request("GET", "/api/v1/foo")

        mock_request.assert_called_once()
        _, kwargs = mock_request.call_args
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer sa_test_key")

    @patch("src.utils.client.requests.Session.request")
    def test_request_does_not_put_auth_in_query_params(self, mock_request: MagicMock) -> None:
        """Regression: headers must be passed as headers=, not a positional arg."""
        mock_request.return_value = _mock_response()

        client = ApiClient("https://example.com", "sa_test_key")
        client.request("GET", "/api/v1/foo")

        call_args, call_kwargs = mock_request.call_args
        self.assertEqual(call_args[0], "GET")
        self.assertEqual(call_args[1], "https://example.com/api/v1/foo")
        self.assertIn("headers", call_kwargs)
        self.assertEqual(call_kwargs["headers"]["Authorization"], "Bearer sa_test_key")

    @patch("src.utils.client.requests.Session.request")
    def test_request_strips_trailing_slash_from_base_url(self, mock_request: MagicMock) -> None:
        mock_request.return_value = _mock_response()

        client = ApiClient("https://example.com/", "sa_test_key")
        client.request("GET", "/api/v1/bar")

        call_args, _ = mock_request.call_args
        self.assertEqual(call_args[1], "https://example.com/api/v1/bar")

    @patch("src.utils.client.requests.Session.request")
    def test_request_merges_extra_headers(self, mock_request: MagicMock) -> None:
        mock_request.return_value = _mock_response()

        client = ApiClient("https://example.com", "sa_test_key")
        client.request("GET", "/api/v1/foo", headers={"Accept": "application/json"})

        _, kwargs = mock_request.call_args
        self.assertEqual(kwargs["headers"]["Accept"], "application/json")
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer sa_test_key")

    @patch("src.utils.client.requests.Session.request")
    def test_request_returns_response(self, mock_request: MagicMock) -> None:
        expected = _mock_response(status_code=201, text='{"ok": true}')
        mock_request.return_value = expected

        client = ApiClient("https://example.com", "sa_test_key")
        response = client.request("POST", "/api/v1/submit", json={"type": "probe"})

        self.assertIs(response, expected)


class TestApiClientHelpers(unittest.TestCase):
    def test_safe_headers_redacts_authorization(self) -> None:
        client = ApiClient("https://example.com", "sa_secret")
        redacted = client.safe_headers(
            {"Authorization": "Bearer sa_secret", "Accept": "application/json"}
        )

        self.assertEqual(redacted["Authorization"], "<REDACTED>")
        self.assertEqual(redacted["Accept"], "application/json")

    def test_safe_headers_leaves_headers_without_auth_untouched(self) -> None:
        client = ApiClient("https://example.com", "sa_secret")
        headers = {"Accept": "application/json"}

        self.assertEqual(client.safe_headers(headers), headers)

    def test_truncate_body_unchanged_when_short(self) -> None:
        client = ApiClient("https://example.com", "sa_test_key")
        body = "short response"

        self.assertEqual(client.truncate_body(body), body)

    def test_truncate_body_truncates_when_long(self) -> None:
        client = ApiClient("https://example.com", "sa_test_key")
        body = "x" * 15_000

        result = client.truncate_body(body)

        self.assertLess(len(result), len(body))
        self.assertTrue(result.startswith("x" * 10_000))
        self.assertIn("truncated from 15000 total characters", result)


class TestHealthCheck(unittest.TestCase):
    @patch("src.utils.client.requests.get")
    def test_health_check_hits_unauthenticated_endpoint(self, mock_get: MagicMock) -> None:
        mock_get.return_value = _mock_response(text='{"status": "ok"}')

        result = health_check("https://example.com/")

        mock_get.assert_called_once_with(
            url="https://example.com/api/v1/health",
            timeout=10,
        )
        self.assertEqual(result, {"status": "ok"})

    @patch("src.utils.client.requests.get")
    def test_health_check_raises_on_non_2xx(self, mock_get: MagicMock) -> None:
        response = _mock_response(status_code=503, text='{"error": "unavailable"}')
        response.raise_for_status.side_effect = requests.HTTPError("503")
        mock_get.return_value = response

        with self.assertRaises(requests.HTTPError):
            health_check("https://example.com")


if __name__ == "__main__":
    unittest.main()
