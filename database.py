import sqlite3
import hashlib
import threading
from datetime import datetime
from config import SQLITE_DB

_lock = threading.Lock()


def get_connection():
    conn = sqlite3.connect(str(SQLITE_DB), timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


def init_db():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS marks (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            device      TEXT NOT NULL,
            mark_date   TEXT NOT NULL,
            event       TEXT,
            event_code  TEXT,
            dni         TEXT NOT NULL,
            raw_line    TEXT NOT NULL,
            file_name   TEXT NOT NULL,
            line_hash   TEXT NOT NULL UNIQUE,
            synced      INTEGER DEFAULT 0,
            error_msg   TEXT,
            created_at  TEXT NOT NULL,
            synced_at   TEXT
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_marks_synced ON marks(synced)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_marks_hash ON marks(line_hash)
    """)
    
    # Migración: Agregar event_code si no existe
    cursor = conn.execute("PRAGMA table_info(marks)")
    columns = [row[1] for row in cursor.fetchall()]
    if 'event_code' not in columns:
        print("[database] Migrando base de datos: Agregando columna 'event_code'")
        conn.execute("ALTER TABLE marks ADD COLUMN event_code TEXT")
        
    conn.commit()
    conn.close()


def make_hash(device, mark_date, dni):
    raw = f"{device}|{mark_date}|{dni}"
    return hashlib.sha256(raw.encode()).hexdigest()


def mark_exists(conn, line_hash):
    cursor = conn.execute("SELECT 1 FROM marks WHERE line_hash = ?", (line_hash,))
    return cursor.fetchone() is not None


def insert_mark(conn, device, mark_date, event, event_code, dni, raw_line, file_name):
    line_hash = make_hash(device, mark_date, dni)
    with _lock:
        if mark_exists(conn, line_hash):
            return False
        now = datetime.now().isoformat()
        conn.execute(
            """INSERT INTO marks (device, mark_date, event, event_code, dni, raw_line, file_name, line_hash, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (device, mark_date, event, event_code, dni, raw_line, file_name, line_hash, now),
        )
        conn.commit()
    return True


def get_pending_marks(conn, limit=50):
    cursor = conn.execute(
        "SELECT * FROM marks WHERE synced = 0 ORDER BY id ASC LIMIT ?",
        (limit,),
    )
    return [dict(row) for row in cursor.fetchall()]


def mark_synced(conn, mark_id):
    now = datetime.now().isoformat()
    with _lock:
        conn.execute(
            "UPDATE marks SET synced = 1, synced_at = ? WHERE id = ?",
            (now, mark_id),
        )
        conn.commit()


def mark_error(conn, mark_id, error_msg):
    with _lock:
        conn.execute(
            "UPDATE marks SET error_msg = ? WHERE id = ?",
            (error_msg, mark_id),
        )
        conn.commit()


def get_all_hashes(conn):
    cursor = conn.execute("SELECT line_hash FROM marks")
    return {row["line_hash"] for row in cursor.fetchall()}
