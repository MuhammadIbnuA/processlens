"""Unit tests for core.validate_log module."""

import pandas as pd
import pytest
from core.validate_log import validate_event_log, format_validation_summary


class TestValidateEventLog:
    """Test cases for validate_event_log function."""
    
    def test_empty_dataframe(self):
        """Test validation of empty DataFrame."""
        df = pd.DataFrame(columns=["case_id", "activity", "timestamp", "resource"])
        result = validate_event_log(df)
        
        assert result["total_events"] == 0
        assert result["total_cases"] == 0
        assert result["total_activities"] == 0
        assert result["total_resources"] == 0
        assert result["missing_case_id"] == 0
        assert result["missing_activity"] == 0
        assert result["missing_timestamp"] == 0
        assert result["duplicate_rows"] == 0
        assert result["single_event_cases"] == 0
        assert result["start_time"] is None
        assert result["end_time"] is None
        assert result["is_valid"] is False
        
    def test_valid_simple_log(self):
        """Test validation of a simple valid log."""
        df = pd.DataFrame({
            "case_id": ["A", "A", "B", "B"],
            "activity": ["start", "end", "start", "end"],
            "timestamp": pd.to_datetime(["2023-01-01", "2023-01-02", "2023-01-03", "2023-01-04"]),
            "resource": ["res1", "res1", "res2", "res2"]
        })
        
        result = validate_event_log(df)
        
        assert result["total_events"] == 4
        assert result["total_cases"] == 2
        assert result["total_activities"] == 2
        assert result["total_resources"] == 2
        assert result["missing_case_id"] == 0
        assert result["missing_activity"] == 0
        assert result["missing_timestamp"] == 0
        assert result["duplicate_rows"] == 0
        assert result["single_event_cases"] == 0
        assert result["is_valid"] is True
        
    def test_missing_case_id(self):
        """Test validation with missing case_id."""
        df = pd.DataFrame({
            "case_id": [None, "A", "B"],
            "activity": ["start", "end", "start"],
            "timestamp": pd.to_datetime(["2023-01-01", "2023-01-02", "2023-01-03"]),
            "resource": ["res1", "res1", "res2"]
        })
        
        result = validate_event_log(df)
        
        assert result["missing_case_id"] == 1
        assert result["is_valid"] is False
        
    def test_missing_activity(self):
        """Test validation with missing activity."""
        df = pd.DataFrame({
            "case_id": ["A", "A", "B"],
            "activity": [None, "end", "start"],
            "timestamp": pd.to_datetime(["2023-01-01", "2023-01-02", "2023-01-03"]),
            "resource": ["res1", "res1", "res2"]
        })
        
        result = validate_event_log(df)
        
        assert result["missing_activity"] == 1
        assert result["is_valid"] is False
        
    def test_missing_timestamp(self):
        """Test validation with missing timestamp."""
        df = pd.DataFrame({
            "case_id": ["A", "A", "B"],
            "activity": ["start", "end", "start"],
            "timestamp": pd.to_datetime(["2023-01-01", None, "2023-01-03"]),
            "resource": ["res1", "res1", "res2"]
        })
        
        result = validate_event_log(df)
        
        assert result["missing_timestamp"] == 1
        assert result["is_valid"] is False
        
    def test_duplicate_rows(self):
        """Test validation with duplicate rows."""
        df = pd.DataFrame({
            "case_id": ["A", "A", "A"],
            "activity": ["start", "start", "end"],
            "timestamp": pd.to_datetime(["2023-01-01", "2023-01-01", "2023-01-02"]),
            "resource": ["res1", "res1", "res1"]
        })
        
        result = validate_event_log(df)
        
        assert result["duplicate_rows"] == 1
        assert result["warnings"]
        assert any("duplikat" in w for w in result["warnings"])
        
    def test_single_event_cases(self):
        """Test validation with single event cases."""
        df = pd.DataFrame({
            "case_id": ["A", "B", "C"],
            "activity": ["start", "start", "end"],
            "timestamp": pd.to_datetime(["2023-01-01", "2023-01-02", "2023-01-03"]),
            "resource": ["res1", "res2", "res3"]
        })
        
        result = validate_event_log(df)
        
        assert result["single_event_cases"] == 3
        assert result["warnings"]
        assert any("satu kejadian" in w for w in result["warnings"])
        
    def test_only_one_activity(self):
        """Test validation with only one unique activity."""
        df = pd.DataFrame({
            "case_id": ["A", "A", "B", "B"],
            "activity": ["start", "start", "start", "start"],
            "timestamp": pd.to_datetime(["2023-01-01", "2023-01-02", "2023-01-03", "2023-01-04"]),
            "resource": ["res1", "res1", "res2", "res2"]
        })
        
        result = validate_event_log(df)
        
        assert result["total_activities"] == 1
        assert result["warnings"]
        assert any("minimal 2 aktivitas" in w for w in result["warnings"])


class TestFormatValidationSummary:
    """Test cases for format_validation_summary function."""
    
    def test_format_with_valid_result(self):
        """Test formatting a valid validation result."""
        validation_result = {
            "is_valid": True,
            "total_events": 100,
            "total_cases": 10,
            "total_activities": 5,
            "total_resources": 3,
            "missing_case_id": 0,
            "missing_activity": 0,
            "missing_timestamp": 0,
            "duplicate_rows": 0,
            "single_event_cases": 0,
            "start_time": pd.Timestamp("2023-01-01"),
            "end_time": pd.Timestamp("2023-12-31"),
            "warnings": []
        }
        
        summary = format_validation_summary(validation_result)
        
        assert "Valid" in summary
        assert "100" in summary
        assert "10" in summary
        
    def test_format_with_invalid_result(self):
        """Test formatting an invalid validation result."""
        validation_result = {
            "is_valid": False,
            "total_events": 50,
            "total_cases": 5,
            "total_activities": 3,
            "total_resources": 2,
            "missing_case_id": 1,
            "missing_activity": 0,
            "missing_timestamp": 0,
            "duplicate_rows": 0,
            "single_event_cases": 0,
            "start_time": pd.Timestamp("2023-01-01"),
            "end_time": pd.Timestamp("2023-06-30"),
            "warnings": ["Test warning"]
        }
        
        summary = format_validation_summary(validation_result)
        
        assert "Tidak Valid" in summary
        assert "Test warning" in summary