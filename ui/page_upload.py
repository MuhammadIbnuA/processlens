"""Upload page - CSV file upload and log validation.

Lets the user upload a CSV, select column mappings,
and validates the log before proceeding.
"""

from __future__ import annotations

import os

import pandas as pd
import streamlit as st

from core.import_log import get_column_names, map_event_log_columns, read_csv_file
from core.transform_log import prepare_event_log
from core.validate_log import validate_event_log
from ui.learning_mode import render_page_learning_content

SAMPLE_DATA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "sample_data",
    "purchasing_sample.csv",
)

def render_upload_page() -> None:
    """Render the CSV upload and column-mapping page with progress indicators."""
    st.header("Unggah Log Kejadian")
    st.write(
        "Unggah file CSV yang berisi log kejadian Anda, "
        "atau muat dataset sampel untuk memulai."
    )
    st.info(
        "Log kejadian mencatat apa yang terjadi dalam sebuah proses. "
        "Setiap baris adalah satu kejadian. "
        "Log process mining biasanya memerlukan ID Kasus, Aktivitas, dan Waktu Kejadian."
    )

    # Mode Pembelajaran
    render_page_learning_content("upload")

    # ------------------------------------------------------------------
    # Load sample button
    # ------------------------------------------------------------------
    if st.button("Muat Data Sampel", key="btn_load_sample"):
        with st.spinner("Memuat data sampel..."):
            try:
                raw = read_csv_file(SAMPLE_DATA_PATH)
                if len(raw) == 0:
                    st.error("File CSV sampel kosong.")
                    return
                st.session_state["raw_df"] = raw
                st.success("Data sampel berhasil dimuat.")
            except (ValueError, FileNotFoundError) as exc:
                st.error(f"Data sampel tidak dapat dimuat: {exc}")

    # ------------------------------------------------------------------
    # File uploader
    # ------------------------------------------------------------------
    uploaded_file = st.file_uploader(
        "Unggah file CSV",
        type=["csv"],
        help="Hanya file .csv yang diterima.",
    )

    if uploaded_file is not None:
        with st.spinner("Membaca file CSV..."):
            try:
                raw = read_csv_file(uploaded_file)
                if len(raw) == 0:
                    st.error("File CSV yang diunggah kosong (tidak ada baris data).")
                    return
                st.session_state["raw_df"] = raw
            except ValueError as exc:
                st.error(str(exc))
                return

    # ------------------------------------------------------------------
    # Preview & column mapping
    # ------------------------------------------------------------------
    raw: pd.DataFrame | None = st.session_state.get("raw_df")
    if raw is None:
        return

    st.subheader("Pratinjau Data")
    st.dataframe(raw.head(10), use_container_width=True)

    with st.spinner("Mengambil nama kolom..."):
        columns = get_column_names(raw)

    st.subheader("Pemetaan Kolom")

    col1, col2 = st.columns(2)
    with col1:
        case_col = st.selectbox("Kolom ID Kasus", columns, index=0)
        activity_col = st.selectbox("Kolom Aktivitas", columns, index=min(1, len(columns) - 1))
    with col2:
        timestamp_col = st.selectbox("Kolom Waktu Kejadian", columns, index=min(2, len(columns) - 1))
        resource_options = ["(tidak ada)"] + columns
        resource_col = st.selectbox(
            "Kolom Sumber Daya (opsional)",
            resource_options,
            index=0,
        )

    resource_mapped = None if resource_col == "(tidak ada)" else resource_col

    # ------------------------------------------------------------------
    # Process button
    # ------------------------------------------------------------------
    if st.button("Proses Log Kejadian", key="btn_process_log"):
        # Check unique columns including resource
        selected = [case_col, activity_col, timestamp_col]
        if resource_mapped is not None:
            selected.append(resource_mapped)
        if len(selected) != len(set(selected)):
            st.error(
                "Kolom mapping tidak boleh sama. "
                "Pilih kolom yang berbeda untuk ID Kasus, Aktivitas, "
                "Waktu Kejadian, dan Sumber Daya."
            )
            return

        with st.spinner("Memproses log kejadian..."):
            try:
                mapped = map_event_log_columns(
                    raw,
                    case_col=case_col,
                    activity_col=activity_col,
                    timestamp_col=timestamp_col,
                    resource_col=resource_mapped,
                )
            except ValueError as exc:
                st.error(str(exc))
                return
            prepared = prepare_event_log(mapped)
            validation = validate_event_log(prepared)

        if len(prepared) == 0:
            st.error(
                "Tidak ada kejadian valid yang tersisa setelah pemrosesan. "
                "Pastikan kolom waktu kejadian berisi tanggal yang dapat dibaca."
            )
            return

        # Warn about unparseable timestamps
        na_ts = mapped["timestamp"].isna().sum()
        if na_ts > 0:
            st.warning(
                f"{na_ts} baris memiliki waktu kejadian yang tidak dapat dibaca dan telah dihapus."
            )

        st.session_state["event_log"] = prepared
        st.session_state["filtered_log"] = prepared.copy()
        st.session_state["validation"] = validation
        st.session_state["column_mapping_done"] = True

        st.success("Log kejadian berhasil diproses!")

    # ------------------------------------------------------------------
    # Validation results
    # ------------------------------------------------------------------
    if not st.session_state.get("column_mapping_done"):
        return

    validation = st.session_state.get("validation")
    if validation is None:
        return

    st.subheader("Hasil Validasi")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Kejadian", validation["total_events"])
    m2.metric("Total Kasus", validation["total_cases"])
    m3.metric("Aktivitas", validation["total_activities"])
    m4.metric("Sumber Daya", validation["total_resources"])

    if validation.get("warnings"):
        st.warning("Peringatan:")
        for w in validation["warnings"]:
            st.write(f"- {w}")

    if validation["is_valid"]:
        st.success("Log kejadian lolos semua pemeriksaan validasi.")
    else:
        st.error(
            "Log kejadian memiliki masalah kritis. "
            "Pastikan case_id, activity, dan timestamp tidak ada yang kosong."
        )

    # ------------------------------------------------------------------
    # Export options
    # ------------------------------------------------------------------
    st.subheader("Ekspor Log Kejadian")
    
    from core.import_log import export_event_log
    
    df = st.session_state["event_log"]
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        csv_data, csv_mime = export_event_log(df, "csv")
        st.download_button(
            label="Unduh CSV",
            data=csv_data,
            file_name="log_kejadian.csv",
            mime=csv_mime,
            help="Format CSV standar untuk dibuka di spreadsheet"
        )
    
    with col2:
        json_data, json_mime = export_event_log(df, "json")
        st.download_button(
            label="Unduh JSON",
            data=json_data,
            file_name="log_kejadian.json",
            mime=json_mime,
            help="Format JSON untuk integrasi sistem"
        )
    
    with col3:
        xlsx_data, xlsx_mime = export_event_log(df, "xlsx")
        st.download_button(
            label="Unduh Excel",
            data=xlsx_data,
            file_name="log_kejadian.xlsx",
            mime=xlsx_mime,
            help="Format Excel untuk dibuka di Microsoft Excel"
        )