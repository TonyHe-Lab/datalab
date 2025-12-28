"""
Unit tests for data transformation utilities.

Tests cover:
1. Schema to ORM model conversions (AC-5)
2. Data cleaning and normalization
3. Serialization/deserialization
4. Type conversion utilities
"""

import pytest
import json
from datetime import datetime, timezone
from pydantic import ValidationError
from src.models.schemas import (
    MaintenanceLogCreate,
    MaintenanceLogRead,
    AIExtractedDataCreate,
    AIExtractedDataRead,
    IssueType,
    AIProcessingRequest,
    ResolutionStep,
)
from src.models.entities import MaintenanceLog, AIExtractedData
from src.models.transformations import (
    maintenance_log_create_to_orm,
    maintenance_log_orm_to_read,
    ai_extracted_data_create_to_orm,
    ai_extracted_data_orm_to_read,
    normalize_maintenance_log_data,
    normalize_ai_extracted_data,
    serialize_for_api,
    deserialize_from_api,
    convert_resolution_steps,
)


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def sample_maintenance_log_schema():
    """Create a sample maintenance log schema."""
    return MaintenanceLogCreate(
        notification_id="NOTIF-2024-001",
        noti_date=datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
        noti_assigned_date=datetime(2024, 1, 15, 11, 0, 0, tzinfo=timezone.utc),
        noti_closed_date=datetime(2024, 1, 16, 9, 0, 0, tzinfo=timezone.utc),
        noti_category_id="CAT-001",
        sys_eq_id="EQ-12345",
        noti_country_id="US",
        sys_fl_id="FL-001",
        sys_mat_id="MAT-789",
        sys_serial_id="SN-123456789",
        noti_trendcode_l1="TREND-L1",
        noti_trendcode_l2="TREND-L2",
        noti_trendcode_l3="TREND-L3",
        noti_issue_type=IssueType.HARDWARE,
        noti_medium_text="Hardware failure reported",
        noti_text="The server experienced a hardware failure.",
    )


@pytest.fixture
def sample_ai_extracted_data_schema():
    """Create a sample AI-extracted data schema."""
    return AIExtractedDataCreate(
        notification_id="NOTIF-2024-001",
        keywords_ai=["server", "hardware", "failure"],
        primary_symptom_ai="Server hardware failure",
        root_cause_ai="RAID controller malfunction",
        summary_ai="Server experienced hardware failure",
        solution_ai="Replace RAID controller",
        solution_type_ai="hardware replacement",
        components_ai=["RAID controller", "server motherboard"],
        processes_ai=["diagnostics", "replacement"],
        main_component_ai="RAID controller",
        main_process_ai="replacement",
        resolution_steps=[
            ResolutionStep(
                step_number=1,
                description="Diagnose the issue",
                duration_minutes=30,
                tools_required=["diagnostic software"],
            ),
            ResolutionStep(
                step_number=2,
                description="Order replacement part",
                duration_minutes=1440,
                tools_required=[],
            ),
        ],
        confidence_score_ai=0.95,
        model_version="gpt-4o-2024-08-06",
    )


# ============================================================================
# Maintenance Log Transformation Tests
# ============================================================================


