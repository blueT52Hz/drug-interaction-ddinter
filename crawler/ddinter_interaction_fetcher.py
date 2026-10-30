"""
Fetch one DDInter interaction page through a given proxy and classify the outcome.

Outcomes of fetch_once():
    ("ok", record)        page parsed (record has RECORD_FIELDS)
    ("missing", None)     ID does not exist (404, or 500 "DoesNotExist")
    ("blocked", reason)   proxy refused / rate-limited: ProxyError, HTTP 403/407/429
    ("error", reason)     anything else (timeouts, other HTTP codes, unparseable page);
                          the worker treats a streak of errors as a block too
"""

import threading

import requests

from ddinter_interaction_page_parser import parse_interaction_page
from ddinter_proxy_pool import to_requests_proxies

BASE_URL = "https://ddinter2.scbdd.com/server/interact/{id}/"
# Block reason meaning the proxy itself is dead -> blocked permanently (persisted)
PROXY_DEAD_REASON = "ProxyError"
BLOCKED_STATUS_CODES = {403, 407, 429}
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/130.0 Safari/537.36"
)
_thread_local = threading.local()


def get_session() -> requests.Session:
    """One requests.Session per worker thread (Session is not thread-safe)."""
    if not hasattr(_thread_local, "session"):
        session = requests.Session()
        session.headers.update({"User-Agent": USER_AGENT})
        _thread_local.session = session
    return _thread_local.session


def fetch_once(interaction_id: int, proxy_url, timeout: float):
    """Single HTTP attempt; see module docstring for the returned (status, payload)."""
    url = BASE_URL.format(id=interaction_id)
    try:
        resp = get_session().get(url, proxies=to_requests_proxies(proxy_url), timeout=timeout)
    except requests.exceptions.ProxyError:
        return "blocked", PROXY_DEAD_REASON
    except requests.RequestException as exc:
        # Only the exception type: messages may contain the proxy URL with credentials
        return "error", type(exc).__name__

    if resp.status_code == 200:
        record = parse_interaction_page(resp.text, interaction_id)
        return ("ok", record) if record else ("error", "unparseable page")
    if resp.status_code == 404 or (resp.status_code == 500 and "DoesNotExist" in resp.text):
        return "missing", None
    if resp.status_code in BLOCKED_STATUS_CODES:
        return "blocked", f"HTTP {resp.status_code}"
    return "error", f"HTTP {resp.status_code}"
