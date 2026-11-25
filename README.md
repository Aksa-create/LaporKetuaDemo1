# LaporKetua — RW 06 Jembatan Besi

Aplikasi web pelaporan masalah lingkungan untuk warga dan pengurus RW. Versi ini adalah **demo fungsional dengan data fiktif** agar seluruh halaman dan alur dapat dicoba sebelum diganti dengan data asli.

## Jalankan di Windows (PowerShell)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
flask --app run.py seed
flask --app run.py run --debug/python run.py
```
Buka `http://127.0.0.1:5000`.

> Seluruh nama, akun, laporan, nomor laporan, dan statistik yang dibuat perintah `seed` adalah data simulasi. Jangan gunakan kredensial demo atau data simulasi pada layanan publik.


## Integrasi Neon PostgreSQL

Template khusus Neon tersedia di `.env.neon.example`. Cara menggunakannya:

1. Buat project/database di Neon Console.
2. Buka **Connect**, pilih database dan role, lalu pilih **Pooled connection** jika tersedia.
3. Salin connection string. Host pooled Neon biasanya memiliki akhiran `-pooler`.
4. Salin `.env.neon.example` menjadi `.env` (atau isi `.env` yang sudah ada).
5. Ganti nilai `DATABASE_URL` dengan connection string Neon. Format yang diterima: `postgresql+psycopg://USER:PASSWORD@HOST/DBNAME?sslmode=require`.
6. Ganti `SECRET_KEY` dengan nilai acak panjang. Jangan membagikan atau mengunggah `.env` ke GitHub.
7. Uji koneksi sebelum membuat tabel:

```powershell
python scripts/check_database.py
```

8. Jika koneksi berhasil, buat tabel dan data referensi/demo:

```powershell
flask --app run.py seed
```

**Penting:** perintah `seed` juga membuat akun dan laporan fiktif untuk demonstrasi. Jalankan hanya pada database demo/kosong. Jangan jalankan pada database produksi yang sudah berisi data asli. Jika password Neon mengandung karakter khusus seperti `@`, `#`, `/`, `:` atau `%`, lakukan URL-encoding pada password sebelum memasukkannya ke URL. Simpan connection string secara privat.

Untuk kembali memakai SQLite lokal, ubah `DATABASE_URL` menjadi `sqlite:///laporketua.db`.

## Modul yang tersedia

- Landing page, registrasi, login, logout, dan pembatasan akses berbasis peran.
- Dashboard warga, pembuatan laporan, unggah foto, pin lokasi Leaflet, riwayat dan notifikasi.
- Dashboard Admin, filter laporan per status/RT, perubahan status, direktori warga, dan peta laporan.
- Dashboard petugas dan pembaruan status sampai selesai dengan catatan.
- Riwayat status, notifikasi, log aktivitas, rekomendasi prioritas berbasis aturan, dan pemeriksaan kandidat duplikat.
- PWA manifest, ikon, dan offline fallback.

## Data wilayah yang dikunci

RW 06, Kelurahan Jembatan Besi, Kecamatan Tambora, Kota Administrasi Jakarta Barat, DKI Jakarta. RT yang valid: `01,02,03,04,05,06,07,08,09,11,12,13,14` (RT 10 memang tidak ada dalam daftar acuan).

Koordinat SDN Jembatan Besi `-6.153027, 106.798433` hanya titik referensi landmark, bukan titik pusat atau batas resmi RW. Polygon RW belum tersedia. Sampai data resmi diterima, laporan di luar/di tepi area harus diverifikasi Admin secara manual. Jangan menganggap marker sekretariat sementara sebagai lokasi resmi.

## Yang harus diganti sebelum data asli / produksi

Lihat `PANDUAN_GANTI_DATA_DUMMY.md` untuk daftar rinci data dan konfigurasi. Minimal: data warga dan RT yang sah, koordinat dan batas RW resmi, kategori final, foto/berkas asli, akun Admin/Petugas, secret key, PostgreSQL, object storage, HTTPS, backup, kebijakan privasi, serta pengujian keamanan.

## Batasan yang belum boleh dianggap selesai

- AI klasifikasi belum memiliki dataset berlabel dan model terlatih. UI/fitur rekomendasi prioritas masih berbasis aturan; tidak ada klaim akurasi ML.
- Penentuan duplikat adalah indikasi awal, bukan keputusan otomatis.
- Peta menampilkan koordinat dummy yang digeser di sekitar landmark untuk simulasi; bukan titik laporan atau batas RW sebenarnya.
- PWA offline hanya fallback halaman; pengiriman laporan offline belum diimplementasikan.
- Sistem reward/poin belum dimasukkan karena perlu persetujuan mekanisme dan sumber hadiah oleh pengurus.
- Belum production-ready sebelum pengujian end-to-end, audit keamanan, storage persisten, dan deployment.

### Pengaturan Neon dari dalam aplikasi

Koneksi database dikonfigurasi hanya melalui file `.env` di sisi server. Tidak ada halaman atau endpoint pengaturan database di dashboard Admin. Salin `.env.example` menjadi `.env`, lalu isi `DATABASE_URL` dengan connection string Neon (format `postgresql+psycopg://...?...sslmode=require`). Jangan pernah memasukkan connection string ke form aplikasi, source code, chat, atau GitHub. File `.env` sudah masuk `.gitignore`. Setelah mengubah `.env`, restart server. Penggantian URL tidak memindahkan data SQLite secara otomatis. Untuk hosting, masukkan `DATABASE_URL` sebagai Environment Variable rahasia pada penyedia hosting, bukan mengunggah `.env`.


## Catatan pembaruan skema untuk instalasi lama

Versi ini menambahkan kolom `report.location_detail`. Untuk database baru/kosong, jalankan `flask --app run.py seed`. Jika database lama sudah berisi data, jangan hapus database dan jangan jalankan seed ulang. Jalankan migrasi aman berikut sebelum membuka halaman laporan:

```powershell
python scripts/migrate_report_location_detail.py
```

Skrip hanya menambahkan kolom nullable jika belum tersedia; data laporan lama tidak dihapus. Laporan lama akan menampilkan keterangan bahwa detail lokasi belum diisi. Semua laporan baru diwajibkan mengisi RT kejadian, patokan lokasi, dan pin koordinat.


### Akses Admin RW

Halaman login publik hanya menyediakan pilihan **Warga** dan **Petugas Lapangan**. Akun Admin tidak dapat masuk melalui form publik, meskipun seseorang mengirim nilai `admin` secara manual. Admin menggunakan halaman akses khusus `/admin/masuk`; alamat ini tidak ditampilkan pada navigasi publik. Pembuatan akun Admin hanya melalui proses provisioning/seed oleh pengelola, bukan pendaftaran warga.
