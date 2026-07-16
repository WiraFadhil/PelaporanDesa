import re
import os
import secrets
from functools import wraps
from bson import ObjectId
from bson.errors import InvalidId
from flask import session, redirect, url_for
from config import ALLOWED_EXTENSIONS, SECRET_KEY
from db import admins_col, residents_col


def s(oid):
    return str(oid)


def safe_id(id_str):
    try:
        return ObjectId(id_str)
    except (InvalidId, TypeError):
        return None


def escape_regex(s):
    return re.sub(r'[.*+?^${}()|[\]\\]', r'\\' + '&', s)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "admin_id" not in session:
            return redirect(url_for("auth.admin_login"))
        return f(*args, **kwargs)
    return wrapper


def resident_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "resident_id" not in session:
            return redirect(url_for("auth.masuk"))
        resident = residents_col.find_one({"_id": ObjectId(session["resident_id"])})
        if not resident:
            session.pop("resident_id", None)
            session.pop("resident_name", None)
            session.pop("resident_nik", None)
            return redirect(url_for("auth.masuk"))
        return f(*args, **kwargs)
    return wrapper


def report_dict(r):
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
