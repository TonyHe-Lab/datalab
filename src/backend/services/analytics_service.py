"""
Analytics service for MTBF and Pareto analysis.
"""

from datetime import date
from typing import Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service for analytics calculations and queries."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def calculate_mtbf(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        equipment_id: Optional[str] = None,
        component: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict]:
        """
        Calculate Mean Time Between Failures (MTBF).

        Args:
            start_date: Start date for analysis
            end_date: End date for analysis
            equipment_id: Filter by equipment ID
            component: Filter by component
            limit: Maximum number of results to return

        Returns:
            List of MTBF calculations
        """
        # Build WHERE clause
        conditions = []
        if start_date:
            conditions.append(f"noti_date >= '{start_date}'")
        if end_date:
            conditions.append(f"noti_date <= '{end_date}'")
        if equipment_id:
            conditions.append(f"sys_eq_id = '{equipment_id}'")

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        # Simplified MTBF calculation query
        # In production, this would be more sophisticated
        query = f"""
        WITH failure_events AS (
            SELECT 
                sys_eq_id as equipment_id,
                noti_date as failure_date,
                LAG(noti_date) OVER (PARTITION BY sys_eq_id ORDER BY noti_date) as prev_failure_date
            FROM notification_text
            WHERE {where_clause}
            ORDER BY sys_eq_id, noti_date
        ),
        time_between_failures AS (
            SELECT 
                equipment_id,
                failure_date,
                prev_failure_date,
                EXTRACT(EPOCH FROM (failure_date - prev_failure_date)) / 86400 as days_between
            FROM failure_events
            WHERE prev_failure_date IS NOT NULL
        )
        SELECT 
            equipment_id,
            COUNT(*) as failure_count,
            AVG(days_between) as avg_mtbf_days,
            MIN(days_between) as min_mtbf_days,
            MAX(days_between) as max_mtbf_days,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY days_between) as median_mtbf_days
        FROM time_between_failures
        GROUP BY equipment_id
        ORDER BY avg_mtbf_days DESC
        """ + (f" LIMIT {limit}" if limit else "")

        try:
            result = await self.db.execute(text(query))
            rows = result.fetchall()

            return [
                {
                    "equipment_id": row[0],
                    "failure_count": row[1],
                    "avg_mtbf_days": float(row[2]) if row[2] else None,
                    "min_mtbf_days": float(row[3]) if row[3] else None,
                    "max_mtbf_days": float(row[4]) if row[4] else None,
                    "median_mtbf_days": float(row[5]) if row[5] else None,
                }
                for row in rows
            ]
        except Exception as e:
            logger.error(f"Error calculating MTBF: {e}")
            raise

    async def calculate_pareto(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 10,
    ) -> List[Dict]:
        """
        Calculate Pareto analysis for top故障部件.

        Args:
            start_date: Start date for analysis
            end_date: End date for analysis
            limit: Number of top items to return

        Returns:
            List of Pareto analysis results
        """
        # Build WHERE clause
        conditions = []
        if start_date:
            conditions.append(f"noti_date >= '{start_date}'")
        if end_date:
            conditions.append(f"noti_date <= '{end_date}'")

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        # Pareto analysis query
        query = f"""
        WITH symptom_counts AS (
            SELECT 
                symptom_ai,
                COUNT(*) as occurrence_count
            FROM ai_extracted_data
            WHERE {where_clause}
            GROUP BY symptom_ai
            HAVING symptom_ai IS NOT NULL AND symptom_ai != ''
        ),
        total_counts AS (
            SELECT SUM(occurrence_count) as total_count
            FROM symptom_counts
        ),
        ranked_symptoms AS (
            SELECT 
                sc.symptom_ai,
                sc.occurrence_count,
                ROW_NUMBER() OVER (ORDER BY sc.occurrence_count DESC) as rank,
                ROUND(sc.occurrence_count * 100.0 / tc.total_count, 2) as percentage
            FROM symptom_counts sc
            CROSS JOIN total_counts tc
        )
        SELECT 
            symptom_ai,
            occurrence_count,
            percentage,
            rank
        FROM ranked_symptoms
        WHERE rank <= {limit}
        ORDER BY rank
        """

        try:
            result = await self.db.execute(text(query))
            rows = result.fetchall()

            # Calculate cumulative percentage
            results = []
            cumulative_percentage = 0.0

            for row in rows:
                percentage = float(row[2]) if row[2] else 0.0
                cumulative_percentage += percentage

                results.append(
                    {
                        "symptom": row[0],
                        "occurrence_count": row[1],
                        "percentage": percentage,
                        "cumulative_percentage": round(cumulative_percentage, 2),
                        "rank": row[3],
                    }
                )

            return results
        except Exception as e:
            logger.error(f"Error calculating Pareto analysis: {e}")
            raise

    async def get_equipment_list(self) -> List[str]:
        """Get list of unique equipment IDs."""
        query = """
        SELECT DISTINCT sys_eq_id
        FROM notification_text
        WHERE sys_eq_id IS NOT NULL
        ORDER BY sys_eq_id
        """

        try:
            result = await self.db.execute(text(query))
            rows = result.fetchall()
            return [row[0] for row in rows if row[0]]
        except Exception as e:
            logger.error(f"Error getting equipment list: {e}")
            return []

    async def get_date_range(self) -> Dict[str, Optional[date]]:
        """Get available date range for analytics."""
        query = """
        SELECT 
            MIN(noti_date) as min_date,
            MAX(noti_date) as max_date
        FROM notification_text
        """

        try:
            result = await self.db.execute(text(query))
            row = result.fetchone()

            return {
                "min_date": row[0] if row and row[0] else None,
                "max_date": row[1] if row and row[1] else None,
            }
        except Exception as e:
            logger.error(f"Error getting date range: {e}")
            return {"min_date": None, "max_date": None}
