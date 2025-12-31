# Analytics SQL Views Documentation

## Overview

This document describes the SQL views and materialized views that support the analytics functionality for monitoring equipment reliability and identifying recurring issues.

## View Architecture

### Regular Views

#### 1. `vw_equipment_failure_events`
**Purpose**: Provides cleaned, joined failure events for MTBF calculation.

**Columns**:
- `id`: Notification ID
- `equipment_id`: Equipment identifier (from `sys_eq_id`)
- `failure_date`: Date of the failure event
- `failure_symptom`: AI-extracted symptom description
- `failed_component`: AI-extracted component that failed
- `issue_type`: Type of issue/mechanical, electrical, etc.)
- `trend_category`: L1 trend code category

**Usage**: Base view for all MTBF calculations.

---

#### 2. `vw_mtbf_calculation_base`
**Purpose**: Calculates time between failures for each equipment.

**Columns**:
- `equipment_id`: Equipment identifier
- `failure_date`: Current failure date
- `prev_failure_date`: Previous failure date (using window function LAG)
- `failure_symptom`: Symptom for current failure
- `failed_component`: Component that failed
- `days_between_failures`: Time elapsed between consecutive failures (in days)

**Usage**: Intermediate view for MTBF statistics aggregation.

---

#### 3. `vw_mtbf_summary_equipment`
**Purpose**: Provides MTBF statistics for each equipment.

**Columns**:
- `equipment_id`: Equipment identifier
- `total_failures`: Total number of failures recorded
- `calculated_failures`: Number of failures used for MTBF calculations (≥2 failures)
- `avg_mtbf_days`: Average time between failures (in days)
- `min_mtbf_days`: Minimum time between failures
- `max_mtbf_days`: Maximum time between failures
- `median_mtbf_days`: Median time between failures (50th percentile)
- `stddev_mtbf_days`: Standard deviation of MTBF days
- `first_failure_date`: Date of first recorded failure
- `last_failure_date`: Date of last recorded failure

**Usage**: Equipment-level MTBF analysis and trending.

---

#### 4. `vw_mtbf_summary_component`
**Purpose**: Provides MTBF statistics for each component across all equipment.

**Columns**:
- `failed_component`: Component name
- `total_failures`: Total failures for this component
- `calculated_failures`: Number of failures used for calculations
- `avg_mtbf_days`: Average time between component failures
- `min_mtbf_days`: Minimum time between failures
- `max_mtbf_days`: Maximum time between failures
- `median_mtbf_days`: Median time between failures

**Usage**: Component reliability analysis across the fleet.

---

#### 5. `vw_symptom_frequency`
**Purpose**: Counts occurrences of each symptom for Pareto analysis.

**Columns**:
- `symptom`: AI-extracted symptom description
- `occurrence_count`: Number of times this symptom has occurred
- `affected_equipment_count`: Number of unique equipment affected by this symptom
- `first_occurrence_date`: Date of first occurrence
- `last_occurrence_date`: Date of most recent occurrence

**Usage**: Base view for Pareto analysis (identifying top failure modes).

---

#### 6. `vw_pareto_analysis`
**Purpose**: Provides complete Pareto analysis with cumulative percentages.

**Columns**:
- `symptom`: Symptom description
- `occurrence_count`: Number of occurrences
- `affected_equipment_count`: Unique equipment affected
- `first_occurrence_date`: First occurrence date
- `last_occurrence_date`: Last occurrence date
- `percentage_of_total`: Percentage of total failures
- `cumulative_percentage`: Cumulative percentage (for Pareto chart)
- `rank`: Rank by frequency (1 = most frequent)

**Usage**: Identifies top failure modes using the 80/20 rule.

---

#### 7. `vw_equipment_health_status`
**Purpose**: Provides current health status for each equipment.

**Columns**:
- `equipment_id`: Equipment identifier
- `last_failure_date`: Most recent failure date
- `failure_count_last_90_days`: Number of failures in last 90 days
- `avg_mtbf_days`: Overall average MTBF
- `health_status`: Health categorization (Critical/Warning/Monitor/Healthy)
- `health_color`: Color code for UI (red/orange/yellow/green)

**Health Status Logic**:
- **Critical**: Failure within last 7 days
- **Warning**: Failure within last 30 days
- **Monitor**: Failure within last 90 days
- **Healthy**: No failures in last 90 days

**Usage**: Dashboard health monitoring and prioritization.

---

### Materialized Views

#### 1. `mv_daily_mtbf_trends`
**Purpose**: Refreshed daily for performance optimization of MTBF trend analysis.

**Columns**:
- `analysis_date`: Date truncated to day
- `equipment_id`: Equipment identifier
- `daily_failures`: Number of failures on this day
- `daily_avg_mtbf`: Average MTBF for failures on this day

**Data Range**: Last 365 days of data

**Refresh Strategy**: Should be refreshed daily using `REFRESH MATERIALIZED VIEW CONCURRENTLY`

**Indexes**:
- `idx_mv_daily_mtbf_date`: On `analysis_date` column
- `idx_mv_daily_mtbf_equipment`: On `equipment_id` column

**Usage**: Time series analysis and MTBF trend visualization.

---

