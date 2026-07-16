"""
app.py — Server-Side Rendering (SSR) untuk Sistem Pelaporan Warga Desa

ARSITEKTUR:
  Setiap route langsung query MongoDB, lalu render_template() dengan data
  dikirim sebagai variabel Jinja (BUKAN jsonify). Semua form pakai
  <form method="POST"> biasa, bukan fetch/JSON. Setelah create/update/delete,
  redirect ke halaman terkait pakai redirect(url_for(.)).
  Tidak ada endpoint /api/... — semuanya langsung di-render dari server.

ALUR:
  Browser → request → Flask route → query MongoDB → render_template(html, data)
  Browser ← HTML lengkap (sudah berisi data dari server) ← Flask

KEUNTUNGAN:
  - Lebih sederhana (satu route per halaman + aksinya)
  - SEO-friendly (konten sudah ada di HTML, tidak perlu JS render)
  - Cocok untuk tugas kuliah karena mudah dijelaskan
"""

import os
import re
import uuid
import secrets
from datetime import datetime, timedelta
from functools import wraps

from bson import ObjectId
from bson.errors import InvalidId

from flask import (
    Flask, request, session,
    send_from_directory, redirect, url_for, render_template
)
from pymongo import MongoClient
import bcrypt

from config import MONGO_URI, DB_NAME, SECRET_KEY, UPLOAD_FOLDER, ALLOWED_EXTENSIONS

# ── Inisialisasi Flask ──────────────────────────────────
app = Flask(__name__)
app.secret_key = SECRET_KEY or secrets.token_hex(32)
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

# ── Koneksi MongoDB ─────────────────────────────────────
client = MongoClient(MONGO_URI)
db = client[DB_NAME]

admins_col = db["admins"]
reports_col = db["reports"]
categories_col = db["categories"]
residents_col = db["residents"]
settings_col = db["settings"]
announcements_col = db["announcements"]


# ── Helper: konversi ObjectId → string untuk Jinja ──────
def s(oid):
    """Mengubah ObjectId MongoDB jadi string agar bisa dipakai di {{ }} Jinja"""
    return str(oid)


def safe_id(id_str):
    """Mengubah string jadi ObjectId, return None jika tidak valid"""
    try:
        return ObjectId(id_str)
    except (InvalidId, TypeError):
        return None


def escape_regex(s):
    """Escape karakter regex agar aman dipakai di $regex MongoDB"""
    return re.sub(r'[.*+?^${}()|[\]\\]', r'\\' + '&', s)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ── Decorator: cek login admin ──────────────────────────
def admin_required(f):
    """Hanya bisa diakses jika session admin_id ada"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "admin_id" not in session:
            # Redirect ke halaman login admin, bukan return 401 JSON
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return wrapper


# ── Decorator: cek login warga ──────────────────────────
def resident_required(f):
    """Hanya bisa diakses jika session resident_id ada"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "resident_id" not in session:
            # Redirect ke halaman masuk warga
            return redirect(url_for("masuk"))
        # Cek apakah warga masih ada di DB
        resident = residents_col.find_one({"_id": ObjectId(session["resident_id"])})
        if not resident:
            session.pop("resident_id", None)
            session.pop("resident_name", None)
            session.pop("resident_nik", None)
            return redirect(url_for("masuk"))
        return f(*args, **kwargs)
    return wrapper


# ── Helpers untuk konversi data (object → dict) ─────────
def report_dict(r):
    """Konversi dokumen report dari MongoDB ke dict siap Jinja"""
    return {
        "id": s(r["_id"]),
        "judul": r.get("judul", ""),
        "deskripsi": r.get("deskripsi", ""),
        "kategori": r.get("kategori", ""),
        "pelapor": r.get("pelapor", ""),
        "nik": r.get("nik", ""),
        "rt": r.get("rt", ""),
        "rw": r.get("rw", ""),
        "lokasi": r.get("lokasi", ""),
        "foto": r.get("foto", []),
        "status": r.get("status", "Diajukan"),
        "tanggal": r.get("tanggal", ""),
        "catatan": r.get("catatan", ""),
    }


def category_dict(c):
    return {
        "id": s(c["_id"]),
        "nama": c.get("nama", ""),
        "icon": c.get("icon", ""),
        "warna": c.get("warna", "blue"),
        "jumlah_laporan": c.get("jumlah_laporan", 0),
    }


