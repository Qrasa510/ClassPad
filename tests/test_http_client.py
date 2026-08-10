import unittest

from requests.adapters import HTTPAdapter

from src.http_client import RETRYABLE_STATUS_CODES, create_retry_session


class HttpClientTests(unittest.TestCase):
    def test_retry_policy_only_retries_temporary_statuses(self):
        session = create_retry_session(retries=3, backoff_factor=1)
        adapter = session.get_adapter("https://")
        self.assertIsInstance(adapter, HTTPAdapter)
        retry = adapter.max_retries
        self.assertEqual(retry.total, 3)
        self.assertIn("POST", retry.allowed_methods)
        self.assertEqual(tuple(retry.status_forcelist), RETRYABLE_STATUS_CODES)
        self.assertNotIn(401, retry.status_forcelist)
        self.assertNotIn(403, retry.status_forcelist)


if __name__ == "__main__":
    unittest.main()