#### 2. `mv_monthly_pareto_summary`
**Purpose**: Refreshed monthly for performance optimization of Pareto trend analysis.

**Columns**:
- `analysis_month`: Date truncated to month
- `symptom`: AI-extracted symptom
- `monthly_occurrences`: Number of occurrences in the month
- `monthly_affected_equipment`: Unique equipment affected in the month

**Data Range**: Last 2 years of data

**Refresh Strategy**: Should be refreshed monthly using `REFRESH MATERIALIZED VIEW CONCURRENTLY`

**Indexes**:
- `idx_mv_monthly_pareto_month`: On `analysis_month` column
- `idx_mv_monthly_pareto_symptom`: On `symptom` column

**Usage**: Monthly Pareto trends and seasonal failure pattern analysis.

---

## Helper Functions

### `refresh_analytics_views()`
**Purpose**: Refresh all materialized views concurrently (without locking reads).

**Parameters**: None

**Returns**: `void`

**Usage**:
```sql
SELECT refresh_analytics_views();
```

Or via API:
```
POST /api/analytics/refresh-views
```

---

### `get_analytics_view_info()`
**Purpose**: Get metadata about all analytics views including row counts and last refresh times.

**Returns**: Table with columns:
- `view_name`: Name of the view
- `view_type`: 'materialized' or 'regular'
- `row_count`: Number of rows in the view
- `last_refresh`: Last refresh timestamp (for materialized views)

**Usage**:
```sql
SELECT * FROM get_analytics_view_info();
```

---

## Query Examples

### Get Top 10 Equipment by MTBF (Most Reliable)
```sql
SELECT 
    equipment_id,
    avg_mtbf_days,
    total_failures,
    last_failure_date
FROM vw_mtbf_summary_equipment
ORDER BY avg_mtbf_days DESC
LIMIT 10;
```

### Get Top 10 Failure Symptoms (Pareto Analysis)
```sql
SELECT 
    symptom,
    occurrence_count,
    percentage_of_total,
    cumulative_percentage,
    rank
FROM vw_pareto_analysis
WHERE rank <= 10
ORDER BY rank;
```

### Get Critical Health Equipment
```sql
SELECT 
    equipment_id,
    health_status,
    last_failure_date,
    failure_count_last_90_days
FROM vw_equipment_health_status
WHERE health_status = 'Critical'
ORDER BY last_failure_date DESC;
```

### Get MTBF Trends for Specific Equipment
```sql
SELECT 
    analysis_date,
    daily_failures,
    daily_avg_mtbf
FROM mv_daily_mtbf_trends
WHERE equipment_id = 'EQ-001'
ORDER BY analysis_date;
```

### Get Component MTBF Comparison
```sql
SELECT 
    failed_component,
    avg_mtbf_days,
    total_failures
FROM vw_mtbf_summary_component
ORDER BY avg_mtbf_days ASC
LIMIT 15;
```

---

## Performance Considerations

1. **Materialized Views**: Used for heavy aggregations that don't need real-time data
2. **Indexes**: Created on all materialized views for fast filtering
3. **Concurrent Refresh**: Materialized views use `CONCURRENTLY` to avoid blocking reads
4. **Data Windowing**: Materialized views limit data to relevant time ranges (1-2 years)
5. **Join Optimization**: Views join only necessary tables and filter early

---

## API Endpoint Mapping

| API Endpoint | Primary View(s) Used |
|-------------|---------------------|
| `GET /api/analytics/mtbf` | `vw_equipment_failure_events`, `vw_mtbf_summary_equipment` |
| `GET /api/analytics/pareto` | `vw_pareto_analysis` |
| `GET /api/analytics/dashboard` | All views aggregated |
| `POST /api/analytics/refresh-views` | All materialized views |

---

## Maintenance

### Refresh Schedule

Recommended refresh frequencies:
- **Daily**: `mv_daily_mtbf_trends` (at 2 AM UTC)
- **Weekly**: `mv_monthly_pareto_summary` (if high data volume)
- **Monthly**: `mv_monthly_pareto_summary` (standard)

### Monitoring

Monitor view refresh times and row counts:
```sql
SELECT * FROM get_analytics_view_info();
```

### Performance Tuning

If queries are slow, consider:
1. Increasing materialized view refresh frequency
2. Adding additional indexes on filter columns
3. Partitioning large tables by date
4. Adjusting data retention windows in materialized views

---

## Troubleshooting

### View Returns No Results
- Check if underlying tables have data: `SELECT COUNT(*) FROM notification_text;`
- Verify view exists: `SELECT * FROM information_schema.views WHERE table_name LIKE 'vw_%';`

### Materialized View is Stale
- Refresh manually: `REFRESH MATERIALIZED VIEW CONCURRENTLY mv_daily_mtbf_trends;`
- Check for concurrent locks that might prevent refresh

### Query Performance Issues
- Run `EXPLAIN ANALYZE` on slow queries
- Check if indexes are being used
- Consider increasing work_mem for complex aggregations

---

## Related Files

- SQL Definition: `src/backend/db/analytics_views.sql`
- Service Implementation: `src/backend/services/analytics_service.py`
- API Endpoints: `src/backend/api/analytics.py`
- API Tests: `tests/backend/api/test_analytics.py`