def resident_dict(r):
    return {
        "id": s(r["_id"]),
        "nik": r.get("nik", ""),
        "nama": r.get("nama", ""),
        "alamat": r.get("alamat", ""),
        "rt": r.get("rt", ""),
        "rw": r.get("rw", ""),
        "telepon": r.get("telepon", ""),
        "status": r.get("status", "Aktif"),
        "terdaftar": r.get("terdaftar", False),
    }


def announcement_dict(a):
    return {
        "id": s(a["_id"]),
        "judul": a.get("judul", ""),
        "isi": a.get("isi", ""),
        "tanggal": a.get("tanggal", ""),
        "jam": a.get("jam", ""),
        "tipe": a.get("tipe", "Informasi"),
    }



# ── HALAMAN PUBLIK / WARGA ─────────────────────────────

@app.route("/")
def index():
    """
    Halaman utama publik.
    Tampilkan: ringkasan statistik, kategori, pengumuman terbaru.
    Data dikirim sebagai variabel Jinja, bukan fetch().
    """

    # Statistik laporan
    total_reports = reports_col.count_documents({})
    diajukan = reports_col.count_documents({"status": "Diajukan"})
    diproses = reports_col.count_documents({"status": "Diproses"})
    selesai = reports_col.count_documents({"status": "Selesai"})

    # Kategori
    categories = [category_dict(c) for c in categories_col.find().sort("nama", 1)]

    # Pengumuman (5 terbaru)
    announcements = [announcement_dict(a) for a in announcements_col.find().sort("tanggal", -1).limit(5)]

    # Laporan terbaru (5 terbaru)
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


# ── Auth Warga ──────────────────────────────────────────

@app.route("/masuk")
def masuk():
    return redirect("/login")

@app.route("/login", methods=["GET", "POST"])
def login():
    """
    Halaman login gabungan: warga (NIK) atau admin (username).
    Tab dipilih via hidden field 'role'.
    """
    if request.method == "POST":
        role = request.form.get("role", "warga")

        if role == "admin":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "").strip()
            if not username or not password:
                return render_template("login.html", error="Username dan password harus diisi")

            admin = admins_col.find_one({"username": username})
            if not admin or not bcrypt.checkpw(password.encode(), admin["password"].encode()):
                return render_template("login.html", error="Username atau password salah")

            session["admin_id"] = s(admin["_id"])
            session["admin_name"] = admin.get("nama", "Admin")
            return redirect(url_for("admin_index"))
        else:
            nik = request.form.get("nik", "").strip()
            password = request.form.get("password", "").strip()

            if not nik or not password:
                return render_template("login.html", error="NIK dan password harus diisi", role="warga")

            resident = residents_col.find_one({"nik": nik})
            if not resident:
                return render_template("login.html", error="NIK tidak terdaftar", role="warga")
            if not resident.get("terdaftar") or "password" not in resident:
                return render_template("login.html", error="Anda belum mendaftar. Silakan daftar terlebih dahulu.", role="warga")
            if not bcrypt.checkpw(password.encode(), resident["password"].encode()):
                return render_template("login.html", error="NIK atau password salah", role="warga")
            if resident.get("status") != "Aktif":
                return render_template("login.html", error="Akun Anda tidak aktif. Hubungi admin.", role="warga")

            session["resident_id"] = s(resident["_id"])
            session["resident_name"] = resident.get("nama", "")
            session["resident_nik"] = nik
            return redirect(url_for("index"))

    return render_template("login.html", error=None)


