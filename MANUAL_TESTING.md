# Panduan Pengujian Manual — ProcessLens EDU

Panduan ini menjalani setiap fitur aplikasi langkah demi langkah.
Ikuti setiap bagian secara berurutan setelah meluncurkan aplikasi.

---

## Prasyarat

```bash
cd processlens-edu
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux
pip install -r requirements.txt
streamlit run app.py
```

Aplikasi terbuka di `http://localhost:8501`.

---

## 1. Pemuatan Pertama (Tidak Crash)

- [ ] Aplikasi terbuka tanpa error di browser.
- [ ] Sidebar menampilkan judul "ProcessLens EDU".
- [ ] Panel filter tidak muncul di sidebar (belum ada data yang dimuat).
- [ ] Enam tab terlihat: Unggah & Pemetaan, Peta Proses, Statistik, Varian, Kasus, Laporan.
- [ ] Setiap tab menampilkan "Silakan unggah dan proses log kejadian terlebih dahulu." (kecuali Unggah & Pemetaan).

---

## 2. Muat Data Sampel

- [ ] Buka tab **Unggah & Pemetaan**.
- [ ] Klik **Muat Data Sampel**.
- [ ] Pesan sukses muncul: "Data sampel berhasil dimuat."
- [ ] Tabel pratinjau data muncul dengan 10 baris dan 6 kolom (case_id, activity, timestamp, resource, amount, department).

---

## 3. Pemetaan Kolom

- [ ] Bagian pemetaan kolom muncul dengan empat dropdown.
- [ ] Kolom ID Kasus default ke "case_id".
- [ ] Kolom Aktivitas default ke "activity".
- [ ] Kolom Waktu Kejadian default ke "timestamp".
- [ ] Kolom Sumber Daya default ke "(tidak ada)".
- [ ] Ubah Kolom Sumber Daya ke "resource".
- [ ] Klik **Proses Log Kejadian**.
- [ ] Pesan sukses muncul: "Log kejadian berhasil diproses!"
- [ ] Hasil validasi menunjukkan: 300 kejadian, 40 kasus, 8 aktivitas, 6 sumber daya.
- [ ] Status menampilkan "Log kejadian lolos semua pemeriksaan validasi."

---

## 4. Filter Sidebar Muncul

- [ ] Setelah pemrosesan, sidebar sekarang menampilkan bagian "Filter".
- [ ] Input rentang tanggal menampilkan rentang penuh (01-03-2024 hingga 27-04-2024).
- [ ] Multiselect aktivitas kosong (tidak ada filter yang diterapkan).
- [ ] Input durasi kasus min/maks menampilkan 0.0.
- [ ] Input N varian teratas menampilkan 0.
- [ ] Jumlah kejadian/kasus muncul di bagian bawah sidebar.

---

## 5. Tab Peta Proses

- [ ] Buka tab **Peta Proses**.
- [ ] Kotak edukasi menjelaskan apa itu DFG.
- [ ] Dua slider muncul: frekuensi aktivitas minimum dan frekuensi transisi minimum.
- [ ] Graf ditampilkan dengan node (aktivitas) dan edge (transisi).
- [ ] Label edge menunjukkan frekuensi transisi.
- [ ] Lima tabel data muncul: Frekuensi Aktivitas, Frekuensi Transisi, Aktivitas Awal, Aktivitas Akhir, Kinerja Transisi.
- [ ] Geser slider frekuensi aktivitas minimum ke atas — graf diperbarui.
- [ ] Geser slider frekuensi transisi minimum ke atas — graf diperbarui.

---

## 6. Tab Statistik

- [ ] Buka tab **Statistik**.
- [ ] Kotak edukasi muncul.
- [ ] Lima sub-tab muncul: Ringkasan, Aktivitas, Waktu, Sumber Daya, Durasi.
- [ ] **Ringkasan**: enam kartu metrik (Kejadian, Kasus, Aktivitas, Varian, Durasi Rata-rata, Durasi Median).
- [ ] **Aktivitas**: graf batang + tabel data untuk frekuensi aktivitas.
- [ ] **Waktu**: graf batang kejadian dari waktu ke waktu dengan toggle Harian/Mingguan.
- [ ] **Sumber Daya**: graf batang + tabel data untuk frekuensi sumber daya.
- [ ] **Durasi**: histogram durasi kasus + tabel data.

---

## 7. Tab Varian

