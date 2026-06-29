"""Utility functions for ProcessLens EDU.

Contains shared utility functions that don't belong to specific modules.
"""

from __future__ import annotations

import pandas as pd


def robust_parse_timestamps(timestamp_series: pd.Series) -> pd.Series:
    """Robustly parse timestamps with explicit format detection to avoid pandas warnings.
    
    First tries explicit DD/MM/YYYY formats, then falls back to dayfirst=True,
    and finally generic parsing. This eliminates pandas warnings about ambiguous
    date formats while maintaining backward compatibility.
    
    Parameters
    ----------
    timestamp_series : pd.Series
        Series containing timestamp strings to parse
        
    Returns
    -------
    pd.Series
        Series with parsed timestamps (or NaT for unparseable values)
    """
    # Try explicit DD/MM/YYYY HH:MM format first
    parsed = pd.to_datetime(timestamp_series, format="%d/%m/%Y %H:%M", errors="coerce")
    
    # If there are still NaT values, try DD/MM/YYYY HH:MM:SS format
    na_mask = parsed.isna()
    if na_mask.any():
        # Update only the NaT values
        subset = timestamp_series[na_mask]
        parsed_update = pd.to_datetime(subset, format="%d/%m/%Y %H:%M:%S", errors="coerce")
        parsed = parsed.mask(na_mask, parsed_update)
        
        # Update mask again
        na_mask = parsed.isna()
        if na_mask.any():
            # Try dayfirst=True as fallback
            subset = timestamp_series[na_mask]
            parsed_update = pd.to_datetime(subset, dayfirst=True, errors="coerce")
            parsed = parsed.mask(na_mask, parsed_update)
            
            # Final fallback to generic parsing
            na_mask = parsed.isna()
            if na_mask.any():
                subset = timestamp_series[na_mask]
                parsed_update = pd.to_datetime(subset, errors="coerce")
                parsed = parsed.mask(na_mask, parsed_update)
    
    return parsed