@app.route("/daftar", methods=["GET", "POST"])
def daftar():
    """
    Halaman registrasi warga.
    Cek setting 'registrasi_warga' dulu — jika False, tolak.
    """
    reg_setting = settings_col.find_one({"_id": "global"})
    if reg_setting and not reg_setting.get("registrasi_warga", False):
        return render_template("daftar.html", error="Pendaftaran warga sedang dinonaktifkan oleh admin")

    if request.method == "POST":
        nik = request.form.get("nik", "").strip()
        password = request.form.get("password", "").strip()
        nama = request.form.get("nama", "").strip()
        alamat = request.form.get("alamat", "").strip()
        rt = request.form.get("rt", "").strip()
        rw = request.form.get("rw", "").strip()
        telepon = request.form.get("telepon", "").strip()

        if not nik or not password:
            return render_template("daftar.html", error="NIK dan password harus diisi")
        if not nama:
            return render_template("daftar.html", error="Nama harus diisi")
        if len(password) < 6:
            return render_template("daftar.html", error="Password minimal 6 karakter")

        existing = residents_col.find_one({"nik": nik})
        if existing:
            if existing.get("terdaftar"):
                return render_template("daftar.html", error="NIK ini sudah terdaftar")
            # NIK ada di database tapi belum terdaftar — update data akun
            hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
            residents_col.update_one(
                {"_id": existing["_id"]},
                {"$set": {
                    "password": hashed, "terdaftar": True,
                    "nama": nama, "alamat": alamat, "rt": rt, "rw": rw, "telepon": telepon
                }}
            )
            resident_id = s(existing["_id"])
            resident_nama = nama
        else:
            # NIK baru — insert dokumen baru
            hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
            result = residents_col.insert_one({
                "nik": nik, "nama": nama, "alamat": alamat,
                "rt": rt, "rw": rw, "telepon": telepon,
                "status": "Aktif", "password": hashed, "terdaftar": True,
            })
            resident_id = s(result.inserted_id)
            resident_nama = nama

        session["resident_id"] = resident_id
        session["resident_name"] = resident_nama
        session["resident_nik"] = nik

        return redirect(url_for("index"))

    return render_template("daftar.html", error=None)


@app.route("/keluar")
def keluar():
    """Logout warga: hapus session, redirect ke index"""
    session.pop("resident_id", None)
    session.pop("resident_name", None)
    session.pop("resident_nik", None)
    return redirect(url_for("index"))


@app.route("/profil", methods=["GET", "POST"])
@resident_required
def profil():
    """
    Halaman profil warga.
    GET = tampilkan form dengan data dari DB.
    POST = update data, redirect ke profil lagi.
    """
    resident = residents_col.find_one({"_id": ObjectId(session["resident_id"])})

    if request.method == "POST":
        nama = request.form.get("nama", "").strip()
        alamat = request.form.get("alamat", "").strip()
        rt = request.form.get("rt", "").strip()
        rw = request.form.get("rw", "").strip()
        telepon = request.form.get("telepon", "").strip()
        password_baru = request.form.get("password_baru", "").strip()

        if not nama:
            return render_template("profil.html", resident=resident_dict(resident), error="Nama harus diisi")

        update = {"nama": nama, "alamat": alamat, "rt": rt, "rw": rw, "telepon": telepon}
        if password_baru:
            if len(password_baru) < 6:
                return render_template("profil.html", resident=resident_dict(resident), error="Password minimal 6 karakter")
            update["password"] = bcrypt.hashpw(password_baru.encode(), bcrypt.gensalt()).decode()

        residents_col.update_one({"_id": resident["_id"]}, {"$set": update})
        session["resident_name"] = nama

        return redirect(url_for("profil"))

    return render_template("profil.html", resident=resident_dict(resident), error=None)


# ── CRUD Laporan (Warga) ────────────────────────────────

@app.route("/laporan-saya")
@resident_required
def laporan_saya():
    """
    Halaman daftar laporan milik warga yang login.
    Filter berdasarkan NIK dari session. Tampilkan juga ringkasan status.
    """
    nik = session["resident_nik"]

    # Ambil parameter filter dari query string (GET request biasa)
    status_filter = request.args.get("status", "")
    search = request.args.get("search", "")

    query = {"nik": nik}
    if status_filter:
        query["status"] = status_filter
    if search:
        safe_search = escape_regex(search)
        query["$or"] = [
            {"judul": {"$regex": safe_search, "$options": "i"}},
            {"deskripsi": {"$regex": safe_search, "$options": "i"}},
        ]

    reports = [report_dict(r) for r in reports_col.find(query).sort("tanggal", -1)]

    # Ringkasan jumlah per status
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


@app.route("/buat-laporan", methods=["GET", "POST"])
@resident_required
def buat_laporan():
    """
    Halaman buat laporan baru.
    GET = tampilkan form dengan daftar kategori.
    POST = simpan ke MongoDB lalu redirect ke laporan-saya.
    """
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

        # Update counter kategori
        categories_col.update_one(
            {"nama": kategori},
            {"$inc": {"jumlah_laporan": 1}}
        )

        return redirect(url_for("laporan_saya"))

    return render_template("buat-laporan.html", categories=categories, error=None)


