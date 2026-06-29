# ProcessLens EDU - Panduan Aplikasi

## Deskripsi Aplikasi
ProcessLens EDU adalah aplikasi web berbasis Python dan Streamlit untuk mining proses edukatif yang membantu mahasiswa mempelajari dasar-dasar process mining dengan mengunggah log kejadian CSV, menemukan peta proses, menganalisis varian, dan mengidentifikasi bottleneck. Aplikasi ini sepenuhnya dalam Bahasa Indonesia dan dirancang untuk pembelajaran proses bisnis dan analisis data proses.

## Fitur Utama

### 1. Unggah & Pemetaan
- **Unggah CSV**: Muat log kejadian CSV apa pun atau gunakan dataset sampel yang disertakan
- **Pemetaan Kolom**: Petakan kolom CSV Anda ke skema log kejadian standar (ID kasus, aktivitas, waktu kejadian, sumber daya)
- **Validasi Log Kejadian**: Pemeriksaan otomatis untuk nilai kosong, duplikat, dan kasus dengan satu kejadian
- **Progress Indicators**: Indikator loading saat proses berlangsung
- **Export Formats**: Ekspor log dalam format CSV, JSON, atau Excel
- **Mode Pembelajaran**: Konten edukasi untuk membantu pemahaman konsep

### 2. Peta Proses
- **Graf Aktivitas Berurutan Langsung (DFG)**: Peta proses interaktif yang menunjukkan urutan aktivitas dan frekuensi transisi
- **Zoomable SVG**: Peta proses dengan kemampuan zoom dan pan menggunakan mouse
- **Tampilan Multi-layout**: Pilihan layout lengkung, polyline, atau ortogonal
- **Kontrol Kepadatan**: Slider untuk mengatur aktivitas dan jalur ditampilkan dalam persentase
- **Label Transisi**: Opsi untuk menampilkan label frekuensi pada jalur
- **Tampilan Kinerja**: Mode untuk menampilkan waktu tunggu rata-rata
- **Filter Visual**: Filter berdasarkan frekuensi aktivitas dan transisi
- **Legenda Interaktif**: Penjelasan elemen peta proses

### 3. Statistik
- **Ringkasan Global**: Metrik keseluruhan dataset (jumlah kejadian, kasus, aktivitas, varian)
- **Frekuensi Aktivitas**: Graf dan tabel untuk menampilkan aktivitas paling sering
- **Analisis Waktu**: Kejadian dari waktu ke waktu dengan agregasi harian/mingguan
- **Beban Kerja Sumber Daya**: Distribusi beban kerja berdasarkan sumber daya
- **Distribusi Durasi Kasus**: Histogram durasi kasus dan statistik waktu
- **Progress Indicators**: Indikator loading saat menghitung statistik

### 4. Varian Proses
- **Deteksi Varian**: Identifikasi dan peringkat jalur proses unik
- **Analisis Per Varian**: Detail untuk setiap varian termasuk durasi rata-rata dan jumlah kasus
- **Drill-down Interaktif**: Jelajahi kasus-kasus individual dalam varian tertentu
- **Visualisasi Perbandingan**: Tabel peringkat untuk membandingkan varian
- **Filter Varian**: Fokus pada varian-varian tertentu

### 5. Penjelajah Kasus
- **Pemilihan Kasus**: Pilih dan periksa kasus individual dari awal hingga akhir
- **Ringkasan Kasus**: Informasi waktu mulai, selesai, durasi, dan jumlah kejadian
- **Linimasa Kejadian**: Tabel dan grafik interaktif untuk urutan kejadian
- **Petunjuk Interpretasi**: Analisis otomatis untuk aktivitas berulang dan jeda waktu
- **Urutan Aktivitas**: Tampilan ringkas dari alur aktivitas dalam satu kasus

### 6. Laporan
- **Laporan Otomatis**: Ringkasan Markdown yang dapat diunduh dengan temuan utama
- **Analisis Komprehensif**: 7 bagian laporan termasuk dataset, validasi, aktivitas teratas, varian, kasus lambat, bottleneck, dan interpretasi
- **Export Laporan**: Unduh laporan dalam format Markdown
- **Export Log**: Unduh log terfilter dalam format CSV
- **Petunjuk Interpretasi**: Panduan untuk membaca dan memahami hasil analisis

## Fitur Tambahan

### Navigasi
- **Keyboard Shortcuts**: Navigasi cepat antar tab dengan Alt+1 hingga Alt+6
- **Auto-refresh Filter**: Filter otomatis diterapkan saat parameter berubah
- **Sidebar Filters**: Filter global yang berlaku di semua halaman

