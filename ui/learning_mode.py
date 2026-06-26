"""Mode Pembelajaran — komponen edukasi untuk ProcessLens EDU.

Menyediakan fungsi-fungsi reusable untuk menampilkan konten
edukasi di setiap halaman aplikasi. Semua teks edukasi disimpan
di sini agar halaman UI tidak menduplikasi konten panjang.
"""

from __future__ import annotations

import streamlit as st


# ======================================================================
# Komponen reusable
# ======================================================================


def render_learning_intro(page_name: str) -> None:
    """Tampilkan pengantar singkat untuk halaman yang sedang dibuka.

    Parameters
    ----------
    page_name : str
        Nama halaman (misalnya "upload", "map", "statistics").
    """
    intros = {
        "upload": (
            "Unggah & Pemetaan",
            "Halaman ini adalah titik awal analisis process mining. "
            "Di sini Anda akan memuat data, memetakan kolom, dan memvalidasi log kejadian.",
        ),
        "map": (
            "Peta Proses",
            "Peta proses menunjukkan alur aktivitas dalam proses Anda. "
            "Gunakan halaman ini untuk memahami bagaimana kejadian-kejadian saling berhubungan.",
        ),
        "statistics": (
            "Statistik",
            "Statistik memberikan ringkasan numerik dari proses. "
            "Gunakan halaman ini untuk mendapatkan gambaran umum sebelum analisis mendalam.",
        ),
        "variants": (
            "Varian",
            "Varian menunjukkan jalur-jalur berbeda yang ditempuh kasus dalam proses. "
            "Memahami varian membantu mengidentifikasi proses standar dan penyimpangan.",
        ),
        "cases": (
            "Kasus",
            "Penjelajah kasus memungkinkan Anda melihat satu instansi proses secara detail. "
            "Gunakan halaman ini untuk memahami perjalanan satu kasus dari awal hingga akhir.",
        ),
        "report": (
            "Laporan",
            "Laporan merangkum temuan utama dari analisis Anda. "
            "Gunakan halaman ini untuk melihat ringkasan yang dapat dibagikan atau digunakan untuk tugas.",
        ),
    }

    if page_name in intros:
        title, content = intros[page_name]
        st.success(f"**Mode Pembelajaran — {title}**  \n{content}")


def render_concept_box(title: str, content: str | list[str]) -> None:
    """Tampilkan kotak konsep dengan judul dan penjelasan.

    Parameters
    ----------
    title : str
        Judul konsep.
    content : str | list[str]
        Penjelasan konsep. Jika list, render sebagai bullet points.
    """
    with st.expander(f"Konsep: {title}", expanded=False):
        if isinstance(content, list):
            for item in content:
                st.markdown(f"- {item}")
        else:
            st.markdown(content)


def render_guided_questions(questions: list[str]) -> None:
    """Tampilkan pertanyaan-pertanyaan panduan untuk refleksi.

    Parameters
    ----------
    questions : list[str]
        Daftar pertanyaan untuk dipikirkan mahasiswa.
    """
    with st.expander("Pertanyaan Panduan", expanded=False):
        for i, q in enumerate(questions, 1):
            st.markdown(f"**{i}.** {q}")


def render_observation_checklist(items: list[str]) -> None:
    """Tampilkan checklist observasi untuk diamati mahasiswa.

    Parameters
    ----------
    items : list[str]
        Daftar item yang perlu diamati.
    """
    with st.expander("Checklist Observasi", expanded=False):
        for item in items:
            st.checkbox(item, key=f"obs_{hash(item)}", disabled=True)


def render_interpretation_hints(hints: list[str]) -> None:
    """Tampilkan petunjuk interpretasi.

    Parameters
    ----------
    hints : list[str]
        Daftar petunjuk interpretasi.
    """
    with st.expander("Petunjuk Interpretasi", expanded=False):
        for hint in hints:
            st.markdown(f"- {hint}")


def render_common_misconceptions(items: list[str]) -> None:
    """Tampilkan kesalahan pemahaman yang sering terjadi.

    Parameters
    ----------
    items : list[str]
        Daftar kesalahan pemahaman beserta koreksinya.
    """
    with st.expander("Kesalahan Pemahaman yang Sering Terjadi", expanded=False):
        for item in items:
            st.markdown(f"- {item}")