# ── Halaman Informasi (Publik) ──────────────────────────

@app.route("/informasi")
def informasi():
    """
    Halaman informasi publik.
    Tampilkan pengumuman + statistik RW.
    """
    announcements = [announcement_dict(a) for a in announcements_col.find().sort("tanggal", -1)]

    # Statistik RW
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


# ═════════════════════════════════════════════════════════
#                   HALAMAN ADMIN
# ═════════════════════════════════════════════════════════

@app.route("/admin/login")
def admin_login():
    return redirect("/login#admin")


@app.route("/admin/logout")
def admin_logout():
    """Logout admin: hapus session admin"""
    session.pop("admin_id", None)
    session.pop("admin_name", None)
    return redirect("/login#admin")


# ── Dashboard Admin ─────────────────────────────────────

@app.route("/admin")
@app.route("/admin/")
@admin_required
def admin_index():
    """
    Dashboard admin: statistik laporan, tabel laporan terbaru.
    """
    total = reports_col.count_documents({})
    diajukan = reports_col.count_documents({"status": "Diajukan"})
    diproses = reports_col.count_documents({"status": "Diproses"})
    selesai = reports_col.count_documents({"status": "Selesai"})

    recent_reports = [report_dict(r) for r in reports_col.find().sort("tanggal", -1).limit(10)]

    # Statistik per kategori (untuk chart)
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


# ── CRUD Laporan (Admin) ────────────────────────────────

@app.route("/admin/reports")
@admin_required
def admin_reports():
    """
    Daftar semua laporan untuk admin.
    Support filter: status, kategori, search.
    """
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


@app.route("/admin/reports/edit/<report_id>", methods=["POST"])
@admin_required
def admin_edit_report(report_id):
    oid = safe_id(report_id)
    if not oid:
        return redirect(url_for("admin_reports"))

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

    return redirect(url_for("admin_reports"))


@app.route("/admin/reports/hapus/<report_id>", methods=["POST"])
@admin_required
def admin_hapus_report(report_id):
    """Hapus laporan, lalu redirect ke daftar laporan"""
    oid = safe_id(report_id)
    if oid:
        reports_col.delete_one({"_id": oid})
    return redirect(url_for("admin_reports"))


# ── CRUD Warga (Admin) ──────────────────────────────────

@app.route("/admin/warga")
@admin_required
def admin_warga():
    """
    Daftar semua warga. Filter: RT, RW, status, search.
    """
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


@app.route("/admin/warga/tambah", methods=["POST"])
@admin_required
def admin_tambah_warga():
    """Tambah warga baru dari form POST, redirect ke daftar warga"""
    nik = request.form.get("nik", "").strip()
    nama = request.form.get("nama", "").strip()

    if not nik or not nama:
        return redirect(url_for("admin_warga"))

    if residents_col.find_one({"nik": nik}):
        return redirect(url_for("admin_warga"))

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

    return redirect(url_for("admin_warga"))


@app.route("/admin/warga/edit/<resident_id>", methods=["POST"])
@admin_required
def admin_edit_warga(resident_id):
    oid = safe_id(resident_id)
    if not oid:
        return redirect(url_for("admin_warga"))

    update = {}
    for field in ["nik", "nama", "alamat", "rt", "rw", "telepon", "status"]:
        val = request.form.get(field)
        if val is not None:
            update[field] = val.strip()
    if update:
        residents_col.update_one({"_id": oid}, {"$set": update})
    return redirect(url_for("admin_warga"))


@app.route("/admin/warga/hapus/<resident_id>", methods=["POST"])
@admin_required
def admin_hapus_warga(resident_id):
    """Hapus warga"""
    oid = safe_id(resident_id)
    if oid:
        residents_col.delete_one({"_id": oid})
    return redirect(url_for("admin_warga"))


# ── CRUD Kategori (Admin) ───────────────────────────────

@app.route("/admin/kategori")
@admin_required
def admin_kategori():
    """Daftar kategori"""
    categories = [category_dict(c) for c in categories_col.find().sort("nama", 1)]
    return render_template("admin/kategori.html", categories=categories)


