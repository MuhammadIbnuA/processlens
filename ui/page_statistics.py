"""Statistics page - descriptive metrics dashboard.

Displays activity frequencies, case durations,
and other summary charts.
"""

from __future__ import annotations

import plotly.express as px
import streamlit as st

from core.statistics import (
    calculate_activity_statistics,
    calculate_case_duration_distribution,
    calculate_events_over_time,
    calculate_global_statistics,
    calculate_resource_statistics,
    seconds_to_readable,
)
from ui.learning_mode import render_page_learning_content

def render_statistics_page() -> None:
    """Render the statistics dashboard with progress indicators."""
    st.header("Statistik")
    st.info(
        "Statistik membantu merangkum perilaku proses, "
        "seperti aktivitas yang paling sering muncul, durasi kasus, "
        "dan beban kerja dari waktu ke waktu."
    )

    # Mode Pembelajaran
    render_page_learning_content("statistics")

    if "filtered_log" not in st.session_state:
        st.warning("Silakan unggah dan proses log kejadian terlebih dahulu.")
        return

    df = st.session_state["filtered_log"]

    if len(df) == 0:
        st.warning("Tidak ada kasus yang sesuai dengan filter saat ini.")
        return

    # Show progress while calculating global statistics
    with st.spinner("Menghitung statistik global..."):
        gs = calculate_global_statistics(df)

    # ------------------------------------------------------------------
    # Tabs
    # ------------------------------------------------------------------
    tab_overview, tab_activities, tab_time, tab_resources, tab_durations = st.tabs(
        ["Ringkasan", "Aktivitas", "Waktu", "Sumber Daya", "Durasi"]
    )

    # ==================================================================
    # Ringkasan
    # ==================================================================
    with tab_overview:
        m1, m2, m3, m4, m5, m6 = st.columns(6)
        m1.metric("Kejadian", gs["total_events"])
        m2.metric("Kasus", gs["total_cases"])
        m3.metric("Aktivitas", gs["total_activities"])
        m4.metric("Varian", gs["total_variants"])
        m5.metric("Durasi Rata-rata", seconds_to_readable(gs["avg_case_duration_seconds"]))
        m6.metric("Durasi Median", seconds_to_readable(gs["median_case_duration_seconds"]))

    # ==================================================================
    # Aktivitas
    # ==================================================================
    with tab_activities:
        with st.spinner("Menghitung statistik aktivitas..."):
            act_stats = calculate_activity_statistics(df)

        try:
            fig = px.bar(
                act_stats,
                x="activity",
                y="frequency",
                text="frequency",
                title="Frekuensi Aktivitas",
            )
            fig.update_layout(xaxis_title="Aktivitas", yaxis_title="Frekuensi")
            st.plotly_chart(fig, use_container_width=True)
        except Exception as exc:
            st.error(f"Graf aktivitas tidak dapat ditampilkan: {exc}")

        display_act = act_stats.rename(columns={
            "activity": "Aktivitas",
            "frequency": "Frekuensi",
            "case_frequency": "Jumlah Kasus",
            "percentage_events": "% Kejadian",
        })
        st.dataframe(display_act, use_container_width=True, hide_index=True)

    # ==================================================================
    # Waktu
    # ==================================================================
    with tab_time:
        st.subheader("Kejadian dari Waktu ke Waktu")
        freq_option = st.selectbox(
            "Periode agregasi",
            ["Harian", "Mingguan"],
            index=0,
        )
        freq = "D" if freq_option == "Harian" else "W"

        with st.spinner("Menghitung kejadian dari waktu ke waktu..."):
            eot = calculate_events_over_time(df, freq=freq)

        try:
            fig = px.bar(
                eot,
                x="period",
                y="event_count",
                title=f"Kejadian per periode {freq_option.lower()}",
            )
            fig.update_layout(xaxis_title="Periode", yaxis_title="Jumlah Kejadian")
            st.plotly_chart(fig, use_container_width=True)
        except Exception as exc:
            st.error(f"Graf waktu tidak dapat ditampilkan: {exc}")

    # ==================================================================
    # Sumber Daya
    # ==================================================================
    with tab_resources:
        with st.spinner("Menghitung statistik sumber daya..."):
            res_stats = calculate_resource_statistics(df)

        try:
            fig = px.bar(
                res_stats,
                x="resource",
                y="frequency",
                text="frequency",
                title="Frekuensi Sumber Daya",
            )
            fig.update_layout(xaxis_title="Sumber Daya", yaxis_title="Frekuensi")
            st.plotly_chart(fig, use_container_width=True)
        except Exception as exc:
            st.error(f"Graf sumber daya tidak dapat ditampilkan: {exc}")

        display_res = res_stats.rename(columns={
            "resource": "Sumber Daya",
            "frequency": "Frekuensi",
            "case_frequency": "Jumlah Kasus",
            "percentage_events": "% Kejadian",
        })
        st.dataframe(display_res, use_container_width=True, hide_index=True)

    # ==================================================================
    # Durasi
    # ==================================================================
    with tab_durations:
        with st.spinner("Menghitung distribusi durasi kasus..."):
            case_dist = calculate_case_duration_distribution(df)

        try:
            fig = px.histogram(
                case_dist,
                x="duration_days",
                nbins=20,
                title="Distribusi Durasi Kasus",
            )
            fig.update_layout(xaxis_title="Durasi (hari)", yaxis_title="Jumlah Kasus")
            st.plotly_chart(fig, use_container_width=True)
        except Exception as exc:
            st.error(f"Graf durasi tidak dapat ditampilkan: {exc}")

        display_dist = case_dist.rename(columns={
            "case_id": "ID Kasus",
            "duration_seconds": "Durasi (dtk)",
            "duration_hours": "Durasi (jam)",
            "duration_days": "Durasi (hari)",
            "event_count": "Jumlah Kejadian",
        })
        st.dataframe(display_dist, use_container_width=True, hide_index=True)