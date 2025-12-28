"""
SQLAlchemy ORM models for database entities.

This module defines the database models that map to the tables defined in
db/init_schema.sql. These models support both sync and async operations.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Float,
    ForeignKey,
    UniqueConstraint,
    Index,
    JSON,
    Boolean,
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy import JSON
from sqlalchemy.sql import func

# Base class for all models
Base = declarative_base()


# ============================================================================
# Maintenance Log Model (notification_text table)
# ============================================================================


class MaintenanceLog(Base):
    """Model for notification_text table (raw maintenance logs from Snowflake)."""

    __tablename__ = "notification_text"

    # Primary key
    notification_id = Column(String, primary_key=True, nullable=False)

    # Timestamp fields
    noti_date = Column(DateTime(timezone=True), nullable=False)
    noti_assigned_date = Column(DateTime(timezone=True), nullable=True)
    noti_closed_date = Column(DateTime(timezone=True), nullable=True)

    # Classification and identification fields
    noti_category_id = Column(String, nullable=True)
    sys_eq_id = Column(String, nullable=True)
    noti_country_id = Column(String, nullable=True)
    sys_fl_id = Column(String, nullable=True)
    sys_mat_id = Column(String, nullable=True)
    sys_serial_id = Column(String, nullable=True)

    # Trend codes
    noti_trendcode_l1 = Column(String, nullable=True)
    noti_trendcode_l2 = Column(String, nullable=True)
    noti_trendcode_l3 = Column(String, nullable=True)

    # Issue type
    noti_issue_type = Column(String, nullable=True)

    # Text content
    noti_medium_text = Column(Text, nullable=True)
    noti_text = Column(Text, nullable=False)

    # System fields
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    ai_extracted_data = relationship(
        "AIExtractedData",
        back_populates="maintenance_log",
        cascade="all, delete-orphan",
    )
    semantic_embedding = relationship(
        "SemanticEmbedding",
        back_populates="maintenance_log",
        uselist=False,
        cascade="all, delete-orphan",
    )

    # Indexes
    __table_args__ = (
        Index("ix_notification_text_date", "noti_date"),
        Index("ix_notification_text_issue_type", "noti_issue_type"),
        Index("ix_notification_text_created_at", "created_at"),
    )

    def __repr__(self):
        return f"<MaintenanceLog(notification_id='{self.notification_id}', date={self.noti_date})>"


# ============================================================================
# AI-Extracted Data Model (ai_extracted_data table)
# ============================================================================


class AIExtractedData(Base):
    """Model for ai_extracted_data table (structured AI output)."""

    __tablename__ = "ai_extracted_data"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign key
    notification_id = Column(
        String,
        ForeignKey("notification_text.notification_id", ondelete="CASCADE"),
        nullable=False,
    )

    # AI extraction fields
    keywords_ai = Column(
        JSON, nullable=True
    )  # List of keywords (JSON for SQLite, JSONB for PostgreSQL)
    primary_symptom_ai = Column(Text, nullable=True)
    root_cause_ai = Column(Text, nullable=True)
    summary_ai = Column(Text, nullable=True)
    solution_ai = Column(Text, nullable=True)
    solution_type_ai = Column(String, nullable=True)
    components_ai = Column(Text, nullable=True)  # Related components (TEXT in database)
    processes_ai = Column(Text, nullable=True)  # Related processes (TEXT in database)
    main_component_ai = Column(String, nullable=True)
    main_process_ai = Column(String, nullable=True)

    # System fields
    confidence_score_ai = Column(Float, nullable=True)
    extracted_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    model_version = Column(String, nullable=True)

    # Relationships
    maintenance_log = relationship("MaintenanceLog", back_populates="ai_extracted_data")

    # Indexes
    __table_args__ = (
        Index("ix_ai_extracted_data_notification_id", "notification_id"),
        Index("ix_ai_extracted_data_extracted_at", "extracted_at"),
        Index("ix_ai_extracted_data_confidence", "confidence_score_ai"),
    )

    def __repr__(self):
        return (
            f"<AIExtractedData(id={self.id}, notification_id='{self.notification_id}')>"
        )


# ============================================================================
# Semantic Embedding Model (semantic_embeddings table)
# ============================================================================


class SemanticEmbedding(Base):
    """Model for semantic_embeddings table (vector embeddings for semantic search)."""

    __tablename__ = "semantic_embeddings"

    # Primary key (also foreign key)
    notification_id = Column(
        String,
        ForeignKey("notification_text.notification_id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )

    # Text content
    source_text_ai = Column(Text, nullable=False)

    # Vector embedding (using pgvector if available, otherwise bytea)
    # Note: We'll handle the vector/bytea column dynamically based on extension availability
    vector = Column(
        String, nullable=True
    )  # Will be dynamically set to vector(1536) if extension available
    vector_bytea = Column(String, nullable=True)  # Fallback: BYTEA

    # System field
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    maintenance_log = relationship(
        "MaintenanceLog", back_populates="semantic_embedding"
    )

    def __repr__(self):
        return f"<SemanticEmbedding(notification_id='{self.notification_id}')>"


# ============================================================================
# ETL Metadata Model (etl_metadata table)
# ============================================================================


class ETLMetadata(Base):
    """Model for etl_metadata table (ETL process tracking)."""

    __tablename__ = "etl_metadata"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Table information
    table_name = Column(String, nullable=False, unique=True)

    # Sync information
    last_sync_timestamp = Column(DateTime(timezone=True), nullable=True)
    rows_processed = Column(Integer, default=0, nullable=False)
    sync_status = Column(
        String, nullable=True
    )  # pending, in_progress, completed, failed
    error_message = Column(Text, nullable=True)

    # System fields
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Indexes
    __table_args__ = (
        Index("ix_etl_metadata_table_name", "table_name"),
        Index("ix_etl_metadata_last_sync", "last_sync_timestamp"),
        Index("ix_etl_metadata_sync_status", "sync_status"),
    )

    def __repr__(self):
        return f"<ETLMetadata(id={self.id}, table_name='{self.table_name}', status='{self.sync_status}')>"


# ============================================================================
# Export
# ============================================================================

__all__ = [
    "Base",
    "MaintenanceLog",
    "AIExtractedData",
    "SemanticEmbedding",
    "ETLMetadata",
]
