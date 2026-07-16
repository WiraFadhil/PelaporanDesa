import os
import uuid
from datetime import datetime
from flask import Blueprint, request, session, redirect, url_for, render_template, send_from_directory
from bson import ObjectId
from db import reports_col, categories_col, residents_col
from helpers import (
    report_dict, category_dict, resident_dict,
    resident_required, safe_id, allowed_file
)

reports_bp = Blueprint("reports", __name__)


@reports_bp.route("/laporan-saya")
@resident_required
def laporan_saya():
    nik = session["resident_nik"]
    status_filter = request.args.get("status", "")
    search = request.args.get("search", "")

    query = {"nik": nik}
    if status_filter:
        query["status"] = status_filter
    if search:
        from helpers import escape_regex
        safe_search = escape_regex(search)
        query["$or"] = [
            {"judul": {"$regex": safe_search, "$options": "i"}},
            {"deskripsi": {"$regex": safe_search, "$options": "i"}},
        ]

    reports = [report_dict(r) for r in reports_col.find(query).sort("tanggal", -1)]
    diajukan = reports_col.count_documents({"nik": nik, "status": "Diajukan"})
    diproses = reports_col.count_documents({"nik": nik, "status": "Diproses"})
    selesai = reports_col.count_documents({"nik": nik, "status": "Selesai"})

    return render_template(
        "laporan-saya.html",
        reports=reports,
        diajukan=diajukan,
        diproses=diproses,
        selesai=selesai,
        status_filter=status_filter,
        search=search,
    )


@reports_bp.route("/buat-laporan", methods=["GET", "POST"])
@resident_required
def buat_laporan():
    categories = [category_dict(c) for c in categories_col.find().sort("nama", 1)]

    if request.method == "POST":
        judul = request.form.get("judul", "").strip()
        deskripsi = request.form.get("deskripsi", "").strip()
        kategori = request.form.get("kategori", "").strip()
        lokasi = request.form.get("lokasi", "").strip()

        if not judul or not deskripsi or not kategori:
            return render_template(
                "buat-laporan.html",
                categories=categories,
                error="Judul, deskripsi, dan kategori harus diisi"
            )

        from flask import current_app as app
        resident = residents_col.find_one({"_id": ObjectId(session["resident_id"])})
        now = datetime.now()

        foto_filenames = []
        foto_files = request.files.getlist("foto")
        for f in foto_files[:3]:
            if f and f.filename != "" and allowed_file(f.filename):
                ext = f.filename.rsplit(".", 1)[1].lower()
                filename = f"{uuid.uuid4().hex}.{ext}"
                f.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
                foto_filenames.append(filename)

        report = {
            "judul": judul,
            "deskripsi": deskripsi,
            "kategori": kategori,
            "pelapor": resident.get("nama", ""),
            "nik": resident.get("nik", ""),
            "rt": resident.get("rt", ""),
            "rw": resident.get("rw", ""),
            "lokasi": lokasi,
            "foto": foto_filenames,
            "status": "Diajukan",
            "tanggal": now.strftime("%d %b %Y"),
            "catatan": "",
            "created_at": now,
        }
        reports_col.insert_one(report)

        categories_col.update_one(
            {"nama": kategori},
            {"$inc": {"jumlah_laporan": 1}}
        )

        return redirect(url_for("reports.laporan_saya"))

    return render_template("buat-laporan.html", categories=categories, error=None)


@reports_bp.route("/upload", methods=["POST"])
def upload_file():
    from flask import current_app as app
    if "file" not in request.files:
        return {"error": "Tidak ada file"}, 400
    file = request.files["file"]
    if file.filename == "" or not allowed_file(file.filename):
        return {"error": "File tidak valid"}, 400

    ext = file.filename.rsplit(".", 1)[1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

    return {"filename": filename, "url": url_for("reports.uploaded_file", filename=filename)}


@reports_bp.route("/uploads/<filename>")
def uploaded_file(filename):
    from flask import current_app as app
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)
