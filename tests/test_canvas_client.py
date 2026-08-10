import unittest

import requests

from src.canvas_client import CanvasAuthError, CanvasClient, CanvasError
from src.models import PushTarget


class FakeResponse:
    def __init__(self, status_code=200):
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            error = requests.HTTPError(f"HTTP {self.status_code}")
            error.response = self
            raise error


class FakeSession:
    def __init__(self, response=None, error=None):
        self.response = response or FakeResponse()
        self.error = error
        self.calls = []

    def post(self, url, **kwargs):
        self.calls.append((url, kwargs))
        if self.error:
            raise self.error
        return self.response


class CanvasClientTests(unittest.TestCase):
    def setUp(self):
        self.target = PushTarget("secret", "device", "Owner")
        self.data = {
            "course": "Math",
            "courseTime": "08:00 — 08:45",
            "remaining": "10",
            "progress": "50",
        }

    def test_successful_push_uses_expected_auth_header(self):
        session = FakeSession()
        CanvasClient(session).push(self.target, self.data, 15)
        self.assertEqual(
            session.calls[0][1]["headers"]["Authorization"], "Bearer secret"
        )

    def test_authentication_error_is_not_generic(self):
        with self.assertRaises(CanvasAuthError):
            CanvasClient(FakeSession(FakeResponse(401))).push(
                self.target, self.data, 15
            )

    def test_network_error_is_wrapped(self):
        with self.assertRaises(CanvasError):
            CanvasClient(FakeSession(error=requests.Timeout("timeout"))).push(
                self.target, self.data, 15
            )


if __name__ == "__main__":
    unittest.main()
