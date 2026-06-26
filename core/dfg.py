"""Build a Directly-Follows Graph (DFG) from an event log.

Computes activity-to-activity transition frequencies and
returns edge lists suitable for visualization with NetworkX / Plotly.
"""

from __future__ import annotations

import streamlit as st
import pandas as pd

@st.cache_data(ttl=3600)  # Cache for 1 hour
def calculate_activity_frequency(df: pd.DataFrame) -> pd.DataFrame:
    """Count how often each activity appears in the log.

    Parameters
    ----------
    df : pd.DataFrame
        Prepared event log containing an ``activity`` column.

    Returns
    -------
    pd.DataFrame
        Columns ``activity`` (str) and ``frequency`` (int),
        sorted descending by frequency.
    """
    freq = df["activity"].value_counts().reset_index()
    freq.columns = ["activity", "frequency"]
    return freq.sort_values("frequency", ascending=False).reset_index(drop=True)

def _boundary_activities(df: pd.DataFrame, which: str) -> pd.DataFrame:
    """Return frequency table for the first or last activity per case.

    Parameters
    ----------
    df : pd.DataFrame
        Prepared event log sorted by ``case_id`` and ``timestamp``.
    which : str
        ``"first"`` or ``"last"``.

    Returns
    -------
    pd.DataFrame
        Columns ``activity`` and ``frequency``, sorted descending.
    """
    if which == "first":
        boundary = df.groupby("case_id")["activity"].first()
    else:
        boundary = df.groupby("case_id")["activity"].last()
    freq = boundary.value_counts().reset_index()
    freq.columns = ["activity", "frequency"]
    return freq.sort_values("frequency", ascending=False).reset_index(drop=True)

@st.cache_data(ttl=3600)  # Cache for 1 hour
def calculate_start_activities(df: pd.DataFrame) -> pd.DataFrame:
    """Identify the first activity of each case.

    Parameters
    ----------
    df : pd.DataFrame
        Prepared event log (must be sorted by ``case_id``, ``timestamp``).

    Returns
    -------
    pd.DataFrame
        Columns ``activity`` and ``frequency``, sorted descending.
    """
    return _boundary_activities(df, "first")

@st.cache_data(ttl=3600)  # Cache for 1 hour
def calculate_end_activities(df: pd.DataFrame) -> pd.DataFrame:
    """Identify the last activity of each case.

    Parameters
    ----------
    df : pd.DataFrame
        Prepared event log (must be sorted by ``case_id``, ``timestamp``).

    Returns
    -------
    pd.DataFrame
        Columns ``activity`` and ``frequency``, sorted descending.
    """
    return _boundary_activities(df, "last")

@st.cache_data(ttl=3600)  # Cache for 1 hour
def calculate_transition_frequency(df: pd.DataFrame) -> pd.DataFrame:
    """Compute direct-follow transition frequencies.

    For every pair of consecutive events within the same case a
    transition ``source -> target`` is recorded.

    Parameters
    ----------
    df : pd.DataFrame
        Prepared event log sorted by ``case_id`` and ``timestamp``.

    Returns
    -------
    pd.DataFrame
        Columns ``source``, ``target``, and ``frequency``,
        sorted descending by frequency.
    """
    shifted = df.groupby("case_id")["activity"].shift(-1)
    pairs = pd.DataFrame({"source": df["activity"], "target": shifted})
    pairs = pairs.dropna(subset=["target"])

    freq = (
        pairs.groupby(["source", "target"])
        .size()
        .reset_index(name="frequency")
    )
    return freq.sort_values("frequency", ascending=False).reset_index(drop=True)

@st.cache_data(ttl=3600)  # Cache for 1 hour
def calculate_transition_performance(df: pd.DataFrame) -> pd.DataFrame:
    """Compute waiting-time statistics for each direct-follow transition.

    Waiting time is defined as ``target_timestamp - source_timestamp``
    for every consecutive event pair within the same case.

    Parameters
    ----------
    df : pd.DataFrame
        Prepared event log sorted by ``case_id`` and ``timestamp``.

    Returns
    -------
    pd.DataFrame
        Columns:

        * ``source`` – source activity name
        * ``target`` – target activity name
        * ``frequency`` – number of observed transitions
        * ``mean_waiting_seconds`` – mean waiting time in seconds
        * ``median_waiting_seconds`` – median waiting time in seconds
        * ``min_waiting_seconds`` – minimum waiting time in seconds
        * ``max_waiting_seconds`` – maximum waiting time in seconds

        Sorted descending by frequency.
    """
    shifted_ts = df.groupby("case_id")["timestamp"].shift(-1)
    shifted_act = df.groupby("case_id")["activity"].shift(-1)

    pairs = pd.DataFrame({
        "source": df["activity"],
        "target": shifted_act,
        "source_ts": df["timestamp"],
        "target_ts": shifted_ts,
    })
    pairs = pairs.dropna(subset=["target", "target_ts"])

    pairs["waiting_seconds"] = (pairs["target_ts"] - pairs["source_ts"]).dt.total_seconds()

    agg = (
        pairs.groupby(["source", "target"])["waiting_seconds"]
        .agg(
            frequency="size",
            mean_waiting_seconds="mean",
            median_waiting_seconds="median",
            min_waiting_seconds="min",
            max_waiting_seconds="max",
        )
        .reset_index()
    )

    return agg.sort_values("frequency", ascending=False).reset_index(drop=True)

def filter_dfg(
    activity_freq: pd.DataFrame,
    transition_freq: pd.DataFrame,
    min_activity_freq: int = 1,
    min_transition_freq: int = 1,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Filter DFG data by minimum frequency thresholds.

    Activities below ``min_activity_freq`` are removed from the
    activity table **and** from both sides of the transition table.

    Transitions below ``min_transition_freq`` are removed from the
    transition table.

    Parameters
    ----------
    activity_freq : pd.DataFrame
        Output of :func:`calculate_activity_frequency`.
    transition_freq : pd.DataFrame
        Output of :func:`calculate_transition_frequency`.
    min_activity_freq : int, optional
        Minimum activity frequency to keep (default 1).
    min_transition_freq : int, optional
        Minimum transition frequency to keep (default 1).

    Returns
    -------
    tuple[pd.DataFrame, pd.DataFrame]
        ``(filtered_activity_freq, filtered_transition_freq)``
    """
    kept_activities = activity_freq[
        activity_freq["frequency"] >= min_activity_freq
    ]["activity"]

    filtered_transitions = transition_freq[
        (transition_freq["source"].isin(kept_activities))
        & (transition_freq["target"].isin(kept_activities))
        & (transition_freq["frequency"] >= min_transition_freq)
    ]

    filtered_activities = activity_freq[
        activity_freq["activity"].isin(
            set(filtered_transitions["source"]) | set(filtered_transitions["target"])
        )
    ]

    return (
        filtered_activities.reset_index(drop=True),
        filtered_transitions.reset_index(drop=True),
    )
