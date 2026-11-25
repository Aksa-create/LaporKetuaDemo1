from zoneinfo import ZoneInfo
from datetime import datetime, timezone
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user, login_user
from ..utils import roles_required
from ..extensions import db
from ..models import Report, User, Category, ReportStatusHistory, Notification, ActivityLog
from ..services.ai_service import find_duplicate_candidates
from sqlalchemy import func

bp = Blueprint("admin", __name__)

STATUSES = [
    "Menunggu Verifikasi",
    "Diverifikasi",
    "Sedang Diproses",
    "Selesai",
    "Ditolak"
]

@bp.route("/masuk", methods=["GET", "POST"])
def login():
    """Private admin sign-in endpoint; public role selector never accepts admin."""
    if current_user.is_authenticated:
        if current_user.role == "admin":
            return redirect(url_for("admin.dashboard"))
        return redirect(url_for("main.dashboard"))
    if request.method == "POST":
        identity = request.form.get("identity", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter(
        (func.lower(User.username) == identity) |
        (func.lower(User.email) == identity)
        ).first()
        if user and user.role == "admin" and user.check_password(password) and user.account_status == "active":
            user.last_login_at = datetime.now(timezone.utc)
            db.session.add(ActivityLog(actor=user, action="admin_login", detail="Admin RW masuk melalui akses khusus"))
            db.session.commit()
            login_user(user, remember=bool(request.form.get("remember")))
            return redirect(url_for("admin.dashboard"))
        flash("Kredensial Admin RW tidak valid atau akun tidak aktif.", "danger")
    return render_template("admin/login.html")


@bp.get("/")
@login_required
@roles_required("admin")
def dashboard():
    reports = Report.query.order_by(
        Report.created_at.desc()
    ).limit(8).all()

    counts = {
        s: Report.query.filter_by(status=s).count()
        for s in STATUSES
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

@bp.get("/laporan")
@login_required
@roles_required("admin")
def reports():
    from ..models import RT

    status = request.args.get("status", "").strip()
    rt = request.args.get("rt", "").strip()

    query = Report.query

    # Filter berdasarkan status laporan
    if status and status in STATUSES:
        query = query.filter(Report.status == status)

    # Filter berdasarkan RT lokasi kejadian
    if rt:
        query = query.filter(
            db.func.trim(Report.rt_number) == rt
        )

    reports = query.order_by(
        Report.created_at.desc()
    ).all()

    petugas_list = User.query.filter_by(
        role="petugas",
        account_status="active"
    ).order_by(User.full_name.asc()).all()

    return render_template(
        "admin/reports.html",
        reports=reports,
        statuses=STATUSES,
        rts=sorted(RT.query.all(), key=lambda rt: int(rt.number)),
        petugas_list=petugas_list,
        selected_status=status,
        selected_rt=rt
    )

@bp.post("/laporan/<int:report_id>/tugaskan")
@login_required
@roles_required("admin")
def assign_petugas(report_id):
    report = db.get_or_404(Report, report_id)

    # Penugasan hanya untuk laporan yang sudah diverifikasi
    if report.status not in ["Diverifikasi", "Sedang Diproses"]:
        flash(
            "Petugas hanya dapat ditugaskan pada laporan yang sudah diverifikasi.",
            "warning"
        )
        return redirect(url_for("admin.reports"))

    petugas_id = request.form.get("petugas_id", type=int)

    if not petugas_id:
        flash("Pilih Petugas terlebih dahulu.", "danger")
        return redirect(url_for("admin.reports"))

    petugas = User.query.filter_by(
        id=petugas_id,
        role="petugas",
        account_status="active"
    ).first()

    if not petugas:
        flash("Petugas tidak ditemukan atau akunnya belum aktif.", "danger")
        return redirect(url_for("admin.reports"))

    old_petugas = report.assigned_petugas

    # Hindari penugasan ulang kepada Petugas yang sama
    if old_petugas and old_petugas.id == petugas.id:
        flash("Laporan ini sudah ditugaskan kepada Petugas tersebut.", "info")
        return redirect(url_for("admin.reports"))

    report.assigned_petugas_id = petugas.id

    # Beri tahu Petugas baru
    db.session.add(Notification(
        user_id=petugas.id,
        title="Tugas Penanganan Laporan Baru",
        message=(
            f"Kamu ditugaskan menangani laporan {report.report_number}: "
            f"{report.title}"
        ),
        report_id=report.id
    ))

    # Beri tahu Petugas sebelumnya jika tugas dialihkan
    if old_petugas:
        db.session.add(Notification(
            user_id=old_petugas.id,
            title="Penugasan Laporan Dialihkan",
            message=(
                f"Tugas laporan {report.report_number} telah dialihkan "
                "kepada Petugas lain oleh Admin RW."
            ),
            report_id=report.id
        ))

    # Beri tahu Warga bahwa laporan sudah memiliki Petugas
    db.session.add(Notification(
        user_id=report.user_id,
        title="Petugas Laporan Telah Ditugaskan",
        message=(
            f"Laporan {report.report_number} telah memiliki Petugas "
            "yang bertanggung jawab untuk penanganannya."
        ),
        report_id=report.id
    ))

    db.session.add(ActivityLog(
        actor_id=current_user.id,
        action="petugas_assigned",
        detail=(
            f"Menugaskan laporan {report.report_number} "
            f"kepada {petugas.full_name}"
        )
    ))

    db.session.commit()

    flash(
        f"Laporan {report.report_number} berhasil ditugaskan kepada "
        f"{petugas.full_name}.",
        "success"
    )

    return redirect(url_for("admin.reports"))

@bp.post("/laporan/<int:report_id>/status")
@login_required
@roles_required("admin")
def update_status(report_id):
    report = db.get_or_404(Report, report_id)
    new_status = request.form.get("status")
    note = request.form.get("note", "").strip()
    if new_status not in STATUSES:
        abort(400)
    if new_status == "Ditolak" and not note:
        flash("Alasan penolakan wajib diisi.", "danger")
        return redirect(url_for("reports.detail", report_id=report.id))
    old_status = report.status
    report.status = new_status
    db.session.add(ReportStatusHistory(report_id=report.id, old_status=old_status, new_status=new_status, note=note, actor_id=current_user.id))
    db.session.add(Notification(user_id=report.user_id, title=f"Status laporan {report.report_number} diperbarui", message=f"Status: {new_status}. {note}".strip(), report_id=report.id))
    db.session.add(ActivityLog(actor_id=current_user.id, action="report_status_updated", detail=f"{report.report_number}: {old_status} → {new_status}"))
    db.session.commit()
    flash("Status laporan berhasil diperbarui dan notifikasi dibuat.", "success")
    return redirect(url_for("reports.detail", report_id=report.id))


@bp.post("/laporan/<int:report_id>/verifikasi")
@login_required
@roles_required("admin")
def verify_report(report_id):
    report = db.get_or_404(Report, report_id)
    if report.status != "Menunggu Verifikasi":
        flash("Laporan ini sudah tidak berada pada status menunggu verifikasi.", "warning")
        return redirect(url_for("admin.reports"))
    old_status = report.status
    report.status = "Diverifikasi"
    db.session.add(ReportStatusHistory(report_id=report.id, old_status=old_status, new_status="Diverifikasi", note="Laporan diverifikasi oleh Admin RW.", actor_id=current_user.id))
    db.session.add(Notification(user_id=report.user_id, title=f"Laporan {report.report_number} telah diverifikasi", message="Laporan kamu telah diverifikasi Admin RW dan siap ditindaklanjuti.", report_id=report.id))
    db.session.add(ActivityLog(actor_id=current_user.id, action="report_verified", detail=f"Memverifikasi laporan {report.report_number}"))
    db.session.commit()
    flash("Laporan berhasil diverifikasi. Petugas dapat melihatnya di daftar pekerjaan.", "success")
    return redirect(url_for("admin.reports"))

@bp.get("/warga")
@login_required
@roles_required("admin")
def residents():
    from ..models import RT

    rt = request.args.get("rt", "")
    status = request.args.get("status", "")

    query = User.query.filter_by(role="warga")

    if rt:
        query = query.filter_by(rt_number=rt)

    if status:
        query = query.filter_by(account_status=status)

    residents = query.order_by(User.created_at.desc()).all()

    # Konversi waktu login dari UTC ke WIB
    jakarta_tz = ZoneInfo("Asia/Jakarta")

    for user in residents:
        if user.last_login_at:
            login_time = user.last_login_at

            # Antisipasi datetime tanpa informasi timezone
            if login_time.tzinfo is None:
                login_time = login_time.replace(tzinfo=timezone.utc)

            user.last_login_display = login_time.astimezone(jakarta_tz)
        else:
            user.last_login_display = None

    return render_template(
        "admin/residents.html",
        residents=residents,
        rts=sorted(RT.query.all(), key=lambda rt: int(rt.number)),
        selected_rt=rt,
        selected_status=status
    )

@bp.get("/petugas")
@login_required
@roles_required("admin")
def pending_petugas():
    petugas_list = User.query.filter_by(
        role="petugas",
        account_status="pending"
    ).order_by(User.created_at.asc()).all()

    return render_template(
        "admin/petugas_pending.html",
        petugas_list=petugas_list
    )


@bp.post("/petugas/<int:user_id>/setujui")
@login_required
@roles_required("admin")
def approve_petugas(user_id):
    petugas = User.query.filter_by(
        id=user_id,
        role="petugas",
        account_status="pending"
    ).first_or_404()

    petugas.account_status = "active"

    db.session.add(Notification(
        user_id=petugas.id,
        title="Pendaftaran Petugas Disetujui",
        message="Selamat! Pendaftaran kamu telah disetujui Admin RW. Sekarang kamu sudah bisa masuk sebagai Petugas Lapangan."
    ))

    db.session.add(ActivityLog(
        actor_id=current_user.id,
        action="petugas_approved",
        detail=f"Menyetujui pendaftaran Petugas {petugas.full_name}"
    ))

    db.session.commit()

    flash(
        f"Akun Petugas {petugas.full_name} berhasil disetujui.",
        "success"
    )

    return redirect(url_for("admin.pending_petugas"))


@bp.post("/petugas/<int:user_id>/tolak")
@login_required
@roles_required("admin")
def reject_petugas(user_id):
    petugas = User.query.filter_by(
        id=user_id,
        role="petugas",
        account_status="pending"
    ).first_or_404()

    petugas.account_status = "rejected"

    db.session.add(Notification(
        user_id=petugas.id,
        title="Pendaftaran Petugas Ditolak",
        message="Mohon maaf, pendaftaran kamu sebagai Petugas Lapangan belum disetujui Admin RW. Silakan hubungi Admin RW untuk informasi lebih lanjut."
    ))

    db.session.add(ActivityLog(
        actor_id=current_user.id,
        action="petugas_rejected",
        detail=f"Menolak pendaftaran Petugas {petugas.full_name}"
    ))

    db.session.commit()

    flash(
        f"Pendaftaran Petugas {petugas.full_name} ditolak.",
        "warning"
    )

    return redirect(url_for("admin.pending_petugas"))


@bp.get("/peta")
@login_required
@roles_required("admin")
def map_view():
    reports = Report.query.order_by(Report.created_at.desc()).all()
    return render_template("admin/map.html", reports=reports)


