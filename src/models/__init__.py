"""
Models package for the datalab project.

This package contains:
1. Pydantic schemas for data validation (schemas.py)
2. SQLAlchemy ORM models for database operations (entities.py)
3. Type definitions and exports
"""

from .schemas import *
from .entities import *

# Re-export commonly used items for convenience
__all__ = [
    # From schemas
    'IssueType',
    'MaintenanceLogBase', 'MaintenanceLogCreate', 'MaintenanceLogRead',
    'ResolutionStep', 'ResolutionStepsType',
    'AIExtractedDataBase', 'AIExtractedDataCreate', 'AIExtractedDataRead',
    'AIProcessingRequest', 'AIProcessingResponse',
    'SearchRequest', 'SearchResult', 'SearchResponse',
    'PaginationParams', 'PaginatedResponse', 'ErrorResponse',
    
    # From entities
    'Base',
    'MaintenanceLog',
    'AIExtractedData',
    'SemanticEmbedding',
    'ETLMetadata',
]

# Version
__version__ = '1.0.0'

# Import transformations
from .transformations import *

# Add transformation exports
__all__ += [
    # Transformation utilities
    'maintenance_log_create_to_orm',
    'maintenance_log_orm_to_read',
    'normalize_maintenance_log_data',
    'ai_extracted_data_create_to_orm',
    'ai_extracted_data_orm_to_read',
    'normalize_ai_extracted_data',
    'serialize_for_api',
    'deserialize_from_api',
    'convert_resolution_steps',
]
