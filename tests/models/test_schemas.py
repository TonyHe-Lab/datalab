"""
Unit tests for Pydantic schemas.

Tests cover:
1. Maintenance log schema validation (AC-1)
2. AI-extracted data schema validation (AC-2)
3. API schema validation (AC-4)
4. Edge cases and error handling
"""

import pytest
from datetime import datetime, timezone
from pydantic import ValidationError
from src.models.schemas import *


# ============================================================================
# Test Data Fixtures
# ============================================================================


@pytest.fixture
def valid_maintenance_log_data():
    """Valid maintenance log data for testing."""
    return {
        "notification_id": "NOTIF-2024-001",
        "noti_date": datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
        "noti_assigned_date": datetime(2024, 1, 15, 11, 0, 0, tzinfo=timezone.utc),
        "noti_closed_date": datetime(2024, 1, 16, 9, 0, 0, tzinfo=timezone.utc),
        "noti_category_id": "CAT-001",
        "sys_eq_id": "EQ-12345",
        "noti_country_id": "US",
        "sys_fl_id": "FL-001",
        "sys_mat_id": "MAT-789",
        "sys_serial_id": "SN-123456789",
        "noti_trendcode_l1": "TREND-L1",
        "noti_trendcode_l2": "TREND-L2",
        "noti_trendcode_l3": "TREND-L3",
        "noti_issue_type": "hardware",
        "noti_medium_text": "Hardware failure reported",
        "noti_text": "The server experienced a hardware failure. The RAID controller failed and needs replacement.",
    }


@pytest.fixture
def valid_ai_extracted_data():
    """Valid AI-extracted data for testing."""
    return {
        "notification_id": "NOTIF-2024-001",
        "keywords_ai": ["server", "hardware", "failure", "RAID", "controller"],
        "primary_symptom_ai": "Server hardware failure",
        "root_cause_ai": "RAID controller malfunction",
        "summary_ai": "Server experienced hardware failure due to RAID controller issue",
        "solution_ai": "Replace RAID controller",
        "solution_type_ai": "hardware replacement",
        "components_ai": ["RAID controller", "server motherboard"],
        "processes_ai": ["diagnostics", "replacement"],
        "main_component_ai": "RAID controller",
        "main_process_ai": "replacement",
        "resolution_steps": [
            {
                "step_number": 1,
                "description": "Diagnose the issue",
                "duration_minutes": 30,
                "tools_required": ["diagnostic software"],
            },
            {
                "step_number": 2,
                "description": "Order replacement part",
                "duration_minutes": 1440,  # 24 hours
                "tools_required": [],
            },
        ],
        "confidence_score_ai": 0.95,
        "model_version": "gpt-4o-2024-08-06",
    }


# ============================================================================
# Maintenance Log Schema Tests (AC-1)
# ============================================================================


