from flask import Blueprint, render_template, redirect, url_for, send_from_directory, current_app, abort
from flask_login import current_user, login_required
from ..models import Report, Notification, Category, User
from ..extensions import db

bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    return render_template("landing.html")

@bp.route("/dashboard")
@login_required
def dashboard():
    if current_user.role == "admin":
        reports = Report.query.order_by(
            Report.created_at.desc()
        ).limit(6).all()

        counts = {
            status: Report.query.filter_by(status=status).count()
            for status in [
                "Menunggu Verifikasi",
                "Diverifikasi",
                "Sedang Diproses",
                "Selesai",
                "Ditolak"
            ]
        }

        pending_petugas_count = User.query.filter_by(
            role="petugas",
            account_status="pending"
        ).count()

        return render_template(
            "admin/dashboard.html",
            reports=reports,
            counts=counts,
            total_users=User.query.filter_by(role="warga").count(),
            total_reports=Report.query.count(),
            pending_petugas_count=pending_petugas_count
        )

    if current_user.role == "petugas":
        return redirect(url_for("petugas.dashboard"))

    reports = Report.query.filter_by(
        user_id=current_user.id
    ).order_by(Report.created_at.desc()).limit(5).all()

    counts = {
        status: Report.query.filter_by(
            user_id=current_user.id,
            status=status
        ).count()
        for status in [
            "Menunggu Verifikasi",
            "Diverifikasi",
            "Sedang Diproses",
            "Selesai",
            "Ditolak"
        ]
    }

    unread = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).count()

    return render_template(
        "warga/dashboard.html",
        reports=reports,
        counts=counts,
        unread=unread
    )


@bp.get("/notifikasi")
@login_required
def notifications():
    items = Notification.query.filter_by(
        user_id=current_user.id
    ).order_by(
        Notification.created_at.desc()
    ).all()

    return render_template(
        "warga/notifications.html",
        notifications=items
    )


@bp.get("/notifikasi/<int:notification_id>/buka")
@login_required
def open_notification(notification_id):
    notification = Notification.query.filter_by(
        id=notification_id,
        user_id=current_user.id
    ).first_or_404()

    if not notification.is_read:
        notification.is_read = True
        db.session.commit()

    if notification.report_id:
        return redirect(
            url_for("reports.detail", report_id=notification.report_id)
        )

    return redirect(url_for("main.notifications"))

@bp.get("/service-worker.js")
def service_worker():
    return send_from_directory(current_app.static_folder, "service-worker.js", mimetype="application/javascript")
