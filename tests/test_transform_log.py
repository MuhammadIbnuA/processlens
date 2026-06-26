"""Unit tests for core.transform_log module."""

import pandas as pd
import pytest
from core.transform_log import (
    prepare_event_log,
    compute_case_durations,
    get_case_summary,
    get_activity_sequences,
    add_case_duration_to_events
)


class TestPrepareEventLog:
    """Test cases for prepare_event_log function."""
    
    def test_prepare_empty_log(self):
        """Test preparing an empty log."""
        df = pd.DataFrame(columns=["case_id", "activity", "timestamp", "resource"])
        result = prepare_event_log(df)
        
        assert len(result) == 0
        assert list(result.columns) == ["case_id", "activity", "timestamp", "resource"]
        
    def test_prepare_simple_log(self):
        """Test preparing a simple log."""
        df = pd.DataFrame({
            "case_id": ["A", "A", "B"],
            "activity": ["start", "end", "start"],
            "timestamp": pd.to_datetime(["2023-01-02", "2023-01-01", "2023-01-03"]),
            "resource": ["res1", "res1", "res2"]
        })
        
        result = prepare_event_log(df)
        
        # Should drop missing values and sort by case_id, then timestamp
        assert len(result) == 3
        assert result.iloc[0]["case_id"] == "A"
        assert result.iloc[0]["timestamp"] < result.iloc[1]["timestamp"]
        assert result.iloc[2]["case_id"] == "B"
        
    def test_prepare_log_with_missing_values(self):
        """Test preparing a log with missing values."""
        df = pd.DataFrame({
            "case_id": ["A", None, "B", "A"],
            "activity": ["start", "end", None, "end"],
            "timestamp": pd.to_datetime(["2023-01-01", "2023-01-02", "2023-01-03", "2023-01-04"]),
            "resource": ["res1", "res1", "res2", "res2"]
        })
        
        result = prepare_event_log(df)
        
        # Should drop rows with missing case_id, activity, or timestamp
        assert len(result) == 2
        # Check that the resulting case IDs are A and A (the remaining rows)
        assert list(result["case_id"]) == ["A", "A"]
        assert list(result["activity"]) == ["start", "end"]
        assert all(result["activity"] == ["start", "end"])
        
    def test_prepare_log_casts_types(self):
        """Test that prepare_event_log casts columns to correct types."""
        df = pd.DataFrame({
            "case_id": [1, 2, 1],
            "activity": [100, 200, 100],
            "timestamp": pd.to_datetime(["2023-01-01", "2023-01-02", "2023-01-03"]),
            "resource": [1.5, 2.5, 1.5]
        })
        
        result = prepare_event_log(df)
        
        # Check that string columns are converted to string type (could be 'object' or pandas string)
        assert pd.api.types.is_string_dtype(result["case_id"])
        assert pd.api.types.is_string_dtype(result["activity"])
        assert pd.api.types.is_string_dtype(result["resource"])
        assert pd.api.types.is_datetime64_any_dtype(result["timestamp"])


class TestComputeCaseDurations:
    """Test cases for compute_case_durations function."""
    
    def test_compute_empty_log(self):
        """Test computing durations for empty log."""
        df = pd.DataFrame(columns=["case_id", "activity", "timestamp", "resource"])
        result = compute_case_durations(df)
        
        assert len(result) == 0
        assert list(result.columns) == ["start_time", "end_time", "duration_seconds"]
        
    def test_compute_simple_durations(self):
        """Test computing durations for a simple log."""
        df = pd.DataFrame({
            "case_id": ["A", "A", "B", "B", "C"],
            "activity": ["start", "end", "start", "end", "single"],
            "timestamp": pd.to_datetime([
                "2023-01-01 10:00:00", 
                "2023-01-01 12:00:00", 
                "2023-01-01 14:00:00",
                "2023-01-01 18:00:00",
                "2023-01-01 20:00:00"
            ]),
            "resource": ["res1", "res1", "res2", "res2", "res3"]
        })
        
        result = compute_case_durations(df)
        
        assert len(result) == 3
        assert result.loc["A"]["duration_seconds"] == 2 * 3600  # 2 hours
        assert result.loc["B"]["duration_seconds"] == 4 * 3600  # 4 hours
        assert result.loc["C"]["duration_seconds"] == 0  # Single event
        
    def test_compute_single_events(self):
        """Test computing durations for single-event cases."""
        df = pd.DataFrame({
            "case_id": ["A", "B"],
            "activity": ["act1", "act2"],
            "timestamp": pd.to_datetime(["2023-01-01", "2023-01-02"]),
            "resource": ["res1", "res2"]
        })
        
        result = compute_case_durations(df)
        
        assert result.loc["A"]["duration_seconds"] == 0
        assert result.loc["B"]["duration_seconds"] == 0