class TestMaintenanceLogTransformations:
    """Tests for maintenance log transformation utilities."""

    def test_maintenance_log_create_to_orm_new(self, sample_maintenance_log_schema):
        """Test converting MaintenanceLogCreate schema to new ORM model."""
        orm_model = maintenance_log_create_to_orm(sample_maintenance_log_schema)

        assert isinstance(orm_model, MaintenanceLog)
        assert orm_model.notification_id == "NOTIF-2024-001"
        assert orm_model.noti_issue_type == "hardware"
        assert orm_model.noti_text == "The server experienced a hardware failure."
        assert orm_model.sys_eq_id == "EQ-12345"

    def test_maintenance_log_create_to_orm_update(self, sample_maintenance_log_schema):
        """Test updating existing ORM model with MaintenanceLogCreate schema."""
        # Create existing model
        existing_log = MaintenanceLog(
            notification_id="NOTIF-2024-001",
            noti_date=datetime.now(timezone.utc),
            noti_text="Original text",
            noti_issue_type="software",
        )

        # Update with schema
        updated_log = maintenance_log_create_to_orm(
            sample_maintenance_log_schema, existing_log
        )

        assert updated_log is existing_log  # Same object
        assert updated_log.noti_text == "The server experienced a hardware failure."
        assert updated_log.noti_issue_type == "hardware"
        assert updated_log.sys_eq_id == "EQ-12345"

    def test_maintenance_log_orm_to_read(self):
        """Test converting ORM model to MaintenanceLogRead schema."""
        # Create ORM model
        orm_model = MaintenanceLog(
            notification_id="NOTIF-2024-001",
            noti_date=datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            noti_text="Test text",
            created_at=datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
        )

        # Convert to schema
        schema = maintenance_log_orm_to_read(orm_model)

        assert isinstance(schema, MaintenanceLogRead)
        assert schema.notification_id == "NOTIF-2024-001"
        assert schema.noti_text == "Test text"
        assert schema.created_at == datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
        assert schema.updated_at == datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)

    def test_normalize_maintenance_log_data_basic(self):
        """Test basic maintenance log data normalization."""
        raw_data = {
            "notification_id": "NOTIF-2024-001",
            "noti_date": "2024-01-15T10:30:00Z",
            "noti_text": "  The server   experienced a hardware failure.  ",
            "notification_issue_type": "HARDWARE FAILURE",
            "sys_eq_id": "  EQ-12345  ",
        }

        normalized = normalize_maintenance_log_data(raw_data)

        assert normalized["notification_id"] == "NOTIF-2024-001"
        assert "  " not in normalized["noti_text"]  # Extra spaces removed
        assert normalized["noti_issue_type"] == "hardware"  # Normalized
        assert (
            normalized["sys_eq_id"] == "  EQ-12345  "
        )  # Not a text field, not trimmed

    def test_normalize_maintenance_log_data_with_mapping(self):
        """Test maintenance log data normalization with custom mapping."""
        raw_data = {
            "notification_id": "NOTIF-2024-001",
            "noti_date": "2024-01-15T10:30:00Z",
            "noti_text": "Test text",
            "notification_issue_type": "HW_PROBLEM",
        }

        issue_type_mapping = {
            "hw_problem": "hardware",
            "sw_bug": "software",
            "net_issue": "network",
        }

        normalized = normalize_maintenance_log_data(raw_data, issue_type_mapping)

        assert normalized["noti_issue_type"] == "hardware"

    def test_normalize_maintenance_log_data_unknown_issue_type(self):
        """Test maintenance log data normalization with unknown issue type."""
        raw_data = {
            "notification_id": "NOTIF-2024-001",
            "noti_date": "2024-01-15T10:30:00Z",
            "noti_text": "Test text",
            "notification_issue_type": "UNKNOWN_CATEGORY",
        }

        normalized = normalize_maintenance_log_data(raw_data)

        assert normalized["noti_issue_type"] == "unknown"

    def test_normalize_maintenance_log_data_null_values(self):
        """Test maintenance log data normalization with null values."""
        raw_data = {
            "notification_id": "NOTIF-2024-001",
            "notification_date": "2024-01-15T10:30:00Z",
            "notification_text": "Test text",
            "notification_assigned_date": None,
            "notification_closed_date": "",
            "noti_category_id": None,
        }

        normalized = normalize_maintenance_log_data(raw_data)

        assert normalized["notification_assigned_date"] is None
        assert normalized["notification_closed_date"] == ""  # Empty string preserved
        assert normalized["noti_category_id"] is None


# ============================================================================
# AI-Extracted Data Transformation Tests
# ============================================================================


