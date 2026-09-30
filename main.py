import threading
from watcher import watch_loop
from syncer import sync_loop


def main():
    print("=== Local Agent - Monitor de Marcaciones ===")
    print("[main] Iniciando watcher (monitoreo de archivos)...")
    print("[main] Iniciando syncer (envío a producción)...")

    t_watcher = threading.Thread(target=watch_loop, daemon=True)
    t_syncer = threading.Thread(target=sync_loop, daemon=True)

    t_watcher.start()
    t_syncer.start()

    print("[main] Sistema operativo. Presione Ctrl+C para detener.")
    try:
        t_watcher.join()
        t_syncer.join()
    except KeyboardInterrupt:
        print("\n[main] Deteniendo...")


if __name__ == "__main__":
    main()
