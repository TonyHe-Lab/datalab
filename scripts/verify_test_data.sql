-- 测试数据验证脚本
-- 验证datalab项目测试数据的完整性和关联性

-- 1. 验证各表数据量
SELECT '=== 各表数据量统计 ===' as info;
SELECT 'notification_text' as table_name, COUNT(*) as row_count FROM notification_text
UNION ALL
SELECT 'ai_extracted_data', COUNT(*) FROM ai_extracted_data
UNION ALL
SELECT 'semantic_embeddings', COUNT(*) FROM semantic_embeddings
UNION ALL
SELECT 'etl_metadata', COUNT(*) FROM etl_metadata;

-- 2. 验证数据完整性
SELECT '=== 数据完整性检查 ===' as info;
-- 检查notification_text表必填字段
SELECT
    'notification_text必填字段检查' as check_type,
    COUNT(*) as total_records,
    SUM(CASE WHEN notification_id IS NULL OR notification_id = '' THEN 1 ELSE 0 END) as missing_notification_id,
    SUM(CASE WHEN noti_date IS NULL THEN 1 ELSE 0 END) as missing_noti_date,
    SUM(CASE WHEN noti_text IS NULL OR noti_text = '' THEN 1 ELSE 0 END) as missing_noti_text
FROM notification_text;

-- 3. 验证数据关联性
SELECT '=== 数据关联性检查 ===' as info;
-- 检查ai_extracted_data与notification_text的关联
SELECT
    'ai_extracted_data外键关联检查' as check_type,
    COUNT(DISTINCT aed.notification_id) as ai_extracted_notification_ids,
    COUNT(DISTINCT nt.notification_id) as notification_text_ids,
    COUNT(DISTINCT aed.notification_id) - COUNT(DISTINCT nt.notification_id) as orphaned_records
FROM ai_extracted_data aed
LEFT JOIN notification_text nt ON aed.notification_id = nt.notification_id;

-- 4. 验证测试数据特征
SELECT '=== 测试数据特征分析 ===' as info;
-- 按问题类型统计
SELECT
    noti_issue_type,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage
FROM notification_text
GROUP BY noti_issue_type
ORDER BY count DESC;

-- 按日期分布统计
SELECT
    DATE(noti_date) as date,
    COUNT(*) as daily_count
FROM notification_text
GROUP BY DATE(noti_date)
ORDER BY date DESC
LIMIT 10;

-- 5. 验证AI提取数据的质量
SELECT '=== AI提取数据质量检查 ===' as info;
SELECT
    'confidence_score分布' as metric,
    COUNT(*) as total,
    ROUND(AVG(confidence_score_ai)::numeric, 3) as avg_confidence,
    ROUND(MIN(confidence_score_ai)::numeric, 3) as min_confidence,
    ROUND(MAX(confidence_score_ai)::numeric, 3) as max_confidence
FROM ai_extracted_data;

-- 6. 验证ETL元数据
SELECT '=== ETL元数据检查 ===' as info;
SELECT
    table_name,
    sync_status,
    rows_processed,
    total_records,
    processed_records,
    last_sync_timestamp
FROM etl_metadata
ORDER BY table_name;

-- 7. 示例查询：查看完整的工单处理流程
SELECT '=== 示例：完整的工单处理流程 ===' as info;
SELECT
    nt.notification_id,
    nt.noti_date,
    nt.noti_issue_type,
    LEFT(nt.noti_text, 100) as issue_description,
    aed.primary_symptom_ai,
    aed.root_cause_ai,
    aed.solution_ai,
    aed.confidence_score_ai
FROM notification_text nt
LEFT JOIN ai_extracted_data aed ON nt.notification_id = aed.notification_id
WHERE nt.notification_id LIKE 'TEST%'
ORDER BY nt.noti_date DESC
LIMIT 5;

-- 8. 数据质量总结
SELECT '=== 数据质量总结 ===' as info;
SELECT
    '总工单数' as metric,
    COUNT(*)::text as value
FROM notification_text
UNION ALL
SELECT
    '已AI提取的工单数',
    COUNT(DISTINCT notification_id)::text
FROM ai_extracted_data
UNION ALL
SELECT
    'AI提取覆盖率(%)',
    ROUND(COUNT(DISTINCT aed.notification_id) * 100.0 / COUNT(DISTINCT nt.notification_id), 2)::text
FROM notification_text nt
LEFT JOIN ai_extracted_data aed ON nt.notification_id = aed.notification_id
UNION ALL
SELECT
    '平均AI置信度',
    ROUND(AVG(confidence_score_ai)::numeric, 3)::text
FROM ai_extracted_data;