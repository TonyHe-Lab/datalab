"""
Data transformation utilities for converting between different schema types.

This module provides helper functions for:
1. Converting between Pydantic schemas and SQLAlchemy models
2. Data cleaning and normalization
3. Type conversion and serialization
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Union
import json
from ..schemas import (
    MaintenanceLogCreate,
    MaintenanceLogRead,
    AIExtractedDataCreate,
    AIExtractedDataRead,
    ResolutionStep,
    ResolutionStepsType,
)
from ..entities import MaintenanceLog, AIExtractedData


# ============================================================================
# Maintenance Log Transformations
# ============================================================================


def maintenance_log_create_to_orm(
    schema: MaintenanceLogCreate, existing_log: Optional[MaintenanceLog] = None
) -> MaintenanceLog:
    """
    Convert MaintenanceLogCreate schema to SQLAlchemy ORM model.

    Args:
        schema: The Pydantic schema to convert
        existing_log: Optional existing ORM model to update

    Returns:
        SQLAlchemy MaintenanceLog model
    """
    if existing_log:
        # Update existing model
        for field, value in schema.model_dump(exclude_unset=True).items():
            setattr(existing_log, field, value)
        return existing_log
    else:
        # Create new model
        return MaintenanceLog(**schema.model_dump())


def maintenance_log_orm_to_read(orm_model: MaintenanceLog) -> MaintenanceLogRead:
    """
    Convert SQLAlchemy MaintenanceLog model to MaintenanceLogRead schema.

    Args:
        orm_model: The SQLAlchemy model to convert

    Returns:
        MaintenanceLogRead schema
    """
    return MaintenanceLogRead.model_validate(orm_model)


def normalize_maintenance_log_data(
    data: Dict[str, Any], issue_type_mapping: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Normalize maintenance log data from various sources.

    Args:
        data: Raw data dictionary
        issue_type_mapping: Optional mapping for issue type normalization

    Returns:
        Normalized data dictionary
    """
    normalized = data.copy()

    # Normalize timestamp fields
    timestamp_fields = [
        "noti_date",
        "noti_assigned_date",
        "noti_closed_date",
    ]

    for field in timestamp_fields:
        if field in normalized and normalized[field]:
            # Handle various timestamp formats
            if isinstance(normalized[field], str):
                # Try to parse string timestamp
                try:
                    # Remove timezone info for simplicity
                    normalized[field] = normalized[field].replace("Z", "+00:00")
                except:
                    pass

    # Normalize issue type - map notification_issue_type to noti_issue_type
    if (
        "notification_issue_type" in normalized
        and normalized["notification_issue_type"]
    ):
        issue_type = str(normalized["notification_issue_type"]).lower().strip()

        # Apply custom mapping if provided
        if issue_type_mapping and issue_type in issue_type_mapping:
            normalized["noti_issue_type"] = issue_type_mapping[issue_type]
        else:
            # Default normalization
            if "hardware" in issue_type or "hw" in issue_type:
                normalized["noti_issue_type"] = "hardware"
            elif "software" in issue_type or "sw" in issue_type:
                normalized["noti_issue_type"] = "software"
            elif "network" in issue_type or "net" in issue_type:
                normalized["noti_issue_type"] = "network"
            elif "config" in issue_type:
                normalized["noti_issue_type"] = "configuration"
            else:
                normalized["noti_issue_type"] = "unknown"

        # Remove the original field to avoid confusion
        del normalized["notification_issue_type"]

    # Clean text fields
    text_fields = ["noti_medium_text", "noti_text"]
    for field in text_fields:
        if field in normalized and normalized[field]:
            # Remove extra whitespace
            normalized[field] = " ".join(str(normalized[field]).split())

    return normalized


# ============================================================================
# AI-Extracted Data Transformations
# ============================================================================