- [ ] Buka tab **Varian**.
- [ ] Kotak edukasi muncul.
- [ ] Metrik ringkasan: Total Varian (2), Varian Paling Sering (V1), Persentase Kasus (75.0%).
- [ ] Tabel varian menampilkan semua varian dengan urutan, jumlah kasus, persentase, durasi rata-rata/median.
- [ ] Selectbox memungkinkan Anda memilih varian untuk drill-down.
- [ ] Pilih V2 (varian pengerjaan ulang) — urutan menampilkan "Request Created -> ... -> Request Revised -> ...".
- [ ] Daftar ID kasus menampilkan 10 kasus.
- [ ] Tabel kejadian menampilkan kejadian untuk kasus-kasus varian terpilih.

---

## 8. Tab Kasus

- [ ] Buka tab **Kasus**.
- [ ] Kotak edukasi muncul.
- [ ] Selectbox mendaftar semua 40 ID kasus.
- [ ] Pilih kasus — ringkasan menampilkan Waktu Mulai, Waktu Selesai, Durasi, Kejadian.
- [ ] Urutan aktivitas ditampilkan.
- [ ] Tabel Linimasa Kejadian menampilkan semua kejadian untuk kasus tersebut.
- [ ] Graf linimasa aktivitas ditampilkan.
- [ ] Petunjuk interpretasi muncul (aktivitas berulang, jeda waktu panjang).

---

## 9. Tab Laporan

- [ ] Buka tab **Laporan**.
- [ ] Kotak edukasi muncul.
- [ ] Laporan Markdown ditampilkan dengan 7 bagian:
  1. Ringkasan Dataset
  2. Ringkasan Validasi
  3. Aktivitas Teratas
  4. Varian Teratas
  5. Kasus Paling Lambat
  6. Transisi Bottleneck
  7. Petunjuk Interpretasi
- [ ] Tombol **Unduh Laporan (Markdown)** berfungsi — mengunduh `laporan_process_mining.md`.
- [ ] Tombol **Unduh Log Terfilter (CSV)** berfungsi — mengunduh `log_kejadian_terfilter.csv`.

---

## 10. Filter Memperbarui Semua Tampilan

- [ ] Di sidebar, atur rentang tanggal sempit (misalnya 15-03-2024 hingga 20-03-2024).
- [ ] Klik **Terapkan Filter**.
- [ ] Jumlah sidebar diperbarui (kejadian/kasus berkurang).
- [ ] Buka **Peta Proses** — graf dan tabel mencerminkan data terfilter.
- [ ] Buka **Statistik** — semua metrik dan graf mencerminkan data terfilter.
- [ ] Buka **Varian** — tabel varian mencerminkan data terfilter.
- [ ] Buka **Kasus** — daftar kasus mencerminkan data terfilter.
- [ ] Buka **Laporan** — laporan mencerminkan data terfilter.
- [ ] Klik **Reset Filter** — semua tampilan kembali ke data penuh.

---

## 11. Filter Aktivitas

- [ ] Di sidebar, pilih "Request Revised" di multiselect Aktivitas.
- [ ] Klik **Terapkan Filter**.
- [ ] Hanya kasus yang mengandung "Request Revised" yang tersisa (varian pengerjaan ulang).
- [ ] Verifikasi di tab **Varian** bahwa hanya varian pengerjaan ulang yang muncul.

---

## 12. Kasus Edge

- [ ] Atur filter yang menghapus semua data (misalnya rentang tanggal sangat sempit).
- [ ] Setiap tab menampilkan "Tidak ada kasus yang sesuai dengan filter saat ini." alih-alih crash.
- [ ] Reset filter untuk memulihkan data.
- [ ] Di **Unggah & Pemetaan**, unggah file CSV kosong — pesan error muncul.
- [ ] Unggah CSV dengan pemetaan kolom yang salah (misalnya aktivitas = waktu kejadian) — pesan error muncul.

---

## Ringkasan Data Sampel yang Diharapkan

| Metrik | Nilai |
|---|---|
| Total kejadian | 300 |
| Total kasus | 40 |
| Aktivitas | 8 |
| Sumber daya | 6 |
| Varian | 2 |
| V1 (normal) | 30 kasus (75%) |
| V2 (pengerjaan ulang) | 10 kasus (25%) |
| Rentang tanggal | 01-03-2024 hingga 27-04-2024 |
