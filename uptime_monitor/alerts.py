"""Send alerts when a site changes state (up -> down or down -> up)."""
import logging
import os
import smtplib
from email.message import EmailMessage

import requests

log = logging.getLogger(__name__)


def should_alert(previous: bool | None, current: bool) -> bool:
    """Alert only on a change of state, so a long outage doesn't spam alerts.

    The very first check alerts only if the site is down.
    """
    if previous is None:
        return not current
    return previous != current


def format_message(result) -> str:
    if result.is_up:
        return f"RECOVERED: {result.site} is back up ({result.response_ms} ms)"
    return f"DOWN: {result.site} is not responding ({result.error})"


def send_alert(text: str) -> None:
    """Send via Telegram and/or email if configured; always log."""
    log.warning(text)
    token, chat_id = os.getenv("TELEGRAM_BOT_TOKEN"), os.getenv("TELEGRAM_CHAT_ID")
    if token and chat_id:
        try:
            requests.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                data={"chat_id": chat_id, "text": text},
                timeout=10,
            )
        except requests.RequestException:
            log.exception("Telegram alert failed")
    host = os.getenv("SMTP_HOST")
    if host:
        msg = EmailMessage()
        msg["Subject"] = text
        msg["From"] = os.environ["ALERT_FROM"]
        msg["To"] = os.environ["ALERT_TO"]
        msg.set_content(text)
        try:
            with smtplib.SMTP(host, int(os.getenv("SMTP_PORT", "587"))) as smtp:
                smtp.starttls()
                smtp.login(os.environ["SMTP_USER"], os.environ["SMTP_PASSWORD"])
                smtp.send_message(msg)
        except (smtplib.SMTPException, OSError):
            log.exception("Email alert failed")
