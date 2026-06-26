"""Validate that an imported DataFrame is a well-formed event log.

Checks for required columns (case ID, activity, timestamp),
data types, missing values, and basic sanity rules.
"""

from __future__ import annotations

import pandas as pd


def validate_event_log(df: pd.DataFrame) -> dict:
    """Validate an event-log DataFrame against the internal schema.

    The DataFrame must already contain the standard columns
    ``case_id``, ``activity``, ``timestamp``, and ``resource``
    (as produced by :func:`core.import_log.map_event_log_columns`).

    Parameters
    ----------
    df : pd.DataFrame
        The mapped event-log DataFrame.

    Returns
    -------
    dict
        A dictionary with the following keys:

        * ``total_events`` – number of rows
        * ``total_cases`` – unique ``case_id`` values
        * ``total_activities`` – unique ``activity`` values
        * ``total_resources`` – unique ``resource`` values
        * ``missing_case_id`` – rows where ``case_id`` is NA
        * ``missing_activity`` – rows where ``activity`` is NA
        * ``missing_timestamp`` – rows where ``timestamp`` is NaT
        * ``duplicate_rows`` – exact duplicate rows
        * ``single_event_cases`` – cases with only one event
        * ``start_time`` – earliest timestamp (or ``None``)
        * ``end_time`` – latest timestamp (or ``None``)
        * ``is_valid`` – ``True`` when the log passes all hard rules
        * ``warnings`` – list of human-readable warning strings
    """
    result: dict = {}

    result["total_events"] = len(df)
    result["total_cases"] = df["case_id"].nunique() if len(df) > 0 else 0
    result["total_activities"] = df["activity"].nunique() if len(df) > 0 else 0
    result["total_resources"] = df["resource"].nunique() if len(df) > 0 else 0

    result["missing_case_id"] = int(df["case_id"].isna().sum())
    result["missing_activity"] = int(df["activity"].isna().sum())
    result["missing_timestamp"] = int(df["timestamp"].isna().sum())

    result["duplicate_rows"] = int(df.duplicated().sum())

    if len(df) > 0:
        case_sizes = df.groupby("case_id").size()
        result["single_event_cases"] = int((case_sizes == 1).sum())
    else:
        result["single_event_cases"] = 0

    valid_ts = df["timestamp"].dropna()
    result["start_time"] = valid_ts.min() if len(valid_ts) > 0 else None
    result["end_time"] = valid_ts.max() if len(valid_ts) > 0 else None

    # Build warnings
    warnings: list[str] = []

    if result["duplicate_rows"] > 0:
        warnings.append(
            f"Ditemukan {result['duplicate_rows']} baris duplikat. "
            "Pertimbangkan untuk menghapusnya agar statistik tidak terpengaruh."
        )

    if result["single_event_cases"] > 0:
        warnings.append(
            f"{result['single_event_cases']} kasus hanya memiliki satu kejadian. "
            "Kasus-kasus ini tidak dapat membentuk transisi aktivitas."
        )

    if result["total_activities"] < 2:
        warnings.append(
            "Log hanya memiliki kurang dari 2 aktivitas berbeda. "
            "Process mining memerlukan minimal 2 aktivitas agar bermakna."
        )

    if result["missing_timestamp"] > 0 and result["total_events"] > 0:
        warnings.append(
            f"{result['missing_timestamp']} baris memiliki waktu kejadian yang tidak dapat dibaca "
            "dan akan dikecualikan dari analisis berbasis waktu."
        )

    result["warnings"] = warnings

    # Hard validity rules
    is_valid = (
        result["missing_case_id"] == 0
        and result["missing_activity"] == 0
        and result["missing_timestamp"] == 0
        and result["total_events"] > 0
        and result["total_cases"] > 0
    )
    result["is_valid"] = is_valid

    return result


def format_validation_summary(validation_result: dict) -> str:
    """Format a validation result as a readable Markdown string.

    Parameters
    ----------
    validation_result : dict
        A dictionary returned by :func:`validate_event_log`.

    Returns
    -------
    str
        A Markdown-formatted summary suitable for reports.
    """
    v = validation_result
    status = "Valid" if v["is_valid"] else "Tidak Valid"

    lines = [
        "## Ringkasan Validasi Log Kejadian",
        "",
        f"**Status:** {status}",
        "",
        "### Jumlah",
        "",
        f"| Metrik | Nilai |",
        f"|---|---|",
        f"| Total kejadian | {v['total_events']} |",
        f"| Total kasus | {v['total_cases']} |",
        f"| Aktivitas berbeda | {v['total_activities']} |",
        f"| Sumber daya berbeda | {v['total_resources']} |",
        "",
        "### Kualitas Data",
        "",
        f"| Masalah | Jumlah |",
        f"|---|---|",
        f"| ID kasus kosong | {v['missing_case_id']} |",
        f"| Aktivitas kosong | {v['missing_activity']} |",
        f"| Waktu kejadian kosong | {v['missing_timestamp']} |",
        f"| Baris duplikat | {v['duplicate_rows']} |",
        f"| Kasus dengan satu kejadian | {v['single_event_cases']} |",
    ]

    if v["start_time"] is not None and v["end_time"] is not None:
        lines += [
            "",
            f"**Rentang waktu:** {v['start_time']} -> {v['end_time']}",
        ]

    if v["warnings"]:
        lines += ["", "### Peringatan", ""]
        for w in v["warnings"]:
            lines.append(f"- {w}")

    return "\n".join(lines)
