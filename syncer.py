import json
import time
import urllib.request
import urllib.error
from config import (
    API_SYNC_ENDPOINT,
    API_TOKEN_ENDPOINT,
    API_USERNAME,
    API_PASSWORD,
    SYNC_INTERVAL,
    MAX_RETRY_INTERVAL,
    MIN_BATCH_SIZE,
    MAX_BATCH_WAIT,
)
from database import get_connection, get_pending_marks, mark_synced


def obtain_token():
    payload = json.dumps({"username": API_USERNAME, "password": API_PASSWORD}).encode()
    req = urllib.request.Request(
        API_TOKEN_ENDPOINT,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
    return data["access"]


token = None


def get_token():
    global token
    if token:
        return token
    try:
        token = obtain_token()
        print("[syncer] Token obtenido exitosamente")
        return token
    except Exception as e:
        print(f"[syncer] Error obteniendo token: {e}")
        return None


def send_marks(marks):
    tk = get_token()
    if not tk:
        return None, "sin_token"

    payload = json.dumps({"marks": marks}).encode()
    req = urllib.request.Request(
        API_SYNC_ENDPOINT,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {tk}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read()), None
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        if e.code == 401:
            global token
            token = None
        return None, f"HTTP {e.code}"
    except Exception as e:
        return None, str(e)


def sync_loop():
    global token
    retry_delay = SYNC_INTERVAL
    idle_ticks = 0

    while True:
        time.sleep(retry_delay)
        conn = get_connection()
        pending = get_pending_marks(conn, limit=50)

        if not pending:
            idle_ticks += 1
            if idle_ticks % 12 == 0:
                print(f"[syncer] Esperando marcas... (token activo)")
            retry_delay = SYNC_INTERVAL
            conn.close()
            continue

        idle_ticks = 0
        count = len(pending)

        if count < MIN_BATCH_SIZE:
            waited = 0
            while waited < MAX_BATCH_WAIT:
                time.sleep(2)
                waited += 2
                more = get_pending_marks(conn, limit=50)
                if len(more) > count:
                    pending = more
                    count = len(pending)
                if count >= MIN_BATCH_SIZE:
                    break

        marks_for_api = [
            {
                "device": m["device"],
                "dni": m["dni"],
                "mark_date": m["mark_date"],
                "event_code": m["event_code"],
            }
            for m in pending
        ]

        result, error = send_marks(marks_for_api)

        if result:
            for m in pending:
                mark_synced(conn, m["id"])
            good = result.get("good", 0)
            unresolved = result.get("unresolved", 0)
            bad = result.get("bad", 0)
            print(f"[syncer] {count} enviadas: {good} creadas, {unresolved} pendientes, {bad} errores")
            retry_delay = SYNC_INTERVAL
        else:
            print(f"[syncer] Error de conexión ({error}) - {count} marcas reintentarán")
            retry_delay = min(retry_delay * 2, MAX_RETRY_INTERVAL)

        conn.close()