class TestAIExtractedDataTransformations:
    """Tests for AI-extracted data transformation utilities."""

    def test_ai_extracted_data_create_to_orm_new(self, sample_ai_extracted_data_schema):
        """Test converting AIExtractedDataCreate schema to new ORM model."""
        orm_model = ai_extracted_data_create_to_orm(sample_ai_extracted_data_schema)

        assert isinstance(orm_model, AIExtractedData)
        assert orm_model.notification_id == "NOTIF-2024-001"
        assert orm_model.confidence_score_ai == 0.95
        assert orm_model.primary_symptom_ai == "Server hardware failure"

        # Check JSON fields are serialized
        assert isinstance(orm_model.keywords_ai, str)  # JSON string
        keywords = json.loads(orm_model.keywords_ai)
        assert keywords == ["server", "hardware", "failure"]

        # components_ai and processes_ai should be comma-separated strings
        assert orm_model.components_ai == "RAID controller, server motherboard"
        assert orm_model.processes_ai == "diagnostics, replacement"

        # resolution_steps should not be in ORM model (not in database)
        assert not hasattr(orm_model, "resolution_steps")

    def test_ai_extracted_data_create_to_orm_update(
        self, sample_ai_extracted_data_schema
    ):
        """Test updating existing ORM model with AIExtractedDataCreate schema."""
        # Create existing model
        existing_data = AIExtractedData(
            notification_id="NOTIF-2024-001",
            primary_symptom_ai="Original symptom",
            confidence_score_ai=0.5,
        )

        # Update with schema
        updated_data = ai_extracted_data_create_to_orm(
            sample_ai_extracted_data_schema, existing_data
        )

        assert updated_data is existing_data  # Same object
        assert updated_data.primary_symptom_ai == "Server hardware failure"
        assert updated_data.confidence_score_ai == 0.95
        assert isinstance(updated_data.keywords_ai, str)  # JSON string

    def test_ai_extracted_data_orm_to_read(self):
        """Test converting ORM model to AIExtractedDataRead schema."""
        # Create ORM model with JSON fields
        orm_model = AIExtractedData(
            id=1,
            notification_id="NOTIF-2024-001",
            keywords_ai='["server", "hardware", "failure"]',
            primary_symptom_ai="Server hardware failure",
            root_cause_ai="RAID controller malfunction",
            components_ai="RAID controller, server motherboard",
            processes_ai="diagnosis, replacement",
            confidence_score_ai=0.95,
            extracted_at=datetime(2024, 1, 15, 11, 0, 0, tzinfo=timezone.utc),
            model_version="gpt-4o",
        )

        # Convert to schema
        schema = ai_extracted_data_orm_to_read(orm_model)

        assert isinstance(schema, AIExtractedDataRead)
        assert schema.id == 1
        assert schema.notification_id == "NOTIF-2024-001"
        assert schema.keywords_ai == ["server", "hardware", "failure"]  # Deserialized
        assert schema.primary_symptom_ai == "Server hardware failure"
        assert schema.components_ai == ["RAID controller", "server motherboard"]
        assert schema.processes_ai == ["diagnosis", "replacement"]
        assert schema.confidence_score_ai == 0.95
        assert schema.model_version == "gpt-4o"

    def test_normalize_ai_extracted_data_basic(self):
        """Test basic AI-extracted data normalization."""
        raw_data = {
            "notification_id": "NOTIF-2024-001",
            "primary_symptom_ai": "  Server hardware   failure  ",
            "confidence_score_ai": 1.2,  # Above 1.0
            "keywords_ai": "server, hardware, failure",
            "components_ai": '["RAID controller", "server motherboard"]',
        }

        normalized = normalize_ai_extracted_data(raw_data)

        assert normalized["primary_symptom_ai"] == "Server hardware failure"  # Cleaned
        assert normalized["confidence_score_ai"] == 1.0  # Clamped to 1.0
        assert normalized["keywords_ai"] == ["server", "hardware", "failure"]  # Parsed
        assert normalized["components_ai"] == [
            "RAID controller",
            "server motherboard",
        ]  # Parsed JSON

    def test_normalize_ai_extracted_data_low_confidence(self):
        """Test AI-extracted data normalization with low confidence."""
        raw_data = {
            "notification_id": "NOTIF-2024-001",
            "primary_symptom_ai": "Server hardware failure",
            "root_cause_ai": "RAID controller malfunction",
            "confidence_score_ai": 0.3,  # Low confidence
            "model_version": "gpt-4o",
        }

        normalized = normalize_ai_extracted_data(raw_data, min_confidence=0.5)

        assert normalized["notification_id"] == "NOTIF-2024-001"
        assert normalized["confidence_score_ai"] == 0.3
        assert normalized["model_version"] == "gpt-4o"
        assert normalized["primary_symptom_ai"] is None  # Cleared due to low confidence
        assert normalized["root_cause_ai"] is None  # Cleared due to low confidence

    def test_normalize_ai_extracted_data_json_parsing(self):
        """Test AI-extracted data normalization with JSON parsing."""
        test_cases = [
            # JSON string
            ('["item1", "item2"]', ["item1", "item2"]),
            # Comma-separated string
            ("item1, item2, item3", ["item1", "item2", "item3"]),
            # Already a list
            (["item1", "item2"], ["item1", "item2"]),
            # Single string
            ("single_item", ["single_item"]),
            # None
            (None, None),
            # Empty string
            ("", []),
        ]

        for input_val, expected in test_cases:
            raw_data = {
                "notification_id": "TEST-001",
                "keywords_ai": input_val,
            }

            normalized = normalize_ai_extracted_data(raw_data)

            if expected is None:
                assert normalized["keywords_ai"] is None
            else:
                assert normalized["keywords_ai"] == expected

    def test_normalize_ai_extracted_data_invalid_json(self):
        """Test AI-extracted data normalization with invalid JSON."""
        raw_data = {
            "notification_id": "NOTIF-2024-001",
            "keywords_ai": "[invalid json",  # Invalid JSON
            "components_ai": "item1, item2, item3",  # Comma-separated
        }

        normalized = normalize_ai_extracted_data(raw_data)

        # Invalid JSON should be treated as comma-separated
        assert isinstance(normalized["keywords_ai"], list)
        assert normalized["components_ai"] == ["item1", "item2", "item3"]


