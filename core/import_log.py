"""Load CSV event logs into a pandas DataFrame.

Responsible for reading uploaded CSV files, parsing timestamps,
and returning a clean DataFrame ready for validation.
"""

from __future__ import annotations

from typing import IO

import pandas as pd

def read_csv_file(uploaded_file: str | IO, chunksize: int | None = None) -> pd.DataFrame:
    """Read an uploaded CSV file into a DataFrame.

    Parameters
    ----------
    uploaded_file : str or file-like
        A file path string or a file-like object with a ``.read()``
        method (e.g. from ``st.file_uploader``).
    chunksize : int or None, optional
        Size of chunks to read (for memory efficiency).  If ``None``,
        the entire file is read at once.

    Returns
    -------
    pd.DataFrame
        The raw contents of the CSV file.

    Raises
    ------
    ValueError
        If the file cannot be parsed as CSV.
    """
    try:
        if chunksize:
            chunks = pd.read_csv(uploaded_file, chunksize=chunksize)
            df = pd.concat(chunks, ignore_index=True)
        else:
            df = pd.read_csv(uploaded_file)
    except Exception as exc:
        raise ValueError(f"Could not read CSV file: {exc}") from exc
    return df


def get_column_names(df: pd.DataFrame) -> list[str]:
    """Return the column names of a DataFrame.

    Parameters
    ----------
    df : pd.DataFrame

    Returns
    -------
    list[str]
        Column names as a list of strings.
    """
    return list(df.columns)


INTERNAL_COLUMNS = ("case_id", "activity", "timestamp", "resource")

def export_event_log(df: pd.DataFrame, format: str = "csv", filename: str = "event_log") -> tuple[bytes, str]:
    """Export event log to various formats.
    
    Parameters
    ----------
    df : pd.DataFrame
        The event log DataFrame to export.
    format : str, optional
        Export format: "csv", "json", or "xlsx". Default "csv".
    filename : str, optional
        Base filename without extension. Default "event_log".
        
    Returns
    -------
    tuple[bytes, str]
        The exported file content as bytes and the MIME type.
    """
    if format.lower() == "csv":
        content = df.to_csv(index=False)
        return content.encode('utf-8'), "text/csv"
    elif format.lower() == "json":
        content = df.to_json(orient="records", date_format="iso", indent=2)
        return content.encode('utf-8'), "application/json"
    elif format.lower() == "xlsx":
        import io
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name="Event_Log", index=False)
        buffer.seek(0)
        return buffer.getvalue(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    else:
        raise ValueError(f"Unsupported format: {format}. Supported formats: csv, json, xlsx")


def map_event_log_columns(
    df: pd.DataFrame,
    case_col: str,
    activity_col: str,
    timestamp_col: str,
    resource_col: str | None = None,
) -> pd.DataFrame:
    """Rename selected columns to the internal event-log schema.

    The internal schema uses four standard columns:

    * ``case_id``   – identifies the process instance
    * ``activity``  – name of the performed activity
    * ``timestamp`` – when the activity happened
    * ``resource``  – who performed the activity

    Any additional columns in the original DataFrame are preserved
    as extra attributes, prefixed with ``attr_`` if their name
    conflicts with an internal column name.

    Parameters
    ----------
    df : pd.DataFrame
        The raw event log.
    case_col : str
        Column name to map to ``case_id``.
    activity_col : str
        Column name to map to ``activity``.
    timestamp_col : str
        Column name to map to ``timestamp``.
    resource_col : str or None, optional
        Column name to map to ``resource``.  If ``None``, a
        ``resource`` column filled with ``"Unknown"`` is created.

    Returns
    -------
    pd.DataFrame
        A new DataFrame with internal columns, timestamp parsed,
        and rows sorted by ``case_id`` then ``timestamp``.

    Raises
    ------
    ValueError
        If required columns do not exist in *df* or if mapping
        columns are not unique.
    """
    # Validate that selected columns exist in the dataframe
    for name, col in [("ID Kasus", case_col), ("Aktivitas", activity_col),
                       ("Waktu Kejadian", timestamp_col)]:
        if col not in df.columns:
            raise ValueError(
                f"Kolom '{col}' yang dipilih untuk {name} tidak ditemukan dalam file CSV."
            )
    if resource_col is not None and resource_col not in df.columns:
        raise ValueError(
            f"Kolom '{resource_col}' yang dipilih untuk Sumber Daya tidak ditemukan dalam file CSV."
        )

    # Validate that mapping columns are unique
    selected = [case_col, activity_col, timestamp_col]
    if resource_col is not None:
        selected.append(resource_col)
    if len(selected) != len(set(selected)):
        raise ValueError(
            "Kolom mapping tidak boleh sama. "
            "Pilih kolom yang berbeda untuk ID Kasus, Aktivitas, "
            "Waktu Kejadian, dan Sumber Daya."
        )

    # Build a fresh dataframe with the four internal columns
    mapped = pd.DataFrame()
    mapped["case_id"] = df[case_col].values
    mapped["activity"] = df[activity_col].values
    mapped["timestamp"] = df[timestamp_col].values
    mapped["resource"] = df[resource_col].values if resource_col is not None else "Unknown"

    # Append additional columns that were not used in the mapping
    mapped_cols = set(selected)
    for col in df.columns:
        if col in mapped_cols:
            continue
        target = col
        if target in INTERNAL_COLUMNS:
            target = f"attr_{col}"
        mapped[target] = df[col].values

    # Parse timestamps
    mapped["timestamp"] = pd.to_datetime(mapped["timestamp"], errors="coerce")

    # Sort and reset index
    mapped = mapped.sort_values(["case_id", "timestamp"]).reset_index(drop=True)

    assert mapped.columns.is_unique, "Internal bug: duplicate column names after mapping"
    return mapped
