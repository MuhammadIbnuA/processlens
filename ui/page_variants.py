"""Variants page - explore process variants.

Shows variant table, variant frequencies,
and allows drilling into individual variants.
"""

from __future__ import annotations

import streamlit as st

from core.statistics import seconds_to_readable
from core.variants import calculate_variants
from ui.learning_mode import render_page_learning_content

MAX_DISPLAYED_EVENTS = 500
MAX_DISPLAYED_CASE_IDS = 50

def render_variants_page() -> None:
    """Render the variants explorer page with progress indicators."""
    st.header("Varian Proses")
    st.info(
        "Varian adalah satu urutan aktivitas unik "
        "yang diikuti oleh satu atau lebih kasus."
    )

    # Mode Pembelajaran
    render_page_learning_content("variants")

    if "filtered_log" not in st.session_state:
        st.warning("Silakan unggah dan proses log kejadian terlebih dahulu.")
        return

    df = st.session_state["filtered_log"]

    if len(df) == 0:
        st.warning("Tidak ada kasus yang sesuai dengan filter saat ini.")
        return

    # Show progress while calculating variants
    with st.spinner("Menghitung varian proses..."):
        variants = calculate_variants(df)

    # ------------------------------------------------------------------
    # Summary metrics
    # ------------------------------------------------------------------
    total_variants = len(variants)
    top = variants.iloc[0] if total_variants > 0 else None

    m1, m2, m3 = st.columns(3)
    m1.metric("Total Varian", total_variants)
    if top is not None:
        m2.metric("Varian Paling Sering", top["variant_id"])
        m3.metric("Persentase Kasus", f"{top['percentage']}%")
    else:
        m2.metric("Varian Paling Sering", "-")
        m3.metric("Persentase Kasus", "-")

    # ------------------------------------------------------------------
    # Variants table
    # ------------------------------------------------------------------
    st.subheader("Semua Varian")

    if len(variants) > 0:
        display_df = variants[[
            "variant_id",
            "sequence",
            "case_count",
            "percentage",
            "avg_duration_seconds",
            "median_duration_seconds",
        ]].copy()
        display_df["avg_duration_seconds"] = display_df["avg_duration_seconds"].apply(
            seconds_to_readable
        )
        display_df["median_duration_seconds"] = display_df["median_duration_seconds"].apply(
            seconds_to_readable
        )
        display_df = display_df.rename(columns={
            "variant_id": "ID Varian",
            "sequence": "Urutan Aktivitas",
            "case_count": "Jumlah Kasus",
            "percentage": "Persentase",
            "avg_duration_seconds": "Durasi Rata-rata",
            "median_duration_seconds": "Durasi Median",
        })

        st.dataframe(display_df, use_container_width=True, hide_index=True)

    # ------------------------------------------------------------------
    # Variant drill-down
    # ------------------------------------------------------------------
    if total_variants == 0:
        return

    st.subheader("Jelajahi Varian")

    variant_ids = variants["variant_id"].tolist()
    selected_id = st.selectbox("Pilih varian", variant_ids)

    row = variants.loc[variants["variant_id"] == selected_id].iloc[0]

    st.markdown(f"**Urutan aktivitas:** {row['sequence']}")
    st.markdown(f"**Jumlah kasus:** {row['case_count']}")
    st.markdown(f"**Durasi rata-rata:** {seconds_to_readable(row['avg_duration_seconds'])}")

    # Case IDs
    case_ids: list[str] = row["case_ids"]
    st.markdown(f"**Kasus ({len(case_ids)}):**")
    if len(case_ids) <= MAX_DISPLAYED_CASE_IDS:
        st.write(", ".join(case_ids))
    else:
        shown = ", ".join(case_ids[:MAX_DISPLAYED_CASE_IDS])
        st.write(f"{shown}, ... dan {len(case_ids) - MAX_DISPLAYED_CASE_IDS} lainnya")

    # Events for selected cases
    st.subheader("Kejadian dalam Varian Terpilih")
    variant_events = df[df["case_id"].isin(case_ids)]

    if len(variant_events) > MAX_DISPLAYED_EVENTS:
        st.info(
            f"Menampilkan {MAX_DISPLAYED_EVENTS} kejadian pertama dari {len(variant_events)} total."
        )
        variant_events = variant_events.head(MAX_DISPLAYED_EVENTS)

    st.dataframe(variant_events, use_container_width=True, hide_index=True)