class TestMaintenanceLogSchemas:
    """Tests for maintenance log schemas."""

    def test_maintenance_log_base_valid(self, valid_maintenance_log_data):
        """Test valid maintenance log base schema."""
        schema = MaintenanceLogBase(**valid_maintenance_log_data)
        assert schema.notification_id == "NOTIF-2024-001"
        assert schema.noti_issue_type == IssueType.HARDWARE
        assert schema.noti_text == valid_maintenance_log_data["noti_text"]

    def test_maintenance_log_base_missing_required(self, valid_maintenance_log_data):
        """Test missing required fields."""
        data = valid_maintenance_log_data.copy()
        del data["notification_id"]

        with pytest.raises(ValidationError) as exc:
            MaintenanceLogBase(**data)

        assert "notification_id" in str(exc.value)

    def test_maintenance_log_base_invalid_issue_type(self, valid_maintenance_log_data):
        """Test invalid issue type validation."""
        data = valid_maintenance_log_data.copy()
        data["noti_issue_type"] = "invalid_type"

        schema = MaintenanceLogBase(**data)
        # Should normalize to UNKNOWN
        assert schema.noti_issue_type == IssueType.UNKNOWN

    def test_maintenance_log_create_valid(self, valid_maintenance_log_data):
        """Test maintenance log create schema."""
        schema = MaintenanceLogCreate(**valid_maintenance_log_data)
        assert schema.notification_id == "NOTIF-2024-001"

    def test_maintenance_log_read_valid(self, valid_maintenance_log_data):
        """Test maintenance log read schema with system fields."""
        data = valid_maintenance_log_data.copy()
        data["created_at"] = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
        data["updated_at"] = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)

        schema = MaintenanceLogRead(**data)
        assert schema.notification_id == "NOTIF-2024-001"
        assert schema.created_at == data["created_at"]
        assert schema.updated_at == data["updated_at"]

    def test_issue_type_normalization(self):
        """Test issue type normalization in validator."""
        test_cases = [
            ("HARDWARE", IssueType.HARDWARE),
            ("hardware", IssueType.HARDWARE),
            ("Hardware Failure", IssueType.HARDWARE),
            ("hw issue", IssueType.HARDWARE),
            ("SOFTWARE", IssueType.SOFTWARE),
            ("software bug", IssueType.SOFTWARE),
            ("sw problem", IssueType.SOFTWARE),
            ("NETWORK", IssueType.NETWORK),
            ("network outage", IssueType.NETWORK),
            ("net issue", IssueType.NETWORK),
            ("CONFIGURATION", IssueType.CONFIGURATION),
            ("config error", IssueType.CONFIGURATION),
            ("unknown", IssueType.UNKNOWN),
            ("other", IssueType.UNKNOWN),
        ]

        for input_value, expected in test_cases:
            data = {
                "notification_id": "TEST-001",
                "noti_date": datetime.now(timezone.utc),
                "noti_text": "Test text",
                "noti_issue_type": input_value,
            }

            schema = MaintenanceLogBase(**data)
            assert schema.noti_issue_type == expected, f"Failed for: {input_value}"

    def test_text_field_validation(self):
        """Test text field validation."""
        # Empty notification_text should fail
        data = {
            "notification_id": "TEST-001",
            "notification_date": datetime.now(timezone.utc),
            "notification_text": "",  # Empty string
        }

        with pytest.raises(ValidationError) as exc:
            MaintenanceLogBase(**data)

        assert "notification_text" in str(exc.value)


# ============================================================================
# AI-Extracted Data Schema Tests (AC-2)
# ============================================================================


class TestAIExtractedDataSchemas:
    """Tests for AI-extracted data schemas."""

    def test_ai_extracted_data_base_valid(self, valid_ai_extracted_data):
        """Test valid AI-extracted data base schema."""
        schema = AIExtractedDataBase(**valid_ai_extracted_data)
        assert schema.notification_id == "NOTIF-2024-001"
        assert schema.confidence_score_ai == 0.95
        assert len(schema.keywords_ai) == 5
        assert schema.primary_symptom_ai == "Server hardware failure"

    def test_ai_extracted_data_base_minimal(self):
        """Test minimal AI-extracted data (only required fields)."""
        data = {
            "notification_id": "NOTIF-2024-001",
        }

        schema = AIExtractedDataBase(**data)
        assert schema.notification_id == "NOTIF-2024-001"
        assert schema.keywords_ai is None
        assert schema.confidence_score_ai is None

    def test_resolution_step_schema(self):
        """Test resolution step schema."""
        step_data = {
            "step_number": 1,
            "description": "Diagnose the issue",
            "duration_minutes": 30,
            "tools_required": ["diagnostic software", "multimeter"],
        }

        step = ResolutionStep(**step_data)
        assert step.step_number == 1
        assert step.description == "Diagnose the issue"
        assert step.duration_minutes == 30
        assert step.tools_required == ["diagnostic software", "multimeter"]

    def test_resolution_steps_validation(self):
        """Test resolution steps validation with different formats."""
        test_cases = [
            # String format
            "1. Diagnose issue\n2. Replace part",
            # List of dictionaries
            [
                {"step_number": 1, "description": "Diagnose"},
                {"step_number": 2, "description": "Replace"},
            ],
            # List of ResolutionStep objects (will be validated)
            [
                {"step_number": 1, "description": "Diagnose"},
                {"step_number": 2, "description": "Replace"},
            ],
            # None
            None,
        ]

        for steps in test_cases:
            data = {
                "notification_id": "TEST-001",
                "resolution_steps": steps,
            }

            schema = AIExtractedDataBase(**data)
            if steps is None:
                assert schema.resolution_steps is None
            else:
                assert schema.resolution_steps is not None

    def test_confidence_score_validation(self):
        """Test confidence score validation."""
        # Valid scores
        for score in [0.0, 0.5, 0.75, 1.0]:
            data = {
                "notification_id": "TEST-001",
                "confidence_score_ai": score,
            }
            schema = AIExtractedDataBase(**data)
            assert schema.confidence_score_ai == score

        # Invalid scores should raise validation error
        invalid_scores = [-0.1, 1.1, 2.0]
        for score in invalid_scores:
            data = {
                "notification_id": "TEST-001",
                "confidence_score_ai": score,
            }
            with pytest.raises(ValidationError):
                AIExtractedDataBase(**data)

    def test_ai_extracted_data_read_valid(self, valid_ai_extracted_data):
        """Test AI-extracted data read schema with system fields."""
        data = valid_ai_extracted_data.copy()
        data["id"] = 1
        data["extracted_at"] = datetime(2024, 1, 15, 11, 0, 0, tzinfo=timezone.utc)

        schema = AIExtractedDataRead(**data)
        assert schema.id == 1
        assert schema.notification_id == "NOTIF-2024-001"
        assert schema.extracted_at == data["extracted_at"]


