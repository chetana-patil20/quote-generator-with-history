from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import requests
from flask import Flask, jsonify, render_template, request

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_QUOTES = [
    {"quote": "Great things are done by a series of small things brought together.", "author": "Vincent van Gogh"},
    {"quote": "It always seems impossible until it's done.", "author": "Nelson Mandela"},
    {"quote": "The secret of getting ahead is getting started.", "author": "Mark Twain"},
    {"quote": "Success is the sum of small efforts, repeated day in and day out.", "author": "Robert Collier"},
    {"quote": "Believe you can and you're halfway there.", "author": "Theodore Roosevelt"},
]


def get_db(db_path: str | Path | None = None) -> sqlite3.Connection:
    path = Path(db_path or os.environ.get("QUOTE_DB_PATH", BASE_DIR / "quotes.db"))
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str | Path | None = None) -> None:
    with get_db(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS quote_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quote TEXT NOT NULL,
                author TEXT NOT NULL,
                source TEXT NOT NULL DEFAULT 'api',
                created_at TEXT NOT NULL
            )
        """)


def fetch_random_quote() -> tuple[dict, str]:
    """Fetch from a public API; fall back to a bundled quote if the API is unavailable."""
    try:
        response = requests.get("https://dummyjson.com/quotes/random", timeout=5)
        response.raise_for_status()
        payload = response.json()
        quote = str(payload.get("quote", "")).strip()
        author = str(payload.get("author", "Unknown")).strip() or "Unknown"
        if quote:
            return {"quote": quote, "author": author}, "api"
    except (requests.RequestException, ValueError, TypeError):
        pass

    # Deterministic fallback based on time so the page still works offline.
    item = DEFAULT_QUOTES[int(datetime.now().timestamp()) % len(DEFAULT_QUOTES)]
    return dict(item), "fallback"


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.environ.get("FLASK_SECRET_KEY", "change-this-development-secret"),
        DATABASE=str(BASE_DIR / "quotes.db"),
        JSON_SORT_KEYS=False,
    )
    if test_config:
        app.config.update(test_config)
    init_db(app.config["DATABASE"])

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.post("/api/quotes/random")
    def random_quote():
        quote, source = fetch_random_quote()
        created_at = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
        with get_db(app.config["DATABASE"]) as conn:
            cursor = conn.execute(
                "INSERT INTO quote_history (quote, author, source, created_at) VALUES (?, ?, ?, ?)",
                (quote["quote"], quote["author"], source, created_at),
            )
            quote_id = cursor.lastrowid
        return jsonify({"id": quote_id, **quote, "source": source, "created_at": created_at})

    @app.get("/api/history")
    def history():
        try:
            limit = min(max(int(request.args.get("limit", 20)), 1), 100)
        except ValueError:
            limit = 20
        with get_db(app.config["DATABASE"]) as conn:
            rows = conn.execute(
                "SELECT id, quote, author, source, created_at FROM quote_history ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return jsonify([dict(row) for row in rows])

    @app.delete("/api/history")
    def clear_history():
        with get_db(app.config["DATABASE"]) as conn:
            conn.execute("DELETE FROM quote_history")
        return jsonify({"message": "History cleared."})

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok", "database": "sqlite"})

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "5000")), debug=True)
