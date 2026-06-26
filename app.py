"""ProcessLens EDU - Educational Process Mining App.

Streamlit entry point that wires together the UI pages
and orchestrates session state across the application.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from core.filters import apply_filters
from ui.page_cases import render_cases_page
from ui.page_map import render_map_page
from ui.page_report import render_report_page
from ui.page_statistics import render_statistics_page
from ui.page_upload import render_upload_page
from ui.page_variants import render_variants_page

st.set_page_config(
    page_title="ProcessLens EDU",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state for theme
if "dark_theme" not in st.session_state:
    st.session_state["dark_theme"] = True

# ======================================================================
# Sidebar – filters and theme toggle
# ======================================================================
st.sidebar.title("ProcessLens EDU")

# Theme toggle
col1, col2 = st.sidebar.columns([3, 1])
with col1:
    st.session_state["dark_theme"] = st.sidebar.toggle(
        "Mode Gelap", 
        value=st.session_state["dark_theme"],
        help="Alihkan antara mode gelap dan terang"
    )

# Mode Pembelajaran
st.session_state["learning_mode"] = st.sidebar.checkbox(
    "Mode Pembelajaran",
    value=False,
    help="Aktifkan untuk melihat konten edukasi di setiap halaman.",
)

event_log: pd.DataFrame | None = st.session_state.get("event_log")

if event_log is not None and len(event_log) > 0:
    st.sidebar.subheader("Filter")

    ts_min = event_log["timestamp"].min()
    ts_max = event_log["timestamp"].max()

    # Create filter inputs with unique keys
    date_start = st.sidebar.date_input("Tanggal mulai", value=ts_min.date(), min_value=ts_min.date(), max_value=ts_max.date(), key="filter_date_start")
    date_end = st.sidebar.date_input("Tanggal selesai", value=ts_max.date(), min_value=ts_min.date(), max_value=ts_max.date(), key="filter_date_end")

    all_activities = sorted(event_log["activity"].unique().tolist())
    selected_activities = st.sidebar.multiselect("Aktivitas yang harus ada dalam kasus", all_activities, key="filter_activities")

    min_dur_days = st.sidebar.number_input("Durasi kasus minimum (hari)", min_value=0.0, value=0.0, step=1.0, key="filter_min_dur")
    max_dur_days = st.sidebar.number_input("Durasi kasus maksimum (hari)", min_value=0.0, value=0.0, step=1.0, key="filter_max_dur")

    top_n_variants = st.sidebar.number_input("N varian teratas (0 = semua)", min_value=0, value=0, step=1, key="filter_top_n")

    # Auto-refresh mechanism: Check if filter values changed since last run
    current_filters = {
        "date_start": date_start,
        "date_end": date_end,
        "activities": selected_activities,
        "min_dur": min_dur_days,
        "max_dur": max_dur_days,
        "top_n": top_n_variants
    }
    
    # Compare with previous filter values
    prev_filters = st.session_state.get("prev_filters", {})
    filters_changed = current_filters != prev_filters
    
    if filters_changed:
        # Update stored filters
        st.session_state["prev_filters"] = current_filters.copy()
        
        # Apply filters automatically
        filters: dict = {}
        
        if date_start != ts_min.date() or date_end != ts_max.date():
            filters["start_date"] = pd.Timestamp(date_start)
            filters["end_date"] = pd.Timestamp(date_end) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)

        if selected_activities:
            filters["activities"] = selected_activities

        if min_dur_days > 0:
            filters["min_duration_seconds"] = min_dur_days * 86400
        if max_dur_days > 0:
            filters["max_duration_seconds"] = max_dur_days * 86400

        if top_n_variants > 0:
            filters["top_n_variants"] = top_n_variants

        # Show progress bar while applying filters
        with st.spinner("Menerapkan filter otomatis..."):
            if filters:
                st.session_state["filtered_log"] = apply_filters(event_log, filters)
            else:
                st.session_state["filtered_log"] = event_log.copy()

    col_apply, col_reset = st.sidebar.columns(2)

    with col_apply:
        # Manual refresh button (for explicit control)
        if st.button("Terapkan Filter", key="btn_apply_filters"):
            filters: dict = {}

            if date_start != ts_min.date() or date_end != ts_max.date():
                filters["start_date"] = pd.Timestamp(date_start)
                filters["end_date"] = pd.Timestamp(date_end) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)

            if selected_activities:
                filters["activities"] = selected_activities

            if min_dur_days > 0:
                filters["min_duration_seconds"] = min_dur_days * 86400
            if max_dur_days > 0:
                filters["max_duration_seconds"] = max_dur_days * 86400

            if top_n_variants > 0:
                filters["top_n_variants"] = top_n_variants

            # Show progress bar while applying filters
            with st.spinner("Menerapkan filter..."):
                st.session_state["filtered_log"] = apply_filters(event_log, filters)

    with col_reset:
        if st.button("Reset Filter", key="btn_reset_filters"):
            # Reset filter inputs to defaults
            st.session_state["filter_date_start"] = ts_min.date()
            st.session_state["filter_date_end"] = ts_max.date()
            st.session_state["filter_activities"] = []
            st.session_state["filter_min_dur"] = 0.0
            st.session_state["filter_max_dur"] = 0.0
            st.session_state["filter_top_n"] = 0
            # Reset filtered log to original
            st.session_state["filtered_log"] = event_log.copy()
            # Clear previous filters
            st.session_state["prev_filters"] = {}

    # Show counts
    filtered_log = st.session_state.get("filtered_log", event_log)
    st.sidebar.divider()
    st.sidebar.caption(
        f"Kejadian: {len(event_log)} -> {len(filtered_log)}  \n"
        f"Kasus: {event_log['case_id'].nunique()} -> {filtered_log['case_id'].nunique()}"
    )

# ======================================================================
# Navigation with keyboard shortcuts
# ======================================================================
tabs = st.tabs([
    "Unggah & Pemetaan (Alt+1)",
    "Peta Proses (Alt+2)", 
    "Statistik (Alt+3)",
    "Varian (Alt+4)",
    "Kasus (Alt+5)",
    "Laporan (Alt+6)",
])

# Add keyboard shortcut handling with JavaScript
st.markdown("""
<script>
document.addEventListener('keydown', function(event) {
    // Alt+1 to Alt+6 for navigation
    if (event.altKey && event.key >= '1' && event.key <= '6') {
        const tabIndex = parseInt(event.key) - 1;
        // Trigger tab click (requires custom handling)
        const tabs = document.querySelectorAll('[data-baseweb="tab"]');
        if (tabs[tabIndex]) {
            tabs[tabIndex].click();
        }
    }
});
</script>
""", unsafe_allow_html=True)

# Render content for each tab
with tabs[0]:
    render_upload_page()
with tabs[1]:
    render_map_page()
with tabs[2]:
    render_statistics_page()
with tabs[3]:
    render_variants_page()
with tabs[4]:
    render_cases_page()
with tabs[5]:
    render_report_page()