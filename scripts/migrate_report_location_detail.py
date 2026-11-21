"""Safely add the nullable report.location_detail column to an existing DB.

Run: python scripts/migrate_report_location_detail.py
This does not delete or rewrite existing reports.
"""
from sqlalchemy import inspect, text
from app import create_app
from app.extensions import db

app = create_app()

with app.app_context():
    inspector = inspect(db.engine)
    if not inspector.has_table("report"):
        print("Tabel report belum ada. Jalankan 'flask --app run.py seed' untuk database baru.")
    else:
        columns = {column["name"] for column in inspector.get_columns("report")}
        if "location_detail" in columns:
            print("Kolom report.location_detail sudah tersedia. Tidak ada perubahan.")
        else:
            with db.engine.begin() as connection:
                connection.execute(text("ALTER TABLE report ADD COLUMN location_detail VARCHAR(255) NULL"))
            print("Berhasil menambahkan report.location_detail. Data laporan lama tetap dipertahankan.")
