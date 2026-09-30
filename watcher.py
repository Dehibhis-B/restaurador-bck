import json
import time
from pathlib import Path
from datetime import datetime
from config import BACKUP_DIR, POINTER_FILE, POLL_INTERVAL
from database import get_connection, init_db, insert_mark, get_all_hashes, make_hash
from parser import parse_bck_line
import syncer


def load_pointer():
    if POINTER_FILE.exists():
        with open(POINTER_FILE) as f:
            return json.load(f)
    return {}


def save_pointer(pointer):
    POINTER_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(POINTER_FILE, "w") as f:
        json.dump(pointer, f, indent=2)


def get_today_filename():
    now = datetime.now()
    return f"01_{now.strftime('%d%m%y')}.bck"


def scan_file(conn, filepath, pointer, existing_hashes):
    pointer_key = str(filepath.resolve())
    if not filepath.exists():
        return 0

    with open(filepath, "r") as f:
        lines = f.readlines()

    last_line = pointer.get(pointer_key, 0)
    if last_line >= len(lines):
        return 0

    count = 0
    for i in range(last_line, len(lines)):
        raw = lines[i]
        parsed = parse_bck_line(raw)
        if parsed is None:
            continue

        lh = make_hash(parsed["device"], parsed["mark_date"], parsed["dni"])
        if lh in existing_hashes:
            continue

        inserted = insert_mark(
            conn,
            device=parsed["device"],
            mark_date=parsed["mark_date"],
            event=parsed["event"],
            event_code=parsed["event_code"],
            dni=parsed["dni"],
            raw_line=parsed["raw_line"],
            file_name=filepath.name,
        )
        if inserted:
            count += 1
            existing_hashes.add(lh)

    pointer[pointer_key] = len(lines)
    save_pointer(pointer)
    return count


def watch_loop():
    init_db()
    pointer = load_pointer()
    conn = get_connection()
    existing_hashes = get_all_hashes(conn)

    last_date = None
    today_file = None
    first = True
    refresh_token_at = 0

    while True:
        if not first:
            time.sleep(POLL_INTERVAL)
        first = False

        try:
            new_date = datetime.now().strftime('%d%m%y')
            if new_date != last_date:
                if today_file:
                    print(f"[watcher] Día cambiado: {today_file.name} -> 01_{new_date}.bck")
                syncer.token = None
                last_date = new_date
                today_file = BACKUP_DIR / f"01_{new_date}.bck"
                pointer_key = str(today_file.resolve())
                if pointer_key not in pointer:
                    pointer[pointer_key] = 0
                print(f"[watcher] Monitoreando: {today_file.name}")

            now_ts = time.time()
            if now_ts > refresh_token_at:
                syncer.token = None
                refresh_token_at = now_ts + 3600

            count = scan_file(conn, today_file, pointer, existing_hashes)
            if count > 0:
                print(f"[watcher] {today_file.name}: +{count} marcas")

        except Exception as e:
            print(f"[watcher] Error: {e}")