### Tema & UI
- **Dark Mode Support**: Toggle antara tema gelap dan terang
- **Progress Indicators**: Loading spinners saat proses berlangsung
- **Responsive Design**: Tampilan yang menyesuaikan ukuran layar

### Filter Lanjutan
- **Filter Rentang Tanggal**: Batasi analisis berdasarkan periode waktu
- **Filter Aktivitas**: Tampilkan hanya kasus yang mengandung aktivitas tertentu
- **Filter Durasi Kasus**: Fokus pada kasus dengan durasi tertentu
- **Filter Top N Varian**: Analisis hanya pada varian proses teratas
- **Filter Gabungan**: Kombinasi berbagai filter untuk analisis presisi

### Analisis Kinerja
- **Bottleneck Detection**: Identifikasi transisi dengan waktu tunggu tinggi
- **Kinerja Transisi**: Tabel dan grafik untuk analisis waktu tunggu
- **Analisis Durasi**: Statistik durasi kasus dan distribusi waktu

### Mode Pembelajaran
- **Konten Edukasi**: Penjelasan konsep, pertanyaan panduan, dan glosarium
- **Petunjuk Interpretasi**: Panduan untuk membaca dan memahami hasil
- **Kesalahan Umum**: Informasi tentang pemahaman yang sering salah
- **Aspek Pedagogis**: Materi pembelajaran terintegrasi

## Teknologi dan Dependencies

### Framework
- **Streamlit**: Framework web untuk aplikasi data science
- **Python 3.8+**: Bahasa pemrograman utama

### Library Analisis
- **Pandas**: Manipulasi dan analisis data
- **Plotly**: Visualisasi interaktif
- **NetworkX**: Analisis graf dan algoritma jaringan
- **Graphviz**: Rendering graf proses (opsional, fallback ke viz.js di cloud)

### Dependencies
```requirements.txt
streamlit
pandas
numpy
plotly
networkx
python-dateutil
graphviz
openpyxl
```

## Penggunaan

### Lokal
1. Clone atau unduh repositori
2. Install dependencies: `pip install -r requirements.txt`
3. Jalankan aplikasi: `streamlit run app.py`
4. Akses aplikasi di browser (biasanya http://localhost:8501)

### Cloud (Streamlit Cloud)
- Aplikasi siap deploy ke Streamlit Cloud
- Fallback otomatis ke renderer standar saat Graphviz tidak tersedia
- Semua fitur utama tetap berfungsi di lingkungan cloud

## Struktur Proyek

```
processlens-edu/
├── app.py                 # Entry point utama
├── requirements.txt       # Dependencies
├── sample_data/          # Data sampel
│   └── purchasing_sample.csv
├── core/                 # Logika bisnis
│   ├── import_log.py     # Impor dan pemetaan log
│   ├── validate_log.py   # Validasi log
│   ├── transform_log.py  # Transformasi log
│   ├── dfg.py           # Directly-Follows Graph
│   ├── statistics.py    # Statistik deskriptif
│   ├── variants.py      # Analisis varian
│   ├── filters.py       # Filter log
│   ├── report.py        # Generasi laporan
│   ├── map_abstraction.py # Abstraksi peta proses
│   ├── process_map_renderer.py # Renderer peta proses
│   └── process_map_layout.py # Layout peta proses
└── ui/                   # Halaman UI
    ├── page_upload.py   # Halaman unggah
    ├── page_map.py      # Halaman peta proses
    ├── page_statistics.py # Halaman statistik
    ├── page_variants.py # Halaman varian
    ├── page_cases.py    # Halaman kasus
    ├── page_report.py   # Halaman laporan
    └── learning_mode.py # Konten pembelajaran
```

## Format Input

### CSV Log Kejadian
- **case_id**: Mengidentifikasi instansi proses (wajib)
- **activity**: Nama langkah yang dilakukan (wajib)
- **timestamp**: Kapan aktivitas terjadi (wajib)
- **resource**: Siapa yang melakukan aktivitas (opsional)

### Contoh Struktur
```
case_id,activity,timestamp,resource,amount,department
C001,Request Created,2024-03-18 10:14:00,Budi,771.52,IT
C001,Manager Approval,2024-03-21 18:19:00,Farah,771.52,IT
```

## Target Penggunaan

### Pendidikan
- Mahasiswa ilmu komputer, sistem informasi, manajemen
- Kursus analisis proses bisnis
- Pelatihan process mining
- Praktikum data science

### Analisis Proses Bisnis
- Identifikasi bottleneck dan waste
- Analisis efisiensi proses
- Studi kasus untuk improvement
- Audit proses operasional

## Lisensi dan Hak Cipta
Aplikasi ini dirancang untuk penggunaan edukatif dan penelitian. Silakan merujuk pada lisensi resmi jika tersedia.