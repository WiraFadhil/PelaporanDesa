# Design Document — Pelaporan Desa

## 1. Arsitektur Aplikasi

**Backend:** Flask (Python 3)
**Database:** MongoDB (via PyMongo)
**Frontend:** Server-rendered HTML + CSS + Vanilla JS

```
┌─────────────────────────────────────┐
│           Browser (Client)           │
├─────────────────┬───────────────────┤
│  Public Pages   │  Admin Pages      │
│  (index.html)   │  (admin/*.html)   │
└────────┬────────┴────────┬──────────┘
         │                 │
         ▼                 ▼
┌─────────────────────────────────────┐
│          Flask (app.py)              │
│  /api/* endpoints (REST JSON)        │
│  /* route → render_template(...)     │
└────────────────┬────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│          MongoDB                     │
│  admins │ reports │ categories      │
│  residents │ settings │ events      │
│  announcements                      │
└─────────────────────────────────────┘
```

## 2. Struktur Direktori

```
projectBDNR/
├── app.py                  # Entry point Flask
├── config.py               # Konfigurasi (env vars)
├── design.md               # Dokumen ini
├── .env                    # Environment variables
├── uploads/                # File uploads
├── static/
│   ├── css/
│   │   └── style.css       # Global stylesheet
│   └── js/
│       └── script.js       # Client-side logic
├── templates/
│   ├── index.html          # Halaman beranda publik
│   ├── buat-laporan.html   # Form laporan publik
│   ├── laporan-saya.html   # Cek status laporan
│   ├── informasi.html      # Info & pengumuman
│   └── admin/
│       ├── login.html      # Login admin
│       ├── index.html      # Dashboard admin
│       ├── reports.html    # Manajemen laporan
│       ├── kategori.html   # Kelola kategori
│       ├── warga.html      # Data warga
│       └── pengaturan.html # Pengaturan sistem
```

## 3. Tech Stack & Alasan

| Layer | Pilihan | Alasan |
|-------|---------|--------|
| Backend | Flask | Ringan, mudah dikembangkan, cocok untuk skala desa |
| Database | MongoDB | Skema fleksibel untuk data laporan yang heterogen |
| Frontend | Vanilla HTML/CSS/JS | Tanpa framework berat, cepat diakses perangkat desa |
| Auth | Session-based + bcrypt | Sederhana, tanpa JWT complexity |
| File Storage | Local filesystem | Skala kecil, tidak perlu cloud storage |

## 4. Database Schema

### admins
```json
{
  "_id": ObjectId,
  "username": "admin",
  "password": "$2b$12...hash...",
  "nama": "Admin Utama",
  "email": "admin@pelaporan-desa.id"
}
```

### reports
```json
{
  "_id": ObjectId,
  "judul": "Jalan Berlubang",
  "deskripsi": "Terdapat lubang besar...",
  "kategori": "Fasilitas Umum",
  "pelapor": "Budi Santoso",
  "nik": "3273010101010001",
  "rt": "01",
  "rw": "01",
  "lokasi": "Gang Mawar, RT 01 RW 01",
  "foto": ["uuid.jpg"],
  "status": "Diajukan | Diproses | Selesai",
  "tanggal": "15 Jun 2026",
  "catatan": "Sedang dijadwalkan perbaikan",
  "created_at": ISODate
}
```

### categories
```json
{
  "_id": ObjectId,
  "nama": "Fasilitas Umum",
  "icon": "building",
  "warna": "blue",
  "jumlah_laporan": 12
}
```

### residents
```json
{
  "_id": ObjectId,
  "nik": "3273010101010001",
  "nama": "Budi Santoso",
  "alamat": "Gang Mawar No. 10",
  "rt": "01",
  "rw": "01",
  "telepon": "081234567890",
  "status": "Aktif | Nonaktif"
}
```

### settings
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

### announcements
```json
{
  "_id": ObjectId,
  "judul": "Kerja Bakti Lingkungan",
  "isi": "Akan diadakan kerja bakti...",
  "tanggal": "15 Jun 2026",
  "jam": "07:00 - 12:00"
}
```

### events
```json
{
  "_id": ObjectId,
  "judul": "Rapat RT Mingguan",
  "tanggal": "Setiap Sabtu",
  "jam": "19:00 - 21:00",
  "deskripsi": "Rapat rutin warga RT 02"
}
```

## 5. API Endpoints

### Auth
| Method | Endpoint | Auth | Deskripsi |
|--------|----------|------|-----------|
| POST | `/api/login` | ❌ | Login admin |
| POST | `/api/logout` | ❌ | Logout |
| GET | `/api/me` | ✅ | Profil admin |

