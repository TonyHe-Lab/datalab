-- 测试数据种子脚本
-- 为datalab项目部署少量生产数据进行测试

-- 1. 首先为notification_text表添加更多测试数据
INSERT INTO notification_text (
    notification_id,
    noti_date,
    noti_assigned_date,
    noti_closed_date,
    noti_category_id,
    sys_eq_id,
    noti_country_id,
    sys_fl_id,
    sys_mat_id,
    sys_serial_id,
    noti_trendcode_l1,
    noti_trendcode_l2,
    noti_trendcode_l3,
    noti_issue_type,
    noti_medium_text,
    noti_text,
    notification_issue_type
) VALUES
-- 硬件故障案例
(
    'TEST001',
    '2025-01-15 09:30:00+08',
    '2025-01-15 10:00:00+08',
    '2025-01-15 16:30:00+08',
    '110',
    '1055000001',
    'CN',
    'FL001',
    'MAT001',
    'SERIAL001',
    'TREND001',
    'TREND001-01',
    'TREND001-01-01',
    'Hardware',
    'CT扫描仪图像伪影',
    '2025-01-15 09:30:00 UTC+8 张三 (Z0012345) *** Issue Reported *** CT扫描仪在腹部扫描时出现环形伪影，影响图像质量。设备型号：SOMATOM Definition Edge。*** Action Taken *** 检查了探测器校准，重新校准后问题解决。',
    'Image Artifact'
),
-- 软件问题案例
(
    'TEST002',
    '2025-01-16 14:20:00+08',
    '2025-01-16 14:30:00+08',
    '2025-01-17 11:45:00+08',
    '120',
    '1055000002',
    'US',
    'FL002',
    'MAT002',
    'SERIAL002',
    'TREND002',
    'TREND002-01',
    'TREND002-01-01',
    'Software',
    'PACS系统连接超时',
    '2025-01-16 14:20:00 EST John Smith (SMITJ001) *** Issue Reported *** PACS系统频繁连接超时，无法传输DICOM图像。错误代码：ERR-408。*** Action Taken *** 检查网络配置，重启PACS服务后恢复正常。',
    'Connection Timeout'
),
-- 网络问题案例
(
    'TEST003',
    '2025-01-17 11:05:00+08',
    '2025-01-17 11:15:00+08',
    '2025-01-18 09:30:00+08',
    '130',
    '1055000003',
    'DE',
    'FL003',
    'MAT003',
    'SERIAL003',
    'TREND003',
    'TREND003-01',
    'TREND003-01-01',
    'Network',
    'MRI设备网络中断',
    '2025-01-17 11:05:00 CET Hans Müller (MULLH001) *** Issue Reported *** MRI设备无法连接到医院网络，无法上传扫描数据。*** Action Taken *** 检查网络交换机，更换故障网线后连接恢复。',
    'Network Disconnection'
),
-- 配置错误案例
(
    'TEST004',
    '2025-01-18 08:45:00+08',
    '2025-01-18 09:00:00+08',
    '2025-01-18 15:20:00+08',
    '140',
    '1055000004',
    'JP',
    'FL004',
    'MAT004',
    'SERIAL004',
    'TREND004',
    'TREND004-01',
    'TREND004-01-01',
    'Configuration',
    '超声设备参数设置错误',
    '2025-01-18 08:45:00 JST 田中太郎 (TANAT001) *** Issue Reported *** 超声设备图像质量下降，怀疑参数设置不当。*** Action Taken *** 恢复出厂默认设置，重新配置扫描参数后图像质量改善。',
    'Parameter Setting Error'
),
-- 维护问题案例
(
    'TEST005',
    '2025-01-19 13:30:00+08',
    '2025-01-19 13:40:00+08',
    '2025-01-20 10:15:00+08',
    '150',
    '1055000005',
    'FR',
    'FL005',
    'MAT005',
    'SERIAL005',
    'TREND005',
    'TREND005-01',
    'TREND005-01-01',
    'Maintenance',
    'X光机定期维护',
    '2025-01-19 13:30:00 CET Pierre Dubois (DUBOP001) *** Issue Reported *** X光机需要定期维护，包括球管检查和校准。*** Action Taken *** 完成球管更换和系统校准，设备性能恢复正常。',
    'Routine Maintenance'
)
ON CONFLICT (notification_id) DO NOTHING;

