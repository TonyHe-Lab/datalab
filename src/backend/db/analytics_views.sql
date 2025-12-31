-- Analytics SQL Views for Medical Work Order Analysis System
-- These views provide optimized queries for MTBF and Pareto analysis
-- ============================================================================
-- MTBF (Mean Time Between Failures) Views
-- ============================================================================
-- View: Equipment Failure Events
-- Provides cleaned failure events for MTBF calculation
CREATE OR REPLACE VIEW vw_equipment_failure_events AS
SELECT nt.notification_id as id,
    nt.sys_eq_id as equipment_id,
    nt.noti_date as failure_date,
    aed.primary_symptom_ai as failure_symptom,
    aed.main_component_ai as failed_component,
    nt.noti_issue_type as issue_type,
    nt.noti_trendcode_l1 as trend_category
FROM notification_text nt
    LEFT JOIN ai_extracted_data aed ON nt.notification_id = aed.notification_id
WHERE nt.noti_date IS NOT NULL
    AND nt.sys_eq_id IS NOT NULL
    AND nt.noti_issue_type IS NOT NULL
ORDER BY nt.sys_eq_id,
    nt.noti_date;
-- View: MTBF Calculation Base
-- Calculates time between failures for each equipment
CREATE OR REPLACE VIEW vw_mtbf_calculation_base AS WITH failure_events AS (
        SELECT equipment_id,
            failure_date,
            failure_symptom,
            failed_component,
            LAG(failure_date) OVER (
                PARTITION BY equipment_id
                ORDER BY failure_date
            ) as prev_failure_date
        FROM vw_equipment_failure_events
    )
SELECT equipment_id,
    failure_date,
    prev_failure_date,
    failure_symptom,
    failed_component,
    EXTRACT(
        EPOCH
        FROM (failure_date - prev_failure_date)
    ) / 86400 as days_between_failures
FROM failure_events
WHERE prev_failure_date IS NOT NULL;
-- View: MTBF Summary by Equipment
-- Provides MTBF statistics for each equipment
CREATE OR REPLACE VIEW vw_mtbf_summary_equipment AS
SELECT equipment_id,
    COUNT(*) as total_failures,
    COUNT(
        CASE
            WHEN days_between_failures IS NOT NULL THEN 1
        END
    ) as calculated_failures,
    AVG(days_between_failures) as avg_mtbf_days,
    MIN(days_between_failures) as min_mtbf_days,
    MAX(days_between_failures) as max_mtbf_days,
    PERCENTILE_CONT(0.5) WITHIN GROUP (
        ORDER BY days_between_failures
    ) as median_mtbf_days,
    STDDEV(days_between_failures) as stddev_mtbf_days,
    MIN(failure_date) as first_failure_date,
    MAX(failure_date) as last_failure_date
FROM vw_mtbf_calculation_base
GROUP BY equipment_id
HAVING COUNT(
        CASE
            WHEN days_between_failures IS NOT NULL THEN 1
        END
    ) >= 2;
-- View: MTBF Summary by Component
-- Provides MTBF statistics for each component
CREATE OR REPLACE VIEW vw_mtbf_summary_component AS
SELECT failed_component,
    COUNT(*) as total_failures,
    COUNT(
        CASE
            WHEN days_between_failures IS NOT NULL THEN 1
        END
    ) as calculated_failures,
    AVG(days_between_failures) as avg_mtbf_days,
    MIN(days_between_failures) as min_mtbf_days,
    MAX(days_between_failures) as max_mtbf_days,
    PERCENTILE_CONT(0.5) WITHIN GROUP (
        ORDER BY days_between_failures
    ) as median_mtbf_days
FROM vw_mtbf_calculation_base
WHERE failed_component IS NOT NULL
GROUP BY failed_component
HAVING COUNT(
        CASE
            WHEN days_between_failures IS NOT NULL THEN 1
        END
    ) >= 2;
-- ============================================================================
-- Pareto Analysis Views
-- ============================================================================
-- View: Symptom Frequency Analysis
-- Counts occurrences of each symptom for Pareto analysis
CREATE OR REPLACE VIEW vw_symptom_frequency AS
SELECT primary_symptom_ai as symptom,
    COUNT(*) as occurrence_count,
    COUNT(DISTINCT sys_eq_id) as affected_equipment_count,
    MIN(noti_date) as first_occurrence_date,
    MAX(noti_date) as last_occurrence_date
FROM ai_extracted_data aed
    JOIN notification_text nt ON aed.notification_id = nt.notification_id
WHERE primary_symptom_ai IS NOT NULL
    AND primary_symptom_ai != ''
GROUP BY primary_symptom_ai
ORDER BY occurrence_count DESC;
-- View: Pareto Analysis with Cumulative Percentage
-- Provides complete Pareto analysis with cumulative percentages
CREATE OR REPLACE VIEW vw_pareto_analysis AS WITH symptom_totals AS (
        SELECT symptom,
            occurrence_count,
            affected_equipment_count,
            first_occurrence_date,
            last_occurrence_date,
            SUM(occurrence_count) OVER () as total_occurrences
        FROM vw_symptom_frequency
    ),
    ranked_symptoms AS (
        SELECT symptom,
            occurrence_count,
            affected_equipment_count,
            first_occurrence_date,
            last_occurrence_date,
            ROUND(occurrence_count * 100.0 / total_occurrences, 2) as percentage_of_total,
            ROW_NUMBER() OVER (
                ORDER BY occurrence_count DESC
            ) as rank
        FROM symptom_totals
    )