# ============================================================================
# Serialization Tests
# ============================================================================


class TestSerialization:
    """Tests for serialization and deserialization utilities."""

    def test_serialize_for_api_pydantic_model(self, sample_maintenance_log_schema):
        """Test serializing Pydantic model for API."""
        result = serialize_for_api(sample_maintenance_log_schema)

        assert isinstance(result, dict)
        assert result["notification_id"] == "NOTIF-2024-001"
        assert result["noti_text"] == "The server experienced a hardware failure."
        assert "noti_date" in result

    def test_serialize_for_api_with_include(self, sample_maintenance_log_schema):
        """Test serializing with include filter."""
        result = serialize_for_api(
            sample_maintenance_log_schema,
            include=["notification_id", "noti_text", "noti_issue_type"],
        )

        assert set(result.keys()) == {
            "notification_id",
            "noti_text",
            "noti_issue_type",
        }
        assert result["notification_id"] == "NOTIF-2024-001"
        assert "noti_date" not in result

    def test_serialize_for_api_with_exclude(self, sample_maintenance_log_schema):
        """Test serializing with exclude filter."""
        result = serialize_for_api(
            sample_maintenance_log_schema,
            exclude=["noti_assigned_date", "noti_closed_date"],
        )

        assert "notification_id" in result
        assert "noti_text" in result
        assert "noti_assigned_date" not in result
        assert "noti_closed_date" not in result

    def test_serialize_for_api_orm_model(self):
        """Test serializing ORM model for API."""
        orm_model = MaintenanceLog(
            notification_id="NOTIF-2024-001",
            noti_date=datetime.now(timezone.utc),
            noti_text="Test text",
        )

        result = serialize_for_api(orm_model)

        assert isinstance(result, dict)
        assert result["notification_id"] == "NOTIF-2024-001"
        assert result["noti_text"] == "Test text"
        assert "_sa_instance_state" not in result  # SQLAlchemy internal removed

    def test_serialize_for_api_dict(self):
        """Test serializing dictionary for API."""
        data = {
            "id": 1,
            "name": "Test",
            "value": 123.45,
        }

        result = serialize_for_api(data)

        assert result == data  # Should return copy
        assert result is not data  # Should be a copy

    def test_deserialize_from_api(self):
        """Test deserializing from API request."""
        request_data = {
            "notification_id": "NOTIF-2024-001",
            "text": "Server hardware failure",
            "model_version": "gpt-4o",
        }

        schema = deserialize_from_api(request_data, AIProcessingRequest)

        assert isinstance(schema, AIProcessingRequest)
        assert schema.notification_id == "NOTIF-2024-001"
        assert schema.text == "Server hardware failure"
        assert schema.model_version == "gpt-4o"

    def test_deserialize_from_api_invalid(self):
        """Test deserializing invalid data from API."""
        request_data = {
            # Missing required fields
            "model_version": "gpt-4o",
        }

        with pytest.raises(ValidationError):
            deserialize_from_api(request_data, AIProcessingRequest)


