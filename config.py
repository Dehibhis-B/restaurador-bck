import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
# BACKUP_DIR = BASE_DIR.parent / "Backup" 
BACKUP_DIR = Path(r"C:\Users\Adm\Desktop\tempus\SMC\COMUNICA\Backup")

SQLITE_DB = BASE_DIR / "local_agent.db"
POINTER_FILE = BASE_DIR / "pointer.json"

API_BASE_URL = os.getenv("API_BASE_URL", "")
API_SYNC_ENDPOINT = f"{API_BASE_URL}/biometric/marks-sync/"
API_TOKEN_ENDPOINT = os.getenv("")

API_USERNAME = os.getenv("API_USERNAME", "")
API_PASSWORD = os.getenv("API_PASSWORD", "")

POLL_INTERVAL = 2
SYNC_INTERVAL = 5
MAX_RETRY_INTERVAL = 60
MIN_BATCH_SIZE = 10
MAX_BATCH_WAIT = 15
