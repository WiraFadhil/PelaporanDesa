# STUDI LANJUT - Lengkap: Pelaporan Desa (Basis Data Non-Relasional)

> Panduan lengkap untuk final exam. Mencakup seluruh arsitektur, skema MongoDB,
> setiap operasi database, alur aplikasi, dan konsep NoSQL yang relevan.

---

## 1. RINGKASAN PROJEK

**Nama:** Pelaporan Desa RT 02 / RW 01
**Tujuan:** Sistem pengaduan dan pelaporan warga desa secara online.
**Tech Stack:**
- Backend: Python Flask
- Database: MongoDB (via PyMongo driver)
- Frontend: HTML + CSS + Vanilla JavaScript (tanpa framework)
- Autentikasi: Session-based + bcrypt password hashing
- File Storage: Filesystem lokal (uploads/)

---

## 2. MENGAPA MONGODB? (Konsep NoSQL)

### 2.1 MongoDB vs Relasional

| Aspek | SQL (MySQL/PostgreSQL) | MongoDB (NoSQL) |
|-------|----------------------|------------------|
| Struktur | Tabel dengan baris & kolom | Collection dokumen BSON/JSON |
| Skema | Skema ketat (schema-on-write) | Skema fleksibel (schema-on-read) |
| Relasi | JOIN antar tabel | Embedded documents atau denormalisasi |
| ID | Auto-increment INTEGER | ObjectId (12 byte hex) |
| Query | SQL string | Metode Python (.find(), .aggregate()) |
| Transaksi | ACID transactions | Limited transactions (sejak v4.0) |
| Skalabilitas | Vertical (tambah RAM/CPU) | Horizontal (sharding) |

### 2.2 Mengapa Cocok untuk Projek Ini

1. **Skema fleksibel:** Laporan bisa punya field berbeda (foto opsional, catatan kosong)
2. **Dokumen JSON-native:** Data dari frontend (JSON) langsung disimpan tanpa mapping
3. **Developer productivity:** Tidak perlu ORM, query langsung pakai Python dict
4. **Cocok untuk CRUD sederhana:** Operasi utama adalah create/read/update/delete

### 2.3 Konsep Dasar MongoDB

```
Database:  pelaporan_desa
  └── Collection: admins, reports, residents, categories, settings, announcements, events
       └── Document: Dokumen individual (seperti "baris" di SQL, tapi fleksibel)
```

**Istilah Penting:**
- **Database** = Kumpulan collection (mirip "schema" di SQL)
- **Collection** = Kumpulan dokumen (mirip "tabel" di SQL)
- **Document** = Satu unit data, format BSON/JSON (mirip "baris" di SQL)
- **Field** = Key-value pair dalam dokumen (mirip "kolom" di SQL)
- **ObjectId** = ID unik 12-byte yang di-generate otomatis oleh MongoDB

---

## 3. STRUKTUR DATABASE (Schema Setiap Collection)

### 3.1 Collection: `admins`

```json
{
  "_id": ObjectId("6650a1b2c3d4e5f6a7b8c9d0"),
  "username": "admin",
  "password": "$2b$12$...bcrypt_hash...",
  "nama": "Admin Utama",
  "email": "admin@pelaporan-desa.id"
}
```

**Penjelasan:**
- `_id`: ObjectId, di-generate otomatis oleh MongoDB
- `password`: Tidak disimpan plain text! Di-hash pakai `bcrypt.hashpw()` dengan salt
- Tidak ada role field — hanya ada satu admin, cukup pakai session

### 3.2 Collection: `reports`

```json
{
  "_id": ObjectId("..."),
  "judul": "Jalan Berlubang di Depan Gang Mawar",
  "deskripsi": "Terdapat lubang besar...",
  "kategori": "Fasilitas Umum",
  "pelapor": "Budi Santoso",
  "nik": "3273010101010001",
  "rt": "01",
  "rw": "01",
  "lokasi": "Gang Mawar, RT 01 RW 01",
  "foto": ["uuid1.jpg", "uuid2.jpg"],
  "status": "Diajukan",
  "tanggal": "15 Jun 2026",
  "catatan": "Sedang dijadwalkan perbaikan",
  "created_at": ISODate("2026-06-15T10:30:00Z")
}
```

**Penjelasan:**
- `kategori`: String biasa (denormalisasi) — tidak menyimpan ObjectId referensi ke categories
- `foto`: Array of strings (filename) — MongoDB mendukung array langsung di dokumen
- `status`: Enum string — "Diajukan" | "Diproses" | "Selesai"
- `created_at`: ISODate untuk sorting, `tanggal`: string yang sudah di-format untuk display

### 3.3 Collection: `categories`

```json
{
  "_id": ObjectId("..."),
  "nama": "Fasilitas Umum",
  "icon": "building",
  "warna": "blue",
  "jumlah_laporan": 12
}
```

**Penjelasan:**
- `jumlah_laporan`: Counter yang di-increment setiap kali laporan baru dengan kategori ini dibuat
- Ini contoh **denormalisasi** — jumlah dihitung dan disimpan, bukan dihitung ulang setiap query

### 3.4 Collection: `residents`

