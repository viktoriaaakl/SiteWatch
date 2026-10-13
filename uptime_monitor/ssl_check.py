"""Warn before a site's SSL certificate expires."""
import socket
import ssl
from datetime import datetime, timezone
from urllib.parse import urlparse

WARN_DAYS = 14


def cert_expiry(hostname: str, port: int = 443, timeout: float = 5.0) -> datetime:
    """Connect over TLS and return the certificate's expiry date (UTC)."""
    context = ssl.create_default_context()
    with socket.create_connection((hostname, port), timeout=timeout) as sock:
        with context.wrap_socket(sock, server_hostname=hostname) as tls:
            not_after = tls.getpeercert()["notAfter"]
    return datetime.fromtimestamp(ssl.cert_time_to_seconds(not_after), tz=timezone.utc)


def days_left(expires: datetime, now: datetime | None = None) -> int:
    now = now or datetime.now(timezone.utc)
    return (expires - now).days


def check_certificates(sites, notify, get_expiry=cert_expiry, warn_days: int = WARN_DAYS) -> dict:
    """Check every https site; alert if a certificate expires soon or can't be read."""
    report = {}
    for site in sites:
        url = urlparse(site.url)
        if url.scheme != "https":
            continue
        try:
            left = days_left(get_expiry(url.hostname, url.port or 443))
        except (OSError, ssl.SSLError, KeyError, ValueError) as exc:
            notify(f"SSL CHECK FAILED: {site.name} ({type(exc).__name__})")
            report[site.name] = None
            continue
        report[site.name] = left
        if left < warn_days:
            notify(f"SSL EXPIRING: {site.name} certificate expires in {left} days")
    return report