class TestGetCaseSummary:
    """Test cases for get_case_summary function."""
    
    def test_get_empty_summary(self):
        """Test getting summary for empty log."""
        df = pd.DataFrame(columns=["case_id", "activity", "timestamp", "resource"])
        result = get_case_summary(df)
        
        assert len(result) == 0
        expected_cols = [
            "case_id", "start_time", "end_time", "event_count", 
            "duration", "duration_seconds", "variant_sequence"
        ]
        assert list(result.columns) == expected_cols
        
    def test_get_simple_summary(self):
        """Test getting summary for a simple log."""
        df = pd.DataFrame({
            "case_id": ["A", "A", "B", "B", "C"],
            "activity": ["start", "end", "start", "end", "single"],
            "timestamp": pd.to_datetime([
                "2023-01-01 10:00:00", 
                "2023-01-01 12:00:00", 
                "2023-01-01 14:00:00",
                "2023-01-01 18:00:00",
                "2023-01-01 20:00:00"
            ]),
            "resource": ["res1", "res1", "res2", "res2", "res3"]
        })
        
        result = get_case_summary(df)
        
        assert len(result) == 3
        assert result.iloc[0]["case_id"] == "A"
        assert result.iloc[0]["event_count"] == 2
        assert result.iloc[0]["duration_seconds"] == 2 * 3600
        assert result.iloc[0]["variant_sequence"] == "start -> end"
        
        assert result.iloc[1]["case_id"] == "B"
        assert result.iloc[1]["event_count"] == 2
        assert result.iloc[1]["duration_seconds"] == 4 * 3600
        assert result.iloc[1]["variant_sequence"] == "start -> end"
        
        assert result.iloc[2]["case_id"] == "C"
        assert result.iloc[2]["event_count"] == 1
        assert result.iloc[2]["duration_seconds"] == 0
        assert result.iloc[2]["variant_sequence"] == "single"


class TestGetActivitySequences:
    """Test cases for get_activity_sequences function."""
    
    def test_get_empty_sequences(self):
        """Test getting sequences for empty log."""
        df = pd.DataFrame(columns=["case_id", "activity", "timestamp", "resource"])
        result = get_activity_sequences(df)
        
        assert result == {}
        
    def test_get_simple_sequences(self):
        """Test getting sequences for a simple log."""
        df = pd.DataFrame({
            "case_id": ["A", "A", "B", "B", "C"],
            "activity": ["start", "end", "start", "end", "single"],
            "timestamp": pd.to_datetime([
                "2023-01-01", "2023-01-02", 
                "2023-01-01", "2023-01-02",
                "2023-01-01"
            ]),
            "resource": ["res1", "res1", "res2", "res2", "res3"]
        })
        
        result = get_activity_sequences(df)
        
        assert result == {
            "A": ["start", "end"],
            "B": ["start", "end"],
            "C": ["single"]
        }
        
    def test_get_complex_sequences(self):
        """Test getting sequences with multiple activities per case."""
        df = pd.DataFrame({
            "case_id": ["A", "A", "A", "A", "B", "B"],
            "activity": ["step1", "step2", "step3", "step4", "step1", "step2"],
            "timestamp": pd.to_datetime([
                "2023-01-01", "2023-01-02", "2023-01-03", "2023-01-04",
                "2023-01-01", "2023-01-02"
            ]),
            "resource": ["res1"] * 6
        })
        
        result = get_activity_sequences(df)
        
        assert result == {
            "A": ["step1", "step2", "step3", "step4"],
            "B": ["step1", "step2"]
        }


class TestAddCaseDurationToEvents:
    """Test cases for add_case_duration_to_events function."""
    
    def test_add_duration_empty_log(self):
        """Test adding duration to empty log."""
        df = pd.DataFrame(columns=["case_id", "activity", "timestamp", "resource"])
        result = add_case_duration_to_events(df)
        
        expected_cols = [
            "case_id", "activity", "timestamp", "resource", 
            "case_start_time", "case_end_time", "case_duration_seconds"
        ]
        assert list(result.columns) == expected_cols
        assert len(result) == 0
        
    def test_add_duration_simple_log(self):
        """Test adding duration to a simple log."""
        df = pd.DataFrame({
            "case_id": ["A", "A", "B"],
            "activity": ["start", "end", "single"],
            "timestamp": pd.to_datetime([
                "2023-01-01 10:00:00", 
                "2023-01-01 12:00:00", 
                "2023-01-01 14:00:00"
            ]),
            "resource": ["res1", "res1", "res2"]
        })
        
        result = add_case_duration_to_events(df)
        
        assert len(result) == 3
        assert result.iloc[0]["case_start_time"] == pd.Timestamp("2023-01-01 10:00:00")
        assert result.iloc[0]["case_end_time"] == pd.Timestamp("2023-01-01 12:00:00")
        assert result.iloc[0]["case_duration_seconds"] == 2 * 3600
        
        assert result.iloc[1]["case_start_time"] == pd.Timestamp("2023-01-01 10:00:00")
        assert result.iloc[1]["case_end_time"] == pd.Timestamp("2023-01-01 12:00:00")
        assert result.iloc[1]["case_duration_seconds"] == 2 * 3600
        
        assert result.iloc[2]["case_start_time"] == pd.Timestamp("2023-01-01 14:00:00")
        assert result.iloc[2]["case_end_time"] == pd.Timestamp("2023-01-01 14:00:00")
        assert result.iloc[2]["case_duration_seconds"] == 0