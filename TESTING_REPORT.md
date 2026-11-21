# LaporKetua — Release Preflight Report

Tanggal pemeriksaan: 12 November 2026

## Pemeriksaan statis yang berhasil

Dijalankan dengan `python scripts/preflight.py`:

- Kompilasi sintaks Python (`compileall`).
- Parsing seluruh template Jinja2.
- Pemeriksaan setiap form POST agar memiliki input CSRF tersembunyi.
- Pemeriksaan daftar RT RW 06 (13 RT: 01–09, 11–14).
- Pemeriksaan keberadaan aset logo, ikon PWA, dan manifest.
- Pemeriksaan sintaks JavaScript menggunakan `node --check`.

Hasil terakhir: **9 pemeriksaan lulus, 0 pemeriksaan statis gagal**.

## Pengujian yang belum dapat dinyatakan lulus

Runtime Flask, database, browser end-to-end, unggah foto, login lintas peran, migrasi PostgreSQL, dan audit keamanan belum dapat dijalankan di lingkungan pembuat karena paket Flask dan dependensinya tidak tersedia dan akses ke Python Package Index gagal akibat DNS/network. Pemeriksaan statis bukan pengganti pengujian tersebut.

## Catatan rilis

- Perbaikan CSRF: form login, pembuatan laporan, dan perubahan status Admin menggunakan hidden input `csrf_token`; token tidak dicetak sebagai teks biasa.
- Logo horizontal: tagline dibuat putih agar terbaca pada navbar navy.
- Data seed tetap data fiktif untuk demonstrasi.
- Belum production-ready. Jalankan smoke test lokal dari `README.md` dan ikuti `PANDUAN_GANTI_DATA_DUMMY.md` sebelum dipakai warga.