```json
{
  "_id": ObjectId("..."),
  "nik": "3273010101010001",
  "nama": "Budi Santoso",
  "alamat": "Gang Mawar No. 10",
  "rt": "01",
  "rw": "01",
  "telepon": "081234567890",
  "status": "Aktif",
  "password": "$2b$12$...bcrypt_hash...",
  "terdaftar": true
}
```

**Penjelasan:**
- `terdaftar`: Boolean — admin bisa daftarkan warga (terdaftar=false), lalu warga daftar sendiri (terdaftar=true)
- `password`: Hanya diisi jika warga sudah mendaftar sendiri
- Warga yang dibuat admin via panel (`POST /api/residents`) tidak punya password

### 3.5 Collection: `settings`

```json
{
  "_id": "global",
  "notifikasi_email": true,
  "verifikasi_laporan": true,
  "registrasi_warga": false,
  "laporan_anonim": false,
  "nama_desa": "Pelaporan Desa",
  "rt": "02",
  "rw": "01",
  "kecamatan": "Kecamatan Contoh",
  "kota": "Kota Contoh",
  "provinsi": "Provinsi Contoh"
}
```

**Penjelasan:**
- Menggunakan `_id` string `"global"` — hanya ada satu dokumen (singleton pattern)
- Tidak pakai ObjectId tapi string biasa sebagai `_id`
- Inilah contoh MongoDB yang **tidak wajib pakai ObjectId** untuk `_id`

### 3.6 Collection: `announcements`

```json
{
  "_id": ObjectId("..."),
  "judul": "Kerja Bakti Lingkungan",
  "isi": "Akan diadakan kerja bakti...",
  "tanggal": "15 Jun 2026",
  "jam": "07:00 - 12:00",
  "tipe": "Penting"
}
```

**Penjelasan:**
- `tipe`: "Penting" | "Himbauan" | "Informasi" — menentukan warna badge di UI

### 3.7 Collection: `events`

```json
{
  "_id": ObjectId("..."),
  "judul": "Rapat RT Mingguan",
  "tanggal": "Setiap Sabtu",
  "jam": "19:00 - 21:00",
  "deskripsi": "Rapat rutin warga RT 02"
}
```

---

## 4. PERBANDINGAN: Relasional vs NoSQL pada Projek Ini

### 4.1 Jika Pakai SQL (Relasional)

```sql
-- Struktur tabel SQL yang diperlukan:
CREATE TABLE admins (id INT PK, username VARCHAR, password VARCHAR, ...);
CREATE TABLE categories (id INT PK, nama VARCHAR, ...);
CREATE TABLE residents (id INT PK, nik VARCHAR UNIQUE, nama VARCHAR, ...);
CREATE TABLE reports (
    id INT PK,
    judul VARCHAR,
    kategori_id INT FK -> categories(id),  -- RELASI
    pelapor_id INT FK -> residents(id),    -- RELASI
    status ENUM('Diajukan','Diproses','Selesai'),
    ...
);
-- Perlu JOIN untuk menampilkan nama kategori dan nama pelapor
SELECT r.*, c.nama as kategori_nama, res.nama as pelapor_nama
FROM reports r
JOIN categories c ON r.kategori_id = c.id
JOIN residents res ON r.pelapor_id = res.id;
```

### 4.2 Pakai MongoDB (NoSQL) — Apa yang Dilakukan

```python
# Tidak perlu JOIN! Kategori dan nama pelapor sudah ada di dokumen:
reports_col.find_one({"_id": ObjectId("...")})
# Result langsung:
# {
#   "judul": "Jalan Berlubang",
#   "kategori": "Fasilitas Umum",    // <- string langsung, bukan FK
#   "pelapor": "Budi Santoso",       // <- string langsung, bukan FK
#   ...
# }
```

**Trade-off:**
- **Kelebihan:** Query lebih cepat, tidak perlu JOIN
- **Kekurangan:** Data duplikasi (nama pelapor tersimpan di setiap laporan). Jika nama berubah, perlu update banyak dokumen

### 4.3 Strategi Denormalisasi yang Dipakai

| Data | Strategi | Alasan |
|------|----------|--------|
| Kategori laporan | String langsung di `reports.kategori` | Query lebih cepat, jarang berubah |
| Nama pelapor | String langsung di `reports.pelapor` | Hindupi JOIN untuk display |
| Jumlah laporan/kategori | Counter di `categories.jumlah_laporan` | Hindari `count_documents` setiap kali |
| RT/RW warga | Tersalin ke `reports.rt/rw` | Warga bisa pindah, laporan tetap |

---

## 5. SETIAP OPERASI MongoDB DI APP.PY (Lengkap)

### 5.1 Koneksi ke MongoDB

```python
from pymongo import MongoClient
client = MongoClient("mongodb://localhost:27017/")
db = client["pelaporan_desa"]

# Referensi collection:
admins_col = db["admins"]          # Cursor ke collection admins
reports_col = db["reports"]
categories_col = db["categories"]
residents_col = db["residents"]
settings_col = db["settings"]
announcements_col = db["announcements"]
events_col = db["events"]
```

**Yang terjadi di belakang:** PyMongo membuka koneksi TCP ke MongoDB server. Koneksi bersifat **lazy** — tidak benar-benar terkoneksi sampai query pertama dilakukan.

