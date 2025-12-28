"""
Pydantic schemas for data validation and serialization.

This module defines all Pydantic schemas used throughout the system:
1. Maintenance log schemas (raw data from Snowflake)
2. AI-extracted data schemas (structured AI output)
3. API request/response schemas
4. Data transformation schemas
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, validator, ConfigDict
from enum import Enum


# ============================================================================
# Enums and Type Definitions
# ============================================================================


class IssueType(str, Enum):
    """Issue type classification for maintenance logs."""

    HARDWARE = "hardware"
    SOFTWARE = "software"
    NETWORK = "network"
    CONFIGURATION = "configuration"
    UNKNOWN = "unknown"


# ============================================================================
# Maintenance Log Schemas (AC-1)
# ============================================================================


class MaintenanceLogBase(BaseModel):
    """Base schema for maintenance log data from Snowflake."""

    notification_id: str = Field(
        ..., description="Unique notification ID from Snowflake"
    )
    noti_date: datetime = Field(..., description="Notification/creation date")
    noti_assigned_date: Optional[datetime] = Field(None, description="Assignment date")
    noti_closed_date: Optional[datetime] = Field(None, description="Closure date")

    # Classification and identification fields
    noti_category_id: Optional[str] = Field(
        None, description="Notification category ID"
    )
    sys_eq_id: Optional[str] = Field(None, description="Equipment ID")
    noti_country_id: Optional[str] = Field(None, description="Country code")
    sys_fl_id: Optional[str] = Field(None, description="Facility location ID")
    sys_mat_id: Optional[str] = Field(None, description="Material number")
    sys_serial_id: Optional[str] = Field(None, description="Serial number")

    # Trend codes
    noti_trendcode_l1: Optional[str] = Field(None, description="Trend code level 1")
    noti_trendcode_l2: Optional[str] = Field(None, description="Trend code level 2")
    noti_trendcode_l3: Optional[str] = Field(None, description="Trend code level 3")

    # Issue type
    noti_issue_type: Optional[IssueType] = Field(
        None, description="Issue type classification"
    )

    # Text content
    noti_medium_text: Optional[str] = Field(None, description="Short warranty text")
    noti_text: str = Field(
        ..., min_length=1, description="Long maintenance log text for AI analysis"
    )

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    @validator("noti_issue_type", pre=True)
    def validate_issue_type(cls, v):
        """Validate and normalize issue type."""
        if v is None:
            return None
        if isinstance(v, IssueType):
            return v
        try:
            return IssueType(v.lower())
        except ValueError:
            # Try to map common variations
            v_lower = v.lower()
            if "hardware" in v_lower or "hw" in v_lower:
                return IssueType.HARDWARE
            elif "software" in v_lower or "sw" in v_lower:
                return IssueType.SOFTWARE
            elif "network" in v_lower or "net" in v_lower:
                return IssueType.NETWORK
            elif "config" in v_lower:
                return IssueType.CONFIGURATION
            else:
                return IssueType.UNKNOWN


class MaintenanceLogCreate(MaintenanceLogBase):
    """Schema for creating new maintenance log records."""

    pass


class MaintenanceLogRead(MaintenanceLogBase):
    """Schema for reading maintenance log records (includes system fields)."""

    created_at: datetime = Field(..., description="Record creation timestamp")
    updated_at: datetime = Field(..., description="Record update timestamp")

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# AI-Extracted Data Schemas (AC-2)
# ============================================================================


class ResolutionStep(BaseModel):
    """Individual resolution step in structured format."""

    step_number: int = Field(..., ge=1, description="Step number")
    description: str = Field(..., description="Step description")
    duration_minutes: Optional[int] = Field(
        None, ge=0, description="Duration in minutes"
    )
    tools_required: Optional[List[str]] = Field(None, description="Required tools")


ResolutionStepsType = Union[str, List[ResolutionStep], List[Dict[str, Any]]]


class AIExtractedDataBase(BaseModel):
    """Base schema for AI-extracted structured data."""

    notification_id: str = Field(..., description="Reference to notification")

    # Core AI extraction dimensions
    keywords_ai: Optional[List[str]] = Field(None, description="Extracted keywords")
    primary_symptom_ai: Optional[str] = Field(None, description="Primary symptom")
    root_cause_ai: Optional[str] = Field(None, description="Root cause")
    summary_ai: Optional[str] = Field(None, description="Summary")
    solution_ai: Optional[str] = Field(None, description="Solution")
    solution_type_ai: Optional[str] = Field(None, description="Solution type")
    components_ai: Optional[List[str]] = Field(None, description="Related components")
    processes_ai: Optional[List[str]] = Field(None, description="Related processes")
    main_component_ai: Optional[str] = Field(None, description="Main component")
    main_process_ai: Optional[str] = Field(None, description="Main process")

    # Resolution steps (flexible format)
    resolution_steps: Optional[ResolutionStepsType] = Field(
        None, description="Resolution steps"
    )

    # System fields
    confidence_score_ai: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="AI confidence score"
    )
    model_version: Optional[str] = Field(None, description="AI model version")

    model_config = ConfigDict(from_attributes=True)

    @validator("resolution_steps", pre=True)
    def validate_resolution_steps(cls, v):
        """Validate resolution steps format."""
        if v is None:
            return None
        if isinstance(v, str):
            return v
        if isinstance(v, list):
            # Try to parse as list of ResolutionStep objects
            try:
                return [
                    ResolutionStep(**item) if isinstance(item, dict) else item
                    for item in v
                ]
            except Exception:
                # Return as-is if parsing fails
                return v
        return v


class AIExtractedDataCreate(AIExtractedDataBase):
    """Schema for creating new AI-extracted data records."""

    pass


class AIExtractedDataRead(AIExtractedDataBase):
    """Schema for reading AI-extracted data records (includes system fields)."""

    id: int = Field(..., description="Primary key")
    extracted_at: datetime = Field(..., description="Extraction timestamp")

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# API Request/Response Schemas (AC-4)
# ============================================================================


class AIProcessingRequest(BaseModel):
    """Request schema for AI processing endpoint."""

    notification_id: str = Field(..., description="Notification ID to process")
    text: str = Field(..., description="Text to analyze")
    model_version: Optional[str] = Field(
        None, description="Specific model version to use"
    )


class AIProcessingResponse(BaseModel):
    """Response schema for AI processing endpoint."""

    success: bool = Field(..., description="Processing success status")
    data: Optional[AIExtractedDataRead] = Field(None, description="Extracted data")
    error: Optional[str] = Field(None, description="Error message if failed")
    processing_time_ms: Optional[int] = Field(
        None, ge=0, description="Processing time in milliseconds"
    )


class SearchRequest(BaseModel):
    """Request schema for semantic search."""

    query: str = Field(..., description="Search query text")
    limit: int = Field(10, ge=1, le=100, description="Maximum results to return")
    similarity_threshold: float = Field(
        0.7, ge=0.0, le=1.0, description="Minimum similarity score"
    )


class SearchResult(BaseModel):
    """Individual search result."""

    notification_id: str = Field(..., description="Notification ID")
    similarity_score: float = Field(..., ge=0.0, le=1.0, description="Similarity score")
    notification_text: str = Field(..., description="Original text")
    summary_ai: Optional[str] = Field(None, description="AI summary if available")


class SearchResponse(BaseModel):
    """Response schema for search endpoint."""

    results: List[SearchResult] = Field(..., description="Search results")
    total_results: int = Field(..., ge=0, description="Total matching results")
    query_time_ms: int = Field(
        ..., ge=0, description="Query execution time in milliseconds"
    )


class PaginationParams(BaseModel):
    """Pagination parameters for list endpoints."""

    page: int = Field(1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(20, ge=1, le=100, description="Items per page")


class PaginatedResponse(BaseModel):
    """Generic paginated response."""

    items: List[Any] = Field(..., description="Page items")
    total: int = Field(..., ge=0, description="Total items")
    page: int = Field(..., ge=1, description="Current page")
    page_size: int = Field(..., ge=1, description="Items per page")
    total_pages: int = Field(..., ge=0, description="Total pages")


class ErrorResponse(BaseModel):
    """Error response schema."""

    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    code: Optional[str] = Field(None, description="Error code")


# ============================================================================
# Export
# ============================================================================

__all__ = [
    # Enums
    "IssueType",
    # Maintenance Log Schemas
    "MaintenanceLogBase",
    "MaintenanceLogCreate",
    "MaintenanceLogRead",
    # AI-Extracted Data Schemas
    "ResolutionStep",
    "ResolutionStepsType",
    "AIExtractedDataBase",
    "AIExtractedDataCreate",
    "AIExtractedDataRead",
    # API Schemas
    "AIProcessingRequest",
    "AIProcessingResponse",
    "SearchRequest",
    "SearchResult",
    "SearchResponse",
    "PaginationParams",
    "PaginatedResponse",
    "ErrorResponse",
]
