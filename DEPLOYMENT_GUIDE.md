# Deployment Guide (Target: Free Tier)

This is a planning guide, not a claim that deployment has been completed.

1. Push the project to a private GitHub repository first. Remove demo credentials and ensure `.env` is ignored.
2. Provision a PostgreSQL free-tier database and copy its pooled connection string into `DATABASE_URL` using `postgresql+psycopg://...?...sslmode=require` format. The project includes `.env.neon.example` as a placeholder template; copy it to `.env` and replace the placeholders. Never commit `.env`. Test with `python scripts/check_database.py` before running database initialization.
3. Choose a hosting provider that currently supports persistent Flask web services, environment variables, HTTPS, and the required Python dependencies. Verify its current free-tier limits before committing.
4. Set `SECRET_KEY` to a long random value and configure `MAX_CONTENT_LENGTH`.
5. Run `flask --app run.py db upgrade` after migrations have been created, then `flask --app run.py seed` only for initial reference data. Do not seed demo users in production.
6. Configure persistent object storage for uploaded photos. The current local `uploads/` folder is development-only and may be ephemeral on cloud hosts.
7. Configure secure cookies, HTTPS, backups, logging, and a production WSGI server.
8. Test signup, login, report creation, photo retrieval, status updates, notifications, role access, PWA installation, and restart persistence using a real deployed URL.

Do not deploy with the default development SECRET_KEY or demo passwords. Free-tier quotas and availability can change; confirm provider terms and limits before launch.


## Rahasia koneksi database

- Simpan `DATABASE_URL` hanya di `.env` pada mesin/server lokal.
- `.env` tidak boleh di-commit; pastikan `.gitignore` tetap mengabaikannya.
- Pada platform hosting, simpan `DATABASE_URL` di pengaturan Environment Variables/Secrets milik platform.
- Dashboard Admin tidak menyediakan halaman untuk melihat atau mengubah kredensial database.
- Jangan pernah menaruh connection string di HTML, JavaScript, file static, atau tabel aplikasi.