# ============================================================================
# Type Conversion Tests
# ============================================================================


class TestTypeConversions:
    """Tests for type conversion utilities."""

    def test_convert_resolution_steps_string_to_json(self):
        """Test converting string resolution steps to JSON."""
        # Use a JSON string as input
        steps = '[{"step_number": 1, "description": "Diagnose issue"}, {"step_number": 2, "description": "Replace part"}]'

        result = convert_resolution_steps(steps, target_format="json")

        assert isinstance(result, str)
        # Should be valid JSON
        parsed = json.loads(result)
        assert isinstance(parsed, list)
        assert len(parsed) == 2

    def test_convert_resolution_steps_list_to_json(self):
        """Test converting list resolution steps to JSON."""
        steps = [
            {"step_number": 1, "description": "Diagnose"},
            {"step_number": 2, "description": "Replace"},
        ]

        result = convert_resolution_steps(steps, target_format="json")

        assert isinstance(result, str)
        parsed = json.loads(result)
        assert len(parsed) == 2
        assert parsed[0]["step_number"] == 1
        assert parsed[0]["description"] == "Diagnose"

    def test_convert_resolution_steps_json_to_list(self):
        """Test converting JSON resolution steps to list."""
        steps = '[{"step_number": 1, "description": "Diagnose"}]'

        result = convert_resolution_steps(steps, target_format="list")

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["step_number"] == 1
        assert result[0]["description"] == "Diagnose"

    def test_convert_resolution_steps_list_to_text(self):
        """Test converting list resolution steps to text."""
        steps = [
            ResolutionStep(
                step_number=1,
                description="Diagnose the issue",
                duration_minutes=30,
                tools_required=["diagnostic software"],
            ),
            ResolutionStep(
                step_number=2,
                description="Replace part",
                duration_minutes=60,
                tools_required=["screwdriver", "multimeter"],
            ),
        ]

        result = convert_resolution_steps(steps, target_format="text")

        assert isinstance(result, str)
        assert "1. Diagnose the issue (30 min) [Tools: diagnostic software]" in result
        assert "2. Replace part (60 min) [Tools: screwdriver, multimeter]" in result

    def test_convert_resolution_steps_dict_list_to_text(self):
        """Test converting dictionary list resolution steps to text."""
        steps = [
            {"step_number": 1, "description": "Diagnose", "duration_minutes": 30},
            {
                "step_number": 2,
                "description": "Replace",
                "tools_required": ["tool1", "tool2"],
            },
        ]

        result = convert_resolution_steps(steps, target_format="text")

        assert isinstance(result, str)
        assert "1. Diagnose (30 min)" in result
        assert "2. Replace [Tools: tool1, tool2]" in result

    def test_convert_resolution_steps_invalid_json(self):
        """Test converting invalid JSON resolution steps."""
        steps = "[invalid json"

        result = convert_resolution_steps(steps, target_format="list")

        # Should treat as single text step
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["description"] == "[invalid json"

    def test_convert_resolution_steps_none(self):
        """Test converting None resolution steps."""
        result = convert_resolution_steps(None, target_format="json")

        assert result is None