SELECT symptom,
    occurrence_count,
    affected_equipment_count,
    first_occurrence_date,
    last_occurrence_date,
    percentage_of_total,
    SUM(percentage_of_total) OVER (
        ORDER BY rank
    ) as cumulative_percentage,
    rank
FROM ranked_symptoms
ORDER BY rank;
-- ============================================================================
-- Equipment Health Views
-- ============================================================================
-- View: Equipment Health Status
-- Provides current health status for each equipment
CREATE OR REPLACE VIEW vw_equipment_health_status AS WITH latest_failures AS (
        SELECT equipment_id,
            MAX(failure_date) as last_failure_date,
            COUNT(*) as failure_count_last_90_days
        FROM vw_equipment_failure_events
        WHERE failure_date >= CURRENT_DATE - INTERVAL '90 days'
        GROUP BY equipment_id
    ),
    mtbf_data AS (
        SELECT equipment_id,
            avg_mtbf_days
        FROM vw_mtbf_summary_equipment
    )
SELECT e.equipment_id,
    e.last_failure_date,
    e.failure_count_last_90_days,
    m.avg_mtbf_days,
    CASE
        WHEN e.last_failure_date IS NULL THEN 'No Failures Recorded'
        WHEN e.last_failure_date >= CURRENT_DATE - INTERVAL '7 days' THEN 'Critical'
        WHEN e.last_failure_date >= CURRENT_DATE - INTERVAL '30 days' THEN 'Warning'
        WHEN e.last_failure_date >= CURRENT_DATE - INTERVAL '90 days' THEN 'Monitor'
        ELSE 'Healthy'
    END as health_status,
    CASE
        WHEN e.last_failure_date IS NULL THEN 'green'
        WHEN e.last_failure_date >= CURRENT_DATE - INTERVAL '7 days' THEN 'red'
        WHEN e.last_failure_date >= CURRENT_DATE - INTERVAL '30 days' THEN 'orange'
        WHEN e.last_failure_date >= CURRENT_DATE - INTERVAL '90 days' THEN 'yellow'
        ELSE 'green'
    END as health_color
FROM latest_failures e
    LEFT JOIN mtbf_data m ON e.equipment_id = m.equipment_id;
-- ============================================================================
-- Materialized Views for Performance
-- ============================================================================
-- Materialized View: Daily MTBF Trends
-- Refreshed daily for performance
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_daily_mtbf_trends AS
SELECT DATE_TRUNC('day', failure_date) as analysis_date,
    equipment_id,
    COUNT(*) as daily_failures,
    AVG(days_between_failures) as daily_avg_mtbf
FROM vw_mtbf_calculation_base
WHERE failure_date >= CURRENT_DATE - INTERVAL '365 days'
GROUP BY DATE_TRUNC('day', failure_date),
    equipment_id WITH DATA;
-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_mv_daily_mtbf_date ON mv_daily_mtbf_trends (analysis_date);
CREATE INDEX IF NOT EXISTS idx_mv_daily_mtbf_equipment ON mv_daily_mtbf_trends (equipment_id);
-- Materialized View: Monthly Pareto Summary
-- Refreshed monthly for performance
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_monthly_pareto_summary AS
SELECT DATE_TRUNC('month', nt.noti_date) as analysis_month,
    aed.primary_symptom_ai as symptom,
    COUNT(*) as monthly_occurrences,
    COUNT(DISTINCT nt.sys_eq_id) as monthly_affected_equipment
FROM ai_extracted_data aed
    JOIN notification_text nt ON aed.notification_id = nt.notification_id
WHERE aed.primary_symptom_ai IS NOT NULL
    AND aed.primary_symptom_ai != ''
    AND nt.noti_date >= CURRENT_DATE - INTERVAL '2 years'
GROUP BY DATE_TRUNC('month', nt.noti_date),
    aed.primary_symptom_ai WITH DATA;
-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_mv_monthly_pareto_month ON mv_monthly_pareto_summary (analysis_month);
CREATE INDEX IF NOT EXISTS idx_mv_monthly_pareto_symptom ON mv_monthly_pareto_summary (symptom);
-- ============================================================================
-- View Refresh Functions
-- ============================================================================
-- Function: Refresh all materialized views
CREATE OR REPLACE FUNCTION refresh_analytics_views() RETURNS void AS $$ BEGIN REFRESH MATERIALIZED VIEW CONCURRENTLY mv_daily_mtbf_trends;
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_monthly_pareto_summary;
END;
$$ LANGUAGE plpgsql;
-- Function: Get analytics view metadata
CREATE OR REPLACE FUNCTION get_analytics_view_info() RETURNS TABLE(
        view_name text,
        view_type text,
        row_count bigint,
        last_refresh timestamp
    ) AS $$ BEGIN RETURN QUERY
SELECT matviewname::text,
    'materialized'::text,
    (
        SELECT COUNT(*)
        FROM mv_daily_mtbf_trends
    ) as row_count,
    last_refresh
FROM pg_catalog.pg_matviews
WHERE schemaname = 'public'
    AND matviewname IN (
        'mv_daily_mtbf_trends',
        'mv_monthly_pareto_summary'
    )
UNION ALL
SELECT table_name::text,
    'regular'::text,
    (
        SELECT COUNT(*)
        FROM vw_mtbf_summary_equipment
    ) as row_count,
    NULL::timestamp
FROM information_schema.views
WHERE table_schema = 'public'
    AND table_name LIKE 'vw_%'
ORDER BY view_name;
END;
$$ LANGUAGE plpgsql;