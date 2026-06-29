"""Transform and enrich the event log DataFrame.

Sorting by timestamp, computing elapsed time between events,
and adding derived columns used by downstream modules.
"""

from __future__ import annotations

import pandas as pd

def prepare_event_log(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and normalise a mapped event-log DataFrame.

    Steps performed:

    1. Copy the input (never mutates the original).
    2. Drop rows where ``case_id``, ``activity``, or ``timestamp`` is missing.
    3. Cast ``case_id``, ``activity``, and ``resource`` to ``str``.
    4. Parse ``timestamp`` with ``pd.to_datetime(errors="coerce")``.
    5. Sort by ``case_id`` then ``timestamp``.
    6. Reset the index.

    Parameters
    ----------
    df : pd.DataFrame
        A DataFrame that already contains ``case_id``, ``activity``,
        ``timestamp``, and ``resource`` columns.

    Returns
    -------
    pd.DataFrame
        The cleaned copy.
    """
    out = df.copy()

    out = out.dropna(subset=["case_id", "activity", "timestamp"])

    out["case_id"] = out["case_id"].astype(str)
    out["activity"] = out["activity"].astype(str)
    out["resource"] = out["resource"].astype(str)

    # Parse timestamps with robust format detection to avoid pandas warnings
    # Use the same robust parser as in import_log to maintain consistency
    from core.import_log import _robust_parse_timestamps
    out["timestamp"] = _robust_parse_timestamps(out["timestamp"])

    out = out.sort_values(["case_id", "timestamp"]).reset_index(drop=True)

    return out

def compute_case_durations(df: pd.DataFrame) -> pd.DataFrame:
    """Compute start, end, and duration for every case.

    Parameters
    ----------
    df : pd.DataFrame
        Prepared event log sorted by ``case_id`` and ``timestamp``.

    Returns
    -------
    pd.DataFrame
        Index: ``case_id``.  Columns: ``start_time``, ``end_time``,
        ``duration_seconds``.
    """
    if len(df) == 0:
        # Return empty DataFrame with correct structure
        return pd.DataFrame(
            columns=["start_time", "end_time", "duration_seconds"],
            dtype='object'
        ).set_index(pd.Index([], name='case_id'))
    
    grouped = df.groupby("case_id")["timestamp"]
    start = grouped.min()
    end = grouped.max()
    
    # Handle empty series case
    if len(start) == 0:
        return pd.DataFrame(
            columns=["start_time", "end_time", "duration_seconds"],
            dtype='object'
        ).set_index(pd.Index([], name='case_id'))
    
    duration_seconds = (end - start).dt.total_seconds()
    
    return pd.DataFrame({
        "start_time": start,
        "end_time": end,
        "duration_seconds": duration_seconds,
    })

def get_case_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Build one summary row per case.

    Parameters
    ----------
    df : pd.DataFrame
        A prepared event log (output of :func:`prepare_event_log`).

    Returns
    -------
    pd.DataFrame
        Columns:

        * ``case_id``
        * ``start_time`` – earliest timestamp in the case
        * ``end_time`` – latest timestamp in the case
        * ``event_count`` – number of events in the case
        * ``duration`` – ``end_time - start_time`` as a ``Timedelta``
        * ``duration_seconds`` – duration in seconds (``float``)
        * ``variant_sequence`` – activities joined by ``" -> "``
    """
    if len(df) == 0:
        return pd.DataFrame(columns=[
            "case_id", "start_time", "end_time", "event_count", 
            "duration", "duration_seconds", "variant_sequence"
        ])
    
    grouped = df.groupby("case_id", sort=True)

    summary = grouped.agg(
        start_time=("timestamp", "min"),
        end_time=("timestamp", "max"),
        event_count=("timestamp", "size"),
    )

    # Calculate duration as timedelta
    summary["duration"] = summary["end_time"] - summary["start_time"]
    summary["duration_seconds"] = summary["duration"].dt.total_seconds()

    def _sequence(group: pd.DataFrame) -> str:
        return " -> ".join(group["activity"].tolist())

    variant_seq = grouped.apply(_sequence, include_groups=False)
    summary["variant_sequence"] = variant_seq

    summary = summary.reset_index()[
        [
            "case_id",
            "start_time",
            "end_time",
            "event_count",
            "duration",
            "duration_seconds",
            "variant_sequence",
        ]
    ]

    return summary

def get_activity_sequences(df: pd.DataFrame) -> dict[str, list[str]]:
    """Return ordered activity sequences keyed by case ID.

    Parameters
    ----------
    df : pd.DataFrame
        A prepared event log.

    Returns
    -------
    dict[str, list[str]]
        ``{case_id: [activity1, activity2, ...]}``
    """
    sequences: dict[str, list[str]] = {}
    for case_id, group in df.groupby("case_id", sort=True):
        sequences[case_id] = group["activity"].tolist()
    return sequences

def add_case_duration_to_events(df: pd.DataFrame) -> pd.DataFrame:
    """Annotate every event with its case's timing information.

    Adds three columns:

    * ``case_start_time`` – earliest timestamp in the event's case
    * ``case_end_time`` – latest timestamp in the event's case
    * ``case_duration_seconds`` – (``case_end_time - case_start_time``) in seconds

    Parameters
    ----------
    df : pd.DataFrame
        A prepared event log.

    Returns
    -------
    pd.DataFrame
        A copy of the input with the three new columns appended.
    """
    if len(df) == 0:
        out = df.copy()
        out["case_start_time"] = pd.Series([], dtype='object', index=out.index)
        out["case_end_time"] = pd.Series([], dtype='object', index=out.index)
        out["case_duration_seconds"] = pd.Series([], dtype='float64', index=out.index)
        return out

    out = df.copy()

    grouped = out.groupby("case_id")["timestamp"]

    out["case_start_time"] = grouped.transform("min")
    out["case_end_time"] = grouped.transform("max")
    out["case_duration_seconds"] = (
        (out["case_end_time"] - out["case_start_time"]).dt.total_seconds()
    )

    return out