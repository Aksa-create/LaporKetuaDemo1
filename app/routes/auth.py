import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from html import escape
from flask import (
    Blueprint, 
    render_template, 
    request, 
    redirect, 
    url_for, 
    flash, 
    current_app
)
from flask_login import login_user, logout_user, current_user, login_required
from ..extensions import db
from ..models import (
    User, 
    RT, 
    ActivityLog,
    PasswordResetToken
)

from ..services.email_service import send_email

bp = Blueprint("auth", __name__)


@bp.route("/daftar", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    rts = RT.query.order_by(RT.number).all()

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        username = request.form.get("username", "").strip().lower()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")
        rt_number = request.form.get("rt_number", "")
        selected_role = request.form.get("role", "").strip().lower()

        # Hanya Warga dan Petugas yang boleh mendaftar
        if selected_role not in {"warga", "petugas"}:
            flash("Jenis akun tidak valid.", "danger")

        elif not all([full_name, username, email, password, confirm, rt_number]):
            flash("Semua kolom wajib diisi.", "danger")

        elif password != confirm:
            flash("Konfirmasi password tidak sama.", "danger")

        elif len(password) < 10:
            flash("Password minimal 10 karakter.", "danger")

        elif not RT.query.filter_by(number=rt_number).first():
            flash("RT tidak terdaftar.", "danger")

        elif User.query.filter(
            (User.username == username) | (User.email == email)
        ).first():
            flash("Username atau email sudah digunakan.", "danger")

        else:
            account_status = (
                "active" if selected_role == "warga" else "pending"
            )

            user = User(
                full_name=full_name,
                username=username,
                email=email,
                rt_number=rt_number,
                role=selected_role,
                account_status=account_status
            )

            user.set_password(password)
            db.session.add(user)
            db.session.commit()

            if selected_role == "petugas":
                flash(
                    "Pendaftaran berhasil. Akun Petugas menunggu persetujuan Admin RW.",
                    "success"
                )
            else:
                flash(
                    "Pendaftaran berhasil. Silakan masuk.",
                    "success"
                )

            return redirect(url_for("auth.login"))

    return render_template("auth/register.html", rts=rts)



@bp.route("/masuk", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        identity = request.form.get("identity", "").strip().lower()
        password = request.form.get("password", "")
        selected_role = request.form.get("role", "").strip().lower()

        allowed_roles = {"warga", "petugas"}

        user = User.query.filter(
            (User.username == identity) | (User.email == identity)
        ).first()

        if selected_role not in allowed_roles:
            flash("Pilih jenis akun yang sesuai.", "danger")

        elif user and user.role == selected_role and user.check_password(password):
            if user.account_status == "pending":
                flash(
                    "Akun Petugas Lapangan masih menunggu persetujuan Admin RW.",
                    "warning"
                )

            elif user.account_status != "active":
                flash("Akun belum aktif. Hubungi Admin RW.", "danger")

            else:
                user.last_login_at = datetime.now(timezone.utc)

                db.session.add(ActivityLog(
                    actor=user,
                    action="login",
                    detail="Pengguna masuk ke aplikasi"
                ))

                db.session.commit()

                login_user(
                    user,
                    remember=bool(request.form.get("remember"))
                )

                return redirect(url_for("main.dashboard"))

        else:
            flash(
                "Kredensial atau jenis akun tidak sesuai.",
                "danger"
            )

    return render_template("auth/login.html")

            

@bp.post("/keluar")
def logout():
    logout_user()
    flash("Kamu sudah keluar.", "info")
    return redirect(url_for("main.index"))


def _get_valid_reset_token(raw_token):
    """Memeriksa token reset password dan masa berlakunya."""

    token_hash = hashlib.sha256(
        raw_token.encode("utf-8")
    ).hexdigest()

    reset_token = PasswordResetToken.query.filter_by(
        token_hash=token_hash,
        used_at=None
    ).first()

    if not reset_token:
        return None

    now = datetime.now(timezone.utc)
    expires_at = reset_token.expires_at

    # Menangani datetime tanpa timezone jika database mengembalikannya.
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if expires_at <= now:
        return None

    return reset_token


@bp.route("/lupa-password", methods=["GET", "POST"])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()

        user = User.query.filter(
            db.func.lower(User.email) == email,
            User.role.in_(["warga", "petugas"])
        ).first()

        # Pesan dibuat sama, baik email ditemukan maupun tidak.
        if user:
            now = datetime.now(timezone.utc)

            # Batasi pengiriman ulang untuk akun yang sama.
            recent_token = PasswordResetToken.query.filter(
                PasswordResetToken.user_id == user.id,
                PasswordResetToken.created_at >= now - timedelta(minutes=1)
            ).first()

            if not recent_token:
                raw_token = secrets.token_urlsafe(32)

                token_hash = hashlib.sha256(
                    raw_token.encode("utf-8")
                ).hexdigest()

                reset_token = PasswordResetToken(
                    user_id=user.id,
                    token_hash=token_hash,
                    expires_at=now + timedelta(minutes=30)
                )

                # Token sebelumnya yang belum digunakan dinonaktifkan.
                PasswordResetToken.query.filter_by(
                    user_id=user.id,
                    used_at=None
                ).update(
                    {"used_at": now},
                    synchronize_session=False
                )

                db.session.add(reset_token)
                db.session.commit()

                reset_link = url_for(
                    "auth.reset_password",
                    token=raw_token,
                    _external=True
                )

                safe_name = escape(user.full_name or "Pengguna")

                email_html = f"""
                <div style="font-family:Arial,sans-serif;max-width:600px;margin:auto;">
                    <h2>Reset Password LaporKetua</h2>

                    <p>Halo {safe_name},</p>

                    <p>
                        Kami menerima permintaan untuk mengatur ulang
                        password akun LaporKetua kamu.
                    </p>

                    <p>
                        Klik tombol berikut untuk membuat password baru:
                    </p>

                    <p>
                        <a href="{reset_link}"
                           style="display:inline-block;padding:12px 20px;
                           background-color:#0d9488;color:white;
                           text-decoration:none;border-radius:6px;">
                            Reset Password
                        </a>
                    </p>

                    <p>Link ini hanya berlaku selama 30 menit.</p>

                    <p>
                        Jika kamu tidak meminta reset password,
                        abaikan email ini.
                    </p>

                    <p>Salam,<br>Tim LaporKetua</p>
                </div>
                """

                try:
                    send_email(
                        to=user.email,
                        subject="Reset Password LaporKetua",
                        html=email_html
                    )
                except Exception:
                    current_app.logger.exception(
                        "Gagal mengirim email reset password."
                    )

                    reset_token.used_at = datetime.now(timezone.utc)
                    db.session.commit()

        flash(
            "Jika email terdaftar, instruksi reset password akan dikirim. "
            "Silakan periksa kotak masuk email kamu.",
            "info"
        )

        return redirect(url_for("auth.login"))

    return render_template("auth/forgot_password.html")


@bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    reset_token = _get_valid_reset_token(token)

    if not reset_token:
        flash(
            "Link reset password tidak valid atau sudah kedaluwarsa.",
            "danger"
        )
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if len(password) < 10:
            flash(
                "Password harus memiliki minimal 10 karakter.",
                "danger"
            )

        elif password != confirm_password:
            flash(
                "Konfirmasi password tidak cocok.",
                "danger"
            )

        else:
            now = datetime.now(timezone.utc)

            user = reset_token.user
            user.set_password(password)

            # Semua token reset milik akun ini dinonaktifkan.
            PasswordResetToken.query.filter_by(
                user_id=user.id,
                used_at=None
            ).update(
                {"used_at": now},
                synchronize_session=False
            )

            db.session.commit()

            flash(
                "Password berhasil diperbarui. Silakan masuk menggunakan password baru.",
                "success"
            )

            return redirect(url_for("auth.login"))

    return render_template("auth/reset_password.html")



@bp.route("/profil", methods=["GET", "POST"])
@login_required
def profile():
    if current_user.role not in {"warga", "petugas"}:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()

        if not full_name or not email:
            flash("Nama lengkap dan email wajib diisi.", "danger")

        elif len(full_name) > 120:
            flash("Nama lengkap maksimal 120 karakter.", "danger")

        elif len(email) > 160 or "@" not in email:
            flash("Format email tidak valid.", "danger")

        else:
            existing_email = User.query.filter(
                db.func.lower(User.email) == email,
                User.id != current_user.id
            ).first()

            if existing_email:
                flash("Email tersebut sudah digunakan akun lain.", "danger")

            else:
                current_user.full_name = full_name
                current_user.email = email

                try:
                    db.session.commit()
                    flash("Profil berhasil diperbarui.", "success")
                    return redirect(url_for("auth.profile"))

                except Exception:
                    db.session.rollback()
                    current_app.logger.exception(
                        "Gagal memperbarui profil pengguna."
                    )
                    flash("Terjadi kesalahan saat memperbarui profil.", "danger")

    return render_template("profile.html")


@bp.route("/ubah-password", methods=["GET", "POST"])
@login_required
def change_password():
    if current_user.role not in {"warga", "petugas"}:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        current_password = request.form.get("current_password", "")
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not current_user.check_password(current_password):
            flash("Password saat ini tidak sesuai.", "danger")

        elif len(new_password) < 10:
            flash("Password baru minimal 10 karakter.", "danger")

        elif new_password != confirm_password:
            flash("Konfirmasi password baru tidak cocok.", "danger")

        elif current_user.check_password(new_password):
            flash("Password baru harus berbeda dari password lama.", "warning")

        else:
            current_user.set_password(new_password)

            try:
                db.session.commit()
                flash("Password berhasil diperbarui.", "success")
                return redirect(url_for("auth.profile"))

            except Exception:
                db.session.rollback()
                current_app.logger.exception(
                    "Gagal memperbarui password pengguna."
                )
                flash("Terjadi kesalahan saat memperbarui password.", "danger")

    return render_template("auth/change_password.html")