def render_mini_glossary(terms: dict[str, str]) -> None:
    """Tampilkan glosarium mini istilah process mining.

    Parameters
    ----------
    terms : dict[str, str]
        Peta istilah ke definisi.
    """
    with st.expander("Glosarium Mini", expanded=False):
        for term, definition in terms.items():
            st.markdown(f"**{term}:** {definition}")


def render_assignment_guide(
    sections: list[tuple[str, list[str]]],
    rubric: list[tuple[str, str]],
) -> None:
    """Tampilkan panduan tugas dan rubrik penilaian.

    Parameters
    ----------
    sections : list[tuple[str, list[str]]]
        Daftar pasangan (judul bagian, daftar pertanyaan).
    rubric : list[tuple[str, str]]
        Daftar pasangan (kriteria, bobot).
    """
    with st.expander("Panduan Tugas Analisis Process Mining", expanded=False):
        for section_title, questions in sections:
            st.markdown(f"### {section_title}")
            for i, q in enumerate(questions, 1):
                st.markdown(f"{i}. {q}")
            st.divider()

        st.markdown("### Rubrik Penilaian")
        rubric_df = [{"Kriteria": k, "Bobot": b} for k, b in rubric]
        st.table(rubric_df)


# ======================================================================
# Konten edukasi per halaman
# ======================================================================

