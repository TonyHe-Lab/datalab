"""
Analytics API endpoints for MTBF and Pareto analysis.
"""

from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.db.session import get_db
from src.backend.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/mtbf")
async def get_mtbf_analysis(
    start_date: Optional[date] = Query(None, description="Start date for analysis"),
    end_date: Optional[date] = Query(None, description="End date for analysis"),
    equipment_id: Optional[str] = Query(None, description="Filter by equipment ID"),
    component: Optional[str] = Query(None, description="Filter by component"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get MTBF (Mean Time Between Failures) analysis.

    Returns MTBF calculations for equipment with optional filtering.
    """
    try:
        service = AnalyticsService(db)
        results = await service.calculate_mtbf(
            start_date=start_date,
            end_date=end_date,
            equipment_id=equipment_id,
            component=component,
        )

        # Get date range for context
        date_range = await service.get_date_range()

        return {
            "success": True,
            "data": results,
            "metadata": {
                "start_date": start_date,
                "end_date": end_date,
                "equipment_id": equipment_id,
                "component": component,
                "available_date_range": date_range,
                "total_records": len(results),
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating MTBF: {str(e)}")


@router.get("/pareto")
async def get_pareto_analysis(
    start_date: Optional[date] = Query(None, description="Start date for analysis"),
    end_date: Optional[date] = Query(None, description="End date for analysis"),
    limit: int = Query(10, ge=1, le=50, description="Number of top items to return"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get Pareto analysis for top故障部件.

    Returns the most frequent故障部件 with occurrence counts and percentages.
    """
    try:
        service = AnalyticsService(db)
        results = await service.calculate_pareto(
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )

        # Get date range for context
        date_range = await service.get_date_range()

        return {
            "success": True,
            "data": results,
            "metadata": {
                "start_date": start_date,
                "end_date": end_date,
                "limit": limit,
                "available_date_range": date_range,
                "total_records": len(results),
            },
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error calculating Pareto analysis: {str(e)}"
        )


@router.get("/equipment")
async def get_equipment_list(
    db: AsyncSession = Depends(get_db),
):
    """Get list of available equipment for filtering."""
    try:
        service = AnalyticsService(db)
        equipment_list = await service.get_equipment_list()

        return {
            "success": True,
            "data": equipment_list,
            "metadata": {
                "total_equipment": len(equipment_list),
            },
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error getting equipment list: {str(e)}"
        )


@router.get("/date-range")
async def get_available_date_range(
    db: AsyncSession = Depends(get_db),
):
    """Get available date range for analytics data."""
    try:
        service = AnalyticsService(db)
        date_range = await service.get_date_range()

        return {
            "success": True,
            "data": date_range,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error getting date range: {str(e)}"
        )


@router.get("/summary")
async def get_analytics_summary(
    db: AsyncSession = Depends(get_db),
):
    """Get analytics summary including available data ranges and equipment."""
    try:
        service = AnalyticsService(db)

        # Get all summary data in parallel
        date_range = await service.get_date_range()
        equipment_list = await service.get_equipment_list()

        # Get sample MTBF and Pareto data for summary
        mtbf_sample = await service.calculate_mtbf(limit=5)
        pareto_sample = await service.calculate_pareto(limit=5)

        return {
            "success": True,
            "data": {
                "date_range": date_range,
                "equipment_count": len(equipment_list),
                "sample_equipment": equipment_list[:5] if equipment_list else [],
                "mtbf_sample": mtbf_sample[:3] if mtbf_sample else [],
                "pareto_sample": pareto_sample[:3] if pareto_sample else [],
            },
            "metadata": {
                "endpoints_available": [
                    "/api/analytics/mtbf",
                    "/api/analytics/pareto",
                    "/api/analytics/equipment",
                    "/api/analytics/date-range",
                    "/api/analytics/summary",
                ],
            },
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error getting analytics summary: {str(e)}"
        )