### Reports
| Method | Endpoint | Auth | Deskripsi |
|--------|----------|------|-----------|
| GET | `/api/reports` | ❌ | List laporan (pagination, filter) |
| GET | `/api/reports/stats` | ❌ | Statistik dashboard |
| POST | `/api/reports` | ❌ | Buat laporan baru |
| GET | `/api/reports/:id` | ❌ | Detail laporan |
| PUT | `/api/reports/:id` | ✅ | Update laporan |
| DELETE | `/api/reports/:id` | ✅ | Hapus laporan |

### Categories
| Method | Endpoint | Auth | Deskripsi |
|--------|----------|------|-----------|
| GET | `/api/categories` | ❌ | List kategori |
| POST | `/api/categories` | ✅ | Tambah kategori |
| PUT | `/api/categories/:id` | ✅ | Edit kategori |
| DELETE | `/api/categories/:id` | ✅ | Hapus kategori |

### Residents
| Method | Endpoint | Auth | Deskripsi |
|--------|----------|------|-----------|
| GET | `/api/residents` | ✅ | List warga (pagination, filter) |
| POST | `/api/residents` | ✅ | Tambah warga |
| PUT | `/api/residents/:id` | ✅ | Edit warga |
| DELETE | `/api/residents/:id` | ✅ | Hapus warga |

### Other
| Method | Endpoint | Auth | Deskripsi |
|--------|----------|------|-----------|
| GET/PUT | `/api/settings` | ✅ | Pengaturan sistem |
| GET | `/api/announcements` | ❌ | Pengumuman (max 5) |
| GET | `/api/events` | ❌ | Agenda/kegiatan (max 5) |
| PUT | `/api/update-admin` | ✅ | Update profil admin |
| POST | `/api/upload` | ❌ | Upload file |

## 6. Design System

### Warna
- **Primary:** `#1A56DB` (biru)
- **Primary Dark:** `#1243AF`
- **Primary Light:** `#E8F0FE`
- **Success:** `#059669` (hijau)
- **Warning:** `#D97706` (kuning/amber)
- **Danger:** `#DC2626` (merah)
- **Gray 50–900:** dari tailwind palette

### Tipografi
- **Font:** Inter (sans-serif)
- **Sizes:** 14px (body), 16px (large), 20px (h3), 24px (h2), 32px (h1)

### Komponen UI (CSS Classes)
- `.container` — wrapper max-width 1200px
- `.header` — navigasi sticky
- `.card` — kartu konten (white, shadow, rounded)
- `.modal` — overlay dialog
- `.btn`, `.btn--primary`, `.btn--ghost`, `.btn--danger` — tombol
- `.badge` — status label (badge--pending, --progress, --done)
- `.form-group`, `.form-input`, `.form-select`, `.form-textarea` — form elements
- `.table` — tabel data
- `.grid` — 3-column grid
- `.stats-grid` — 4-column stat cards
- `.toast` — notifikasi toast

### Page Structure (Public)
```
Header (brand + nav + user avatar)
Main
  ├── Beranda: Hero → Stats → Kategori → Laporan Terbaru → Pengumuman
  ├── Laporan Saya: Form NIK → Tabel riwayat laporan
  ├── Buat Laporan: Form lengkap
  └── Informasi: Pengumuman + Agenda
Footer
```

### Page Structure (Admin)
```
Sidebar (logo + menu items)
Main
  ├── Dashboard: Stats cards → Grafik kategori → Laporan terbaru
  ├── Laporan: Table + filter → Modal detail/edit
  ├── Kategori: Table + form add/edit
  ├── Warga: Table + filter → Modal add/edit
  └── Pengaturan: Form settings → Profil admin
```

## 7. Status Laporan Workflow

```
Diajukan ──► Diproses ──► Selesai
     ▲                        │
     └────────────────────────┘ (bisa ubah manual)
```

## 8. Routing (Frontend)

Semua halaman di-render via Flask `render_template`. Routing diatur oleh backend:

| URL | Template |
|-----|----------|
| `/` | `index.html` |
| `/buat-laporan.html` | `buat-laporan.html` |
| `/laporan-saya.html` | `laporan-saya.html` |
| `/informasi.html` | `informasi.html` |
| `/admin/login` | `admin/login.html` |
| `/admin/*` | `admin/*.html` |
| `/uploads/*` | static file |

Fallback: unknown path → `index.html` (SPA-like behavior).

## 9. Keamanan

- Session-based auth dengan secret key
- Password di-hash dengan bcrypt
- File upload terbatas pada extensi gambar (png/jpg/jpeg/gif/webp)
- Maksimal upload 5MB
- CORS terbatas ke origin lokal
- Admin endpoints dilindungi `@login_required`

## 10. Pengembangan ke Depan (Future Scope)

- Filter laporan berdasarkan rentang tanggal
- Export laporan ke PDF/Excel
- Notifikasi email real-time
- Registrasi warga mandiri
- Upload multiple foto per laporan
- Dark mode
- Mobile app (PWA)