### 5.2 INSERT Operations

#### `insert_one()` — Insert satu dokumen

```python
# 1. Insert admin (seed_database, app.py:864)
admins_col.insert_one({
    "username": "admin",
    "password": bcrypt.hashpw("admin123".encode(), bcrypt.gensalt()).decode(),
    "nama": "Admin Utama",
    "email": "admin@pelaporan-desa.id"
})
# MongoDB otomatis generate _id: ObjectId("...")
# Return: InsertOneResult(ObjectId("..."), acknowledged=True)

# 2. Insert laporan baru (app.py:432)
report = {
    "judul": "Jalan Berlubang",
    "deskripsi": "Terdapat lubang besar...",
    "kategori": "Fasilitas Umum",
    "pelapor": "Budi Santoso",
    "nik": "3273010101010001",
    "status": "Diajukan",
    "tanggal": "15 Jun 2026",
    "created_at": datetime.now(),  # Simpan datetime object, bukan string
    ...
}
result = reports_col.insert_one(report)
new_id = str(result.inserted_id)  # ObjectId -> string untuk response

# 3. Insert warga baru (app.py:613)
residents_col.insert_one({
    "nik": "3273010101010007",
    "nama": "Warga Baru",
    "status": "Aktif",
    "terdaftar": False,  # Belum daftar sendiri
})

# 4. Insert kategori (app.py:512)
categories_col.insert_one({
    "nama": "Kebersihan",
    "icon": "trash",
    "warna": "green",
    "jumlah_laporan": 0,  # Mulai dari 0
})

# 5. Insert pengumuman (app.py:736)
announcements_col.insert_one({
    "judul": "Kerja Bakti",
    "isi": "Akan diadakan kerja bakti...",
    "tanggal": "15 Jun 2026",
    "jam": "07:00 - 12:00",
    "tipe": "Penting",
})
```

### 5.3 READ Operations

#### `find_one()` — Cari satu dokumen

```python
# 1. Cari admin by username (login, app.py:146)
admin = admins_col.find_one({"username": "admin"})
# Filter: {"username": "admin"}
# Return: Document dict atau None

# 2. Cari admin by _id (session check, app.py:165)
admin = admins_col.find_one({"_id": ObjectId(session["admin_id"])})
# Penting: ObjectId("...") bukan string "..."
# MongoDB tidak akan menemukan jika tipe tidak cocok

# 3. Cari warga by NIK (login warga, app.py:258)
resident = residents_col.find_one({"nik": "3273010101010001"})

# 4. Cari pengaturan global (app.py:656)
s = settings_col.find_one({"_id": "global"})
# _id di sini string "global", bukan ObjectId!

# 5. Cek duplikasi NIK (app.py:600)
if residents_col.find_one({"nik": nik}):
    return jsonify({"error": "NIK sudah terdaftar"}), 400

# 6. Cek duplikasi nama kategori (app.py:503)
if categories_col.find_one({"nama": nama}):
    return jsonify({"error": "Kategori sudah ada"}), 400
```

#### `find()` — Cari banyak dokumen (dengan filter, sort, skip, limit)

```python
# 1. List laporan dengan filter + pagination (app.py:329-330)
query = {}
if status:
    query["status"] = status           # Filter exact match
if kategori:
    query["kategori"] = kategori       # Filter exact match
if search:
    query["$or"] = [                   # Filter regex (partial match)
        {"judul": {"$regex": search, "$options": "i"}},
        {"pelapor": {"$regex": search, "$options": "i"}},
    ]

total = reports_col.count_documents(query)   # Hitung total
cursor = reports_col.find(query)             # Mulai query
    .sort("tanggal", -1)                     # Sort descending (terbaru duluan)
    .skip((page - 1) * per_page)             # Skip untuk pagination
    .limit(per_page)                         # Batasi jumlah hasil
reports = [serialize_report(r) for r in cursor]  # Convert ke list of dict
```

**Operasi MongoDB yang terjadi:**
```
db.reports.find({
    "status": "Diajukan",
    "$or": [
        {"judul": {"$regex": "jalan", "$options": "i"}},
        {"pelapor": {"$regex": "jalan", "$options": "i"}}
    ]
}).sort({"tanggal": -1}).skip(0).limit(10)
```

#### `count_documents()` — Hitung jumlah dokumen

```python
# Hitung total laporan (app.py:384)
total = reports_col.count_documents({})         # {} = tanpa filter = semua

# Hitung per status (app.py:385-387)
diajukan = reports_col.count_documents({"status": "Diajukan"})
diproses = reports_col.count_documents({"status": "Diproses"})
selesai  = reports_col.count_documents({"status": "Selesai"})

# Hitung laporan warga tertentu (app.py:366-368)
diajukan = reports_col.count_documents({"nik": nik, "status": "Diajukan"})
# Kombinasi 2 filter = AND logic
```

### 5.4 UPDATE Operations

#### `update_one()` — Update satu dokumen

