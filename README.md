# ProcessLens EDU

Aplikasi process mining edukasi berbasis CSV yang dibangun dengan Python dan Streamlit.

ProcessLens EDU membantu mahasiswa mempelajari dasar-dasar process mining dengan mengunggah log kejadian, menemukan peta proses, menganalisis varian, dan mengidentifikasi bottleneck. Tidak perlu database, login, atau pengaturan rumit — cukup unggah CSV dan jelajahi.

## Fitur

- **Unggah CSV** — muat log kejadian CSV apa pun atau gunakan dataset sampel yang disertakan.
- **Pemetaan Kolom** — petakan kolom CSV Anda ke skema log kejadian standar (ID kasus, aktivitas, waktu kejadian, sumber daya).
- **Validasi Log Kejadian** — pemeriksaan otomatis untuk nilai kosong, duplikat, dan kasus dengan satu kejadian.
- **Graf Aktivitas Berurutan Langsung (DFG)** — peta proses interaktif yang menunjukkan urutan aktivitas dan frekuensi transisi.
- **Statistik** — metrik global, frekuensi aktivitas, beban kerja sumber daya, kejadian dari waktu ke waktu, dan distribusi durasi kasus.
- **Analisis Varian** — identifikasi dan peringkat jalur proses unik, jelajahi varian secara detail.
- **Penjelajah Kasus** — periksa kasus individual dengan linimasa kejadian dan detail waktu.
- **Filter** — filter berdasarkan rentang tanggal, keberadaan aktivitas, durasi kasus, atau N varian teratas.
- **Laporan Markdown** — buat laporan ringkasan yang dapat diunduh dengan temuan utama.

## Instalasi

```bash
# Kloning atau unduh proyek
cd processlens-edu

# Buat virtual environment
python -m venv .venv

# Aktifkan
# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate

# Instal dependensi
pip install -r requirements.txt

# Jalankan aplikasi
streamlit run app.py
```

Aplisasi terbuka di `http://localhost:8501`.

## Format CSV

CSV Anda harus berisi kolom yang dapat dipetakan ke field logis berikut:

| Field | Wajib | Deskripsi |
|---|---|---|
| **case_id** | Ya | Mengidentifikasi instansi proses (misalnya ID pesanan, ID permintaan). |
| **activity** | Ya | Nama langkah yang dilakukan (misalnya "Setuju Permintaan"). |
| **timestamp** | Ya | Kapan aktivitas terjadi (format apa pun yang dapat dibaca oleh pandas). |
| **resource** | Tidak | Siapa yang melakukan aktivitas. Default "Unknown" jika tidak ada. |

Kolom tambahan (misalnya `amount`, `department`) akan dipertahankan dan tersedia untuk analisis.

### Dataset Sampel

File `sample_data/purchasing_sample.csv` yang disertakan berisi 40 kasus pembelian dengan aktivitas berikut:

- Request Created
- Manager Approval
- Request Revised
- Purchase Order Created
- Vendor Confirmation
- Goods Received
- Invoice Received
- Payment Completed

Sampel mencakup kasus normal, loop pengerjaan ulang (Request Revised), dan kasus lambat dengan waktu tunggu panjang — berguna untuk menjelajahi semua fitur aplikasi.

## Tujuan Pembelajaran

Setelah menggunakan ProcessLens EDU, mahasiswa diharapkan mampu:

1. **Memahami struktur log kejadian** — apa yang dimaksud dengan kasus, aktivitas, dan waktu kejadian.
2. **Membangun peta proses** — membuat Graf Aktivitas Berurutan Langsung dari urutan kejadian.
3. **Mengidentifikasi varian** — mengenali bahwa kasus mengikuti jalur berbeda melalui proses.
4. **Menganalisis bottleneck** — menemukan transisi dengan waktu tunggu panjang.
5. **Menggunakan filter** — mengajukan dan menjawab pertanyaan proses seperti "kasus mana yang membutuhkan waktu lebih dari 30 hari?" atau "apa yang terjadi ketika permintaan direvisi?".
6. **Menginterpretasi hasil** — menghubungkan output process mining dengan perilaku proses di dunia nyata.

## Keterbatasan

ProcessLens EDU dirancang untuk pembelajaran. Aplikasi ini secara sengaja tidak menyertakan fitur yang ada di alat produksi:

- Hanya input CSV — tidak mendukung XES, XLSX, atau database.
- Tidak ada integrasi PM4Py.
- Tidak ada pemodelan Petri net atau BPMN.
- Tidak ada pemeriksaan kesesuaian (conformance checking).
- Tidak ada analitik prediktif.

Untuk process mining tingkat lanjut, pertimbangkan alat seperti [PM4Py](https://pm4py.fit.fraunhofer.de/) atau [Celonis](https://www.celonis.com/).

## Struktur Proyek

```
processlens-edu/
├── app.py                  # Titik masuk Streamlit
├── requirements.txt
├── README.md
├── core/                   # Logika bisnis
│   ├── import_log.py       # Pemuatan CSV dan pemetaan kolom
│   ├── validate_log.py     # Validasi log kejadian
│   ├── transform_log.py    # Pembersihan dan pengayaan data
│   ├── dfg.py              # Perhitungan Graf Aktivitas Berurutan Langsung
│   ├── statistics.py       # Statistik deskriptif
│   ├── variants.py         # Deteksi varian
│   ├── filters.py          # Utilitas filtering
│   └── report.py           # Pembuatan laporan markdown
├── ui/                     # Halaman Streamlit
│   ├── page_upload.py      # Unggah dan pemetaan kolom
│   ├── page_map.py         # Visualisasi peta proses
│   ├── page_statistics.py  # Dasbor statistik
│   ├── page_variants.py    # Penjelajah varian
│   ├── page_cases.py       # Tampilan level kasus
│   └── page_report.py      # Halaman laporan dengan unduhan
└── sample_data/
    └── purchasing_sample.csv
```
