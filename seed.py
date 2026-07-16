import bcrypt
from db import admins_col, categories_col, residents_col, reports_col, announcements_col, settings_col

def seed_database():
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
