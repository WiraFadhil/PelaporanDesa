from flask import Blueprint, render_template
from db import reports_col, categories_col, announcements_col, residents_col
from helpers import report_dict, category_dict, announcement_dict, resident_dict

public_bp = Blueprint("public", __name__)


@public_bp.route("/")
def index():
    total_reports = reports_col.count_documents({})
    diajukan = reports_col.count_documents({"status": "Diajukan"})
    diproses = reports_col.count_documents({"status": "Diproses"})
    selesai = reports_col.count_documents({"status": "Selesai"})

    categories = [category_dict(c) for c in categories_col.find().sort("nama", 1)]
    announcements = [announcement_dict(a) for a in announcements_col.find().sort("tanggal", -1).limit(5)]
    recent_reports = [report_dict(r) for r in reports_col.find().sort("created_at", -1).limit(5)]

    return render_template(
        "index.html",
        total_reports=total_reports,
        diajukan=diajukan,
        diproses=diproses,
        selesai=selesai,
        categories=categories,
        announcements=announcements,
        recent_reports=recent_reports,
    )


@public_bp.route("/informasi")
def informasi():
    announcements = [announcement_dict(a) for a in announcements_col.find().sort("tanggal", -1)]
    total_warga = residents_col.count_documents({})
    warga_aktif = residents_col.count_documents({"status": "Aktif"})
    total_rt_01 = residents_col.count_documents({"rt": "01"})
    total_rt_02 = residents_col.count_documents({"rt": "02"})

    return render_template(
        "informasi.html",
        announcements=announcements,
        total_warga=total_warga,
        warga_aktif=warga_aktif,
        total_rt_01=total_rt_01,
        total_rt_02=total_rt_02,
    )