# ============================================================================
# API Schema Tests (AC-4)
# ============================================================================


class TestAPISchemas:
    """Tests for API request/response schemas."""

    def test_ai_processing_request(self):
        """Test AI processing request schema."""
        data = {
            "notification_id": "NOTIF-2024-001",
            "text": "Server hardware failure. RAID controller needs replacement.",
            "model_version": "gpt-4o",
        }

        schema = AIProcessingRequest(**data)
        assert schema.notification_id == "NOTIF-2024-001"
        assert "Server hardware" in schema.text
        assert schema.model_version == "gpt-4o"

    def test_ai_processing_response_success(self, valid_ai_extracted_data):
        """Test AI processing response schema for success case."""
        extracted_data = AIExtractedDataRead(
            **valid_ai_extracted_data, id=1, extracted_at=datetime.now(timezone.utc)
        )

        data = {
            "success": True,
            "data": extracted_data,
            "processing_time_ms": 1250,
        }

        schema = AIProcessingResponse(**data)
        assert schema.success is True
        assert schema.data is not None
        assert schema.data.notification_id == "NOTIF-2024-001"
        assert schema.processing_time_ms == 1250
        assert schema.error is None

    def test_ai_processing_response_error(self):
        """Test AI processing response schema for error case."""
        data = {
            "success": False,
            "error": "Model inference failed",
            "processing_time_ms": 500,
        }

        schema = AIProcessingResponse(**data)
        assert schema.success is False
        assert schema.data is None
        assert schema.error == "Model inference failed"
        assert schema.processing_time_ms == 500

    def test_search_request(self):
        """Test search request schema."""
        data = {
            "query": "hardware failure server",
            "limit": 20,
            "similarity_threshold": 0.8,
        }

        schema = SearchRequest(**data)
        assert schema.query == "hardware failure server"
        assert schema.limit == 20
        assert schema.similarity_threshold == 0.8

    def test_search_request_defaults(self):
        """Test search request schema defaults."""
        data = {
            "query": "test query",
        }

        schema = SearchRequest(**data)
        assert schema.query == "test query"
        assert schema.limit == 10  # Default
        assert schema.similarity_threshold == 0.7  # Default

    def test_search_result(self):
        """Test search result schema."""
        data = {
            "notification_id": "NOTIF-2024-001",
            "similarity_score": 0.92,
            "notification_text": "Server hardware failure",
            "summary_ai": "Hardware issue with RAID controller",
        }

        schema = SearchResult(**data)
        assert schema.notification_id == "NOTIF-2024-001"
        assert schema.similarity_score == 0.92
        assert schema.notification_text == "Server hardware failure"
        assert schema.summary_ai == "Hardware issue with RAID controller"

    def test_search_response(self):
        """Test search response schema."""
        results = [
            SearchResult(
                notification_id="NOTIF-2024-001",
                similarity_score=0.92,
                notification_text="Server hardware failure",
            ),
            SearchResult(
                notification_id="NOTIF-2024-002",
                similarity_score=0.85,
                notification_text="Network connectivity issue",
            ),
        ]

        data = {
            "results": results,
            "total_results": 2,
            "query_time_ms": 150,
        }

        schema = SearchResponse(**data)
        assert len(schema.results) == 2
        assert schema.total_results == 2
        assert schema.query_time_ms == 150
        assert schema.results[0].notification_id == "NOTIF-2024-001"
        assert schema.results[1].notification_id == "NOTIF-2024-002"

    def test_pagination_params(self):
        """Test pagination parameters schema."""
        data = {
            "page": 2,
            "page_size": 50,
        }

        schema = PaginationParams(**data)
        assert schema.page == 2
        assert schema.page_size == 50

    def test_pagination_params_defaults(self):
        """Test pagination parameters schema defaults."""
        data = {}  # Empty dict should use defaults

        schema = PaginationParams(**data)
        assert schema.page == 1  # Default
        assert schema.page_size == 20  # Default

    def test_paginated_response(self):
        """Test paginated response schema."""
        items = [
            {"id": 1, "name": "Item 1"},
            {"id": 2, "name": "Item 2"},
            {"id": 3, "name": "Item 3"},
        ]

        data = {
            "items": items,
            "total": 100,
            "page": 2,
            "page_size": 3,
            "total_pages": 34,
        }

        schema = PaginatedResponse(**data)
        assert len(schema.items) == 3
        assert schema.total == 100
        assert schema.page == 2
        assert schema.page_size == 3
        assert schema.total_pages == 34

    def test_error_response(self):
        """Test error response schema."""
        data = {
            "error": "Resource not found",
            "detail": "The requested notification ID does not exist",
            "code": "NOT_FOUND",
        }

        schema = ErrorResponse(**data)
        assert schema.error == "Resource not found"
        assert schema.detail == "The requested notification ID does not exist"
        assert schema.code == "NOT_FOUND"


