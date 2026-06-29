"""Report page - summary report view.

Presents a consolidated report of key findings
from the loaded event log.
"""

from __future__ import annotations

import io

import pandas as pd
import streamlit as st

from core.report import generate_markdown_report
from ui.learning_mode import render_page_learning_content

EXCEL_MAX_CELL_LENGTH = 32000  # Leave some buffer below the 32767 limit


def _truncate_long_cells_for_excel(df: pd.DataFrame) -> pd.DataFrame:
    """Truncate cells with content longer than Excel's cell limit.
    
    Excel has a hard limit of 32767 characters per cell. This function
    safely truncates cells longer than the limit and appends a marker
    to indicate data was truncated.
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame to process
        
    Returns
    -------
    pd.DataFrame
        DataFrame with long cells truncated
    """
    df_copy = df.copy()
    
    # Process all object/string columns
    for col in df_copy.columns:
        if df_copy[col].dtype == "object":
            # Convert to string and check length
            mask = df_copy[col].apply(
                lambda x: isinstance(x, str) and len(x) > EXCEL_MAX_CELL_LENGTH
            )
            
            if mask.any():
                # Truncate long cells and add indicator
                truncated_values = df_copy.loc[mask, col].apply(
                    lambda x: x[:EXCEL_MAX_CELL_LENGTH - 15] + " ... [TRUNCATED]" if isinstance(x, str) and len(x) > EXCEL_MAX_CELL_LENGTH else x
                )
                df_copy.loc[mask, col] = truncated_values
    
    return df_copy


def render_report_page() -> None:
    """Render the process-mining report page with progress indicators and additional export formats."""
    st.header("Laporan")
    st.info(
        "Laporan merangkum log kejadian yang telah difilter "
        "dan dapat digunakan sebagai titik awal untuk tugas praktikum."
    )

    # Mode Pembelajaran
    render_page_learning_content("report")

    if "filtered_log" not in st.session_state:
        st.warning("Silakan unggah dan proses log kejadian terlebih dahulu.")
        return

    df = st.session_state["filtered_log"]

    if len(df) == 0:
        st.warning("Tidak ada kasus yang sesuai dengan filter saat ini.")
        return

    validation = st.session_state.get("validation")
    
    # Show progress while generating report
    with st.spinner("Menghasilkan laporan..."):
        report_md = generate_markdown_report(df, validation_result=validation)
    
    st.markdown(report_md)

    st.divider()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.download_button(
            label="Unduh Laporan (Markdown)",
            data=report_md,
            file_name="laporan_process_mining.md",
            mime="text/markdown",
        )

    with col2:
        # Export filtered log as CSV
        csv_data = df.to_csv(index=False)
        st.download_button(
            label="Unduh Log Terfilter (CSV)",
            data=csv_data,
            file_name="log_kejadian_terfilter.csv",
            mime="text/csv",
        )

    with col3:
        # Export as JSON
        json_data = df.to_json(orient="records", date_format="iso", indent=2)
        st.download_button(
            label="Unduh Log Terfilter (JSON)",
            data=json_data,
            file_name="log_kejadian_terfilter.json",
            mime="application/json",
        )

    with col4:
        # Export as Excel (if available)
        try:
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Event_Log', index=False)
                
                # Also add statistics sheets
                from core.statistics import calculate_activity_statistics, calculate_resource_statistics, calculate_case_duration_distribution
                from core.variants import calculate_variants
                
                activity_stats = calculate_activity_statistics(df)
                resource_stats = calculate_resource_statistics(df)
                case_durations = calculate_case_duration_distribution(df)
                variants = calculate_variants(df)
                
                activity_stats.to_excel(writer, sheet_name='Activity_Stats', index=False)
                resource_stats.to_excel(writer, sheet_name='Resource_Stats', index=False)
                case_durations.to_excel(writer, sheet_name='Case_Durations', index=False)
                # Truncate long cells in variants dataframe to avoid Excel cell limit (32767 chars)
                variants_truncated = _truncate_long_cells_for_excel(variants.copy())
                variants_truncated.to_excel(writer, sheet_name='Variants', index=False)
            
            excel_data = buffer.getvalue()
            st.download_button(
                label="Unduh Log Terfilter (Excel)",
                data=excel_data,
                file_name="log_kejadian_terfilter.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        except ImportError:
            st.info("Install openpyxl untuk dukungan export Excel: `pip install openpyxl`")