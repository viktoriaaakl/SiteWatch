"""SQLite storage for check results."""
import sqlite3
from datetime import datetime, timedelta, timezone

SCHEMA = """
CREATE TABLE IF NOT EXISTS checks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    site TEXT NOT NULL,
    checked_at TEXT NOT NULL,
    is_up INTEGER NOT NULL,
    status_code INTEGER,
    response_ms REAL,
    error TEXT
);
CREATE INDEX IF NOT EXISTS idx_checks_site_time ON checks (site, checked_at);
"""


def connect(path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def save_check(conn, result) -> None:
    conn.execute(
        "INSERT INTO checks (site, checked_at, is_up, status_code, response_ms, error) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (result.site, result.checked_at.isoformat(), int(result.is_up),
         result.status_code, result.response_ms, result.error),
    )
    conn.commit()


def last_status(conn, site: str) -> bool | None:
    """Return True/False for the latest check, or None if never checked."""
    row = conn.execute(
        "SELECT is_up FROM checks WHERE site = ? ORDER BY id DESC LIMIT 1", (site,)
    ).fetchone()
    return None if row is None else bool(row["is_up"])


def summary(conn, site: str, hours: int = 24, now: datetime | None = None) -> dict:
    """Uptime %, average response time and check count for the last `hours`."""
    now = now or datetime.now(timezone.utc)
    since = (now - timedelta(hours=hours)).isoformat()
    row = conn.execute(
        "SELECT COUNT(*) AS n, SUM(is_up) AS up, AVG(CASE WHEN is_up THEN response_ms END) AS avg_ms "
        "FROM checks WHERE site = ? AND checked_at >= ?",
        (site, since),
    ).fetchone()
    n = row["n"] or 0
    uptime = round(100 * (row["up"] or 0) / n, 2) if n else None
    avg_ms = round(row["avg_ms"], 1) if row["avg_ms"] is not None else None
    return {"site": site, "checks": n, "uptime_pct": uptime, "avg_response_ms": avg_ms}