_PAGE_CONTENT: dict[str, dict] = {
    "upload": {
        "concepts": [
            (
                "Apa itu Event Log?",
                "Event log adalah data yang mencatat kejadian dalam suatu proses. "
                "Dalam process mining, setiap baris biasanya mewakili satu kejadian. "
                "Minimal, event log membutuhkan **ID kasus**, **aktivitas**, "
                "dan **waktu kejadian**.",
            ),
            (
                "Tiga Kolom Utama",
                "- **ID Kasus**: penanda satu proses atau satu instance, "
                "misalnya nomor tiket, nomor pesanan, atau ID mahasiswa.\n"
                "- **Aktivitas**: nama kegiatan yang terjadi, "
                "misalnya Request Created, Approval, atau Payment Completed.\n"
                "- **Waktu Kejadian**: waktu ketika aktivitas terjadi.",
            ),
        ],
        "questions": [
            "Kolom mana yang merepresentasikan satu kasus dari awal sampai akhir?",
            "Kolom mana yang berisi nama aktivitas?",
            "Apakah timestamp sudah terbaca sebagai tanggal dan waktu?",
            "Apakah ada data kosong pada ID kasus, aktivitas, atau timestamp?",
        ],
        "observations": [
            "Saya sudah memilih kolom Case ID dengan benar.",
            "Saya sudah memilih kolom Activity dengan benar.",
            "Saya sudah memilih kolom Timestamp dengan benar.",
            "Saya sudah memeriksa jumlah event dan jumlah case.",
            "Saya sudah membaca warning validasi jika ada.",
        ],
        "misconceptions": [
            "Satu baris bukan berarti satu case — satu case terdiri dari banyak event.",
            "Case ID bukan nama orang; sebaiknya berupa nomor pesanan, tiket, atau transaksi.",
            "Format timestamp yang salah dapat membuat urutan proses menjadi kacau.",
        ],
        "glossary": {
            "Event": "Satu kejadian dalam proses.",
            "Case": "Satu instance proses dari awal sampai akhir.",
            "Activity": "Aktivitas yang dilakukan dalam proses.",
            "Timestamp": "Waktu terjadinya event.",
        },
    },
    "map": {
        "concepts": [
            (
                "Cara Membaca Peta Proses",
                "Peta proses menunjukkan alur aktivitas berdasarkan urutan kejadian "
                "dalam event log. Node merepresentasikan aktivitas, sedangkan panah "
                "merepresentasikan perpindahan dari satu aktivitas ke aktivitas berikutnya.",
            ),
            (
                "Arti Node dan Edge",
                "- **Node**: aktivitas dalam proses.\n"
                "- **Edge/panah**: transisi antar aktivitas.\n"
                "- **Angka pada node**: frekuensi aktivitas.\n"
                "- **Angka pada panah**: frekuensi transisi.\n"
                "- **MULAI**: titik awal kasus.\n"
                "- **SELESAI**: titik akhir kasus.",
            ),
            (
                "Loop dan Rework",
                "Jika aktivitas yang sama muncul berulang dalam satu case, "
                "hal ini dapat menunjukkan rework, revisi, pengulangan, "
                "atau proses yang tidak langsung selesai.",
            ),
        ],
        "questions": [
            "Aktivitas apa yang paling sering terjadi?",
            "Dari aktivitas mana proses paling sering dimulai?",
            "Di aktivitas mana proses paling sering berakhir?",
            "Apakah ada loop atau aktivitas yang berulang?",
            "Transisi mana yang paling sering dilewati?",
            "Apakah ada jalur yang terlihat tidak biasa?",
        ],
        "observations": [
            "Saya dapat menyebutkan aktivitas awal proses.",
            "Saya dapat menyebutkan aktivitas akhir proses.",
            "Saya dapat menemukan transisi paling dominan.",
            "Saya dapat mengenali apakah ada loop atau rework.",
            "Saya dapat menjelaskan perbedaan node dan edge.",
        ],
        "interpretation_hints": [
            "Node dengan frekuensi tinggi dapat menunjukkan aktivitas penting "
            "atau aktivitas yang sering diulang.",
            "Edge dengan frekuensi tinggi menunjukkan jalur proses yang umum.",
            "Banyak jalur bercabang dapat menunjukkan variasi proses.",
            "Loop dapat menunjukkan revisi, koreksi, atau pengerjaan ulang.",
            "Jika terlalu banyak node dan edge, gunakan threshold untuk "
            "menyederhanakan peta.",
        ],
        "misconceptions": [
            "Peta proses bukan flowchart rancangan — ini rekonstruksi dari data aktual.",
            "Jalur paling sering belum tentu jalur yang paling benar atau efisien.",
            "Proses yang rumit belum tentu salah; perlu dianalisis penyebab variasinya.",
        ],
        "glossary": {
            "Node": "Lingkaran dalam graf yang merepresentasikan satu aktivitas.",
            "Edge": "Panah dalam graf yang merepresentasikan transisi antar aktivitas.",
            "DFG (Directly-Follows Graph)": "Graf yang menunjukkan urutan langsung antar aktivitas.",
            "Transisi": "Perpindahan dari satu aktivitas ke aktivitas berikutnya.",
            "Frekuensi Transisi": "Berapa kali transisi tertentu terjadi dalam log.",
            "Waktu Tunggu": "Selisih waktu antara akhir aktivitas sebelumnya dan awal aktivitas berikutnya.",
            "Bottleneck": "Transisi dengan waktu tunggu yang sangat panjang, menghambat alur proses.",
            "Rework": "Pengerjaan ulang aktivitas yang sudah dilakukan sebelumnya.",
        },
    },
    "statistics": {
        "concepts": [
            (
                "Mengapa Statistik Penting?",
                "Statistik membantu merangkum perilaku proses secara kuantitatif. "
                "Dari statistik, kita bisa melihat aktivitas paling sering, durasi kasus, "
                "beban kerja resource, dan pola kejadian dari waktu ke waktu.",
            ),
            (
                "Frekuensi Aktivitas",
                "Frekuensi aktivitas menunjukkan seberapa sering suatu aktivitas muncul "
                "dalam event log. Jika frekuensinya jauh lebih tinggi daripada jumlah case, "
                "aktivitas tersebut mungkin sering diulang.",
            ),
            (
                "Durasi Kasus",
                "Durasi kasus dihitung dari timestamp pertama sampai timestamp terakhir "
                "dalam satu case. Durasi ini membantu menemukan proses yang cepat, lambat, "
                "atau menyimpang.",
            ),
            (
                "Frekuensi Resource",
                "Frekuensi resource menunjukkan siapa atau unit mana yang paling sering "
                "menjalankan aktivitas. Ini dapat digunakan untuk membaca distribusi beban kerja.",
            ),
        ],
        "questions": [
            "Aktivitas apa yang paling sering muncul?",
            "Apakah aktivitas paling sering tersebut wajar?",
            "Berapa durasi rata-rata dan median kasus?",
            "Apakah rata-rata durasi jauh lebih besar dari median?",
            "Resource mana yang paling banyak terlibat?",
            "Apakah ada periode waktu dengan jumlah event yang tinggi?",
        ],
        "observations": [
            "Saya dapat membedakan total event dan total case.",
            "Saya dapat membaca aktivitas paling dominan.",
            "Saya dapat membaca durasi rata-rata dan median.",
            "Saya dapat mengidentifikasi resource dengan workload tinggi.",
            "Saya dapat mengenali kemungkinan outlier dari distribusi durasi.",
        ],
        "interpretation_hints": [
            "Jika rata-rata durasi jauh lebih tinggi daripada median, "
            "mungkin ada beberapa case sangat lambat.",
            "Aktivitas dengan frekuensi sangat tinggi dapat menunjukkan "
            "aktivitas utama atau rework.",
            "Resource dengan frekuensi tinggi mungkin memiliki beban kerja besar.",
            "Lonjakan event pada periode tertentu dapat menunjukkan pola "
            "operasional atau batch processing.",
        ],
        "misconceptions": [
            "Total event tidak sama dengan total case — satu case bisa memiliki banyak event.",
            "Rata-rata durasi bisa dipengaruhi outlier; median lebih tahan terhadap nilai ekstrem.",
            "Resource paling sering muncul belum tentu paling lambat atau paling bermasalah.",
        ],
        "glossary": {
            "Event": "Satu kejadian dalam proses.",
            "Case": "Satu instance proses dari awal sampai akhir.",
            "Durasi Kasus": "Selisih waktu antara kejadian pertama dan terakhir dalam satu kasus.",
            "Durasi Rata-rata": "Rata-rata waktu yang dibutuhkan untuk menyelesaikan satu kasus.",
            "Durasi Median": "Nilai tengah durasi kasus — tidak terpengaruh oleh nilai ekstrem.",
            "Frekuensi Aktivitas": "Berapa kali suatu aktivitas muncul dalam seluruh log.",
            "Frekuensi Resource": "Berapa kali resource terlibat dalam kejadian.",
            "Outlier": "Nilai yang jauh berbeda dari kebanyakan data lainnya.",
        },
    },
    "variants": {
        "concepts": [
            (
                "Apa itu Varian?",
                "Varian adalah satu pola urutan aktivitas yang diikuti oleh satu "
                "atau lebih case. Jika dua case memiliki urutan aktivitas yang sama, "
                "maka keduanya termasuk dalam varian yang sama.\n\n"
                "**Contoh:**\n"
                "Jika Case A memiliki urutan Request Created -> Approval -> Payment, "
                "dan Case B memiliki urutan yang sama, maka keduanya termasuk "
                "dalam varian yang sama.",
            ),
            (
                "Mengapa Varian Penting?",
                "Analisis varian membantu melihat apakah proses berjalan konsisten "
                "atau memiliki banyak variasi. Semakin banyak varian, semakin beragam "
                "jalur proses yang terjadi.",
            ),
        ],
        "questions": [
            "Varian apa yang paling sering terjadi?",
            "Berapa persen case yang mengikuti varian paling umum?",
            "Apakah top 3 varian sudah mencakup sebagian besar kasus?",
            "Apakah ada varian yang hanya terjadi satu kali?",
            "Apakah varian tertentu memiliki durasi lebih lama?",
            "Apakah ada varian yang mengandung aktivitas berulang?",
        ],
        "observations": [
            "Saya dapat menjelaskan arti varian.",
            "Saya dapat menemukan varian paling dominan.",
            "Saya dapat melihat case yang termasuk dalam varian tertentu.",
            "Saya dapat membedakan varian umum dan varian langka.",
            "Saya dapat menghubungkan varian dengan durasi proses.",
        ],
        "interpretation_hints": [
            "Varian dominan menunjukkan jalur proses yang paling umum.",
            "Banyak varian langka dapat menunjukkan pengecualian, anomali, "
            "atau proses yang kurang standar.",
            "Varian dengan durasi tinggi perlu diperiksa lebih lanjut.",
            "Varian yang mengandung aktivitas berulang dapat menunjukkan rework.",
        ],
        "misconceptions": [
            "Varian bukan jumlah aktivitas — varian adalah urutan aktivitas.",
            "Varian yang jarang terjadi belum tentu salah; perlu dianalisis konteksnya.",
            "Varian paling sering belum tentu paling efisien.",
        ],
        "glossary": {
            "Varian": "Satu pola urutan aktivitas yang diikuti oleh satu atau lebih case.",
            "Varian Dominan": "Varian yang paling sering muncul dalam log.",
            "Urutan Aktivitas": "Daftar aktivitas yang dilalui kasus dari awal hingga akhir.",
            "Rework Loop": "Pola di mana aktivitas diulang, misalnya Approval -> Revision -> Approval.",
        },
    },
    "cases": {
        "concepts": [
            (
                "Mengapa Perlu Melihat Case Individual?",
                "Statistik dan peta proses memberikan gambaran umum, tetapi case explorer "
                "membantu memeriksa contoh proses secara detail. Ini penting untuk "
                "memvalidasi temuan dan memahami kejadian nyata di balik angka.",
            ),
            (
                "Cara Membaca Timeline Case",
                "Timeline case menunjukkan urutan aktivitas dari awal sampai akhir "
                "untuk satu case. Dari sini, kita dapat melihat durasi, aktivitas "
                "berulang, dan jeda waktu antar aktivitas.",
            ),
        ],
        "questions": [
            "Aktivitas pertama dalam case ini apa?",
            "Aktivitas terakhir dalam case ini apa?",
            "Berapa lama durasi case ini?",
            "Apakah ada aktivitas yang berulang?",
            "Apakah ada jeda waktu yang terlalu panjang antar aktivitas?",
            "Apakah case ini mengikuti varian umum atau varian langka?",
        ],
        "observations": [
            "Saya dapat membaca urutan aktivitas dalam satu case.",
            "Saya dapat menemukan durasi case.",
            "Saya dapat mengidentifikasi aktivitas yang berulang.",
            "Saya dapat mengenali jeda waktu yang panjang.",
            "Saya dapat menghubungkan case ini dengan varian prosesnya.",
        ],
        "interpretation_hints": [
            "Case dengan durasi sangat panjang dapat menjadi kandidat bottleneck.",
            "Aktivitas berulang dalam case dapat menunjukkan revisi atau rework.",
            "Jeda panjang antar event dapat menunjukkan waktu tunggu.",
            "Case detail membantu memastikan apakah kesimpulan dari statistik "
            "benar secara konteks.",
        ],
        "misconceptions": [
            "Satu case tidak cukup untuk menyimpulkan keseluruhan proses.",
            "Case lambat belum tentu salah — bisa jadi memang kompleks.",
            "Aktivitas berulang harus dicek konteksnya sebelum disebut masalah.",
        ],
        "glossary": {
            "Timeline": "Urutan kejadian dalam satu kasus dari awal hingga akhir.",
            "Jeda Waktu": "Selisih waktu yang panjang antara dua kejadian berturut-turut.",
            "Durasi Kasus": "Total waktu dari kejadian pertama hingga terakhir dalam kasus.",
            "Rework": "Pengulangan aktivitas yang sudah dilakukan sebelumnya dalam kasus yang sama.",
        },
    },
    "report": {
        "concepts": [
            (
                "Membaca Laporan",
                "Laporan memuat tujuh bagian utama:\n"
                "1. **Ringkasan Dataset** — gambaran umum data\n"
                "2. **Ringkasan Validasi** — kualitas data\n"
                "3. **Aktivitas Teratas** — aktivitas paling sering\n"
                "4. **Varian Teratas** — jalur proses paling umum\n"
                "5. **Kasus Paling Lambat** — kasus yang membutuhkan waktu terlama\n"
                "6. **Transisi Bottleneck** — transisi dengan waktu tunggu terpanjang\n"
                "7. **Petunjuk Interpretasi** — panduan membaca hasil",
            ),
            (
                "Menggunakan Laporan untuk Tugas",
                "Laporan dapat diunduh dalam format Markdown. "
                "Gunakan laporan sebagai dasar untuk:\n"
                "- Menjawab pertanyaan analisis proses\n"
                "- Mengidentifikasi area perbaikan\n"
                "- Membuat rekomendasi proses\n"
                "- Membandingkan hasil sebelum dan sesudah filter",
            ),
        ],
        "questions": [
            "Aktivitas apa yang paling sering muncul di bagian Aktivitas Teratas?",
            "Varian mana yang mendominasi? Berapa persen kasus yang mengikuti varian ini?",
            "Transisi mana yang memiliki waktu tunggu terpanjang? Apa dampaknya terhadap proses?",
            "Jika Anda hanya bisa memperbaiki satu transisi, mana yang akan Anda pilih? Mengapa?",
            "Bagaimana hasil berubah jika Anda menerapkan filter yang berbeda?",
        ],
        "assignment_sections": [
            (
                "A. Pemahaman Dataset",
                [
                    "Berapa total kejadian dan total kasus dalam dataset?",
                    "Apa saja aktivitas yang ada dalam proses? Berapa jumlahnya?",
                    "Siapa atau unit mana saja yang terlibat sebagai sumber daya (resource)?",
                ],
            ),
            (
                "B. Analisis Peta Proses",
                [
                    "Aktivitas apa yang menjadi titik awal dan titik akhir proses?",
                    "Transisi mana yang paling sering terjadi?",
                    "Apakah terdapat loop atau aktivitas yang berulang? Jelaskan.",
                    "Apakah ada jalur yang tidak biasa atau jarang dilalui?",
                    "Transisi mana yang menunjukkan waktu tunggu terpanjang (bottleneck)?",
                ],
            ),
            (
                "C. Analisis Statistik",
                [
                    "Aktivitas apa yang paling sering muncul? Mengapa menurut Anda?",
                    "Berapa durasi rata-rata dan median kasus? Apakah ada perbedaan signifikan?",
                    "Resource mana yang paling banyak terlibat dalam proses?",
                    "Apakah terdapat outlier pada distribusi durasi kasus?",
                ],
            ),
            (
                "D. Analisis Varian",
                [
                    "Varian apa yang paling dominan? Berapa persen kasus yang mengikutinya?",
                    "Berapa total varian yang terdeteksi?",
                    "Apakah top 3 varian sudah mencakup sebagian besar kasus?",
                    "Apakah ada varian yang mengandung aktivitas berulang?",
                ],
            ),
            (
                "E. Analisis Kasus",
                [
                    "Pilih satu kasus dan jelaskan perjalanannya dari awal hingga akhir.",
                    "Apakah ada aktivitas yang berulang dalam kasus tersebut?",
                    "Berapa durasi kasus tersebut? Apakah tergolong normal atau outlier?",
                    "Apakah terdapat jeda waktu yang panjang antar aktivitas?",
                ],
            ),
            (
                "F. Kesimpulan",
                [
                    "Apa temuan utama dari analisis proses ini?",
                    "Di mana letak bottleneck dan apa dampaknya terhadap proses?",
                    "Apa rekomendasi perbaikan yang dapat Anda berikan?",
                    "Apa keterbatasan dari analisis ini dan apa yang perlu diteliti lebih lanjut?",
                ],
            ),
        ],
        "rubric": [
            ("Pemahaman event log", "20%"),
            ("Analisis process map", "20%"),
            ("Analisis statistik dan varian", "25%"),
            ("Analisis case dan bottleneck", "20%"),
            ("Kesimpulan dan rekomendasi", "15%"),
        ],
        "glossary": {
            "Bottleneck": "Titik dalam proses yang menyebabkan keterlambatan karena waktu tunggu panjang.",
            "Waktu Tunggu Rata-rata": "Rata-rata waktu yang dihabiskan antara dua aktivitas berturut-turut.",
            "Waktu Tunggu Maksimum": "Waktu tunggu terpanjang yang pernah tercatat untuk transisi tertentu.",
            "Laporan Markdown": "Format teks yang dapat dibaca oleh manusia dan dikonversi ke berbagai format dokumen.",
        },
    },
}


def render_page_learning_content(page_name: str) -> None:
    """Dispatch semua konten edukasi untuk halaman yang diberikan.

    Fungsi ini memeriksa ``st.session_state["learning_mode"]`` dan
    merender pengantar, konsep, pertanyaan, checklist, petunjuk,
    kesalahan pemahaman, dan glosarium sesuai *page_name*.

    Parameters
    ----------
    page_name : str
        Salah satu: "upload", "map", "statistics", "variants",
        "cases", "report".
    """
    if not st.session_state.get("learning_mode", False):
        return

    data = _PAGE_CONTENT.get(page_name)
    if data is None:
        return

    render_learning_intro(page_name)

    for title, content in data.get("concepts", []):
        render_concept_box(title, content)

    if "questions" in data:
        render_guided_questions(data["questions"])

    if "observations" in data:
        render_observation_checklist(data["observations"])

    if "interpretation_hints" in data:
        render_interpretation_hints(data["interpretation_hints"])

    if "misconceptions" in data:
        render_common_misconceptions(data["misconceptions"])

    if "assignment_sections" in data and "rubric" in data:
        render_assignment_guide(data["assignment_sections"], data["rubric"])

    if "glossary" in data:
        render_mini_glossary(data["glossary"])
