# Panduan mengganti data dummy menjadi data asli

## 1. Data wilayah
- Pertahankan daftar RT sesuai data yang telah diverifikasi: 01–09, 11–14.
- Konfirmasi nama resmi RW/kelurahan/kecamatan/kota/provinsi.
- Ganti koordinat simulasi laporan dengan koordinat hasil pemetaan lapangan.
- Minta polygon/batas RW resmi dari pengurus/instansi. Jangan membuat polygon berdasarkan perkiraan.
- Koordinat SDN Jembatan Besi `-6.153027, 106.798433` adalah landmark referensi saja, bukan pusat RW.

## 2. Data warga dan akun
- Hapus seluruh akun `*_demo` dan `adminrw`, `petugas_demo` setelah membuat akun resmi.
- Impor warga melalui proses yang disetujui pengurus; verifikasi RT dan status warga.
- Jangan memakai email contoh `@example.local` untuk komunikasi sungguhan.
- Setel ulang seluruh password; jangan membagikan satu password bersama untuk akun warga.

## 3. Laporan dan foto
- Hapus laporan `LK-2026-0001` dan seterusnya yang dibuat seed.
- Atur kebijakan retensi foto, batas ukuran, dan izin akses.
- Gunakan object storage persisten untuk deployment; folder lokal server tidak dijamin tersimpan.

## 4. Konfigurasi keamanan dan database
- Buat `SECRET_KEY` acak yang kuat di `.env` / environment hosting.
- Isi `DATABASE_URL` PostgreSQL/Neon yang benar; jangan commit `.env`.
- Siapkan backup database, HTTPS, logging aman, pembatasan percobaan login, dan monitoring.
- Ganti password demo dan nonaktifkan akun demo.

## 5. AI dan notifikasi
- Kumpulkan dataset laporan Bahasa Indonesia yang sudah dianonimkan dan diberi label oleh manusia.
- Pisahkan train/test, evaluasi precision, recall, F1, confusion matrix sebelum mengaktifkan klasifikasi.
- Prioritas otomatis tetap rekomendasi; Admin yang menetapkan keputusan akhir.
- Sambungkan kanal notifikasi resmi hanya setelah persetujuan dan konfigurasi kredensial.

## 6. Sebelum peluncuran
- Uji semua role di browser desktop dan HP.
- Uji alur: daftar → login → buat laporan → verifikasi → proses → selesai → notifikasi.
- Uji validasi file, CSRF, akses laporan antarwarga, akses role, dan pemulihan backup.
- Minta persetujuan pengurus RW terkait SOP, privasi, moderasi, SLA, dan sumber biaya operasional.
