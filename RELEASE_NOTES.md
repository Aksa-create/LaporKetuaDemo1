# LaporKetua Demo Release — 12 November 2026

## Perbaikan pada paket ini
- Memperbaiki CSRF token yang sebelumnya tampil sebagai teks pada halaman login, form laporan, dan form perubahan status Admin.
- Memastikan seluruh form POST memiliki hidden CSRF field.
- Memperbaiki kontras tagline logo horizontal pada navbar gelap.
- Menambahkan skrip pemeriksaan statis `scripts/preflight.py`.
- Memperbarui laporan pengujian dengan hasil pemeriksaan aktual dan keterbatasan runtime.
- Mengurangi dependensi Python yang tidak digunakan langsung oleh aplikasi.

## Jalankan pemeriksaan

```powershell
python scripts/preflight.py
```

## Status
Paket ini adalah demo aplikasi dengan data simulasi. Pemeriksaan statis lulus; runtime dan end-to-end harus diuji pada komputer pengguna setelah dependensi terpasang. Jangan digunakan untuk operasional publik sebelum checklist produksi pada `DEPLOYMENT_GUIDE.md` diselesaikan.


## Security update: database credentials
- Removed the Admin database settings page, navigation item, dashboard shortcut, and server endpoint.
- Neon credentials are now configured only through server-side `.env` / hosting secrets.
- `.env` remains excluded by `.gitignore`; `.env.example` contains placeholders only.

## Revisi laporan & login — 12 November 2026
- Login menampilkan pilihan Warga, Petugas Lapangan, dan Admin RW. Backend memvalidasi role pilihan terhadap role akun yang tersimpan.
- Form laporan meminta RT lokasi kejadian dan patokan/detail lokasi secara terpisah dari RT domisili akun warga.
- RT kejadian dan detail lokasi tampil pada riwayat laporan warga, dashboard Admin, daftar kelola laporan, detail laporan, peta Admin, dan dashboard Petugas.
- Tombol Verifikasi khusus tersedia pada dashboard Admin, daftar laporan Admin, dan detail laporan. Aksi hanya menerima laporan berstatus Menunggu Verifikasi dan mencatat histori, notifikasi, serta activity log.
- Ditambahkan skrip migrasi aman untuk menambah kolom `report.location_detail` pada database lama tanpa menghapus data.
- Pemeriksaan statis terbaru: 15/15 lulus. Pengujian runtime/database/browser tetap perlu dilakukan pada lingkungan pengguna.
