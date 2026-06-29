"""Unit tests for robust datetime parsing functionality."""

import pandas as pd
import pytest
from core.import_log import _robust_parse_timestamps


class TestRobustDatetimeParsing:
    """Test cases for robust datetime parsing."""
    
    def test_dd_mm_yyyy_hh_mm_format(self):
        """Test parsing DD/MM/YYYY HH:MM format."""
        series = pd.Series(["29/06/2026 13:25", "01/01/2024 00:00"])
        result = _robust_parse_timestamps(series)
        
        assert len(result) == 2
        assert pd.notna(result[0])  # Should parse successfully
        assert pd.notna(result[1])  # Should parse successfully
        
    def test_dd_mm_yyyy_hh_mm_ss_format(self):
        """Test parsing DD/MM/YYYY HH:MM:SS format."""
        series = pd.Series(["01/03/2024 09:44:00", "15/12/2023 14:30:45"])
        result = _robust_parse_timestamps(series)
        
        assert len(result) == 2
        assert pd.notna(result[0])  # Should parse successfully
        assert pd.notna(result[1])  # Should parse successfully
        
    def test_invalid_dates_return_nat(self):
        """Test that invalid dates return NaT."""
        series = pd.Series(["invalid_date", "32/13/2024 25:99", ""])
        result = _robust_parse_timestamps(series)
        
        assert len(result) == 3
        assert pd.isna(result[0])  # Should be NaT
        assert pd.isna(result[1])  # Should be NaT
        assert pd.isna(result[2])  # Should be NaT
        
    def test_mixed_formats(self):
        """Test parsing mixed date formats."""
        series = pd.Series([
            "29/06/2026 13:25",      # DD/MM/YYYY HH:MM
            "01/03/2024 09:44:00",  # DD/MM/YYYY HH:MM:SS
            "2024-03-01 09:44:00",  # ISO format (fallback)
            "invalid",              # Invalid (should be NaT)
        ])
        result = _robust_parse_timestamps(series)
        
        assert len(result) == 4
        assert pd.notna(result[0])  # DD/MM/YYYY HH:MM format
        assert pd.notna(result[1])  # DD/MM/YYYY HH:MM:SS format
        assert pd.notna(result[2])  # ISO format (fallback)
        assert pd.isna(result[3])   # Invalid date
        
    def test_empty_series(self):
        """Test parsing empty series."""
        series = pd.Series([], dtype=object)
        result = _robust_parse_timestamps(series)
        
        assert len(result) == 0
        
    def test_all_nat_values(self):
        """Test series with all NaT values."""
        series = pd.Series([None, None, None])
        result = _robust_parse_timestamps(series)
        
        assert len(result) == 3
        assert all(pd.isna(val) for val in result)