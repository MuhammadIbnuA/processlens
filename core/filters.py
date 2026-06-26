"""Filtering utilities for event logs.

Filter by case attributes, activity names, time ranges,
or variant membership.
"""

from __future__ import annotations

import pandas as pd

from core.transform_log import compute_case_durations
from core.variants import calculate_variants


def apply_filters(df: pd.DataFrame, filters: dict) -> pd.DataFrame:
    """Apply a chain of filters in a fixed order.

    Order: date range -> activity -> case duration -> top variants.
    
    This maintains the original behavior where each filter is applied
    sequentially to the result of the previous filter.

    Parameters
    ----------
    df : pd.DataFrame
        Prepared event log.
    filters : dict
        Any combination of:
        * ``start_date`` – lower timestamp bound
        * ``end_date`` – upper timestamp bound
        * ``activities`` – list of activity names
        * ``min_duration_seconds`` – minimum case duration
        * ``max_duration_seconds`` – maximum case duration
        * ``top_n_variants`` – number of top variants to keep

    Returns
    -------
    pd.DataFrame
        Filtered copy (index reset).
    """
    out = df.copy()

    # Apply date range filter
    start_date = filters.get("start_date")
    end_date = filters.get("end_date")
    if start_date is not None or end_date is not None:
        out = filter_by_date_range(
            out,
            start_date=start_date,
            end_date=end_date,
        )

    # Apply activity filter
    activities = filters.get("activities")
    if activities:
        out = filter_cases_containing_activity(out, activities=activities)

    # Apply duration filter
    min_seconds = filters.get("min_duration_seconds")
    max_seconds = filters.get("max_duration_seconds")
    if min_seconds is not None or max_seconds is not None:
        out = filter_by_case_duration(
            out,
            min_seconds=min_seconds,
            max_seconds=max_seconds,
        )

    # Apply top variants filter
    top_n = filters.get("top_n_variants")
    if top_n is not None:
        # Calculate variants on the original dataframe to maintain original semantics
        all_variants = calculate_variants(df)
        top = all_variants.head(top_n)
        matching_cases = [cid for ids in top["case_ids"] for cid in ids]
        out = out[out["case_id"].isin(matching_cases)].reset_index(drop=True)
    else:
        out = out.reset_index(drop=True)

    return out


def filter_by_date_range(
    df: pd.DataFrame,
    start_date: str | pd.Timestamp | None = None,
    end_date: str | pd.Timestamp | None = None,
) -> pd.DataFrame:
    """Keep events whose timestamp falls within the given range.

    Parameters
    ----------
    df : pd.DataFrame
        Prepared event log with a ``timestamp`` column.
    start_date : str, pd.Timestamp, or None
        Inclusive lower bound.  ``None`` means no lower bound.
    end_date : str, pd.Timestamp, or None
        Inclusive upper bound.  ``None`` means no upper bound.

    Returns
    -------
    pd.DataFrame
        Filtered copy (index reset).
    """
    out = df.copy()
    if start_date is not None:
        start = pd.to_datetime(start_date)
        out = out[out["timestamp"] >= start]
    if end_date is not None:
        end = pd.to_datetime(end_date)
        out = out[out["timestamp"] <= end]
    return out.reset_index(drop=True)


def filter_cases_containing_activity(
    df: pd.DataFrame,
    activities: list[str] | None = None,
) -> pd.DataFrame:
    """Keep complete cases that contain at least one of the given activities.

    Parameters
    ----------
    df : pd.DataFrame
        Prepared event log.
    activities : list[str] or None
        Activity names to match.  ``None`` or empty list returns the
        input unchanged.

    Returns
    -------
    pd.DataFrame
        All rows belonging to matching cases (index reset).
    """
    if not activities:
        return df.copy()

    matching_cases = df.loc[
        df["activity"].isin(activities), "case_id"
    ].unique()

    return df[df["case_id"].isin(matching_cases)].reset_index(drop=True)


def filter_by_case_duration(
    df: pd.DataFrame,
    min_seconds: float | None = None,
    max_seconds: float | None = None,
) -> pd.DataFrame:
    """Keep complete cases whose total duration falls within bounds.

    Duration is ``max(timestamp) - min(timestamp)`` per case.

    Parameters
    ----------
    df : pd.DataFrame
        Prepared event log.
    min_seconds : float or None
        Minimum case duration in seconds (inclusive).  ``None`` means
        no lower bound.
    max_seconds : float or None
        Maximum case duration in seconds (inclusive).  ``None`` means
        no upper bound.

    Returns
    -------
    pd.DataFrame
        All rows belonging to matching cases (index reset).
    """
    if min_seconds is None and max_seconds is None:
        return df.copy()

    dur = compute_case_durations(df)
    durations = dur["duration_seconds"]

    mask = pd.Series(True, index=durations.index)
    if min_seconds is not None:
        mask &= durations >= min_seconds
    if max_seconds is not None:
        mask &= durations <= max_seconds

    matching_cases = durations[mask].index
    return df[df["case_id"].isin(matching_cases)].reset_index(drop=True)


def filter_top_variants(
    df: pd.DataFrame,
    top_n: int | None = None,
) -> pd.DataFrame:
    """Keep complete cases belonging to the *N* most frequent variants.

    Parameters
    ----------
    df : pd.DataFrame
        Prepared event log.
    top_n : int or None
        Number of top variants to keep.  ``None`` returns the input
        unchanged.

    Returns
    -------
    pd.DataFrame
        All rows belonging to matching cases (index reset).
    """
    if top_n is None:
        return df.copy()

    variants = calculate_variants(df)
    top = variants.head(top_n)
    matching_cases = [cid for ids in top["case_ids"] for cid in ids]

    return df[df["case_id"].isin(matching_cases)].reset_index(drop=True)