-- 2. 为ai_extracted_data表添加测试数据
INSERT INTO ai_extracted_data (
    notification_id,
    keywords_ai,
    primary_symptom_ai,
    root_cause_ai,
    summary_ai,
    solution_ai,
    solution_type_ai,
    components_ai,
    processes_ai,
    main_component_ai,
    main_process_ai,
    confidence_score_ai,
    model_version
) VALUES
-- 对应TEST001的AI提取数据
(
    'TEST001',
    '["CT扫描仪", "图像伪影", "腹部扫描", "探测器校准"]'::jsonb,
    'CT扫描图像出现环形伪影',
    '探测器校准偏差',
    'CT扫描仪在腹部扫描时出现图像伪影，通过重新校准探测器解决问题',
    '重新校准探测器',
    'Calibration',
    '探测器, X射线管',
    '图像采集, 校准流程',
    '探测器',
    '图像采集',
    0.92,
    'gpt-4o-2025-01-15'
),
-- 对应TEST002的AI提取数据
(
    'TEST002',
    '["PACS系统", "连接超时", "DICOM", "网络配置"]'::jsonb,
    'PACS系统频繁连接超时',
    '网络服务配置问题',
    'PACS系统无法传输DICOM图像，通过重启服务解决连接问题',
    '重启PACS服务并检查网络配置',
    'Service Restart',
    'PACS服务器, 网络接口',
    '图像传输, 网络通信',
    'PACS服务器',
    '图像传输',
    0.88,
    'gpt-4o-2025-01-15'
),
-- 对应TEST003的AI提取数据
(
    'TEST003',
    '["MRI", "网络中断", "数据上传", "网线故障"]'::jsonb,
    'MRI设备无法连接到医院网络',
    '物理网线故障',
    'MRI设备网络连接中断，更换故障网线后恢复',
    '更换故障网线',
    'Hardware Replacement',
    '网络接口, 网线, 交换机',
    '网络连接, 数据传输',
    '网线',
    '网络连接',
    0.95,
    'gpt-4o-2025-01-15'
),
-- 对应TEST004的AI提取数据
(
    'TEST004',
    '["超声设备", "参数设置", "图像质量", "配置恢复"]'::jsonb,
    '超声设备图像质量下降',
    '参数设置不当',
    '超声设备因参数设置错误导致图像质量下降，恢复默认设置后改善',
    '恢复出厂设置并重新配置参数',
    'Configuration Reset',
    '超声探头, 控制面板',
    '参数配置, 图像处理',
    '控制面板',
    '参数配置',
    0.85,
    'gpt-4o-2025-01-15'
),
-- 对应TEST005的AI提取数据
(
    'TEST005',
    '["X光机", "定期维护", "球管更换", "系统校准"]'::jsonb,
    'X光机需要定期维护',
    '设备正常磨损',
    'X光机完成定期维护包括球管更换和系统校准',
    '更换球管并校准系统',
    'Preventive Maintenance',
    'X射线球管, 发生器',
    '维护流程, 校准流程',
    'X射线球管',
    '维护流程',
    0.90,
    'gpt-4o-2025-01-15'
)
ON CONFLICT (id) DO NOTHING;

-- 3. 为etl_metadata表添加测试数据
INSERT INTO etl_metadata (
    table_name,
    last_sync_timestamp,
    rows_processed,
    sync_status,
    checkpoint_data,
    checkpoint_timestamp,
    batch_size,
    total_records,
    processed_records
) VALUES
(
    'notification_text',
    '2025-01-20 10:00:00+08',
    16, -- 原有11条 + 新增5条
    'completed',
    '{"last_notification_id": "TEST005", "last_noti_date": "2025-01-19 13:30:00+08"}'::jsonb,
    '2025-01-20 10:00:00+08',
    1000,
    16,
    16
),
(
    'ai_extracted_data',
    '2025-01-20 10:05:00+08',
    5,
    'completed',
    '{"last_id": 5}'::jsonb,
    '2025-01-20 10:05:00+08',
    500,
    5,
    5
)
ON CONFLICT (table_name) DO UPDATE SET
    last_sync_timestamp = EXCLUDED.last_sync_timestamp,
    rows_processed = EXCLUDED.rows_processed,
    sync_status = EXCLUDED.sync_status,
    checkpoint_data = EXCLUDED.checkpoint_data,
    checkpoint_timestamp = EXCLUDED.checkpoint_timestamp,
    total_records = EXCLUDED.total_records,
    processed_records = EXCLUDED.processed_records,
    updated_at = now();

-- 4. 注意：semantic_embeddings表需要向量数据，这里暂时不添加
-- 该表需要通过AI模型生成嵌入向量后插入

-- 显示插入结果
SELECT 'notification_text' as table_name, COUNT(*) as row_count FROM notification_text
UNION ALL
SELECT 'ai_extracted_data', COUNT(*) FROM ai_extracted_data
UNION ALL
SELECT 'semantic_embeddings', COUNT(*) FROM semantic_embeddings
UNION ALL
SELECT 'etl_metadata', COUNT(*) FROM etl_metadata;

-- 显示新增的测试数据
SELECT '=== 新增的notification_text数据 ===' as info;
SELECT notification_id, noti_date, noti_issue_type, LEFT(noti_text, 80) as text_preview
FROM notification_text
WHERE notification_id LIKE 'TEST%'
ORDER BY notification_id;

SELECT '=== 新增的ai_extracted_data数据 ===' as info;
SELECT aed.id, aed.notification_id, aed.primary_symptom_ai, aed.root_cause_ai, aed.solution_ai
FROM ai_extracted_data aed
JOIN notification_text nt ON aed.notification_id = nt.notification_id
WHERE nt.notification_id LIKE 'TEST%'
ORDER BY aed.id;