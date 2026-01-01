"""
Analytics service for MTBF and Pareto analysis.
"""

from datetime import date, datetime
from typing import Dict, List, Optional, Any
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
        rolling_days: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[Dict]:
        """
        Calculate Mean Time Between Failures (MTBF).

        Args:
            start_date: Start date for analysis
            end_date: End date for analysis
            equipment_id: Filter by equipment ID
            component: Filter by component
            rolling_days: Rolling average window in days
            limit: Maximum number of results to return

        Returns:
            List of MTBF calculations
        """
        # Build WHERE clause
        conditions = []
        if start_date:
            conditions.append(f"nt.noti_date >= '{start_date}'")
        if end_date:
            conditions.append(f"nt.noti_date <= '{end_date}'")
        if equipment_id:
            conditions.append(f"nt.sys_eq_id = '{equipment_id}'")
        if component:
            conditions.append(f"aed.main_component_ai = '{component}'")

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        # Join condition for component filtering
        join_clause = (
            "JOIN ai_extracted_data aed ON nt.notification_id = aed.notification_id"
            if component
            else "LEFT JOIN ai_extracted_data aed ON nt.notification_id = aed.notification_id"
        )

        # MTBF calculation query with rolling averages if specified
        if rolling_days:
            # Rolling average calculation
            query = f"""
            WITH failure_events AS (
                SELECT 
                    nt.sys_eq_id as equipment_id,
                    nt.noti_date as failure_date,
                    LAG(nt.noti_date) OVER (PARTITION BY nt.sys_eq_id ORDER BY nt.noti_date) as prev_failure_date,
                    COALESCE(aed.main_component_ai, 'Unknown') as failed_component
                FROM notification_text nt
                {join_clause}
                WHERE {where_clause}
                ORDER BY nt.sys_eq_id, nt.noti_date
            ),
            time_between_failures AS (
                SELECT 
                    equipment_id,
                    failure_date,
                    prev_failure_date,
                    EXTRACT(EPOCH FROM (failure_date - prev_failure_date)) / 86400 as days_between,
                    failed_component
                FROM failure_events
                WHERE prev_failure_date IS NOT NULL
            ),
            rolling_averages AS (
                SELECT 
                    equipment_id,
                    failure_date,
                    days_between,
                    failed_component,
                    AVG(days_between) OVER (
                        PARTITION BY equipment_id 
                        ORDER BY failure_date 
                        ROWS BETWEEN {rolling_days - 1} PRECEDING AND CURRENT ROW
                    ) as rolling_avg_mtbf
                FROM time_between_failures
            )
            SELECT 
                equipment_id,
                failed_component,
                COUNT(*) as failure_count,
                AVG(days_between) as avg_mtbf_days,
                AVG(rolling_avg_mtbf) as overall_rolling_avg,
                MIN(days_between) as min_mtbf_days,
                MAX(days_between) as max_mtbf_days,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY days_between) as median_mtbf_days,
                MIN(failure_date) as first_failure_date,
                MAX(failure_date) as last_failure_date
            FROM rolling_averages
            GROUP BY equipment_id, failed_component
            ORDER BY avg_mtbf_days DESC
            """ + (f" LIMIT {limit}" if limit else "")
        else:
            # Standard MTBF calculation
            query = f"""
            WITH failure_events AS (
                SELECT 
                    nt.sys_eq_id as equipment_id,
                    nt.noti_date as failure_date,
                    LAG(nt.noti_date) OVER (PARTITION BY nt.sys_eq_id ORDER BY nt.noti_date) as prev_failure_date,
                    COALESCE(aed.main_component_ai, 'Unknown') as failed_component
                FROM notification_text nt
                {join_clause}
                WHERE {where_clause}
                ORDER BY nt.sys_eq_id, nt.noti_date
            ),
            time_between_failures AS (
                SELECT 
                    equipment_id,
                    failure_date,
                    prev_failure_date,
                    EXTRACT(EPOCH FROM (failure_date - prev_failure_date)) / 86400 as days_between,
                    failed_component
                FROM failure_events
                WHERE prev_failure_date IS NOT NULL
            )
            SELECT 
                equipment_id,
                failed_component,
                COUNT(*) as failure_count,
                AVG(days_between) as avg_mtbf_days,
                MIN(days_between) as min_mtbf_days,
                MAX(days_between) as max_mtbf_days,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY days_between) as median_mtbf_days,
                MIN(failure_date) as first_failure_date,
                MAX(failure_date) as last_failure_date
            FROM time_between_failures
            GROUP BY equipment_id, failed_component
            ORDER BY avg_mtbf_days DESC
            """ + (f" LIMIT {limit}" if limit else "")

        try:
            result = await self.db.execute(text(query))
            rows = result.fetchall()

            return [
                {
                    "equipment_id": row[0],
                    "failed_component": row[1],
                    "failure_count": row[2],
                    "avg_mtbf_days": float(row[3]) if row[3] else None,
                    "min_mtbf_days": float(row[4]) if row[4] else None,
                    "max_mtbf_days": float(row[5]) if row[5] else None,
                    "median_mtbf_days": float(row[6]) if row[6] else None,
                    "first_failure_date": None
                    if not row[7]
                    else row[7].isoformat()
                    if hasattr(row[7], "isoformat")
                    else str(row[7]),
                    "last_failure_date": None
                    if not row[8]
                    else row[8].isoformat()
                    if hasattr(row[8], "isoformat")
                    else str(row[8]),
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
                primary_symptom_ai as symptom,
                COUNT(*) as occurrence_count
            FROM ai_extracted_data
            WHERE {where_clause}
            GROUP BY primary_symptom_ai
            HAVING primary_symptom_ai IS NOT NULL AND primary_symptom_ai != ''
        ),
        total_counts AS (
            SELECT SUM(occurrence_count) as total_count
            FROM symptom_counts
        ),
        ranked_symptoms AS (
            SELECT
                sc.symptom,
                sc.occurrence_count,
                ROW_NUMBER() OVER (ORDER BY sc.occurrence_count DESC) as rank,
                ROUND(sc.occurrence_count * 100.0 / tc.total_count, 2) as percentage
            FROM symptom_counts sc
            CROSS JOIN total_counts tc
        )
        SELECT
            symptom,
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

    async def get_pareto_for_visualization(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 10,
    ) -> Dict[str, Any]:
        """
        Get Pareto analysis formatted for visualization (charts and graphs).

        Args:
            start_date: Start date for analysis
            end_date: End date for analysis
            limit: Number of top items to return

        Returns:
            Dict with data structured for various chart types
        """
        raw_data = await self.calculate_pareto(
            start_date=start_date, end_date=end_date, limit=limit
        )

        # Format for different chart types
        return {
            # For bar chart: component names and counts
            "bar_chart": {
                "labels": [item["symptom"] for item in raw_data],
                "data": [item["occurrence_count"] for item in raw_data],
                "title": "Top Failure Symptoms by Occurrence Count",
            },
            # For pie chart: component names and percentages
            "pie_chart": {
                "labels": [item["symptom"] for item in raw_data],
                "data": [item["percentage"] for item in raw_data],
                "title": "Failure Symptom Distribution",
            },
            # For cumulative Pareto chart
            "pareto_chart": {
                "labels": [item["symptom"] for item in raw_data],
                "occurrence_data": [item["occurrence_count"] for item in raw_data],
                "percentage_data": [item["percentage"] for item in raw_data],
                "cumulative_data": [item["cumulative_percentage"] for item in raw_data],
                "title": "Pareto Analysis: Top Failure Symptoms",
            },
            # Raw data with metadata
            "raw_data": raw_data,
            "chart_config": {
                "animate": True,
                "responsive": True,
                "plugins": {
                    "legend": {"position": "top"},
                    "tooltip": {
                        "callbacks": {
                            "label": lambda item: f"{item.label}: {item.raw} occurrences ({item.parsed}%)"
                        }
                    },
                },
            },
        }

    async def get_mtbf_for_visualization(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        equipment_id: Optional[str] = None,
        component: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Get MTBF analysis formatted for visualization (time series charts).

        Args:
            start_date: Start date for analysis
            end_date: End date for analysis
            equipment_id: Filter by equipment ID
            component: Filter by component
            limit: Maximum number of results to return

        Returns:
            Dict with data structured for time series charts
        """
        raw_data = await self.calculate_mtbf(
            start_date=start_date,
            end_date=end_date,
            equipment_id=equipment_id,
            component=component,
            limit=limit,
        )

        # Format for time series charts
        return {
            # For bar chart: equipment IDs and MTBF values
            "bar_chart": {
                "labels": [item["equipment_id"] for item in raw_data],
                "avg_mtbf_data": [item["avg_mtbf_days"] for item in raw_data],
                "median_mtbf_data": [item["median_mtbf_days"] for item in raw_data],
                "failure_counts": [item["failure_count"] for item in raw_data],
                "title": "MTBF by Equipment",
            },
            # Detailed data for tables
            "detailed_view": raw_data,
            # Chart configuration
            "chart_config": {
                "type": "bar",
                "options": {
                    "responsive": True,
                    "plugins": {
                        "legend": {"position": "top"},
                        "tooltip": {"mode": "index", "intersect": False},
                    },
                    "scales": {
                        "y": {
                            "beginAtZero": True,
                            "title": {"display": True, "text": "Days Between Failures"},
                        },
                        "y_count": {
                            "beginAtZero": True,
                            "position": "right",
                            "title": {"display": True, "text": "Failure Count"},
                            "grid": {"drawOnChartArea": False},
                        },
                    },
                },
            },
            "metadata": {
                "show_component_level": component is not None,
                "total_equipment_analyzed": len(
                    set(item["equipment_id"] for item in raw_data)
                ),
            },
        }

    async def get_analytics_dashboard_data(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Get comprehensive analytics data for dashboard.

        Args:
            start_date: Start date for analysis
            end_date: End date for analysis

        Returns:
            Dict with all analytics data for dashboard
        """
        # Get date range if not specified
        if not start_date or not end_date:
            date_range = await self.get_date_range()
            start_date = start_date or date_range.get("min_date")
            end_date = end_date or date_range.get("max_date")

        # Gather all analytics data
        mtbf_data = await self.get_mtbf_for_visualization(
            start_date=start_date, end_date=end_date, limit=15
        )

        pareto_data = await self.get_pareto_for_visualization(
            start_date=start_date, end_date=end_date, limit=10
        )

        # Get equipment health status
        health_query = """
        SELECT 
            equipment_id,
            health_status,
            health_color,
            last_failure_date,
            failure_count_last_90_days,
            avg_mtbf_days
        FROM vw_equipment_health_status
        ORDER BY 
            CASE health_status
                WHEN 'Critical' THEN 1
                WHEN 'Warning' THEN 2
                WHEN 'Monitor' THEN 3
                ELSE 4
            END
        LIMIT 20
        """

        try:
            result = await self.db.execute(text(health_query))
            health_rows = result.fetchall()

            health_data = [
                {
                    "equipment_id": row[0],
                    "health_status": row[1],
                    "health_color": row[2],
                    "last_failure_date": row[3].isoformat() if row[3] else None,
                    "failure_count_90_days": row[4],
                    "avg_mtbf_days": float(row[5]) if row[5] else None,
                }
                for row in health_rows
            ]
        except Exception as e:
            logger.error(f"Error getting equipment health: {e}")
            health_data = []

        return {
            "mtbf": mtbf_data,
            "pareto": pareto_data,
            "equipment_health": {
                "data": health_data,
                "chart_config": {
                    "type": "doughnut",
                    "data": {
                        "labels": ["Critical", "Warning", "Monitor", "Healthy"],
                        "datasets": [
                            {
                                "data": [
                                    len(
                                        [
                                            h
                                            for h in health_data
                                            if h["health_status"] == "Critical"
                                        ]
                                    ),
                                    len(
                                        [
                                            h
                                            for h in health_data
                                            if h["health_status"] == "Warning"
                                        ]
                                    ),
                                    len(
                                        [
                                            h
                                            for h in health_data
                                            if h["health_status"] == "Monitor"
                                        ]
                                    ),
                                    len(
                                        [
                                            h
                                            for h in health_data
                                            if h["health_status"] == "Healthy"
                                            or h["health_status"]
                                            == "No Failures Recorded"
                                        ]
                                    ),
                                ],
                                "backgroundColor": [
                                    "#ef4444",
                                    "#f97316",
                                    "#eab308",
                                    "#22c55e",
                                ],
                            }
                        ],
                    },
                    "options": {
                        "responsive": True,
                        "plugins": {"legend": {"position": "bottom"}},
                    },
                },
            },
            "date_range": {"start": start_date, "end": end_date},
        }

    async def refresh_materialized_views(self) -> Dict[str, Any]:
        """
        Refresh all analytics materialized views.

        Returns:
            Dict with refresh status and timestamp
        """
        refresh_queries = [
            "REFRESH MATERIALIZED VIEW CONCURRENTLY mv_daily_mtbf_trends",
            "REFRESH MATERIALIZED VIEW CONCURRENTLY mv_monthly_pareto_summary",
        ]

        results = {
            "success": True,
            "refreshed_views": [],
            "timestamp": datetime.now().isoformat(),
        }

        for query in refresh_queries:
            try:
                await self.db.execute(text(query))
                view_name = query.split()[-1]
                results["refreshed_views"].append(view_name)
                logger.info(f"Successfully refreshed materialized view: {view_name}")
            except Exception as e:
                logger.error(f"Error refreshing materialized view: {e}")
                results["success"] = False
                results["error"] = str(e)

        await self.db.commit()
        return results
