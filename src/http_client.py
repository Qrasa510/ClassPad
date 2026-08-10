import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


RETRYABLE_STATUS_CODES = (429, 500, 502, 503, 504)


def create_retry_session(retries: int = 3, backoff_factor: float = 1.0) -> requests.Session:
    """Create a session that retries temporary network and server failures.

    Authentication and other permanent 4xx errors are deliberately not retried.
    """
    retry_policy = Retry(
        total=retries,
        connect=retries,
        read=retries,
        status=retries,
        allowed_methods=frozenset({"GET", "POST"}),
        status_forcelist=RETRYABLE_STATUS_CODES,
        backoff_factor=backoff_factor,
        respect_retry_after_header=True,
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry_policy)
    session = requests.Session()
    session.mount("https://", adapter)
    return session
