"""Small Flask dashboard showing uptime for each site."""
from flask import Flask, jsonify, render_template

from . import storage
from .config import DB_PATH, SITES_FILE, load_sites


def create_app(db_path: str = DB_PATH, sites_file: str = SITES_FILE) -> Flask:
    app = Flask(__name__)

    def collect():
        conn = storage.connect(db_path)
        rows = []
        for site in load_sites(sites_file):
            row = storage.summary(conn, site.name)
            row["url"] = site.url
            row["is_up"] = storage.last_status(conn, site.name)
            rows.append(row)
        conn.close()
        return rows

    @app.get("/")
    def index():
        return render_template("index.html", rows=collect())

    @app.get("/api/status")
    def api_status():
        return jsonify(collect())

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app


if __name__ == "__main__":
    create_app().run(host="0.0.0.0", port=8000)
