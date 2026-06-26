"""Generate summary reports from analysis results.

Collects key metrics and prepares data structures
for the report page.
"""

from __future__ import annotations

import pandas as pd

from core.dfg import calculate_transition_performance
from core.statistics import (
    calculate_activity_statistics,
    calculate_case_duration_distribution,
    calculate_global_statistics,
    seconds_to_readable,
)
from core.variants import calculate_variants


def generate_markdown_report(
    df: pd.DataFrame,
    validation_result: dict | None = None,
) -> str:
    """Build a complete Markdown process-mining report.

    Parameters
    ----------
    df : pd.DataFrame
        Prepared event log with ``case_id``, ``activity``,
        ``timestamp``, and ``resource`` columns.
    validation_result : dict or None, optional
        Output of :func:`core.validate_log.validate_event_log`.
        When provided the validation section is included.

    Returns
    -------
    str
        A Markdown-formatted report.
    """
    lines: list[str] = []
    _add = lines.append

    _add("# Laporan Process Mining")
    _add("")

    # ------------------------------------------------------------------
    # 1. Ringkasan Dataset
    # ------------------------------------------------------------------
    gs = calculate_global_statistics(df)

    _add("## 1. Ringkasan Dataset")
    _add("")
    _add(f"- **Total kejadian:** {gs['total_events']}")
    _add(f"- **Total kasus:** {gs['total_cases']}")
    _add(f"- **Total aktivitas:** {gs['total_activities']}")
    _add(f"- **Total sumber daya:** {gs['total_resources']}")
    if pd.notna(gs["start_time"]) and pd.notna(gs["end_time"]):
        _add(f"- **Rentang waktu:** {gs['start_time']} -> {gs['end_time']}")
    _add("")

    # ------------------------------------------------------------------
    # 2. Ringkasan Validasi
    # ------------------------------------------------------------------
    if validation_result is not None:
        _add("## 2. Ringkasan Validasi")
        _add("")
        status = "Valid" if validation_result.get("is_valid") else "Tidak Valid"
        _add(f"- **Status:** {status}")
        _add(f"- **ID kasus kosong:** {validation_result.get('missing_case_id', 0)}")
        _add(f"- **Aktivitas kosong:** {validation_result.get('missing_activity', 0)}")
        _add(f"- **Waktu kejadian kosong:** {validation_result.get('missing_timestamp', 0)}")
        _add(f"- **Baris duplikat:** {validation_result.get('duplicate_rows', 0)}")
        _add(f"- **Kasus dengan satu kejadian:** {validation_result.get('single_event_cases', 0)}")

        warnings = validation_result.get("warnings", [])
        if warnings:
            _add("")
            _add("**Peringatan:**")
            for w in warnings:
                _add(f"- {w}")
        _add("")

    # ------------------------------------------------------------------
    # 3. Aktivitas Teratas
    # ------------------------------------------------------------------
    act_stats = calculate_activity_statistics(df).head(10)

    _add("## 3. Aktivitas Teratas")
    _add("")
    _add("| # | Aktivitas | Frekuensi | Kasus | % Kejadian |")
    _add("|---|---|---|---|---|")
    for i, row in act_stats.iterrows():
        _add(
            f"| {i + 1} | {row['activity']} | {row['frequency']} "
            f"| {row['case_frequency']} | {row['percentage_events']}% |"
        )
    _add("")

    # ------------------------------------------------------------------
    # 4. Varian Teratas
    # ------------------------------------------------------------------
    variants = calculate_variants(df).head(10)

    _add("## 4. Varian Teratas")
    _add("")
    _add("| # | Varian | Kasus | % | Durasi Rata-rata |")
    _add("|---|---|---|---|---|")
    for _, row in variants.iterrows():
        dur = seconds_to_readable(row["avg_duration_seconds"])
        seq = row["sequence"]
        if len(seq) > 80:
            seq = seq[:77] + "..."
        _add(
            f"| {row['variant_id']} | {seq} | {row['case_count']} "
            f"| {row['percentage']}% | {dur} |"
        )
    _add("")

    # ------------------------------------------------------------------
    # 5. Kasus Paling Lambat
    # ------------------------------------------------------------------
    case_dist = calculate_case_duration_distribution(df)
    slowest = case_dist.sort_values("duration_seconds", ascending=False).head(10)

    _add("## 5. Kasus Paling Lambat")
    _add("")
    _add("| # | ID Kasus | Durasi | Kejadian |")
    _add("|---|---|---|---|")
    for i, (_, row) in enumerate(slowest.iterrows(), 1):
        dur = seconds_to_readable(row["duration_seconds"])
        _add(f"| {i} | {row['case_id']} | {dur} | {int(row['event_count'])} |")
    _add("")

    # ------------------------------------------------------------------
    # 6. Transisi Bottleneck
    # ------------------------------------------------------------------
    perf = calculate_transition_performance(df).head(10)

    _add("## 6. Transisi Bottleneck")
    _add("")
    _add("| # | Transisi | Frek | Tunggu Rata-rata | Tunggu Median | Tunggu Maks |")
    _add("|---|---|---|---|---|---|")
    for i, (_, row) in enumerate(perf.iterrows(), 1):
        _add(
            f"| {i} | {row['source']} -> {row['target']} | {row['frequency']} "
            f"| {seconds_to_readable(row['mean_waiting_seconds'])} "
            f"| {seconds_to_readable(row['median_waiting_seconds'])} "
            f"| {seconds_to_readable(row['max_waiting_seconds'])} |"
        )
    _add("")

    # ------------------------------------------------------------------
    # 7. Petunjuk Interpretasi
    # ------------------------------------------------------------------
    _add("## 7. Petunjuk Interpretasi")
    _add("")
    _add("- **Frekuensi aktivitas yang tinggi** dapat menunjukkan langkah penting "
          "atau langkah yang sering diulang dalam proses.")
    _add("- **Aktivitas yang berulang** (misalnya Persetujuan -> Revisi -> Persetujuan) "
          "dapat menunjukkan adanya pengerjaan ulang.")
    _add("- **Waktu tunggu yang panjang** antara dua aktivitas dapat menunjukkan "
          "bottleneck atau keterbatasan sumber daya.")
    _add("- **Jumlah varian yang banyak** dapat menunjukkan variasi proses yang tinggi, "
          "yang mengindikasikan kurangnya standarisasi.")
    _add("- **Jumlah varian yang sedikit** dengan jumlah kasus tinggi menunjukkan proses "
          "yang terstruktur dan terstandarisasi dengan baik.")
    _add("")

    return "\n".join(lines)
