"""
Health check endpoints.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.db.session import get_db, test_connection

router = APIRouter()


@router.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {"status": "healthy", "service": "medical-work-order-analysis"}


@router.get("/health/db")
async def db_health_check(db: AsyncSession = Depends(get_db)):
    """Database health check endpoint."""
    is_connected = await test_connection()

    if is_connected:
        return {"status": "healthy", "database": "connected"}
    else:
        return {"status": "unhealthy", "database": "disconnected"}, 503