@app.route("/admin/kategori/tambah", methods=["POST"])
@admin_required
def admin_tambah_kategori():
    """Tambah kategori baru"""
    nama = request.form.get("nama", "").strip()
    if not nama:
        return redirect(url_for("admin_kategori"))

    if categories_col.find_one({"nama": nama}):
        return redirect(url_for("admin_kategori"))

    categories_col.insert_one({
        "nama": nama,
        "icon": request.form.get("icon", ""),
        "warna": request.form.get("warna", "blue"),
        "jumlah_laporan": 0,
    })

    return redirect(url_for("admin_kategori"))


@app.route("/admin/kategori/edit/<cat_id>", methods=["GET", "POST"])
@admin_required
def admin_edit_kategori(cat_id):
    """Edit kategori"""
    oid = safe_id(cat_id)
    if not oid:
        return redirect(url_for("admin_kategori"))

    cat = categories_col.find_one({"_id": oid})
    if not cat:
        return redirect(url_for("admin_kategori"))

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

        return redirect(url_for("admin_kategori"))

    return redirect(url_for("admin_kategori"))


@app.route("/admin/kategori/hapus/<cat_id>", methods=["POST"])
@admin_required
def admin_hapus_kategori(cat_id):
    """Hapus kategori"""
    oid = safe_id(cat_id)
    if oid:
        categories_col.delete_one({"_id": oid})
    return redirect(url_for("admin_kategori"))


# ── CRUD Pengumuman (Admin) ─────────────────────────────

@app.route("/admin/pengumuman")
@admin_required
def admin_pengumuman():
    """Daftar pengumuman"""
    announcements = [announcement_dict(a) for a in announcements_col.find().sort("tanggal", -1)]
    return render_template("admin/pengumuman.html", announcements=announcements)


@app.route("/admin/pengumuman/tambah", methods=["POST"])
@admin_required
def admin_tambah_pengumuman():
    """Tambah pengumuman"""
    judul = request.form.get("judul", "").strip()
    isi = request.form.get("isi", "").strip()
    if not judul or not isi:
        return redirect(url_for("admin_pengumuman"))

    now = datetime.now()
    announcements_col.insert_one({
        "judul": judul,
        "isi": isi,
        "tanggal": now.strftime("%d %b %Y"),
        "jam": request.form.get("jam", now.strftime("%H:%M")),
        "tipe": request.form.get("tipe", "Informasi"),
    })

    return redirect(url_for("admin_pengumuman"))


@app.route("/admin/pengumuman/edit/<announcement_id>", methods=["POST"])
@admin_required
def admin_edit_pengumuman(announcement_id):
    """Edit pengumuman"""
    oid = safe_id(announcement_id)
    if not oid:
        return redirect(url_for("admin_pengumuman"))

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

    return redirect(url_for("admin_pengumuman"))


@app.route("/admin/pengumuman/hapus/<announcement_id>", methods=["POST"])
@admin_required
def admin_hapus_pengumuman(announcement_id):
    """Hapus pengumuman"""
    oid = safe_id(announcement_id)
    if oid:
        announcements_col.delete_one({"_id": oid})
    return redirect(url_for("admin_pengumuman"))


# ── Pengaturan (Admin) ──────────────────────────────────

@app.route("/admin/pengaturan", methods=["GET", "POST"])
@admin_required
def admin_pengaturan():
    """
    Halaman pengaturan desa & admin.
    GET = tampilkan form dengan data dari DB.
    POST = simpan perubahan.
    """
    if request.method == "POST":
        # Deteksi bagian mana yang dikirim: jika ada field "nama_admin",
        # berarti ini form update profil admin.
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
                        return redirect(url_for("admin_pengaturan"))
                    update["password"] = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

                if update:
                    admins_col.update_one({"_id": ObjectId(session["admin_id"])}, {"$set": update})
                    if "nama" in update:
                        session["admin_name"] = update["nama"]
        else:
            # Form pengaturan desa
            allowed_fields = {
                "notifikasi_email", "verifikasi_laporan", "registrasi_warga",
                "laporan_anonim", "nama_desa", "rt", "rw", "kecamatan", "kota", "provinsi"
            }
            update = {}
            for field in allowed_fields:
                val = request.form.get(field)
                if val is not None:
                    # Boolean fields from checkbox: jika dicentang kirim "on", jika tidak tidak ada
                    if field in ("notifikasi_email", "verifikasi_laporan", "registrasi_warga", "laporan_anonim"):
                        update[field] = (val == "on")
                    else:
                        update[field] = val.strip()

            if update:
                settings_col.update_one({"_id": "global"}, {"$set": update}, upsert=True)

        return redirect(url_for("admin_pengaturan"))

    # GET: ambil data dari DB untuk diisi ke form
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


