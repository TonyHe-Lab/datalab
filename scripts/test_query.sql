-- 测试查询：获取数据库信息
SELECT
    CURRENT_DATABASE() as database,
    CURRENT_SCHEMA() as schema,
    CURRENT_WAREHOUSE() as warehouse,
    CURRENT_ROLE() as role,
    CURRENT_VERSION() as version,
    CURRENT_TIMESTAMP() as current_time;