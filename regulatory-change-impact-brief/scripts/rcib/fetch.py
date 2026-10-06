"""Read-only HTTP access. No credentials, cookies or auth headers are ever sent (decision D-003)."""

from __future__ import annotations

import urllib.error
import urllib.request
from dataclasses import dataclass, field

from .util import utc_now

USER_AGENT = "regulatory-change-impact-brief/1.0 (read-only compliance review; contact: Quillhaven Operations)"
TIMEOUT_S = 45


@dataclass
class Response:
    method: str
    url: str
    requested_at: str
    status: int | None = None
    final_url: str | None = None
    content_type: str | None = None
    headers: dict = field(default_factory=dict)
    data: bytes | None = None
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None and self.status == 200 and self.data is not None


def request(url: str, method: str = "GET", body: bytes | None = None, content_type: str | None = None) -> Response:
    """Perform one read-only request. GET everywhere, except the read-only page-load POST the
    Notion page client itself uses (it changes nothing on the server)."""
    if method not in ("GET", "POST"):
        raise ValueError("only read-only GET/POST requests are permitted")
    resp = Response(method=method, url=url, requested_at=utc_now())
    headers = {"User-Agent": USER_AGENT, "Accept": "*/*"}
    if content_type:
        headers["Content-Type"] = content_type
    req = urllib.request.Request(url, data=body, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_S) as r:
            resp.status = r.status
            resp.final_url = r.geturl()
            resp.headers = {k.lower(): v for k, v in r.headers.items()}
            resp.content_type = resp.headers.get("content-type")
            resp.data = r.read()
    except urllib.error.HTTPError as e:
        resp.status = e.code
        resp.final_url = e.geturl()
        resp.headers = {k.lower(): v for k, v in (e.headers or {}).items()}
        resp.content_type = resp.headers.get("content-type")
        resp.error = f"HTTP {e.code} {e.reason}"
    except Exception as e:  # network, TLS, timeout
        resp.error = f"{type(e).__name__}: {e}"
    return resp
