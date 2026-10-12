"""Perform a single HTTP health check."""
import time
from dataclasses import dataclass
from datetime import datetime, timezone

import requests

from .config import Site


@dataclass
class CheckResult:
    site: str
    checked_at: datetime
    is_up: bool
    status_code: int | None
    response_ms: float | None
    error: str | None = None


def check_site(site: Site, session: requests.Session | None = None) -> CheckResult:
    """Send a GET request and decide whether the site is up."""
    http = session or requests
    started = time.perf_counter()
    now = datetime.now(timezone.utc)
    try:
        resp = http.get(site.url, timeout=site.timeout, headers={"User-Agent": "uptime-monitor/1.0"})
        elapsed = (time.perf_counter() - started) * 1000
        is_up = resp.status_code == site.expected_status
        error = None if is_up else f"Unexpected status {resp.status_code}"
        return CheckResult(site.name, now, is_up, resp.status_code, round(elapsed, 1), error)
    except requests.RequestException as exc:
        return CheckResult(site.name, now, False, None, None, type(exc).__name__)
