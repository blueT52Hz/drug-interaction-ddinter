"""
Proxy pool with exclusive assignment: each worker thread owns one proxy and
keeps it until the proxy gets blocked, then acquires a fresh, never-used one.

States of a proxy during a run:
    unused  -> waiting in the pool
    in use  -> handed to a worker by acquire() (never handed out twice)
    blocked -> reported by mark_blocked(); never reused in this run

Permanently blocked proxies (dead proxy: ProxyError) are also appended to blocked_file
("<user@host:port>\t<time>\t<reason>", no password) and skipped on later runs; delete a
line to allow that proxy again. Temporary blocks (HTTP 403/429, error streaks) only
last for the current run.

Supported proxy.txt line formats (blank lines and '#' comments are ignored):
    host:port
    host:port:user:password
    scheme://[user:password@]host:port   (socks5://... needs requests[socks])
Credentials are never included in error messages or logs.
"""

import threading
from collections import deque
from datetime import datetime
from pathlib import Path
from urllib.parse import quote, unquote


def parse_proxy_line(line: str, line_no: int):
    """Convert one proxy.txt line into a proxy URL, or None for blank/comment lines."""
    line = line.strip()
    if not line or line.startswith("#"):
        return None
    if "://" in line:
        return line
    parts = line.split(":")
    if len(parts) == 2:
        host, port = parts
        return f"http://{host}:{port}"
    if len(parts) == 4:
        host, port, user, password = parts
        return f"http://{quote(user, safe='')}:{quote(password, safe='')}@{host}:{port}"
    raise ValueError(f"Invalid proxy format on line {line_no} (expected host:port[:user:pass])")


def mask_proxy_url(proxy_url) -> str:
    """Hide credentials: http://user:pass@host:port -> http://***@host:port."""
    if proxy_url is None:
        return "direct"
    if "@" not in proxy_url:
        return proxy_url
    scheme, _, rest = proxy_url.partition("://")
    return f"{scheme}://***@{rest.rsplit('@', 1)[1]}"


def to_requests_proxies(proxy_url):
    """requests-style proxies dict, or None for a direct connection."""
    return {"http": proxy_url, "https": proxy_url} if proxy_url else None


def proxy_key(proxy_url: str) -> str:
    """Identify a proxy without its password: 'user@host:port' or 'host:port'."""
    rest = proxy_url.partition("://")[2] or proxy_url
    if "@" not in rest:
        return rest
    credentials, host_port = rest.rsplit("@", 1)
    return f"{unquote(credentials.split(':', 1)[0])}@{host_port}"


def load_blocked_keys(blocked_file) -> set:
    """Proxy keys listed in blocked_file (first tab-separated field of each line)."""
    if not blocked_file or not blocked_file.exists():
        return set()
    with blocked_file.open(encoding="utf-8") as f:
        return {line.split("\t", 1)[0].strip() for line in f if line.strip() and not line.startswith("#")}


class ProxyPool:
    def __init__(self, proxy_urls, blocked_file: Path = None):
        self.blocked_file = blocked_file
        all_urls = list(dict.fromkeys(proxy_urls))  # dedupe, keep file order
        blocked_before = load_blocked_keys(blocked_file)
        self.skipped_blocked = [u for u in all_urls if proxy_key(u) in blocked_before]
        self.proxy_urls = [u for u in all_urls if proxy_key(u) not in blocked_before]
        self._unused = deque(self.proxy_urls)
        self.in_use = set()
        self.blocked = {}  # proxy_url -> reason (blocked during this run)
        self._lock = threading.Lock()

    @classmethod
    def from_file(cls, path: Path, blocked_file: Path = None):
        with path.open(encoding="utf-8") as f:
            urls = [parse_proxy_line(line, i) for i, line in enumerate(f, start=1)]
        return cls((url for url in urls if url), blocked_file)

    def _append_blocked_file(self, proxy_url: str, reason: str):
        """Persist a blocked proxy (caller holds the lock). A write error must not stop the crawl."""
        if not self.blocked_file:
            return
        try:
            self.blocked_file.parent.mkdir(parents=True, exist_ok=True)
            with self.blocked_file.open("a", encoding="utf-8") as f:
                f.write(f"{proxy_key(proxy_url)}\t{datetime.now().isoformat(timespec='seconds')}\t{reason}\n")
        except OSError as exc:
            print(f"WARNING: cannot write {self.blocked_file}: {exc}")

    def acquire(self):
        """Take the next never-used proxy and mark it in use; None when the pool is exhausted."""
        with self._lock:
            if not self._unused:
                return None
            proxy_url = self._unused.popleft()
            self.in_use.add(proxy_url)
            return proxy_url

    def mark_blocked(self, proxy_url: str, reason: str, permanent: bool):
        """Never hand this proxy out again in this run; if permanent, also persist it to blocked_file."""
        with self._lock:
            self.in_use.discard(proxy_url)
            self.blocked[proxy_url] = reason
            if permanent:
                self._append_blocked_file(proxy_url, reason)

    def unused_count(self) -> int:
        with self._lock:
            return len(self._unused)

    def describe(self) -> str:
        with self._lock:
            return (f"{len(self.proxy_urls)} proxies: {len(self.in_use)} in use, "
                    f"{len(self._unused)} unused, {len(self.blocked)} blocked this run "
                    f"(+{len(self.skipped_blocked)} skipped, blocked earlier)")
