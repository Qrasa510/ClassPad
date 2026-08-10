import unittest

import requests

from src.canvas_client import CanvasAuthError, CanvasClient, CanvasError
from src.models import PushTarget


def make_response(status_code=200):
    response = requests.Response()
    response.status_code = status_code
    response.url = "https://example.test/canvas"
    return response


class FakeSession:
    def __init__(self, response=None, error=None):
        self.response = response if response is not None else make_response()
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
            CanvasClient(FakeSession(make_response(401))).push(
                self.target, self.data, 15
            )

    def test_network_error_is_wrapped(self):
        with self.assertRaises(CanvasError):
            CanvasClient(FakeSession(error=requests.Timeout("timeout"))).push(
                self.target, self.data, 15
            )


if __name__ == "__main__":
    unittest.main()