# ============================================================================
# Integration Tests
# ============================================================================


class TestIntegration:
    """Integration tests for transformation workflows."""

    def test_complete_transformation_workflow(self):
        """Test complete transformation workflow."""
        # 1. Raw data from source
        raw_data = {
            "notification_id": "WORKFLOW-001",
            "noti_date": "2024-01-15T10:30:00Z",
            "noti_text": "  Server hardware   failure. RAID controller issue.  ",
            "notification_issue_type": "HW_PROBLEM",
            "sys_eq_id": "EQ-12345",
        }

        # 2. Normalize
        normalized = normalize_maintenance_log_data(
            raw_data, issue_type_mapping={"hw_problem": "hardware"}
        )

        assert normalized["noti_issue_type"] == "hardware"
        assert "  " not in normalized["noti_text"]

        # 3. Create schema
        schema = MaintenanceLogCreate(**normalized)

        assert schema.notification_id == "WORKFLOW-001"
        assert schema.noti_issue_type == IssueType.HARDWARE

        # 4. Convert to ORM
        orm_model = maintenance_log_create_to_orm(schema)

        # Set timestamps for testing
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)
        orm_model.created_at = now
        orm_model.updated_at = now
        assert orm_model.noti_issue_type == "hardware"
        assert orm_model.noti_text == "Server hardware failure. RAID controller issue."

        # 5. Convert back to read schema
        read_schema = maintenance_log_orm_to_read(orm_model)

        assert isinstance(read_schema, MaintenanceLogRead)
        assert read_schema.notification_id == "WORKFLOW-001"
        assert read_schema.noti_issue_type == IssueType.HARDWARE

        # 6. Serialize for API
        api_response = serialize_for_api(read_schema)

        assert isinstance(api_response, dict)
        assert api_response["notification_id"] == "WORKFLOW-001"
        assert api_response["noti_issue_type"] == "hardware"

    def test_ai_data_transformation_workflow(self):
        """Test AI data transformation workflow."""
        # 1. Raw AI data from source
        raw_ai_data = {
            "notification_id": "WORKFLOW-001",
            "primary_symptom_ai": "  Server hardware failure  ",
            "root_cause_ai": "RAID controller malfunction  ",
            "confidence_score_ai": 0.92,
            "keywords_ai": "server, hardware, failure, raid",
            "resolution_steps": [
                {"step_number": 1, "description": "Diagnose"},
                {"step_number": 2, "description": "Replace"},
            ],
        }

        # 2. Normalize
        normalized = normalize_ai_extracted_data(raw_ai_data)

        assert normalized["primary_symptom_ai"] == "Server hardware failure"
        assert normalized["keywords_ai"] == ["server", "hardware", "failure", "raid"]

        # 3. Create schema
        schema = AIExtractedDataCreate(**normalized)

        assert schema.notification_id == "WORKFLOW-001"
        assert schema.confidence_score_ai == 0.92
        # Note: resolution_steps is in schema but not in database

        # 4. Convert to ORM (resolution_steps will be removed as it's not in database)
        orm_model = ai_extracted_data_create_to_orm(schema)

        assert isinstance(orm_model, AIExtractedData)
        assert orm_model.notification_id == "WORKFLOW-001"
        assert isinstance(orm_model.keywords_ai, str)  # JSON string

        # Simulate database operations by setting fields that would be set by DB
        # In real usage, these would be set by the database
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)
        orm_model.id = 1
        orm_model.extracted_at = now

        # 5. Convert back to read schema
        read_schema = ai_extracted_data_orm_to_read(orm_model)

        assert isinstance(read_schema, AIExtractedDataRead)
        assert read_schema.id == 1
        assert read_schema.notification_id == "WORKFLOW-001"
        assert read_schema.keywords_ai == ["server", "hardware", "failure", "raid"]
        assert read_schema.extracted_at == now
