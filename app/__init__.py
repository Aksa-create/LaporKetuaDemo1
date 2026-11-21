import os
from datetime import timezone
from zoneinfo import ZoneInfo

from flask import Flask, render_template
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate
from dotenv import load_dotenv

from .extensions import db
from .models import User, RT, Category, Notification


login_manager = LoginManager()
csrf = CSRFProtect()
migrate = Migrate()


def create_app(test_config=None):
    load_dotenv()

    app = Flask(__name__, instance_relative_config=True)

    database_url = os.getenv(
        "DATABASE_URL",
        "sqlite:///laporketua.db"
    )

    if database_url.startswith("postgres://"):
        database_url = database_url.replace(
            "postgres://",
            "postgresql+psycopg://",
            1
        )
    elif database_url.startswith("postgresql://"):
        database_url = database_url.replace(
            "postgresql://",
            "postgresql+psycopg://",
            1
        )

    app.config.from_mapping(
        SECRET_KEY=os.getenv(
            "SECRET_KEY",
            "dev-only-change-this-secret"
        ),
        SQLALCHEMY_DATABASE_URI=database_url,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        UPLOAD_FOLDER=os.path.abspath(
            os.getenv("UPLOAD_FOLDER", "uploads")
        ),
        MAX_CONTENT_LENGTH=int(
            os.getenv("MAX_CONTENT_LENGTH", 6 * 1024 * 1024)
        ),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        REMEMBER_COOKIE_HTTPONLY=True,
        
        # Resend Email API
        RESEND_API_KEY=os.getenv("RESEND_API_KEY"),
        MAIL_DEFAULT_SENDER=os.getenv(
        "MAIL_DEFAULT_SENDER",
        "onboarding@resend.dev"),
    )

    if test_config:
        app.config.update(test_config)

    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # ==================================================
    # FILTER WAKTU UTC KE WIB
    # ==================================================

    @app.template_filter("wib_datetime")
    def wib_datetime(value, fmt="%d/%m/%Y %H:%M"):
        if value is None:
            return ""

        # Anggap datetime tanpa timezone sebagai UTC.
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)

        return value.astimezone(
            ZoneInfo("Asia/Jakarta")
        ).strftime(fmt)

    # ==================================================
    # INISIALISASI EXTENSIONS
    # ==================================================

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db)

    login_manager.login_view = "auth.login"
    login_manager.login_message = "Silakan masuk terlebih dahulu."
    login_manager.login_message_category = "info"

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    @app.context_processor
    def inject_unread_notifications():
        from flask_login import current_user

        unread_count = 0

        if current_user.is_authenticated:
            unread_count = Notification.query.filter_by(
                user_id=current_user.id,
                is_read=False
            ).count()

        return {
            "unread_notification_count": unread_count
        }

    # ==================================================
    # REGISTER BLUEPRINT
    # ==================================================

    from .routes.auth import bp as auth_bp
    from .routes.main import bp as main_bp
    from .routes.reports import bp as reports_bp
    from .routes.admin import bp as admin_bp
    from .routes.petugas import bp as petugas_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(reports_bp, url_prefix="/laporan")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(petugas_bp, url_prefix="/petugas")

    # ==================================================
    # PWA SERVICE WORKER
    # ==================================================

    @app.route("/service-worker.js")
    def service_worker():
        response = app.send_static_file("service-worker.js")
        response.headers["Content-Type"] = "application/javascript"
        response.headers["Service-Worker-Allowed"] = "/"
        response.headers["Cache-Control"] = "no-cache"
        return response

    # ==================================================
    # ERROR HANDLER
    # ==================================================

    @app.errorhandler(413)
    def too_large(_error):
        return render_template("errors/413.html"), 413

    
    # ==================================================
    # DATABASE SEED
    # ==================================================

    @app.cli.command("seed")
    def seed():
        """Create database tables and RW 06 reference data."""

        db.create_all()

        # ----------------------------------------------
        # DATA RT RW 06
        # ----------------------------------------------

        rt_numbers = [
            "01", "02", "03", "04", "05",
            "06", "07", "08", "09", "11",
            "12", "13", "14"
        ]

        for number in rt_numbers:
            existing_rt = RT.query.filter_by(
                number=number,
                rw_code="RW06-JB"
            ).first()

            if not existing_rt:
                db.session.add(
                    RT(number=number, rw_code="RW06-JB")
                )

        # ----------------------------------------------
        # KATEGORI LAPORAN
        # ----------------------------------------------

        category_names = [
            "Jalan Rusak",
            "Sampah Menumpuk",
            "Lampu Jalan Mati",
            "Saluran Air Tersumbat",
            "Pohon Tumbang",
            "Fasilitas Umum Rusak",
            "Keamanan Lingkungan",
            "Pasca Kebakaran / Penanganan Puing",
            "Lainnya"
        ]

        for name in category_names:
            existing_category = Category.query.filter_by(
                name=name
            ).first()

            if not existing_category:
                db.session.add(
                    Category(name=name, is_active=True)
                )

        db.session.commit()

        print(
            "Seed berhasil.\n"
            "Data referensi RW 06 dan kategori laporan telah disiapkan."
        )

    return app
