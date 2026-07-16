from datetime import datetime
from flask import Blueprint, request, session, redirect, url_for, render_template
from bson import ObjectId
import bcrypt
from db import (
    admins_col, reports_col, categories_col,
    residents_col, settings_col, announcements_col
)
from helpers import (
    report_dict, category_dict, resident_dict, announcement_dict,
    admin_required, safe_id, escape_regex
)

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/")
@admin_bp.route("")
@admin_required
def admin_index():
    total = reports_col.count_documents({})
    diajukan = reports_col.count_documents({"status": "Diajukan"})
    diproses = reports_col.count_documents({"status": "Diproses"})
    selesai = reports_col.count_documents({"status": "Selesai"})

    recent_reports = [report_dict(r) for r in reports_col.find().sort("tanggal", -1).limit(10)]

    cat_pipeline = [
        {"$group": {"_id": "$kategori", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
    ]
    kategori_stats = {c["_id"]: c["count"] for c in reports_col.aggregate(cat_pipeline) if c["_id"]}

    return render_template(
        "admin/index.html",
        total=total,
        diajukan=diajukan,
        diproses=diproses,
        selesai=selesai,
        reports=recent_reports,
        kategori_stats=kategori_stats,
    )


# ── CRUD Laporan ──

@admin_bp.route("/reports")
@admin_required
def admin_reports():
    status_filter = request.args.get("status", "")
    kategori_filter = request.args.get("kategori", "")
    search = request.args.get("search", "")

    query = {}
    if status_filter:
        query["status"] = status_filter
    if kategori_filter:
        query["kategori"] = kategori_filter
    if search:
        safe_search = escape_regex(search)
        query["$or"] = [
            {"judul": {"$regex": safe_search, "$options": "i"}},
            {"pelapor": {"$regex": safe_search, "$options": "i"}},
        ]

    reports = [report_dict(r) for r in reports_col.find(query).sort("tanggal", -1)]
    categories = [category_dict(c) for c in categories_col.find().sort("nama", 1)]

    return render_template(
        "admin/reports.html",
        reports=reports,
        categories=categories,
        status_filter=status_filter,
        kategori_filter=kategori_filter,
        search=search,
    )


@admin_bp.route("/reports/edit/<report_id>", methods=["POST"])
@admin_required
def admin_edit_report(report_id):
    oid = safe_id(report_id)
    if not oid:
        return redirect(url_for("admin.admin_reports"))

    update = {}
    for field in ["judul", "deskripsi", "kategori", "status", "lokasi"]:
        val = request.form.get(field)
        if val is not None:
            update[field] = val.strip()
    catatan = request.form.get("catatan", "").strip()
    if catatan:
        update["catatan"] = catatan

    if update:
        reports_col.update_one({"_id": oid}, {"$set": update})
    return redirect(url_for("admin.admin_reports"))


@admin_bp.route("/reports/hapus/<report_id>", methods=["POST"])
@admin_required
def admin_hapus_report(report_id):
    oid = safe_id(report_id)
    if oid:
        reports_col.delete_one({"_id": oid})
    return redirect(url_for("admin.admin_reports"))


# ── CRUD Warga ──

@admin_bp.route("/warga")
@admin_required
def admin_warga():
    rt_filter = request.args.get("rt", "")
    rw_filter = request.args.get("rw", "")
    status_filter = request.args.get("status", "")
    search = request.args.get("search", "")

    query = {}
    if rt_filter:
        query["rt"] = rt_filter
    if rw_filter:
        query["rw"] = rw_filter
    if status_filter:
        query["status"] = status_filter
    if search:
        safe_search = escape_regex(search)
        query["$or"] = [
            {"nama": {"$regex": safe_search, "$options": "i"}},
            {"nik": {"$regex": safe_search, "$options": "i"}},
        ]

    residents = [resident_dict(r) for r in residents_col.find(query).sort("nama", 1)]

    return render_template(
        "admin/warga.html",
        residents=residents,
        rt_filter=rt_filter,
        rw_filter=rw_filter,
        status_filter=status_filter,
        search=search,
    )


@admin_bp.route("/warga/tambah", methods=["POST"])
@admin_required
def admin_tambah_warga():
    nik = request.form.get("nik", "").strip()
    nama = request.form.get("nama", "").strip()
    if not nik or not nama:
        return redirect(url_for("admin.admin_warga"))

    if residents_col.find_one({"nik": nik}):
        return redirect(url_for("admin.admin_warga"))

    residents_col.insert_one({
        "nik": nik,
        "nama": nama,
        "alamat": request.form.get("alamat", "").strip(),
        "rt": request.form.get("rt", "").strip(),
        "rw": request.form.get("rw", "").strip(),
        "telepon": request.form.get("telepon", "").strip(),
        "status": request.form.get("status", "Aktif"),
        "terdaftar": False,
    })
    return redirect(url_for("admin.admin_warga"))


@admin_bp.route("/warga/edit/<resident_id>", methods=["POST"])
@admin_required
def admin_edit_warga(resident_id):
    oid = safe_id(resident_id)
    if not oid:
        return redirect(url_for("admin.admin_warga"))

    update = {}
    for field in ["nik", "nama", "alamat", "rt", "rw", "telepon", "status"]:
        val = request.form.get(field)
        if val is not None:
            update[field] = val.strip()
    if update:
        residents_col.update_one({"_id": oid}, {"$set": update})
    return redirect(url_for("admin.admin_warga"))


@admin_bp.route("/warga/hapus/<resident_id>", methods=["POST"])
@admin_required
def admin_hapus_warga(resident_id):
    oid = safe_id(resident_id)
    if oid:
        residents_col.delete_one({"_id": oid})
    return redirect(url_for("admin.admin_warga"))


# ── CRUD Kategori ──

@admin_bp.route("/kategori")
@admin_required
def admin_kategori():
    categories = [category_dict(c) for c in categories_col.find().sort("nama", 1)]
    return render_template("admin/kategori.html", categories=categories)


@admin_bp.route("/kategori/tambah", methods=["POST"])
@admin_required
def admin_tambah_kategori():
    nama = request.form.get("nama", "").strip()
    if not nama:
        return redirect(url_for("admin.admin_kategori"))
    if categories_col.find_one({"nama": nama}):
        return redirect(url_for("admin.admin_kategori"))

    categories_col.insert_one({
        "nama": nama,
        "icon": request.form.get("icon", ""),
        "warna": request.form.get("warna", "blue"),
        "jumlah_laporan": 0,
    })
    return redirect(url_for("admin.admin_kategori"))


@admin_bp.route("/kategori/edit/<cat_id>", methods=["GET", "POST"])
@admin_required
def admin_edit_kategori(cat_id):
    oid = safe_id(cat_id)
    if not oid:
        return redirect(url_for("admin.admin_kategori"))

    cat = categories_col.find_one({"_id": oid})
    if not cat:
        return redirect(url_for("admin.admin_kategori"))

    if request.method == "POST":
        update = {}
        if request.form.get("nama"):
            update["nama"] = request.form["nama"].strip()
        if request.form.get("warna"):
            update["warna"] = request.form["warna"]
        if request.form.get("icon"):
            update["icon"] = request.form["icon"]
        if update:
            categories_col.update_one({"_id": oid}, {"$set": update})
        return redirect(url_for("admin.admin_kategori"))

    return redirect(url_for("admin.admin_kategori"))


@admin_bp.route("/kategori/hapus/<cat_id>", methods=["POST"])
@admin_required
def admin_hapus_kategori(cat_id):
    oid = safe_id(cat_id)
    if oid:
        categories_col.delete_one({"_id": oid})
    return redirect(url_for("admin.admin_kategori"))


# ── CRUD Pengumuman ──

@admin_bp.route("/pengumuman")
@admin_required
def admin_pengumuman():
    announcements = [announcement_dict(a) for a in announcements_col.find().sort("tanggal", -1)]
    return render_template("admin/pengumuman.html", announcements=announcements)


@admin_bp.route("/pengumuman/tambah", methods=["POST"])
@admin_required
def admin_tambah_pengumuman():
    judul = request.form.get("judul", "").strip()
    isi = request.form.get("isi", "").strip()
    if not judul or not isi:
        return redirect(url_for("admin.admin_pengumuman"))

    now = datetime.now()
    announcements_col.insert_one({
        "judul": judul,
        "isi": isi,
        "tanggal": now.strftime("%d %b %Y"),
        "jam": request.form.get("jam", now.strftime("%H:%M")),
        "tipe": request.form.get("tipe", "Informasi"),
    })
    return redirect(url_for("admin.admin_pengumuman"))


@admin_bp.route("/pengumuman/edit/<announcement_id>", methods=["POST"])
@admin_required
def admin_edit_pengumuman(announcement_id):
    oid = safe_id(announcement_id)
    if not oid:
        return redirect(url_for("admin.admin_pengumuman"))

    update = {}
    if request.form.get("judul"):
        update["judul"] = request.form["judul"].strip()
    if request.form.get("isi"):
        update["isi"] = request.form["isi"].strip()
    if request.form.get("jam"):
        update["jam"] = request.form["jam"].strip()
    if request.form.get("tipe"):
        update["tipe"] = request.form["tipe"].strip()

    if update:
        announcements_col.update_one({"_id": oid}, {"$set": update})
    return redirect(url_for("admin.admin_pengumuman"))


@admin_bp.route("/pengumuman/hapus/<announcement_id>", methods=["POST"])
@admin_required
def admin_hapus_pengumuman(announcement_id):
    oid = safe_id(announcement_id)
    if oid:
        announcements_col.delete_one({"_id": oid})
    return redirect(url_for("admin.admin_pengumuman"))


# ── Pengaturan ──

@admin_bp.route("/pengaturan", methods=["GET", "POST"])
@admin_required
def admin_pengaturan():
    if request.method == "POST":
        if request.form.get("nama_admin") is not None:
            admin = admins_col.find_one({"_id": ObjectId(session["admin_id"])})
            if admin:
                update = {}
                nama = request.form.get("nama_admin", "").strip()
                if nama:
                    update["nama"] = nama
                email = request.form.get("email", "").strip()
                if email:
                    update["email"] = email
                username = request.form.get("username", "").strip()
                if username:
                    update["username"] = username
                password = request.form.get("password", "").strip()
                if password:
                    if len(password) < 6:
                        return redirect(url_for("admin.admin_pengaturan"))
                    update["password"] = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

                if update:
                    admins_col.update_one({"_id": ObjectId(session["admin_id"])}, {"$set": update})
                    if "nama" in update:
                        session["admin_name"] = update["nama"]
        else:
            allowed_fields = {
                "notifikasi_email", "verifikasi_laporan", "registrasi_warga",
                "laporan_anonim", "nama_desa", "rt", "rw", "kecamatan", "kota", "provinsi"
            }
            update = {}
            for field in allowed_fields:
                val = request.form.get(field)
                if val is not None:
                    if field in ("notifikasi_email", "verifikasi_laporan", "registrasi_warga", "laporan_anonim"):
                        update[field] = (val == "on")
                    else:
                        update[field] = val.strip()

            if update:
                settings_col.update_one({"_id": "global"}, {"$set": update}, upsert=True)

        return redirect(url_for("admin.admin_pengaturan"))

    s = settings_col.find_one({"_id": "global"}) or {}
    admin = admins_col.find_one({"_id": ObjectId(session["admin_id"])}) or {}

    settings = {
        "notifikasi_email": s.get("notifikasi_email", True),
        "verifikasi_laporan": s.get("verifikasi_laporan", True),
        "registrasi_warga": s.get("registrasi_warga", False),
        "laporan_anonim": s.get("laporan_anonim", False),
        "nama_desa": s.get("nama_desa", "Pelaporan Desa"),
        "rt": s.get("rt", "02"),
        "rw": s.get("rw", "01"),
        "kecamatan": s.get("kecamatan", "Kecamatan Contoh"),
        "kota": s.get("kota", "Kota Contoh"),
        "provinsi": s.get("provinsi", "Provinsi Contoh"),
    }

    admin_data = {
        "nama": admin.get("nama", ""),
        "email": admin.get("email", ""),
        "username": admin.get("username", ""),
    }

    return render_template("admin/pengaturan.html", settings=settings, admin_data=admin_data)