```python
# 1. Update dengan $set (app.py:470)
reports_col.update_one(
    {"_id": oid},                    # Filter: cari dokumen dengan _id ini
    {"$set": {                       # $set: update field tertentu
        "status": "Diproses",
        "catatan": "Sedang diproses"
    }}
)

# 2. Update warga (app.py:634)
residents_col.update_one(
    {"_id": oid},
    {"$set": {
        "nik": "3273010101010001",
        "nama": "Budi Santoso Updated",
        "alamat": "Alamat Baru"
    }}
)

# 3. Update dengan $inc (increment counter) (app.py:434-436)
categories_col.update_one(
    {"nama": "Fasilitas Umum"},     # Filter by nama (bukan _id!)
    {"$inc": {"jumlah_laporan": 1}} # $inc: tambah 1 ke field jumlah_laporan
)
# INI PENTING: $inc adalah atomic operation!
# Tidak perlu read-modify-write (read dulu, tambah 1, lalu write)
# MongoDB menjamin tidak ada race condition

# 4. Upsert (insert jika belum ada) (app.py:692-696)
settings_col.update_one(
    {"_id": "global"},
    {"$set": update},
    upsert=True,   # Jika tidak ada dokumen dengan _id "global", buat baru!
)

# 5. Register warga — update field yang sudah ada (app.py:217-220)
residents_col.update_one(
    {"_id": existing["_id"]},
    {"$set": {
        "password": hashed,
        "terdaftar": True,
        "nama": nama,
        ...
    }}
)

# 6. Update admin profile (app.py:814)
admins_col.update_one(
    {"_id": ObjectId(session["admin_id"])},
    {"$set": {"nama": "Admin Baru", "email": "baru@email.com"}}
)
```

**Operator Update yang Dipakai:**

| Operator | Fungsi | Contoh |
|----------|--------|--------|
| `$set` | Set nilai field | `{"$set": {"status": "Aktif"}}` |
| `$inc` | Tambahkan angka | `{"$inc": {"jumlah_laporan": 1}}` |
| `upsert` | Auto-create jika tidak ada | `update_one(..., upsert=True)` |

### 5.5 DELETE Operations

```python
# 1. Hapus laporan (app.py:483)
reports_col.delete_one({"_id": oid})
# delete_one: Hapus SATU dokumen yang match pertama

# 2. Hapus kategori (app.py:549)
categories_col.delete_one({"_id": oid})

# 3. Hapus warga (app.py:647)
residents_col.delete_one({"_id": oid})

# 4. Hapus pengumuman (app.py:772)
announcements_col.delete_one({"_id": oid})
```

### 5.6 AGGREGATE Operations

```python
# Pipeline aggregation untuk statistik kategori (app.py:389-393)
category_pipeline = [
    {"$group": {"_id": "$kategori", "count": {"$sum": 1}}},
    {"$sort": {"count": -1}},
]
cat_stats = list(reports_col.aggregate(category_pipeline))
```

**Penjelasan Pipeline:**
```
$group:
  _id: "$kategori"     ← Group BY field "kategori"
                        ← "$kategori" artinya "ambil nilai field kategori"
  count: {"$sum": 1}   ← Hitung jumlah per grup

$sort:
  count: -1             ← Sort descending (kategori terbanyak di atas)

Hasil contoh:
[
  {"_id": "Fasilitas Umum", "count": 12},
  {"_id": "Kebersihan", "count": 8},
  {"_id": "Penerangan", "count": 6},
  ...
]
```

**Operasi MongoDB yang setara di SQL:**
```sql
SELECT kategori, COUNT(*) as count
FROM reports
GROUP BY kategori
ORDER BY count DESC;
```

---

## 6. KONEKSI antar Collection (Relasi di NoSQL)

### 6.1 Tidak Ada Formal Relationship

MongoDB **tidak punya foreign key constraint**. Relasi di-handle di level aplikasi:

```
reports.nik  ──────────►  residents.nik
    │                         │
    │  (tidak ada constraint,  │
    │   hanya string match)    │
    │                          │
reports.kategori ──────► categories.nama
    │                         │
    │  (tidak ada constraint)  │
    │                          │
reports.rt/rw ─────────► (RT/RW warga, tidak ada collection terpisah)
```

### 6.2 Cara Relasi Diimplementasikan

**Relasi Reports → Residents (via NIK):**
```python
# Saat buat laporan, ambil data warga dan simpan langsung:
resident = residents_col.find_one({"_id": ObjectId(session["resident_id"])})
report = {
    "pelapor": resident.get("nama", ""),    # Copy nama
    "nik": resident.get("nik", ""),          # Copy NIK
    "rt": resident.get("rt", ""),            # Copy RT
    "rw": resident.get("rw", ""),            # Copy RW
    ...
}

# Saat query laporan warga:
query = {"nik": nik}  # Filter by NIK yang tersimpan di laporan
cursor = reports_col.find(query)
```

**Relasi Reports → Categories (via nama):**
```python
# Saat buat laporan:
report = {"kategori": "Fasilitas Umum"}  # String nama, bukan ID

# Saat admin update status laporan, update counter kategori:
categories_col.update_one(
    {"nama": report["kategori"]},
    {"$inc": {"jumlah_laporan": 1}}
)
```

### 6.3 Embedded vs Referenced

