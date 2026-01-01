-- 医疗设备故障数据查询示例
-- 这些查询适用于医疗设备故障诊断与分析平台

-- 1. 获取最近30天的故障工单
SELECT
    ticket_id,
    device_type,
    device_model,
    facility_name,
    reported_date,
    symptom_description,
    priority_level,
    status,
    resolution_time_hours
FROM maintenance_logs
WHERE reported_date >= DATEADD(day, -30, CURRENT_DATE())
ORDER BY reported_date DESC
LIMIT 1000;

-- 2. 按设备类型统计故障数量
SELECT
    device_type,
    COUNT(*) as fault_count,
    AVG(resolution_time_hours) as avg_resolution_time,
    MIN(reported_date) as first_fault_date,
    MAX(reported_date) as last_fault_date
FROM maintenance_logs
WHERE reported_date >= DATEADD(month, -6, CURRENT_DATE())
GROUP BY device_type
ORDER BY fault_count DESC;

-- 3. 获取高优先级未解决的故障
SELECT
    ticket_id,
    device_type,
    device_model,
    facility_name,
    reported_date,
    symptom_description,
    technician_assigned,
    estimated_resolution_date
FROM maintenance_logs
WHERE priority_level IN ('HIGH', 'CRITICAL')
  AND status IN ('OPEN', 'IN_PROGRESS')
  AND reported_date >= DATEADD(day, -7, CURRENT_DATE())
ORDER BY priority_level, reported_date;

-- 4. 设备MTBF（平均故障间隔时间）分析
WITH fault_events AS (
    SELECT
        device_id,
        device_type,
        reported_date,
        LAG(reported_date) OVER (PARTITION BY device_id ORDER BY reported_date) as previous_fault_date
    FROM maintenance_logs
    WHERE status = 'CLOSED'
      AND resolution_time_hours IS NOT NULL
)
SELECT
    device_type,
    COUNT(*) as total_faults,
    AVG(DATEDIFF(hour, previous_fault_date, reported_date)) as avg_mtbf_hours,
    MIN(DATEDIFF(hour, previous_fault_date, reported_date)) as min_mtbf_hours,
    MAX(DATEDIFF(hour, previous_fault_date, reported_date)) as max_mtbf_hours
FROM fault_events
WHERE previous_fault_date IS NOT NULL
GROUP BY device_type
HAVING COUNT(*) >= 5
ORDER BY avg_mtbf_hours;

-- 5. Pareto分析：最常见的故障症状
SELECT
    symptom_category,
    COUNT(*) as occurrence_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage,
    SUM(COUNT(*)) OVER (ORDER BY COUNT(*) DESC) as cumulative_count,
    ROUND(SUM(COUNT(*)) OVER (ORDER BY COUNT(*) DESC) * 100.0 / SUM(COUNT(*)) OVER (), 2) as cumulative_percentage
FROM maintenance_logs
WHERE reported_date >= DATEADD(month, -12, CURRENT_DATE())
GROUP BY symptom_category
ORDER BY occurrence_count DESC;

-- 6. 按设施统计设备可靠性
SELECT
    facility_name,
    device_type,
    COUNT(*) as total_devices,
    SUM(CASE WHEN status = 'CLOSED' THEN 1 ELSE 0 END) as resolved_faults,
    SUM(CASE WHEN status IN ('OPEN', 'IN_PROGRESS') THEN 1 ELSE 0 END) as pending_faults,
    AVG(resolution_time_hours) as avg_resolution_time,
    ROUND(SUM(CASE WHEN status = 'CLOSED' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as resolution_rate
FROM maintenance_logs
WHERE reported_date >= DATEADD(month, -3, CURRENT_DATE())
GROUP BY facility_name, device_type
ORDER BY facility_name, resolution_rate DESC;

-- 7. 季节性故障模式分析
SELECT
    EXTRACT(YEAR FROM reported_date) as year,
    EXTRACT(MONTH FROM reported_date) as month,
    device_type,
    COUNT(*) as fault_count,
    AVG(resolution_time_hours) as avg_resolution_time
FROM maintenance_logs
WHERE reported_date >= DATEADD(year, -2, CURRENT_DATE())
GROUP BY EXTRACT(YEAR FROM reported_date), EXTRACT(MONTH FROM reported_date), device_type
ORDER BY year DESC, month DESC, fault_count DESC;

-- 8. 备件使用分析
SELECT
    spare_part_code,
    spare_part_description,
    device_type,
    COUNT(*) as usage_count,
    SUM(quantity_used) as total_quantity,
    AVG(unit_cost) as avg_unit_cost,
    SUM(quantity_used * unit_cost) as total_cost
FROM spare_parts_usage
WHERE usage_date >= DATEADD(month, -6, CURRENT_DATE())
GROUP BY spare_part_code, spare_part_description, device_type
ORDER BY total_cost DESC;

-- 9. 技术人员绩效分析
SELECT
    technician_id,
    technician_name,
    COUNT(*) as assigned_tickets,
    SUM(CASE WHEN status = 'CLOSED' THEN 1 ELSE 0 END) as resolved_tickets,
    AVG(resolution_time_hours) as avg_resolution_time,
    ROUND(SUM(CASE WHEN status = 'CLOSED' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as resolution_rate,
    AVG(customer_satisfaction_score) as avg_satisfaction_score
FROM maintenance_logs
WHERE reported_date >= DATEADD(month, -3, CURRENT_DATE())
  AND technician_id IS NOT NULL
GROUP BY technician_id, technician_name
HAVING COUNT(*) >= 5
ORDER BY resolution_rate DESC, avg_resolution_time;

-- 10. 预测性维护：频繁故障的设备
SELECT
    device_id,
    device_type,
    device_model,
    facility_name,
    installation_date,
    COUNT(*) as fault_count_last_year,
    AVG(resolution_time_hours) as avg_resolution_time,
    MIN(reported_date) as first_fault_date,
    MAX(reported_date) as last_fault_date,
    DATEDIFF(day, MAX(reported_date), CURRENT_DATE()) as days_since_last_fault
FROM maintenance_logs
WHERE reported_date >= DATEADD(year, -1, CURRENT_DATE())
GROUP BY device_id, device_type, device_model, facility_name, installation_date
HAVING COUNT(*) >= 3
ORDER BY fault_count_last_year DESC, days_since_last_fault;