# ============================================================================
# Edge Case Tests
# ============================================================================


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_large_text_fields(self):
        """Test handling of large text fields."""
        large_text = "A" * 10000  # 10KB of text

        data = {
            "notification_id": "TEST-001",
            "noti_date": datetime.now(timezone.utc),
            "noti_text": large_text,
        }

        schema = MaintenanceLogBase(**data)
        assert len(schema.noti_text) == 10000
        assert schema.noti_text.startswith("A")

    def test_special_characters(self):
        """Test handling of special characters in text fields."""
        special_text = (
            "Test with special chars: é, ñ, 中文, 🚀, <script>alert('xss')</script>"
        )

        data = {
            "notification_id": "TEST-001",
            "noti_date": datetime.now(timezone.utc),
            "noti_text": special_text,
            "noti_issue_type": "software",
        }

        schema = MaintenanceLogBase(**data)
        assert "中文" in schema.noti_text
        assert "🚀" in schema.noti_text
        assert schema.noti_issue_type == IssueType.SOFTWARE

    def test_null_and_empty_values(self):
        """Test handling of null and empty values."""
        data = {
            "notification_id": "TEST-001",
            "noti_date": datetime.now(timezone.utc),
            "noti_text": "Valid text",
            "noti_assigned_date": None,
            "noti_closed_date": None,
            "noti_category_id": None,
            "sys_eq_id": "",
            "noti_issue_type": None,
        }

        schema = MaintenanceLogBase(**data)
        assert schema.noti_assigned_date is None
        assert schema.noti_closed_date is None
        assert schema.noti_category_id is None
        assert schema.sys_eq_id == ""  # Empty string is allowed
        assert schema.noti_issue_type is None

    def test_datetime_formats(self):
        """Test handling of different datetime formats."""
        from datetime import datetime

        # ISO format string
        iso_date = "2024-01-15T10:30:00Z"

        data = {
            "notification_id": "TEST-001",
            "noti_date": iso_date,
            "noti_text": "Test text",
        }

        schema = MaintenanceLogBase(**data)
        assert isinstance(schema.noti_date, datetime)
        # Pydantic should parse ISO format correctly


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