| Type | Contoh di Projek | Kapan Dipakai |
|------|------------------|---------------|
| **Embedded** | `reports.foto: [array of strings]` | Data kecil, selalu diakses bersamaan |
| **Referenced** | `reports.nik → residents.nik` | Data besar, sering di-update terpisah |
| **Denormalized** | `reports.pelapor: "Budi Santoso"` | Performa > konsistensi |

---

## 7. OID / ObjectId — Penjelasan Lengkap

### 7.1 Apa itu ObjectId?

```python
from bson import ObjectId

oid = ObjectId()  # Generate baru
print(oid)        # 6650a1b2c3d4e5f6a7b8c9d0 (24 karakter hex)
print(len(oid.binary))  # 12 bytes
```

**Struktur 12 byte ObjectId:**
```
4 bytes  +  5 bytes   +  3 bytes
Timestamp   Random      Counter
(UNIX)      (unique)    (sequential)
```

### 7.2 Penting: ObjectId vs String

```python
# BENAR:
reports_col.find_one({"_id": ObjectId("6650a1b2c3d4e5f6a7b8c9d0")})

# SALAH — tidak akan menemukan:
reports_col.find_one({"_id": "6650a1b2c3d4e5f6a7b8c9d0"})
# TypeError: ObjectId required
```

### 7.3 Converting ObjectId ↔ String

```python
# ObjectId -> String (untuk dikirim ke frontend):
str_id = str(report["_id"])  # "6650a1b2c3d4e5f6a7b8c9d0"

# String -> ObjectId (untuk query):
oid = ObjectId(str_id)

# Dengan error handling:
def safe_object_id(id_str):
    try:
        return ObjectId(id_str)
    except (InvalidId, TypeError):
        return None
```

### 7.4 Custom _id (bukan ObjectId)

```python
# Settings collection pakai string sebagai _id:
settings_col.update_one(
    {"_id": "global"},    # "global" bukan ObjectId!
    {"$set": {...}},
    upsert=True
)
```

---

## 8. QUERY OPERATORS MongoDB

### 8.1 Operator Filter yang Dipakai

```python
# Exact match:
{"status": "Diajukan"}
{"nik": "3273010101010001"}

# $or — OR logic:
{"$or": [
    {"judul": {"$regex": "jalan", "$options": "i"}},
    {"pelapor": {"$regex": "jalan", "$options": "i"}}
]}

# $regex — Pattern matching (LIKE di SQL):
{"judul": {"$regex": "jalan", "$options": "i"}}
# $options: "i" = case-insensitive

# Multiple filters = AND logic:
{"nik": "3273010101010001", "status": "Diajukan"}
# Semua kondisi harus terpenuhi (implicit AND)
```

### 8.2 Operator Update yang Dipakai

```python
# $set — Set field value:
{"$set": {"status": "Diproses", "catatan": "Proses..."}}

# $inc — Increment numeric field:
{"$inc": {"jumlah_laporan": 1}}
```

### 8.3 Cursor Methods

```python
cursor = reports_col.find(query)
cursor.sort("tanggal", -1)   # -1 = descending, 1 = ascending
cursor.skip(10)               # Skip 10 dokumen pertama
cursor.limit(5)               # Ambil max 5 dokumen

# Kombinasi untuk pagination:
# Halaman 1: skip(0).limit(5)
# Halaman 2: skip(5).limit(5)
# Halaman 3: skip(10).limit(5)
# Formula: skip((page - 1) * per_page).limit(per_page)
```

---

## 9. AUTENTIKASI & SESSION

### 9.1 Login Admin

```
1. User submit username + password
2. Backend: admins_col.find_one({"username": username})
3. Backend: bcrypt.checkpw(password, admin["password"])
4. Jika cocok: session["admin_id"] = str(admin["_id"])
5. Flask menyimpan session di cookie (ter-encrypt)
6. Setiap request berikutnya, cookie dikirim otomatis
7. Decorator @login_required cek session["admin_id"]
```

**Kode:**
```python
# Login (app.py:137-152)
admin = admins_col.find_one({"username": username})
if not admin or not bcrypt.checkpw(password.encode(), admin["password"].encode()):
    return jsonify({"error": "Username atau password salah"}), 401

session["admin_id"] = str(admin["_id"])
session["admin_name"] = admin.get("nama", "Admin")

# Protected route check (app.py:87-93)
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "admin_id" not in session:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated
```

### 9.2 Login Warga

```
1. User submit NIK + password
2. Backend: residents_col.find_one({"nik": nik})
3. Cek: warga terdaftar? password ada? status aktif?
4. Jika cocok: session["resident_id"] = str(resident["_id"])
5. Decorator @resident_login_required cek session["resident_id"]
```

### 9.3 Password Hashing

```python
import bcrypt

# Hash password:
hashed = bcrypt.hashpw("admin123".encode(), bcrypt.gensalt()).decode()
# bcrypt.gensalt() = generate random salt
# bcrypt.hashpw() = hash dengan salt
# .decode() = convert bytes ke string untuk disimpan

# Verifikasi password:
bcrypt.checkpw("admin123".encode(), admin["password"].encode())
# Return True/False
```

**Mengapa bcrypt?**
- Password TIDAK pernah disimpan plain text
- bcrypt otomatis generate salt unik per password
- Brute-force sangat lambat (cost factor 12 = 2^12 = 4096 iterasi)

