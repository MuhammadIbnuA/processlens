"""Cases page - individual case explorer.

Allows the user to select and inspect a single case,
viewing its event sequence and timing details.
"""

from __future__ import annotations

import plotly.express as px
import streamlit as st

from core.statistics import seconds_to_readable
from core.variants import get_case_variant
from ui.learning_mode import render_page_learning_content

def render_cases_page() -> None:
    """Render the individual case explorer page with progress indicators."""
    st.header("Penjelajah Kasus")
    st.info(
        "Penjelajah kasus memungkinkan Anda memeriksa satu instansi proses "
        "dari awal hingga akhir."
    )

    # Mode Pembelajaran
    render_page_learning_content("cases")

    if "filtered_log" not in st.session_state:
        st.warning("Silakan unggah dan proses log kejadian terlebih dahulu.")
        return

    df = st.session_state["filtered_log"]

    if len(df) == 0:
        st.warning("Tidak ada kasus yang sesuai dengan filter saat ini.")
        return

    # ------------------------------------------------------------------
    # Case selector
    # ------------------------------------------------------------------
    case_ids = sorted(df["case_id"].unique().tolist())
    selected_case = st.selectbox("Pilih kasus", case_ids)

    with st.spinner("Memuat detail kasus..."):
        case_events = df[df["case_id"] == selected_case].sort_values("timestamp")

    if len(case_events) == 0:
        st.warning(f"Tidak ada kejadian ditemukan untuk kasus {selected_case}.")
        return

    # ------------------------------------------------------------------
    # Case summary
    # ------------------------------------------------------------------
    start_time = case_events["timestamp"].min()
    end_time = case_events["timestamp"].max()
    duration_seconds = (end_time - start_time).total_seconds()
    event_count = len(case_events)
    
    with st.spinner("Menghitung urutan aktivitas..."):
        try:
            variant_seq = get_case_variant(df, selected_case)
        except KeyError:
            variant_seq = " -> ".join(case_events["activity"].tolist())

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Waktu Mulai", str(start_time))
    m2.metric("Waktu Selesai", str(end_time))
    m3.metric("Durasi", seconds_to_readable(duration_seconds))
    m4.metric("Jumlah Kejadian", event_count)

    st.markdown(f"**Urutan aktivitas:** {variant_seq}")

    # ------------------------------------------------------------------
    # Event timeline table
    # ------------------------------------------------------------------
    st.subheader("Linimasa Kejadian")
    display_events = case_events.rename(columns={
        "case_id": "ID Kasus",
        "activity": "Aktivitas",
        "timestamp": "Waktu Kejadian",
        "resource": "Sumber Daya",
    })
    st.dataframe(display_events, use_container_width=True, hide_index=True)

    # ------------------------------------------------------------------
    # Timeline chart
    # ------------------------------------------------------------------
    st.subheader("Linimasa Aktivitas")

    with st.spinner("Menggambar grafik linimasa..."):
        chart_df = case_events[["timestamp", "activity"]].copy()
        chart_df["activity_label"] = chart_df["activity"]

    try:
        with st.spinner("Menghasilkan grafik..."):
            fig = px.scatter(
                chart_df,
                x="timestamp",
                y="activity_label",
                text="activity_label",
                title=f"Kasus {selected_case} - Linimasa Aktivitas",
            )
            fig.update_traces(
                marker=dict(size=14, color="#4A90D9"),
                textposition="top center",
            )
            fig.update_layout(
                xaxis_title="Waktu Kejadian",
                yaxis_title="Aktivitas",
                height=400,
            )
        st.plotly_chart(fig, use_container_width=True)
    except Exception as exc:
        st.error(f"Linimasa tidak dapat ditampilkan: {exc}")

    # ------------------------------------------------------------------
    # Interpretation hints
    # ------------------------------------------------------------------
    st.subheader("Petunjuk Interpretasi")

    # Check for repeated activities
    activity_counts = case_events["activity"].value_counts()
    repeated = activity_counts[activity_counts > 1]
    if len(repeated) > 0:
        acts = ", ".join(repeated.index.tolist())
        st.info(
            f"**Aktivitas berulang terdeteksi:** {acts}. "
            "Ini dapat menunjukkan pengerjaan ulang atau loop proses."
        )

    # Check for long gaps
    if len(case_events) > 1:
        timestamps = case_events["timestamp"].tolist()
        gaps = []
        for i in range(1, len(timestamps)):
            gap_hours = (timestamps[i] - timestamps[i - 1]).total_seconds() / 3600
            if gap_hours > 48:
                gaps.append((
                    case_events.iloc[i - 1]["activity"],
                    case_events.iloc[i]["activity"],
                    gap_hours,
                ))
        if gaps:
            for src, tgt, hours in gaps:
                days = hours / 24
                st.warning(
                    f"**Jeda waktu panjang ({days:.1f} hari)** antara "
                    f"*{src}* dan *{tgt}*. "
                    "Ini dapat menunjukkan waktu tunggu atau bottleneck."
                )
    else:
        st.info("Kasus ini hanya memiliki satu kejadian — tidak ada transisi untuk dianalisis.")