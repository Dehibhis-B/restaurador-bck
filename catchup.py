"""
Script manual para procesar archivos .bck atrasados.
Se ejecuta solo cuando hubo corte de luz/internet.

Uso:
    python catchup.py                       # procesa todos los pendientes
    python catchup.py --today               # solo el archivo del día
    python catchup.py 01_030726.bck         # un archivo específico
"""
import sys
import time
from pathlib import Path
from config import BACKUP_DIR
from database import get_connection, init_db, get_all_hashes
from watcher import load_pointer, save_pointer, scan_file


def process_one(filepath, conn, pointer, existing_hashes):
    if not filepath.exists():
        print(f"[catchup] {filepath.name} no existe")
        return 0
    count = scan_file(conn, filepath, pointer, existing_hashes)
    if count > 0:
        print(f"[catchup] {filepath.name}: +{count} marcas")
    else:
        print(f"[catchup] {filepath.name}: sin marcas nuevas")
    return count


def process_all(conn, pointer, existing_hashes):
    if not BACKUP_DIR.exists():
        print(f"[catchup] Carpeta no encontrada: {BACKUP_DIR}")
        return

    files = sorted(BACKUP_DIR.glob("*.bck"))
    if not files:
        print("[catchup] No hay archivos .bck")
        return

    print(f"[catchup] Procesando {len(files)} archivos secuencialmente...")
    total = 0
    for filepath in files:
        count = process_one(filepath, conn, pointer, existing_hashes)
        total += count
        time.sleep(0.5)
    print(f"[catchup] Total: {total} marcas procesadas")


def main():
    init_db()
    pointer = load_pointer()
    conn = get_connection()
    existing_hashes = get_all_hashes(conn)

    args = sys.argv[1:]

    if not args:
        process_all(conn, pointer, existing_hashes)
    elif args[0] == "--today":
        from datetime import datetime
        filename = f"01_{datetime.now().strftime('%d%m%y')}.bck"
        process_one(BACKUP_DIR / filename, conn, pointer, existing_hashes)
    else:
        for name in args:
            process_one(BACKUP_DIR / name, conn, pointer, existing_hashes)

    conn.close()


if __name__ == "__main__":
    main()