def ai_extracted_data_create_to_orm(
    schema: AIExtractedDataCreate, existing_data: Optional[AIExtractedData] = None
) -> AIExtractedData:
    """
    Convert AIExtractedDataCreate schema to SQLAlchemy ORM model.

    Args:
        schema: The Pydantic schema to convert
        existing_data: Optional existing ORM model to update

    Returns:
        SQLAlchemy AIExtractedData model
    """
    data = schema.model_dump(exclude_unset=True)

    # Remove resolution_steps field as it's not in database
    data.pop("resolution_steps", None)

    # Handle JSON fields
    if "keywords_ai" in data and data["keywords_ai"] is not None:
        if isinstance(data["keywords_ai"], list):
            data["keywords_ai"] = json.dumps(data["keywords_ai"])

    # Handle TEXT fields that might be lists in schema
    text_list_fields = ["components_ai", "processes_ai"]
    for field in text_list_fields:
        if field in data and data[field] is not None:
            if isinstance(data[field], list):
                # Convert list to comma-separated string for TEXT field
                data[field] = ", ".join(data[field])

    if existing_data:
        # Update existing model
        for field, value in data.items():
            setattr(existing_data, field, value)
        return existing_data
    else:
        # Create new model
        return AIExtractedData(**data)


def ai_extracted_data_orm_to_read(orm_model: AIExtractedData) -> AIExtractedDataRead:
    """
    Convert SQLAlchemy AIExtractedData model to AIExtractedDataRead schema.

    Args:
        orm_model: The SQLAlchemy model to convert

    Returns:
        AIExtractedDataRead schema
    """
    data = {}

    # Copy all attributes
    for column in orm_model.__table__.columns:
        column_name = column.name
        if hasattr(orm_model, column_name):
            value = getattr(orm_model, column_name)

            # Handle JSON fields
            if column_name == "keywords_ai":
                if value is not None:
                    try:
                        data[column_name] = json.loads(value)
                    except:
                        data[column_name] = value
                else:
                    data[column_name] = None
            # Handle TEXT fields that might be comma-separated lists
            elif column_name in ["components_ai", "processes_ai"]:
                if value is not None:
                    # Try to parse as JSON first, then as comma-separated list
                    try:
                        data[column_name] = json.loads(value)
                    except:
                        # If not JSON, treat as comma-separated list
                        if isinstance(value, str):
                            data[column_name] = [
                                item.strip()
                                for item in value.split(",")
                                if item.strip()
                            ]
                        else:
                            data[column_name] = value
                else:
                    data[column_name] = None
            else:
                data[column_name] = value

    return AIExtractedDataRead.model_validate(data)


def normalize_ai_extracted_data(
    data: Dict[str, Any], min_confidence: float = 0.0
) -> Dict[str, Any]:
    """
    Normalize AI-extracted data.

    Args:
        data: Raw AI-extracted data
        min_confidence: Minimum confidence score to include

    Returns:
        Normalized data
    """
    normalized = data.copy()

    # Ensure confidence score is within bounds
    if "confidence_score_ai" in normalized:
        confidence = normalized["confidence_score_ai"]
        if confidence is not None:
            # Clamp to [0, 1]
            confidence = max(0.0, min(1.0, float(confidence)))
            normalized["confidence_score_ai"] = confidence

            # Filter low-confidence data
            if confidence < min_confidence:
                # Clear extracted fields but keep metadata
                fields_to_clear = [
                    "keywords_ai",
                    "primary_symptom_ai",
                    "root_cause_ai",
                    "summary_ai",
                    "solution_ai",
                    "solution_type_ai",
                    "components_ai",
                    "processes_ai",
                    "main_component_ai",
                    "main_process_ai",
                    "resolution_steps",
                ]
                for field in fields_to_clear:
                    if field in normalized:
                        normalized[field] = None

    # Normalize list fields
    list_fields = ["keywords_ai", "components_ai", "processes_ai"]
    for field in list_fields:
        if field in normalized and normalized[field] is not None:
            if isinstance(normalized[field], str):
                try:
                    normalized[field] = json.loads(normalized[field])
                except:
                    # If not valid JSON, treat as comma-separated list
                    normalized[field] = [
                        item.strip()
                        for item in normalized[field].split(",")
                        if item.strip()
                    ]
            elif not isinstance(normalized[field], list):
                normalized[field] = [normalized[field]]

    # Clean text fields
    text_fields = [
        "primary_symptom_ai",
        "root_cause_ai",
        "summary_ai",
        "solution_ai",
        "solution_type_ai",
        "main_component_ai",
        "main_process_ai",
    ]
    for field in text_fields:
        if field in normalized and normalized[field]:
            # Remove extra whitespace and normalize line endings
            text = str(normalized[field])
            text = " ".join(text.split())
            normalized[field] = text

    return normalized


