import os
import sqlite3
from datetime import datetime, timezone
from flask import Flask, jsonify, request

DB_PATH = os.getenv("DB_PATH", "/data/app.db")
BACKUP_DIR = os.getenv("BACKUP_DIR", "/backup")

app = Flask(__name__)


def get_conn():
    return sqlite3.connect(DB_PATH)


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL,
            message TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def get_event_count():
    init_db()
    conn = get_conn()
    cur = conn.execute("SELECT COUNT(*) FROM events")
    n = cur.fetchone()[0]
    conn.close()
    return n


def get_latest_backup_info():
    if not os.path.exists(BACKUP_DIR):
        return None, None

    if not os.path.isdir(BACKUP_DIR):
        return None, None

    backup_files = [
        os.path.join(BACKUP_DIR, f)
        for f in os.listdir(BACKUP_DIR)
        if f.endswith(".db")
    ]

    if not backup_files:
        return None, None

    latest_file = max(backup_files, key=os.path.getmtime)
    latest_mtime = os.path.getmtime(latest_file)

    now = datetime.now(timezone.utc).timestamp()
    age_seconds = int(now - latest_mtime)

    return os.path.basename(latest_file), age_seconds


@app.get("/")
def hello():
    init_db()
    return jsonify(status="Bonjour tout le monde !")


@app.get("/health")
def health():
    init_db()
    return jsonify(status="ok")


@app.get("/add")
def add():
    init_db()
    msg = request.args.get("message", "hello")
    ts = datetime.utcnow().isoformat() + "Z"

    conn = get_conn()
    conn.execute(
        "INSERT INTO events (ts, message) VALUES (?, ?)",
        (ts, msg)
    )
    conn.commit()
    conn.close()

    return jsonify(
        status="added",
        timestamp=ts,
        message=msg
    )


@app.get("/consultation")
def consultation():
    init_db()
    conn = get_conn()
    cur = conn.execute(
        "SELECT id, ts, message FROM events ORDER BY id DESC LIMIT 50"
    )
    rows = [
        {"id": r[0], "timestamp": r[1], "message": r[2]}
        for r in cur.fetchall()
    ]
    conn.close()
    return jsonify(rows)


@app.get("/count")
def count():
    return jsonify(count=get_event_count())


@app.get("/status")
def status():
    count_value = get_event_count()
    last_backup_file, backup_age_seconds = get_latest_backup_info()

    return jsonify(
        count=count_value,
        last_backup_file=last_backup_file,
        backup_age_seconds=backup_age_seconds
    )


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=8080)