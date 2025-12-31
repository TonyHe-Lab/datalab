"""
Database session management for async SQLAlchemy.
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from src.backend.core.config import settings

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_pre_ping=True,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Base class for models
Base = declarative_base()


async def get_db() -> AsyncSession:
    """Get database session dependency."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Initialize database connection and create tables if needed."""
    # Note: In production, use Alembic migrations instead
    async with engine.begin() as conn:
        # Create tables if they don't exist
        # For now, we'll just test the connection
        pass


async def test_connection():
    """Test database connection."""
    try:
        async with AsyncSessionLocal() as session:
            # Simple query to test connection
            result = await session.execute("SELECT 1")
            return result.scalar() == 1
    except Exception as e:
        print(f"Database connection error: {e}")
        return False
