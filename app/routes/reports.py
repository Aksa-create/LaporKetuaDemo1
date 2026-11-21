
import math
import os
import uuid
import warnings

from datetime import datetime

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)

from flask_login import current_user, login_required
from PIL import Image, UnidentifiedImageError
from werkzeug.utils import secure_filename

from ..extensions import db
from ..models import (
    AIPrediction,
    ActivityLog,
    Category,
    Notification,
    Report,
    ReportStatusHistory,
    RT,
)

from ..services.ai_service import (
    classify_report,
    find_duplicate_candidates,
    recommend_priority,
)


bp = Blueprint("reports", __name__)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
ALLOWED_IMAGE_FORMATS = {"PNG", "JPEG", "WEBP"}
ALLOWED_URGENCY = {"Rendah", "Sedang", "Tinggi"}

MIN_TITLE_LENGTH = 5
MAX_TITLE_LENGTH = 160

MIN_DESCRIPTION_LENGTH = 15
MAX_DESCRIPTION_LENGTH = 5000

MIN_LOCATION_LENGTH = 5
MAX_LOCATION_LENGTH = 255

MAX_IMAGE_PIXELS = 20_000_000
MAX_DUPLICATE_CANDIDATES = 500


def allowed_file(filename):
    return (
        bool(filename)
        and "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


def is_valid_image(file_storage):
    """Periksa format, dimensi, dan integritas gambar."""
    try:
        file_storage.stream.seek(0)

        with warnings.catch_warnings():
            warnings.simplefilter(
                "error",
                Image.DecompressionBombWarning
            )

            with Image.open(file_storage.stream) as image:
                if image.format not in ALLOWED_IMAGE_FORMATS:
                    file_storage.stream.seek(0)
                    return False

                width, height = image.size

                if width <= 0 or height <= 0:
                    file_storage.stream.seek(0)
                    return False

                if width * height > MAX_IMAGE_PIXELS:
                    file_storage.stream.seek(0)
                    return False

                image.verify()

        file_storage.stream.seek(0)
        return True

    except (
        UnidentifiedImageError,
        OSError,
        ValueError,
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
    ):
        file_storage.stream.seek(0)
        return False


def _remove_uploaded_file(filename):
    """Hapus file upload dari folder upload aplikasi."""
    if not filename:
        return

    safe_filename = os.path.basename(filename)

    photo_path = os.path.join(
        current_app.config["UPLOAD_FOLDER"],
        safe_filename
    )

    try:
        if os.path.isfile(photo_path):
            os.remove(photo_path)

    except OSError:
        current_app.logger.exception(
            "Gagal menghapus file upload %s",
            safe_filename
        )


# =========================================================
# BUAT LAPORAN BARU
# =========================================================

@bp.route("/baru", methods=["GET", "POST"])
@login_required
def create():

    if current_user.role != "warga":
        abort(403)

    categories = (
        Category.query
        .filter_by(is_active=True)
        .order_by(Category.name)
        .all()
    )

    rts = RT.query.order_by(RT.number).all()

    if request.method == "POST":

        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        category_id = request.form.get("category_id", type=int)

        category = None

        if category_id is not None:
            category = Category.query.filter_by(
                id=category_id,
                is_active=True
            ).first()

        lat = request.form.get("latitude", type=float)
        lng = request.form.get("longitude", type=float)

        urgency = request.form.get("urgency", "Sedang").strip()
        rt_number = request.form.get("rt_number", "").strip()

        location_detail = request.form.get(
            "location_detail", ""
        ).strip()

        photo = request.files.get("photo")

        # VALIDASI JUDUL
        if not (
            MIN_TITLE_LENGTH <= len(title) <= MAX_TITLE_LENGTH
        ):
            flash(
                "Judul laporan harus terdiri dari 5 sampai 160 karakter.",
                "danger"
            )

        # VALIDASI DESKRIPSI
        elif not (
            MIN_DESCRIPTION_LENGTH
            <= len(description)
            <= MAX_DESCRIPTION_LENGTH
        ):
            flash(
                "Deskripsi harus terdiri dari 15 sampai 5.000 karakter.",
                "danger"
            )

        # VALIDASI KATEGORI AKTIF
        elif not category:
            flash(
                "Kategori tidak valid atau sudah tidak aktif.",
                "danger"
            )

        # VALIDASI URGENSI
        elif urgency not in ALLOWED_URGENCY:
            flash(
                "Tingkat urgensi tidak valid.",
                "danger"
            )

        # VALIDASI RT
        elif not RT.query.filter_by(number=rt_number).first():
            flash(
                "RT yang dipilih tidak terdaftar.",
                "danger"
            )

        # VALIDASI DETAIL LOKASI
        elif not (
            MIN_LOCATION_LENGTH
            <= len(location_detail)
            <= MAX_LOCATION_LENGTH
        ):
            flash(
                "Detail lokasi harus terdiri dari 5 sampai 255 karakter.",
                "danger"
            )

        # VALIDASI KOORDINAT KOSONG
        elif lat is None or lng is None:
            flash(
                "Pin lokasi harus ditentukan pada peta.",
                "danger"
            )

        # VALIDASI KOORDINAT
        elif not (
            math.isfinite(lat)
            and math.isfinite(lng)
            and -90 <= lat <= 90
            and -180 <= lng <= 180
        ):
            flash(
                "Koordinat lokasi tidak valid.",
                "danger"
            )

        # VALIDASI EKSTENSI FOTO
        elif photo and photo.filename and not allowed_file(photo.filename):
            flash(
                "Foto harus berformat PNG, JPG, JPEG, atau WEBP.",
                "danger"
            )

        # VALIDASI ISI DAN DIMENSI FOTO
        elif photo and photo.filename and not is_valid_image(photo):
            flash(
                "File tidak valid atau dimensi gambar terlalu besar.",
                "danger"
            )

        else:

            filename = None

            try:

                # Simpan foto bila ada.
                if photo and photo.filename:

                    safe_original_name = secure_filename(photo.filename)

                    filename = (
                        f"{uuid.uuid4().hex}_{safe_original_name}"
                    )

                    photo_path = os.path.join(
                        current_app.config["UPLOAD_FOLDER"],
                        filename
                    )

                    photo.save(photo_path)

                # Klasifikasi dan rekomendasi AI.
                ai_category, confidence, model_status = classify_report(
                    title,
                    description
                )

                priority = recommend_priority(
                    category.name,
                    urgency,
                    description
                )

                # Buat objek laporan.
                report = Report(
                    report_number=(
                        f"LK-{datetime.now().strftime('%y%m%d')}-"
                        f"{uuid.uuid4().hex[:6].upper()}"
                    ),

                    user_id=current_user.id,
                    category_id=category.id,

                    title=title,
                    description=description,

                    photo_filename=filename,

                    latitude=lat,
                    longitude=lng,

                    rt_number=rt_number,
                    location_detail=location_detail,

                    urgency=urgency,
                    priority=priority,

                    ai_category=ai_category,
                    ai_confidence=confidence
                )

                db.session.add(report)
                db.session.flush()

                # Riwayat status awal.
                db.session.add(
                    ReportStatusHistory(
                        report_id=report.id,
                        old_status=None,
                        new_status=report.status,
                        note="Laporan dibuat oleh warga.",
                        actor_id=current_user.id
                    )
                )

                # Catatan hasil prediksi AI.
                db.session.add(
                    AIPrediction(
                        report_id=report.id,
                        model_name=(
                            "TF-IDF classifier"
                            if model_status == "model"
                            else "Belum tersedia"
                        ),
                        predicted_category=ai_category,
                        confidence=confidence,
                        recommendation=priority
                    )
                )

                # Catatan aktivitas.
                db.session.add(
                    ActivityLog(
                        actor_id=current_user.id,
                        action="report_created",
                        detail=f"Membuat laporan {report.report_number}"
                    )
                )

                # =================================================
                # DETEKSI DUPLIKAT
                # =================================================

                # Ambil maksimal 500 laporan terbaru
                # dengan kategori dan RT yang sama.
                existing_reports = (
                    Report.query
                    .filter(
                        Report.category_id == category.id,
                        Report.rt_number == rt_number,
                        Report.id != report.id
                    )
                    .order_by(Report.created_at.desc())
                    .limit(MAX_DUPLICATE_CANDIDATES)
                    .all()
                )

                # Deteksi kemungkinan laporan duplikat
                # berdasarkan kemiripan teks dan lokasi.
                duplicates = find_duplicate_candidates(
                    title,
                    description,
                    category.name,
                    existing_reports,
                    rt_number=rt_number,
                    latitude=lat,
                    longitude=lng
                )

                # Simpan seluruh transaksi.
                db.session.commit()

            except Exception:

                db.session.rollback()

                _remove_uploaded_file(filename)

                current_app.logger.exception(
                    "Gagal membuat laporan baru untuk user %s",
                    current_user.id
                )

                flash(
                    "Laporan gagal dikirim. Silakan coba kembali.",
                    "danger"
                )

                return redirect(url_for("reports.create"))

            # =================================================
            # PESAN SETELAH TRANSAKSI BERHASIL
            # =================================================

            if duplicates:

                flash(
                    f"Laporan terkirim. Sistem menemukan "
                    f"{len(duplicates)} kemungkinan laporan serupa "
                    "untuk ditinjau Admin.",
                    "info"
                )

            elif model_status != "model":

                flash(
                    "Laporan terkirim. Model klasifikasi belum dilatih; "
                    "kategori tetap menggunakan pilihan warga dan "
                    "dapat ditinjau Admin.",
                    "success"
                )

            else:

                flash(
                    "Laporan berhasil dikirim.",
                    "success"
                )

            return redirect(
                url_for("reports.detail", report_id=report.id)
            )

    # Tampilkan form untuk GET maupun POST
    # dengan input tidak valid.
    return render_template(
        "warga/report_form.html",
        categories=categories,
        rts=rts
    )


# =========================================================
# DAFTAR LAPORAN MILIK WARGA
# =========================================================

@bp.get("/")
@login_required
def list_mine():

    if current_user.role == "admin":
        return redirect(url_for("admin.reports"))

    if current_user.role != "warga":
        abort(403)

    reports = (
        Report.query
        .filter_by(user_id=current_user.id)
        .order_by(Report.created_at.desc())
        .all()
    )

    return render_template(
        "warga/reports.html",
        reports=reports
    )


# =========================================================
# DETAIL LAPORAN
# =========================================================

@bp.get("/<int:report_id>")
@login_required
def detail(report_id):

    report = db.get_or_404(Report, report_id)

    if current_user.role == "warga":

        if report.user_id != current_user.id:
            abort(403)

    elif current_user.role == "petugas":

        if report.assigned_petugas_id != current_user.id:
            abort(403)

    elif current_user.role != "admin":
        abort(403)

    return render_template(
        "reports/detail.html",
        report=report
    )


# =========================================================
# HAPUS LAPORAN
# =========================================================

@bp.post("/<int:report_id>/hapus")
@login_required
def delete_report(report_id):

    report = db.get_or_404(Report, report_id)

    if current_user.role == "warga":

        if report.user_id != current_user.id:
            abort(403)

    elif current_user.role != "admin":
        abort(403)

    report_number = report.report_number
    photo_filename = report.photo_filename

    try:

        Notification.query.filter_by(
            report_id=report.id
        ).delete(synchronize_session=False)

        AIPrediction.query.filter_by(
            report_id=report.id
        ).delete(synchronize_session=False)

        # Riwayat status mengikuti cascade pada Report.history.
        db.session.delete(report)

        db.session.commit()

    except Exception:

        db.session.rollback()

        current_app.logger.exception(
            "Gagal menghapus laporan %s",
            report_number
        )

        flash(
            "Laporan gagal dihapus. Silakan coba lagi.",
            "danger"
        )

        if current_user.role == "admin":
            return redirect(url_for("admin.reports"))

        return redirect(url_for("reports.list_mine"))

    # Hapus foto setelah transaksi database berhasil.
    _remove_uploaded_file(photo_filename)

    flash(
        f"Laporan {report_number} berhasil dihapus.",
        "success"
    )

    if current_user.role == "admin":
        return redirect(url_for("admin.reports"))

    return redirect(url_for("reports.list_mine"))


# =========================================================
# AKSES FOTO LAPORAN
# =========================================================

@bp.get("/foto/<path:filename>")
@login_required
def photo(filename):

    report = Report.query.filter_by(
        photo_filename=filename
    ).first_or_404()

    if current_user.role == "warga":

        if report.user_id != current_user.id:
            abort(403)

    elif current_user.role == "petugas":

        if report.assigned_petugas_id != current_user.id:
            abort(403)

    elif current_user.role != "admin":
        abort(403)

    return send_from_directory(
        current_app.config["UPLOAD_FOLDER"],
        filename
    )
