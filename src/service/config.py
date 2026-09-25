"""Configuration from the environment (.env.local is read the same way the PoC does)."""
import os
import pathlib
import secrets
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "src"))
from bakeoff import load_env  # noqa: E402

ENV = load_env()  # API keys + any RETAIN_* settings in .env.local
for k, v in ENV.items():
    os.environ.setdefault(k, v)

DB_PATH = ROOT / "data" / "service.db"
APPLE_BUNDLE_ID = os.environ.get("RETAIN_APPLE_BUNDLE_ID", "com.retain.app")
APPLE_ISSUER = "https://appleid.apple.com"
APPLE_JWKS_URL = "https://appleid.apple.com/auth/keys"
SESSION_SECRET = os.environ.get("RETAIN_SESSION_SECRET") or secrets.token_hex(32)
SESSION_DAYS = int(os.environ.get("RETAIN_SESSION_DAYS", "180"))
DEV_TOKEN = os.environ.get("RETAIN_DEV_TOKEN")  # if set: Bearer <DEV_TOKEN> == the dev user
DAILY_CAP = int(os.environ.get("RETAIN_DAILY_CAP", "30"))
MIN_WORDS = int(os.environ.get("RETAIN_MIN_WORDS", "25"))  # a short Reddit comment is still a read
MAX_CHARS = 24000
if not os.environ.get("RETAIN_SESSION_SECRET"):
    print("[warn] RETAIN_SESSION_SECRET not set — sessions won't survive a restart")
