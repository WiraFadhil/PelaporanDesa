from flask import Blueprint, request, session, redirect, url_for, render_template
import bcrypt
from bson import ObjectId
from db import admins_col, residents_col, settings_col
from helpers import s, safe_id

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
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
            return redirect(url_for("admin.admin_index"))

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
        return redirect(url_for("public.index"))

    return render_template("login.html", error=None)


@auth_bp.route("/masuk")
def masuk():
    return redirect("/login")


@auth_bp.route("/daftar", methods=["GET", "POST"])
def daftar():
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
        return redirect(url_for("public.index"))

    return render_template("daftar.html", error=None)


@auth_bp.route("/keluar")
def keluar():
    session.pop("resident_id", None)
    session.pop("resident_name", None)
    session.pop("resident_nik", None)
    return redirect(url_for("public.index"))


@auth_bp.route("/admin/login")
def admin_login():
    return redirect("/login#admin")


@auth_bp.route("/admin/logout")
def admin_logout():
    session.pop("admin_id", None)
    session.pop("admin_name", None)
    return redirect("/login#admin")


@auth_bp.route("/profil", methods=["GET", "POST"])
def profil():
    from helpers import resident_required, resident_dict
    return _profil()


def _profil():
    if "resident_id" not in session:
        return redirect(url_for("auth.masuk"))
    from bson import ObjectId
    from db import residents_col
    from helpers import resident_dict
    import bcrypt

    resident = residents_col.find_one({"_id": ObjectId(session["resident_id"])})
    if not resident:
        return redirect(url_for("auth.masuk"))

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
        return redirect(url_for("auth.profil"))

    return render_template("profil.html", resident=resident_dict(resident), error=None)
