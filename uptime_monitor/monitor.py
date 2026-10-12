"""Main loop: check every site, store results, alert on changes."""
import argparse
import logging
import time

import requests

from . import alerts, storage
from .checker import check_site
from .config import DB_PATH, INTERVAL_SECONDS, SITES_FILE, load_sites

log = logging.getLogger(__name__)


def run_once(conn, sites, session=None, notify=alerts.send_alert) -> list:
    results = []
    for site in sites:
        previous = storage.last_status(conn, site.name)
        result = check_site(site, session)
        storage.save_check(conn, result)
        if alerts.should_alert(previous, result.is_up):
            notify(alerts.format_message(result))
        log.info("%s up=%s %s ms", site.name, result.is_up, result.response_ms)
        results.append(result)
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Website uptime monitor")
    parser.add_argument("--once", action="store_true", help="run a single round of checks")
    parser.add_argument("--interval", type=int, default=INTERVAL_SECONDS)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    sites = load_sites(SITES_FILE)
    conn = storage.connect(DB_PATH)
    session = requests.Session()
    while True:
        run_once(conn, sites, session)
        if args.once:
            break
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