# ============================================================================
# Serialization Utilities
# ============================================================================


def serialize_for_api(
    data: Any, include: Optional[List[str]] = None, exclude: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Serialize data for API responses.

    Args:
        data: Data to serialize (Pydantic model or dict)
        include: Fields to include
        exclude: Fields to exclude

    Returns:
        Serialized dictionary
    """
    if hasattr(data, "model_dump"):
        # Pydantic model
        return data.model_dump(include=include, exclude=exclude)
    elif hasattr(data, "__dict__"):
        # Object with __dict__
        result = data.__dict__.copy()
        # Remove SQLAlchemy internal attributes
        result.pop("_sa_instance_state", None)
        return result
    elif isinstance(data, dict):
        # Already a dictionary
        return data.copy()
    else:
        # Other types
        return {"value": data}


def deserialize_from_api(data: Dict[str, Any], schema_class: Any) -> Any:
    """
    Deserialize data from API request.

    Args:
        data: Data from API request
        schema_class: Pydantic schema class to validate against

    Returns:
        Validated schema instance
    """
    return schema_class.model_validate(data)


# ============================================================================
# Type Conversion Utilities
# ============================================================================


def convert_resolution_steps(
    steps: ResolutionStepsType, target_format: str = "json"
) -> Union[str, List[Dict[str, Any]]]:
    """
    Convert resolution steps between different formats.

    Args:
        steps: Resolution steps in any supported format
        target_format: Target format ('json', 'list', 'text')

    Returns:
        Converted resolution steps
    """
    if steps is None:
        return None

    if target_format == "json":
        if isinstance(steps, str):
            return steps
        elif isinstance(steps, list):
            return json.dumps(
                [
                    step.model_dump() if isinstance(step, ResolutionStep) else step
                    for step in steps
                ]
            )

    elif target_format == "list":
        if isinstance(steps, str):
            try:
                return json.loads(steps)
            except:
                # If not JSON, treat as single text step
                return [{"description": steps}]
        elif isinstance(steps, list):
            return [
                step.model_dump() if isinstance(step, ResolutionStep) else step
                for step in steps
            ]

    elif target_format == "text":
        if isinstance(steps, str):
            return steps
        elif isinstance(steps, list):
            text_steps = []
            for i, step in enumerate(steps, 1):
                if isinstance(step, ResolutionStep):
                    desc = step.description
                    if step.duration_minutes:
                        desc += f" ({step.duration_minutes} min)"
                    if step.tools_required:
                        desc += f" [Tools: {', '.join(step.tools_required)}]"
                    text_steps.append(f"{i}. {desc}")
                elif isinstance(step, dict):
                    desc = step.get("description", "")
                    if "duration_minutes" in step:
                        desc += f" ({step['duration_minutes']} min)"
                    if "tools_required" in step:
                        desc += f" [Tools: {', '.join(step['tools_required'])}]"
                    text_steps.append(f"{i}. {desc}")
                else:
                    text_steps.append(f"{i}. {step}")
            return "\n".join(text_steps)

    return steps


# ============================================================================
# Export
# ============================================================================

__all__ = [
    # Maintenance Log Transformations
    "maintenance_log_create_to_orm",
    "maintenance_log_orm_to_read",
    "normalize_maintenance_log_data",
    # AI-Extracted Data Transformations
    "ai_extracted_data_create_to_orm",
    "ai_extracted_data_orm_to_read",
    "normalize_ai_extracted_data",
    # Serialization Utilities
    "serialize_for_api",
    "deserialize_from_api",
    # Type Conversion Utilities
    "convert_resolution_steps",
]