---

## 10. PAGINATION

### 10.1 Backend (Python/PyMongo)

```python
page = int(request.args.get("page", 1))
per_page = int(request.args.get("per_page", 10))

# Hitung total
total = reports_col.count_documents(query)

# Hitung total halaman
pages = max(1, (total + per_page - 1) // per_page)
# Contoh: 25 total, 10 per_page = (25+9)//10 = 3 halaman

# Query dengan pagination
cursor = reports_col.find(query) \
    .sort("tanggal", -1) \
    .skip((page - 1) * per_page) \
    .limit(per_page)
```

### 10.2 Frontend (JavaScript)

```javascript
// Kirim request dengan parameter page
api('/api/reports?page=2&per_page=10')

// Render tombol pagination
for (var i = 1; i <= data.pages; i++) {
    var btn = document.createElement('button');
    btn.textContent = i;
    btn.addEventListener('click', function() {
        loadReports(pageNum);  // Muat halaman yang dipilih
    });
}
```

---

## 11. AGGREGATION PIPELINE (Deep Dive)

### 11.1 Pipeline yang Dipakai

```python
# Statistik laporan per kategori (app.py:389-393)
pipeline = [
    {"$group": {"_id": "$kategori", "count": {"$sum": 1}}},
    {"$sort": {"count": -1}},
]
results = list(reports_col.aggregate(pipeline))
```

### 11.2 Stage-by-Stage Explanation

```
Input: Semua dokumen di collection "reports"

Stage 1: $group
┌──────────────────────────────────────────────────┐
│ Group by field "kategori"                        │
│                                                  │
│ Input:  [doc1(kategori=A), doc2(kategori=B),     │
│          doc3(kategori=A), doc4(kategori=A)]     │
│                                                  │
│ Output: [{_id: "A", count: 3},                  │
│          {_id: "B", count: 1}]                  │
└──────────────────────────────────────────────────┘

Stage 2: $sort
┌──────────────────────────────────────────────────┐
│ Sort by "count" descending (-1)                  │
│                                                  │
│ Input:  [{_id: "A", count: 3},                  │
│          {_id: "B", count: 1}]                  │
│                                                  │
│ Output: [{_id: "A", count: 3},                  │
│          {_id: "B", count: 1}]                  │
└──────────────────────────────────────────────────┘
```

### 11.3 SQL Equivalent

```sql
SELECT kategori, COUNT(*) as count
FROM reports
GROUP BY kategori
ORDER BY count DESC;
```

### 11.4 Pipeline Lain yang Mungkin Ditanya

```python
# Average (rata-rata)
[{"$group": {"_id": "$kategori", "avg": {"$avg": "$jumlah_laporan"}}}]

# Min/Max
[{"$group": {"_id": null, "min_date": {"$min": "$created_at"}, "max_date": {"$max": "$created_at"}}}]

# Limit hasil
[{"$group": {"_id": "$kategori", "count": {"$sum": 1}}}, {"$limit": 3}]

# Unwind array
[{"$unwind": "$foto"}, {"$group": {"_id": "$_id", "foto_count": {"$sum": 1}}}]
```

---

## 12. UPSERT — Insert atau Update

```python
# Upsert = Update jika ada, Insert jika belum ada (app.py:692-696)
settings_col.update_one(
    {"_id": "global"},         # Cari dokumen dengan _id = "global"
    {"$set": {"rt": "02"}},    # Update field rt
    upsert=True                # Jika tidak ditemukan, BUAT dokumen baru!
)

# Hasil di MongoDB:
# Jika ada: Update field rt
# Jika belum ada: Insert {_id: "global", rt: "02"}
```

---

## 13. FILE UPLOAD & STORAGE

```python
# Upload flow (app.py:820-836):
# 1. Terima file dari form
file = request.files["file"]

# 2. Validasi extension
if not allowed_file(file.filename):  # Cek .png/.jpg/.jpeg/.gif/.webp
    return jsonify({"error": "Jenis file tidak diizinkan"}), 400

# 3. Generate nama file unik (UUID)
ext = file.filename.rsplit(".", 1)[1].lower()
filename = f"{uuid.uuid4().hex}.{ext}"  # Contoh: "a1b2c3d4...hex.jpg"

# 4. Simpan ke folder uploads/
filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
file.save(filepath)

# 5. Return nama file (disimpan di reports.foto array)
return jsonify({"filename": filename, "url": f"/uploads/{filename}"})

# Yang masuk ke MongoDB:
# "foto": ["a1b2c3d4e5f6...jpg"]  — hanya filename, bukan file binary
```

**Mengapa tidak simpan file di MongoDB?**
- MongoDB bisa simpan Binary (BSON BinData), tapi:
  - Ukuran database membengkak
  - Tidak efisien untuk image serving
  - Tidak bisa di-cache oleh browser
- Filesystem lebih cepat untuk serving static files

---

## 14. ARSITEKTUR API (RESTful Pattern)

### 14.1 Pattern CRUD

```
CREATE:  POST   /api/reports         → Insert dokumen baru
READ:    GET    /api/reports         → Query + return list
READ:    GET    /api/reports/:id     → Find one by _id
UPDATE:  PUT    /api/reports/:id     → Update one by _id
DELETE:  DELETE /api/reports/:id     → Delete one by _id
```

