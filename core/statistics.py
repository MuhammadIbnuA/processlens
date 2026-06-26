"""Descriptive statistics for event logs and cases.

Case durations, activity frequencies, throughput times,
and other summary metrics.
"""

from __future__ import annotations

import math

import streamlit as st
import pandas as pd

from core.transform_log import compute_case_durations

@st.cache_data(ttl=3600)  # Cache for 1 hour
def calculate_global_statistics(df: pd.DataFrame) -> dict:
    """Compute high-level statistics for the entire event log.

    Parameters
    ----------
    df : pd.DataFrame
        Prepared event log with ``case_id``, ``activity``,
        ``timestamp``, and ``resource`` columns.

    Returns
    -------
    dict
        Keys:

        * ``total_events``
        * ``total_cases``
        * ``total_activities``
        * ``total_resources``
        * ``total_variants`` – unique activity sequences across cases
        * ``avg_case_duration_seconds``
        * ``median_case_duration_seconds``
        * ``min_case_duration_seconds``
        * ``max_case_duration_seconds``
        * ``start_time`` – earliest timestamp
        * ``end_time`` – latest timestamp
    """
    dur = compute_case_durations(df)
    case_durations = dur["duration_seconds"]

    variants = (
        df.groupby("case_id")["activity"]
        .apply(lambda s: " -> ".join(s), include_groups=False)
        .nunique()
    )

    return {
        "total_events": len(df),
        "total_cases": df["case_id"].nunique(),
        "total_activities": df["activity"].nunique(),
        "total_resources": df["resource"].nunique(),
        "total_variants": variants,
        "avg_case_duration_seconds": case_durations.mean(),
        "median_case_duration_seconds": case_durations.median(),
        "min_case_duration_seconds": case_durations.min(),
        "max_case_duration_seconds": case_durations.max(),
        "start_time": df["timestamp"].min(),
        "end_time": df["timestamp"].max(),
    }

@st.cache_data(ttl=3600)  # Cache for 1 hour
def calculate_events_over_time(
    df: pd.DataFrame, freq: str = "D"
) -> pd.DataFrame:
    """Count events per time period.

    Parameters
    ----------
    df : pd.DataFrame
        Prepared event log with a ``timestamp`` column.
    freq : str, optional
        Pandas offset alias (``"D"`` for daily, ``"W"`` for weekly,
        ``"h"`` for hourly, etc.).  Default ``"D"``.

    Returns
    -------
    pd.DataFrame
        Columns ``period`` and ``event_count``, sorted by period.
    """
    ts = df.set_index("timestamp")
    counts = ts.groupby(pd.Grouper(freq=freq)).size().reset_index(name="event_count")
    counts = counts.rename(columns={"timestamp": "period"})
    return counts.sort_values("period").reset_index(drop=True)

def _entity_statistics(df: pd.DataFrame, entity_col: str) -> pd.DataFrame:
    """Per-entity descriptive statistics (activity or resource).

    Parameters
    ----------
    df : pd.DataFrame
        Prepared event log.
    entity_col : str
        Column to group by (e.g. ``"activity"`` or ``"resource"``).

    Returns
    -------
    pd.DataFrame
        Columns named after *entity_col*, ``frequency``,
        ``case_frequency``, and ``percentage_events``.
        Sorted descending by frequency.
    """
    total_events = len(df)

    freq = df.groupby(entity_col).agg(
        frequency=("case_id", "size"),
        case_frequency=("case_id", "nunique"),
    ).reset_index()

    freq["percentage_events"] = (freq["frequency"] / total_events * 100).round(2)

    return freq.sort_values("frequency", ascending=False).reset_index(drop=True)

@st.cache_data(ttl=3600)  # Cache for 1 hour
def calculate_activity_statistics(df: pd.DataFrame) -> pd.DataFrame:
    """Per-activity descriptive statistics.

    Parameters
    ----------
    df : pd.DataFrame
        Prepared event log.

    Returns
    -------
    pd.DataFrame
        Columns:

        * ``activity``
        * ``frequency`` – total occurrences
        * ``case_frequency`` – number of distinct cases the activity
          appears in
        * ``percentage_events`` – share of all events (0-100)

        Sorted descending by frequency.
    """
    return _entity_statistics(df, "activity")

@st.cache_data(ttl=3600)  # Cache for 1 hour
def calculate_resource_statistics(df: pd.DataFrame) -> pd.DataFrame:
    """Per-resource descriptive statistics.

    Parameters
    ----------
    df : pd.DataFrame
        Prepared event log.

    Returns
    -------
    pd.DataFrame
        Columns:

        * ``resource``
        * ``frequency`` – total events performed
        * ``case_frequency`` – number of distinct cases touched
        * ``percentage_events`` – share of all events (0-100)

        Sorted descending by frequency.
    """
    return _entity_statistics(df, "resource")

@st.cache_data(ttl=3600)  # Cache for 1 hour
def calculate_case_duration_distribution(df: pd.DataFrame) -> pd.DataFrame:
    """Compute duration and event count for every case.

    Parameters
    ----------
    df : pd.DataFrame
        Prepared event log.

    Returns
    -------
    pd.DataFrame
        Columns:

        * ``case_id``
        * ``duration_seconds``
        * ``duration_hours``
        * ``duration_days``
        * ``event_count``

        Sorted by ``case_id``.
    """
    dur = compute_case_durations(df)
    count = df.groupby("case_id")["timestamp"].size()

    result = pd.DataFrame({
        "case_id": dur.index,
        "duration_seconds": dur["duration_seconds"].values,
        "duration_hours": (dur["duration_seconds"] / 3600).values,
        "duration_days": (dur["duration_seconds"] / 86400).values,
        "event_count": count.values,
    })

    return result.sort_values("case_id").reset_index(drop=True)

def seconds_to_readable(seconds: float) -> str:
    """Convert a duration in seconds to a human-readable string.

    Chooses the largest practical unit:

    * >= 86 400 s  -> days
    * >= 3 600 s   -> hours
    * >= 60 s      -> minutes
    * otherwise    -> seconds

    Parameters
    ----------
    seconds : float
        Duration in seconds.

    Returns
    -------
    str
        e.g. ``"2.5 days"``, ``"1.0 hours"``, ``"45.0 minutes"``
    """
    if seconds is None or math.isnan(seconds):
        return "N/A"
    if seconds >= 86_400:
        return f"{seconds / 86400:.1f} days"
    if seconds >= 3_600:
        return f"{seconds / 3600:.1f} hours"
    if seconds >= 60:
        return f"{seconds / 60:.1f} minutes"
    return f"{seconds:.1f} seconds"
