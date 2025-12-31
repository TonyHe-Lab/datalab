"""
API metadata endpoints.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def api_info():
    """API information endpoint."""
    return {
        "name": "Medical Work Order Analysis API",
        "version": "1.0.0",
        "description": "API for medical work order analysis and analytics",
        "endpoints": {
            "health": "/api/health",
            "health_db": "/api/health/db",
            "docs": "/docs",
            "redoc": "/redoc",
        },
        "features": [
            "Health monitoring",
            "Database connectivity",
            "Analytics endpoints",
            "Interactive documentation",
        ],
    }


@router.get("/version")
async def version():
    """API version endpoint."""
    return {"version": "1.0.0", "api": "medical-work-order-analysis"}
