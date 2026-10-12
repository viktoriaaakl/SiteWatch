from datetime import datetime, timedelta, timezone

import requests

from uptime_monitor import alerts, storage
from uptime_monitor.checker import CheckResult, check_site
from uptime_monitor.config import Site
from uptime_monitor.monitor import run_once


class FakeResponse:
    def __init__(self, status_code):
        self.status_code = status_code


class FakeSession:
    """Returns a sequence of status codes, or raises for 'timeout'."""

    def __init__(self, outcomes):
        self.outcomes = list(outcomes)

    def get(self, url, timeout, headers=None):
        outcome = self.outcomes.pop(0)
        if outcome == "timeout":
            raise requests.Timeout()
        return FakeResponse(outcome)


SITE = Site(name="example", url="https://example.com")


def test_site_up_when_status_matches():
    result = check_site(SITE, FakeSession([200]))
    assert result.is_up and result.status_code == 200 and result.error is None


def test_site_down_on_wrong_status():
    result = check_site(SITE, FakeSession([503]))
    assert not result.is_up and "503" in result.error


def test_site_down_on_timeout():
    result = check_site(SITE, FakeSession(["timeout"]))
    assert not result.is_up and result.error == "Timeout"


def test_should_alert_only_on_state_change():
    assert alerts.should_alert(None, False) is True
    assert alerts.should_alert(None, True) is False
    assert alerts.should_alert(True, False) is True
    assert alerts.should_alert(False, False) is False
    assert alerts.should_alert(False, True) is True


def test_run_once_alerts_on_outage_and_recovery(tmp_path):
    conn = storage.connect(str(tmp_path / "test.db"))
    sent = []
    session = FakeSession([200, 500, 500, 200])
    for _ in range(4):
        run_once(conn, [SITE], session, notify=sent.append)
    assert len(sent) == 2
    assert sent[0].startswith("DOWN") and sent[1].startswith("RECOVERED")


def test_summary_calculates_uptime(tmp_path):
    conn = storage.connect(str(tmp_path / "test.db"))
    now = datetime.now(timezone.utc)
    for i, up in enumerate([True, True, True, False]):
        storage.save_check(conn, CheckResult("example", now - timedelta(minutes=i), up,
                                             200 if up else 500, 100.0 if up else None))
    s = storage.summary(conn, "example", now=now)
    assert s["checks"] == 4 and s["uptime_pct"] == 75.0 and s["avg_response_ms"] == 100.0