### 14.2 Endpoint Lengkap

```
AUTH:
  POST /api/login              → admins_col.find_one + session
  POST /api/logout             → session.clear()
  GET  /api/me                 → admins_col.find_one({"_id": ObjectId(...)})
  POST /api/register           → residents_col.insert_one / update_one
  POST /api/masuk              → residents_col.find_one({"nik": ...})
  POST /api/keluar             → session.pop()

REPORTS:
  GET    /api/reports          → reports_col.find(query).sort().skip().limit()
  GET    /api/reports/stats    → reports_col.count_documents() + aggregate()
  POST   /api/reports          → reports_col.insert_one() + categories_col.update_one($inc)
  GET    /api/reports/:id      → reports_col.find_one({"_id": ObjectId(...)})
  PUT    /api/reports/:id      → reports_col.update_one({"_id": ...}, {"$set": ...})
  DELETE /api/reports/:id      → reports_col.delete_one({"_id": ...})
  GET    /api/reports/saya     → reports_col.find({"nik": ...}) + count per status

CATEGORIES:
  GET    /api/categories       → categories_col.find().sort("nama", 1)
  POST   /api/categories       → categories_col.insert_one()
  PUT    /api/categories/:id   → categories_col.update_one({"_id": ...}, {"$set": ...})
  DELETE /api/categories/:id   → categories_col.delete_one({"_id": ...})

RESIDENTS:
  GET    /api/residents        → residents_col.find(query).sort().skip().limit()
  POST   /api/residents        → residents_col.insert_one()
  PUT    /api/residents/:id    → residents_col.update_one({"_id": ...}, {"$set": ...})
  DELETE /api/residents/:id    → residents_col.delete_one({"_id": ...})

SETTINGS:
  GET    /api/settings         → settings_col.find_one({"_id": "global"})
  PUT    /api/settings         → settings_col.update_one({"_id": "global"}, upsert=True)

ANNOUNCEMENTS:
  GET    /api/announcements    → announcements_col.find().sort().limit()
  POST   /api/announcements    → announcements_col.insert_one()
  PUT    /api/announcements/:id → announcements_col.update_one()
  DELETE /api/announcements/:id → announcements_col.delete_one()

EVENTS:
  GET    /api/events           → events_col.find().sort().limit(5)

ADMIN:
  PUT    /api/update-admin     → admins_col.update_one()
  POST   /api/upload           → file.save() (filesystem, bukan MongoDB)
```

---

## 15. SEED DATA (Data Awal)

### 15.1 Kapan Seed Terjadi?

```python
# app.py:860-938
def seed_database():
    if admins_col.count_documents({}) > 0:
        return  # Skip jika sudah ada data
    # ... insert data awal
```

**Dipanggil sekali saat pertama kali app dijalankan.**

### 15.2 Data yang Di-seed

| Collection | Jumlah | Keterangan |
|-----------|--------|------------|
| admins | 1 | Username: admin, Password: admin123 |
| categories | 6 | Fasilitas Umum, Kebersihan, Keamanan, Penerangan, Administrasi, Lainnya |
| residents | 6 | Warga contoh dengan password default 123456 |
| reports | 6 | Laporan contoh dengan status berbeda |
| announcements | 3 | Pengumuman contoh (Penting, Informasi) |
| events | 3 | Agenda kegiatan rutin |
| settings | 1 | Dokumen global settings |

---

## 16. FRONTEND ↔ BACKEND INTERACTION

### 16.1 Flow Lengkap: Warga Buat Laporan

```
1. Warga buka buat-laporan.html
2. JS: loadReportCategories() → GET /api/categories
3. MongoDB: categories_col.find().sort("nama", 1)
4. JS: Render radio button kategori dari data

5. Warga isi form + submit
6. JS: fetch("/api/reports", {method: "POST", body: JSON.stringify(data)})
7. Flask: @resident_login_required → cek session["resident_id"]
8. Flask: residents_col.find_one({"_id": ObjectId(session["resident_id"])})
9. Flask: reports_col.insert_one(report)
10. Flask: categories_col.update_one({"nama": ...}, {"$inc": {"jumlah_laporan": 1}})
11. Flask: Return 201 Created
12. JS: Redirect ke laporan-saya.html
```

### 16.2 Flow Lengkap: Admin Update Status

```
1. Admin buka /admin/reports.html
2. JS: loadAdminReports() → GET /api/reports?status=&page=1
3. MongoDB: reports_col.find(query).sort().skip().limit()
4. JS: Render table rows dari data

5. Admin klik "Detail" pada laporan
6. JS: GET /api/reports/:id → reports_col.find_one({"_id": ObjectId(...)})
7. JS: Show modal dengan data laporan

8. Admin ubah status ke "Diproses" + tambah catatan
9. JS: PUT /api/reports/:id → {"status": "Diproses", "catatan": "..."}
10. MongoDB: reports_col.update_one({"_id": oid}, {"$set": {...}})
11. JS: Reload table
```

---

## 17. KEAMANAN (Security)

### 17.1 Yang Diproteksi

