"""Load the list of sites to monitor and runtime settings."""
import json
import os
from dataclasses import dataclass


@dataclass
class Site:
    name: str
    url: str
    timeout: float = 5.0
    expected_status: int = 200


def load_sites(path: str) -> list[Site]:
    """Read sites from a JSON file: [{"name": ..., "url": ...}, ...]."""
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    sites = [Site(**item) for item in raw]
    names = [s.name for s in sites]
    if len(names) != len(set(names)):
        raise ValueError("Site names must be unique")
    return sites


DB_PATH = os.getenv("UPTIME_DB", "uptime.db")
SITES_FILE = os.getenv("UPTIME_SITES", "sites.json")
INTERVAL_SECONDS = int(os.getenv("UPTIME_INTERVAL", "60"))
