"""Check database connectivity using DATABASE_URL from .env without printing secrets."""
import os
import sys
from dotenv import load_dotenv
from sqlalchemy import text

load_dotenv()
url = os.getenv("DATABASE_URL", "").strip()
if not url:
    print("[FAIL] DATABASE_URL belum diisi di file .env")
    sys.exit(1)
if "USER:PASSWORD@HOST/DBNAME" in url or "GANTI" in url:
    print("[FAIL] DATABASE_URL masih berupa placeholder. Isi dengan connection string dari Neon.")
    sys.exit(1)

try:
    from app import create_app
    from app.extensions import db
    app = create_app()
    with app.app_context():
        with db.engine.connect() as connection:
            version = connection.execute(text("SELECT version()")).scalar_one()
            current_db = connection.execute(text("SELECT current_database()")).scalar_one()
            print("[PASS] Koneksi database berhasil.")
            print(f"[INFO] Database: {current_db}")
            print(f"[INFO] Server: {version.split(',')[0]}")
except Exception as exc:
    print("[FAIL] Koneksi database gagal.")
    print(f"[INFO] {type(exc).__name__}: {exc}")
    print("Periksa DATABASE_URL, username/password, hostname, nama database, dan sslmode=require.")
    sys.exit(1)
