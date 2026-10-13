from datetime import datetime, timedelta, timezone

from uptime_monitor.config import Site
from uptime_monitor.ssl_check import check_certificates, days_left

NOW = datetime.now(timezone.utc)


def expiry_in(days):
    return lambda host, port: NOW + timedelta(days=days, hours=1)


def test_days_left():
    assert days_left(NOW + timedelta(days=30, hours=1), NOW) == 30


def test_no_alert_when_certificate_is_fine():
    alerts = []
    report = check_certificates([Site("a", "https://a.com")], alerts.append, expiry_in(60))
    assert report == {"a": 60} and alerts == []


def test_alert_when_certificate_expires_soon():
    alerts = []
    check_certificates([Site("a", "https://a.com")], alerts.append, expiry_in(5))
    assert alerts == ["SSL EXPIRING: a certificate expires in 5 days"]


def test_alert_when_certificate_cannot_be_read():
    def broken(host, port):
        raise OSError("connection refused")

    alerts = []
    report = check_certificates([Site("a", "https://a.com")], alerts.append, broken)
    assert report == {"a": None} and "SSL CHECK FAILED" in alerts[0]


def test_http_sites_are_skipped():
    alerts = []
    report = check_certificates([Site("a", "http://a.com")], alerts.append, expiry_in(1))
    assert report == {} and alerts == []
