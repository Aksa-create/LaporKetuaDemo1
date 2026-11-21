# Development Log

## 2026-11-12 — Sprint 0 / MVP foundation
- Created modular Flask application structure.
- Added user authentication and role checks.
- Added seed command for RW 06, 13 RT, categories, demo accounts.
- Added resident report form, image upload, manual map pin, report timeline.
- Added admin dashboard, resident list, report filters, map markers and status management.
- Added in-app notifications.
- Added rule-based priority recommendation.
- Added optional ML model loading; no model/dataset or accuracy claim is included.
- Added PWA manifest and service worker shell cache.
- Pending: install dependencies, run tests, harden uploads, persistent object storage, assigned field officer workflow, full AI training/evaluation, production deployment.


## Revisi alur laporan & login (12 Nov 2026)
- Login sekarang meminta pilihan jenis akun: Warga, Petugas Lapangan, atau Admin RW. Server mencocokkan pilihan dengan role akun tersimpan; pilihan ini tidak mengubah hak akses.
- Form laporan mewajibkan RT lokasi kejadian dan patokan/detail lokasi yang mudah ditemukan. RT kejadian tidak lagi diturunkan dari RT profil warga.
- Daftar laporan warga, dashboard Admin, halaman kelola laporan, detail laporan, peta Admin, dan dashboard Petugas menampilkan RT serta detail lokasi kejadian.
- Admin mendapat tombol Verifikasi khusus pada dashboard, daftar laporan, dan detail laporan. Aksi mencatat histori, notifikasi warga, dan activity log; hanya berlaku untuk status Menunggu Verifikasi.
- Skema Report mendapat kolom `location_detail`; instalasi lama perlu migrasi database.
- Ditambahkan skrip migrasi aman `scripts/migrate_report_location_detail.py` untuk database lama; menambah kolom nullable tanpa menghapus data.
