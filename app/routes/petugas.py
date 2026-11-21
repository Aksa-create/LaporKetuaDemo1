from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from ..utils import roles_required
from ..extensions import db
from ..models import Report, ReportStatusHistory, Notification, ActivityLog
from datetime import datetime, timezone

bp = Blueprint("petugas", __name__)


@bp.get("/")
@login_required
@roles_required("petugas")
def dashboard():
    reports = Report.query.filter(
        Report.assigned_petugas_id == current_user.id,
        Report.status.in_(["Diverifikasi", "Sedang Diproses"])
    ).order_by(
        Report.created_at.desc()
    ).all()

    verified_count = sum(
        1 for report in reports
        if report.status == "Diverifikasi"
    )

    processing_count = sum(
        1 for report in reports
        if report.status == "Sedang Diproses"
    )

    return render_template(
        "petugas/dashboard.html",
        reports=reports,
        verified_count=verified_count,
        processing_count=processing_count
    )


@bp.post("/laporan/<int:report_id>/update")
@login_required
@roles_required("petugas")
def update_report(report_id):

    # Petugas hanya boleh mengubah laporan yang ditugaskan kepadanya.
    report = Report.query.filter_by(
        id=report_id,
        assigned_petugas_id=current_user.id
    ).first_or_404()

    status = request.form.get("status")
    note = request.form.get("note", "").strip()

    # Batasi perpindahan status sesuai alur pekerjaan Petugas.
    if report.status == "Diverifikasi":
        allowed_statuses = ["Sedang Diproses"]
    elif report.status == "Sedang Diproses":
        allowed_statuses = ["Selesai"]
    else:
        abort(400)

    if status not in allowed_statuses:
        abort(400)

    if status == "Selesai" and not note:
        flash("Catatan penyelesaian wajib diisi.", "danger")
        return redirect(url_for("petugas.dashboard"))

    old = report.status
    report.status = status
    report.updated_at = datetime.now(timezone.utc)

    db.session.add(
        ReportStatusHistory(
            report_id=report.id,
            old_status=old,
            new_status=status,
            note=note,
            actor_id=current_user.id
        )
    )

    db.session.add(
        Notification(
            user_id=report.user_id,
            title=f"Laporan {report.report_number} diperbarui",
            message=f"Petugas memperbarui status menjadi {status}. {note}".strip(),
            report_id=report.id
        )
    )

    db.session.add(
        ActivityLog(
            actor_id=current_user.id,
            action="field_update",
            detail=f"{report.report_number}: {status}"
        )
    )

    db.session.commit()

    flash("Progres laporan berhasil diperbarui.", "success")

    return redirect(url_for("petugas.dashboard"))
