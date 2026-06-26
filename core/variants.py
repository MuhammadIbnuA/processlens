"""Detect and rank process variants.

A variant is a unique sequence of activities.  This module groups
cases by their activity sequence and computes variant frequencies.
"""

from __future__ import annotations

import streamlit as st
import pandas as pd

from core.transform_log import compute_case_durations

@st.cache_data(ttl=3600)  # Cache for 1 hour
def calculate_variants(df: pd.DataFrame) -> pd.DataFrame:
    """Identify all process variants and rank them by frequency.

    A *variant* is a unique ordered sequence of activities observed
    across one or more cases.

    Parameters
    ----------
    df : pd.DataFrame
        Prepared event log with ``case_id``, ``activity``, and
        ``timestamp`` columns.  Must be sorted by ``case_id`` and
        ``timestamp``.

    Returns
    -------
    pd.DataFrame
        Columns:

        * ``variant_id`` – short identifier (``V1``, ``V2``, …)
        * ``sequence`` – activities joined by ``" -> "``
        * ``case_count`` – number of cases with this variant
        * ``percentage`` – share of all cases (0-100)
        * ``avg_duration_seconds`` – mean case duration in seconds
        * ``median_duration_seconds`` – median case duration in seconds
        * ``case_ids`` – list of ``case_id`` values

        Sorted descending by ``case_count``.
    """
    # Build per-case info: sequence, duration, case_id
    grouped = df.groupby("case_id")

    sequences = grouped["activity"].apply(
        lambda s: " -> ".join(s), include_groups=False
    )
    dur = compute_case_durations(df)
    durations = dur["duration_seconds"]

    case_info = pd.DataFrame({
        "case_id": sequences.index,
        "sequence": sequences.values,
        "duration_seconds": durations.values,
    })

    # Group by variant sequence
    variant_groups = case_info.groupby("sequence", sort=False)

    total_cases = len(case_info)

    variants = variant_groups.agg(
        case_count=("case_id", "size"),
        avg_duration_seconds=("duration_seconds", "mean"),
        median_duration_seconds=("duration_seconds", "median"),
        case_ids=("case_id", list),
    ).reset_index()

    variants["percentage"] = (variants["case_count"] / total_cases * 100).round(2)

    variants = variants.sort_values("case_count", ascending=False).reset_index(drop=True)

    variants["variant_id"] = ["V" + str(i + 1) for i in range(len(variants))]

    return variants[[
        "variant_id",
        "sequence",
        "case_count",
        "percentage",
        "avg_duration_seconds",
        "median_duration_seconds",
        "case_ids",
    ]]

def get_cases_for_variant(variants_df: pd.DataFrame, variant_id: str) -> list[str]:
    """Return the case IDs belonging to a specific variant.

    Parameters
    ----------
    variants_df : pd.DataFrame
        Output of :func:`calculate_variants`.
    variant_id : str
        The variant to look up (e.g. ``"V1"``).

    Returns
    -------
    list[str]
        List of case ID strings.

    Raises
    ------
    KeyError
        If *variant_id* is not found.
    """
    match = variants_df.loc[variants_df["variant_id"] == variant_id]
    if match.empty:
        raise KeyError(f"Variant '{variant_id}' not found.")
    return match.iloc[0]["case_ids"]

def get_case_variant(df: pd.DataFrame, case_id: str) -> str:
    """Return the activity sequence for a single case.

    Parameters
    ----------
    df : pd.DataFrame
        Prepared event log sorted by ``case_id`` and ``timestamp``.
    case_id : str
        The case to inspect.

    Returns
    -------
    str
        Activities joined by ``" -> "``.

    Raises
    ------
    KeyError
        If *case_id* is not found in the DataFrame.
    """
    case = df.loc[df["case_id"] == case_id]
    if case.empty:
        raise KeyError(f"Case '{case_id}' not found.")
    return " -> ".join(case["activity"].tolist())