| Aspek | Cara |
|-------|------|
| Password | bcrypt hash (tidak plain text) |
| API endpoints | @login_required decorator (cek session) |
| File upload | Validasi extension + max 5MB |
| Session | HTTPOnly cookie + SameSite=Lax |
| CORS | Hanya localhost:5000 |
| Input | .strip() + validasi required fields |
| Regex injection | escape_regex() pada search input |
| XSS | esc() function escape HTML entities di frontend |
| ObjectId | safe_object_id() handle invalid ID |

### 17.2 Session Flow

```
1. Login → session["admin_id"] = "6650a1b2..."
2. Flask encrypt session data → kirim sebagai cookie "_flask_session"
3. Browser otomatis kirim cookie setiap request
4. Flask decrypt cookie → restore session dict
5. Route cek session["admin_id"] ada atau tidak
```

---

## 18. PERTANYAAN UMUM FINAL EXAM

### Q: Apa itu MongoDB?
**A:** MongoDB adalah NoSQL document-oriented database yang menyimpan data dalam format BSON (Binary JSON) di collection-collection. Tidak pakai tabel/baris seperti SQL, tapi pakai dokumen-field.

### Q: Apa bedanya ObjectId dengan auto-increment ID?
**A:** ObjectId di-generate client-side (12 byte: timestamp + random + counter), tidak perlu coordination dengan server. Auto-increment butuh sequence table di server. ObjectId bisa di-generate tanpa koneksi ke DB.

### Q: Kenapa project ini tidak pakai relasi Foreign Key?
**A:** MongoDB tidak support JOIN secara native. Data denormalisasi (nama pelapor disimpan langsung di laporan) untuk performa query lebih cepat. Trade-off: data duplikasi.

### Q: Bagaimana cara MongoDB handle query?
**A:** MongoDB pakai query operator ($regex, $or, $set, $inc, dll) yang dipanggil lewat PyMongo driver. Tidak ada SQL string, tapi method chaining: `find(query).sort().skip().limit()`.

### Q: Apa itu Aggregation Pipeline?
**A:** Serangkaian stage ($group, $sort, $match, $project, dll) yang diproses berurutan. Data masuk di stage pertama, keluar di stage terakhir. Mirip dengan pipa data atau SQL GROUP BY + HAVING.

### Q: Apa itu Upsert?
**A:** Operation yang melakukan update jika dokumen sudah ada, atau insert jika belum ada. Contoh di projek: settings_col.update_one({"_id": "global"}, {"$set": ...}, upsert=True)

### Q: Bagaimana performa MongoDB untuk data besar?
**A:** MongoDB mendukung index untuk mempercepat query. Untuk projek ini, _id sudah ter-index otomatis. Field yang sering di-query (nik, status, kategori) bisa ditambah index: `reports_col.create_index("nik")`

### Q: Apa kelebihan MongoDB dibanding SQL untuk projek ini?
**A:**
1. Skema fleksibel — field laporan bisa berubah tanpa ALTER TABLE
2. Query cepat untuk read operation
3. JSON native — tidak perlu ORM
4. Mudah prototype dan develop
5. Array field (foto) tanpa junction table

### Q: Apa kekurangan MongoDB?
**A:**
1. Tidak ada ACID transaction (untuk multi-collection)
2. Data duplikasi (denormalization)
3. Tidak ada JOIN — harus handle di aplikasi
4. Konsistensi data lemah (tidak ada constraint)

### Q: Jelaskan operasi CRUD yang dipakai di project ini
**A:**
- **C**reate: `insert_one()` — menambah 1 dokumen baru
- **R**ead: `find_one()` — cari 1 dokumen, `find()` — cari banyak
- **U**pdate: `update_one()` dengan operator $set/$inc
- **D**elete: `delete_one()` — hapus 1 dokumen

### Q: Apa itu $inc dan kapan dipakai?
**A:** $inc adalah atomic increment operator. Dipakai saat ingin menambah angka tanpa race condition. Contoh: `categories_col.update_one({"nama": "A"}, {"$inc": {"jumlah_laporan": 1}})` — aman meski banyak request bersamaan.

### Q: Bagaimana cara kerja pagination di MongoDB?
**A:** Menggunakan `.skip(n).limit(m)`. skip(n) melewati n dokumen pertama, limit(m) membatasi hasil m dokumen. Untuk halaman ke-P dengan M items: skip((P-1)*M).limit(M).

### Q: Apa itu denormalisasi di MongoDB?
**A:** Menyimpan data duplikat di beberapa dokumen untuk performa. Contoh: nama pelapor disimpan di dokumen laporan, bukan hanya NIK reference. Walaupun data sama di banyak tempat, query lebih cepat karena tidak perlu JOIN.

### Q: Bagaimana cara MongoDB menyimpan array?
**A:** Field bisa berisi array langsung di dokumen. Contoh: `"foto": ["file1.jpg", "file2.jpg"]`. Di SQL perlu junction table terpisah.

### Q: Apa itu BSON vs JSON?
**A:** BSON (Binary JSON) adalah format internal MongoDB. BSON mendukung lebih banyak tipe data (ObjectId, Date, Binary, dll) dan lebih efisien untuk parsing. JSON hanya punya string, number, boolean, array, object, null.
