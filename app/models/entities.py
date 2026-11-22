from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from ..extensions import db


def utcnow():
    return datetime.now(timezone.utc)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    username = db.Column(db.String(40), unique=True, nullable=False, index=True)
    email = db.Column(db.String(160), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)

    role = db.Column(db.String(20), nullable=False, default="warga")
    rt_number = db.Column(db.String(2), db.ForeignKey("rt.number"), nullable=True)
    account_status = db.Column(db.String(24), nullable=False, default="active")

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=utcnow,
        nullable=False
    )
    last_login_at = db.Column(db.DateTime(timezone=True))

    # Laporan yang dibuat oleh pengguna
    reports = db.relationship(
        "Report",
        backref="reporter",
        lazy=True,
        foreign_keys="Report.user_id"
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class RT(db.Model):
    number = db.Column(db.String(2), primary_key=True)
    rw_code = db.Column(db.String(30), nullable=False, default="RW06-JB")


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)


class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    report_number = db.Column(
        db.String(30),
        unique=True,
        nullable=False,
        index=True
    )

    # Warga yang membuat laporan
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False,
        index=True
    )

    # Petugas yang bertanggung jawab menangani laporan
    assigned_petugas_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=True,
        index=True
    )

    category_id = db.Column(
        db.Integer,
        db.ForeignKey("category.id"),
        nullable=False
    )

    title = db.Column(db.String(160), nullable=False)
    description = db.Column(db.Text, nullable=False)
    photo_filename = db.Column(db.String(255))

    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)

    rt_number = db.Column(
        db.String(2),
        db.ForeignKey("rt.number"),
        nullable=False
    )
    location_detail = db.Column(db.String(255), nullable=True)

    status = db.Column(
        db.String(32),
        nullable=False,
        default="Menunggu Verifikasi",
        index=True
    )

    priority = db.Column(db.String(20), nullable=False, default="Sedang")
    urgency = db.Column(db.String(20), default="Sedang")

    ai_category = db.Column(db.String(80))
    ai_confidence = db.Column(db.Float)

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=utcnow,
        nullable=False
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
        nullable=False
    )

    # Relasi kategori, RT, dan Petugas
    category = db.relationship("Category")
    rt = db.relationship("RT")

    assigned_petugas = db.relationship(
        "User",
        foreign_keys=[assigned_petugas_id],
        backref=db.backref("assigned_reports", lazy=True)
    )

    # Riwayat perubahan status laporan
    history = db.relationship(
        "ReportStatusHistory",
        backref="report",
        cascade="all, delete-orphan",
        order_by="ReportStatusHistory.created_at"
    )


class ReportStatusHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    report_id = db.Column(
        db.Integer,
        db.ForeignKey("report.id"),
        nullable=False,
        index=True
    )

    old_status = db.Column(db.String(32))
    new_status = db.Column(db.String(32), nullable=False)
    note = db.Column(db.Text)

    actor_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=utcnow,
        nullable=False
    )

    actor = db.relationship("User")


class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False,
        index=True
    )

    title = db.Column(db.String(140), nullable=False)
    message = db.Column(db.String(300), nullable=False)

    report_id = db.Column(
        db.Integer,
        db.ForeignKey("report.id")
    )

    is_read = db.Column(db.Boolean, default=False, nullable=False)

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=utcnow,
        nullable=False
    )


class ActivityLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    actor_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id")
    )

    action = db.Column(db.String(120), nullable=False)
    detail = db.Column(db.String(300))

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=utcnow,
        nullable=False
    )

    actor = db.relationship("User")


class AIPrediction(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    report_id = db.Column(
        db.Integer,
        db.ForeignKey("report.id"),
        nullable=False
    )

    model_name = db.Column(db.String(100), nullable=False)
    predicted_category = db.Column(db.String(80))
    confidence = db.Column(db.Float)
    recommendation = db.Column(db.String(20))

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=utcnow,
        nullable=False
    )


class PasswordResetToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False,
        index=True
    )

    token_hash = db.Column(
        db.String(64),
        unique=True,
        nullable=False,
        index=True
    )

    expires_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False
    )

    used_at = db.Column(
        db.DateTime(timezone=True),
        nullable=True
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=utcnow,
        nullable=False
    )

    user = db.relationship(
        "User",
        backref=db.backref(
            "password_reset_tokens",
            lazy=True,
            cascade="all, delete-orphan"
        )
    )

