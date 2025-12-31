"""
Configuration and fixtures for backend tests.
"""

import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Generator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from src.backend.core.config import settings

# Test database engine
test_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
)

# Test session factory
TestAsyncSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Base class for test models
Base = declarative_base()


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Fixture for providing a database session for tests.
    """
    async with TestAsyncSessionLocal() as session:
        yield session
        await session.rollback()


@pytest.fixture
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """
    Fixture for providing an event loop for async tests.
    """
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_notification_data() -> dict:
    """
    Fixture for sample notification data.
    """
    return {
        "noti_id": "TEST-001",
        "noti_date": "2025-12-31",
        "noti_text": "Equipment failure due to bearing wear",
        "sys_eq_id": "EQ-001",
        "noti_issue_type": "FAILURE",
        "noti_trendcode_l1": "MECHANICAL",
        "noti_trendcode_l2": "BEARING",
        "noti_trendcode_l3": "WEAR",
    }


@pytest.fixture
def sample_extracted_data() -> dict:
    """
    Fixture for sample AI extracted data.
    """
    return {
        "notification_id": "TEST-001",
        "symptom_ai": "Bearing wear detected",
        "root_cause": "Insufficient lubrication",
        "resolution_steps": [
            {"step": 1, "action": "Inspect bearing"},
            {"step": 2, "action": "Replace bearing"},
            {"step": 3, "action": "Reassemble and test"},
        ],
        "component": "Bearing",
        "confidence_score": 0.95,
    }