# ── File Upload ─────────────────────────────────────────

@app.route("/upload", methods=["POST"])
@admin_required
def upload_file():
    """Upload file, return JSON (dipakai drag-and-drop di form laporan)"""
    if "file" not in request.files:
        return {"error": "Tidak ada file"}, 400
    file = request.files["file"]
    if file.filename == "" or not allowed_file(file.filename):
        return {"error": "File tidak valid"}, 400

    ext = file.filename.rsplit(".", 1)[1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

    return {"filename": filename, "url": url_for("uploaded_file", filename=filename)}


@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


# ── Error Handler ───────────────────────────────────────

@app.errorhandler(404)
def not_found(e):
    return "<h1>404 - Halaman tidak ditemukan</h1><p><a href='/'>Kembali ke Beranda</a></p>", 404


@app.errorhandler(500)
def server_error(e):
    return "<h1>500 - Terjadi kesalahan server</h1><p><a href='/'>Kembali ke Beranda</a></p>", 500


# ── Seed Data ───────────────────────────────────────────

def seed_database():
    """Isi database awal jika masih kosong — hanya dijalankan sekali"""
    if admins_col.count_documents({}) > 0:
        return

    admins_col.insert_one({
        "username": "admin",
        "password": bcrypt.hashpw("admin123".encode(), bcrypt.gensalt()).decode(),
        "nama": "Admin Utama",
        "email": "admin@pelaporan-desa.id",
    })

    categories = [
        {"nama": "Fasilitas Umum", "icon": "building", "warna": "blue", "jumlah_laporan": 12},
        {"nama": "Kebersihan", "icon": "trash", "warna": "green", "jumlah_laporan": 8},
        {"nama": "Keamanan", "icon": "shield", "warna": "red", "jumlah_laporan": 5},
        {"nama": "Penerangan", "icon": "lightbulb", "warna": "amber", "jumlah_laporan": 6},
        {"nama": "Administrasi", "icon": "document", "warna": "purple", "jumlah_laporan": 4},
        {"nama": "Lainnya", "icon": "plus-circle", "warna": "gray", "jumlah_laporan": 3},
    ]
    for c in categories:
        categories_col.insert_one(c)

    default_password = bcrypt.hashpw("123456".encode(), bcrypt.gensalt()).decode()
    residents = [
        {"nik": "3273010101010001", "nama": "Budi Santoso", "alamat": "Gang Mawar No. 10", "rt": "01", "rw": "01", "telepon": "081234567890", "status": "Aktif", "password": default_password, "terdaftar": True},
        {"nik": "3273010101010002", "nama": "Siti Nurhaliza", "alamat": "Gang Melati No. 5", "rt": "01", "rw": "01", "telepon": "081234567891", "status": "Aktif", "password": default_password, "terdaftar": True},
        {"nik": "3273010101010003", "nama": "Agus Wijaya", "alamat": "Gang Anggrek No. 12", "rt": "02", "rw": "01", "telepon": "081234567892", "status": "Aktif", "password": default_password, "terdaftar": True},
        {"nik": "3273010101010004", "nama": "Dewi Lestari", "alamat": "Gang Mawar No. 8", "rt": "01", "rw": "01", "telepon": "081234567893", "status": "Aktif", "password": default_password, "terdaftar": True},
        {"nik": "3273010101010005", "nama": "Rudi Hermawan", "alamat": "Gang Anggrek No. 3", "rt": "02", "rw": "01", "telepon": "081234567894", "status": "Aktif", "password": default_password, "terdaftar": True},
        {"nik": "3273010101010006", "nama": "Ani Martini", "alamat": "Gang Melati No. 15", "rt": "01", "rw": "01", "telepon": "081234567895", "status": "Aktif", "password": default_password, "terdaftar": True},
    ]
    for r in residents:
        residents_col.insert_one(r)

    reports_data = [
        {"judul": "Jalan Berlubang di Depan Gang Mawar", "deskripsi": "Terdapat lubang besar di jalan depan Gang Mawar yang membahayakan pengendara motor.", "kategori": "Fasilitas Umum", "pelapor": "Budi Santoso", "nik": "3273010101010001", "rt": "01", "rw": "01", "lokasi": "Gang Mawar, RT 01 RW 01", "foto": [], "status": "Diajukan", "tanggal": "15 Jun 2026", "catatan": ""},
        {"judul": "Tumpukan Sampah di TPS RW 01", "deskripsi": "Tumpukan sampah sudah tidak terkendali di TPS RW 01, perlu segera diangkut.", "kategori": "Kebersihan", "pelapor": "Siti Nurhaliza", "nik": "3273010101010002", "rt": "01", "rw": "01", "lokasi": "TPS RW 01", "foto": [], "status": "Diproses", "tanggal": "14 Jun 2026", "catatan": "Sedang dijadwalkan pengangkutan"},
        {"judul": "Lampu Jalan Mati Sepanjang Gang Melati", "deskripsi": "Lampu penerangan jalan di Gang Melati mati total selama 3 hari terakhir.", "kategori": "Penerangan", "pelapor": "Agus Wijaya", "nik": "3273010101010003", "rt": "02", "rw": "01", "lokasi": "Gang Melati", "foto": [], "status": "Selesai", "tanggal": "13 Jun 2026", "catatan": "Lampu telah diperbaiki"},
        {"judul": "Saluran Air Tersumbat di RW 01", "deskripsi": "Saluran air di depan masjid tersumbat menyebabkan genangan air.", "kategori": "Fasilitas Umum", "pelapor": "Dewi Lestari", "nik": "3273010101010004", "rt": "01", "rw": "01", "lokasi": "Depan Masjid RW 01", "foto": [], "status": "Diajukan", "tanggal": "12 Jun 2026", "catatan": ""},
        {"judul": "Penerangan Jalan Kurang di Gang Anggrek", "deskripsi": "Gang Anggrek sangat gelap karena tidak ada lampu jalan, rawan kejahatan.", "kategori": "Keamanan", "pelapor": "Rudi Hermawan", "nik": "3273010101010005", "rt": "02", "rw": "01", "lokasi": "Gang Anggrek", "foto": [], "status": "Diproses", "tanggal": "10 Jun 2026", "catatan": "Sedang dalam pengajuan pemasangan"},
        {"judul": "Permohonan Surat Keterangan Domisili", "deskripsi": "Saya membutuhkan surat keterangan domisili untuk keperluan administrasi.", "kategori": "Administrasi", "pelapor": "Ani Martini", "nik": "3273010101010006", "rt": "01", "rw": "01", "lokasi": "Gang Melati No. 15", "foto": [], "status": "Selesai", "tanggal": "08 Jun 2026", "catatan": "Surat sudah diterbitkan"},
    ]
    for r in reports_data:
        reports_col.insert_one(r)

    announcements = [
        {"judul": "Kerja Bakti Lingkungan", "isi": "Akan diadakan kerja bakti lingkungan pada hari Minggu, 20 Juni 2026. Seluruh warga diharapkan berpartisipasi.", "tanggal": "15 Jun 2026", "jam": "07:00 - 12:00", "tipe": "Penting"},
        {"judul": "Pembayaran Iuran Warga", "isi": "Pembayaran iuran warga bulan Juni akan dilaksanakan pada tanggal 25-27 Juni 2026 di balai RW.", "tanggal": "14 Jun 2026", "jam": "08:00 - 16:00", "tipe": "Informasi"},
        {"judul": "Posyandu Balita", "isi": "Posyandu balita akan dilayani pada hari Rabu, 16 Juni 2026. Bawa kartu menuju sehat.", "tanggal": "13 Jun 2026", "jam": "09:00 - 14:00", "tipe": "Informasi"},
    ]
    for a in announcements:
        announcements_col.insert_one(a)

    settings_col.update_one(
        {"_id": "global"},
        {"$set": {
            "notifikasi_email": True, "verifikasi_laporan": True,
            "registrasi_warga": False, "laporan_anonim": False,
            "nama_desa": "Pelaporan Desa", "rt": "02", "rw": "01",
            "kecamatan": "Kecamatan Contoh", "kota": "Kota Contoh", "provinsi": "Provinsi Contoh",
        }},
        upsert=True,
    )

    print("Database seeded successfully!")


# ── Main ────────────────────────────────────────────────

if __name__ == "__main__":
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    seed_database()
    print(f"Server running at http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=True)
