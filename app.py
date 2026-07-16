from flask import Flask
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

from config import UPLOAD_FOLDER
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

from routes.auth import auth_bp
from routes.public import public_bp
from routes.reports import reports_bp
from routes.admin import admin_bp

app.register_blueprint(auth_bp)
app.register_blueprint(public_bp)
app.register_blueprint(reports_bp)
app.register_blueprint(admin_bp)


@app.errorhandler(404)
def not_found(e):
    return "<h1>404 - Halaman tidak ditemukan</h1><p><a href='/'>Kembali ke Beranda</a></p>", 404


@app.errorhandler(500)
def server_error(e):
    return "<h1>500 - Terjadi kesalahan server</h1><p><a href='/'>Kembali ke Beranda</a></p>", 500
