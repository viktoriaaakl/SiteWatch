import json
from datetime import datetime, timezone

from uptime_monitor import storage
from uptime_monitor.checker import CheckResult
from uptime_monitor.dashboard import create_app


def test_api_status(tmp_path):
    sites = tmp_path / "sites.json"
    sites.write_text(json.dumps([{"name": "example", "url": "https://example.com"}]))
    db = tmp_path / "t.db"
    conn = storage.connect(str(db))
    storage.save_check(conn, CheckResult("example", datetime.now(timezone.utc), True, 200, 50.0))
    client = create_app(str(db), str(sites)).test_client()
    data = client.get("/api/status").get_json()
    assert data[0]["is_up"] is True and data[0]["uptime_pct"] == 100.0
    assert client.get("/").status_code == 200
