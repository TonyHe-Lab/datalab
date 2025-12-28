-- db/init_schema.sql
-- Idempotent schema + extensions for datalab project
-- Creates required extensions, tables and indexes if not present
-- PR #4: Epic 2 - Incremental ETL Schema (完整版本)
-- ============================================
-- 扩展创建
-- ============================================
-- Create extension if allowed (requires superuser on some PG installs)
DO $$ BEGIN IF NOT EXISTS (
    SELECT 1
    FROM pg_extension
    WHERE extname = 'vector'
) THEN -- attempt to create vector extension; if not permitted this will fail
BEGIN EXECUTE 'CREATE EXTENSION IF NOT EXISTS vector';
EXCEPTION
WHEN others THEN RAISE NOTICE 'Could not create extension vector (insufficient privileges or not available)';
END;
END IF;
END $$;
-- ============================================
-- 通知工单主表 (notification_text)
-- 存储从Snowflake同步的原始工单数据
-- ============================================
CREATE TABLE IF NOT EXISTS notification_text (
    -- 主键：通知工单ID（来自Snowflake系统的唯一工单号）
    notification_id TEXT PRIMARY KEY,
    -- 时间相关字段
    notification_date TIMESTAMP WITH TIME ZONE NOT NULL,
    -- 工单通知/创建日期，用于增量同步
    notification_assigned_date TIMESTAMP WITH TIME ZONE,
    -- 工单分配日期
    notification_closed_date TIMESTAMP WITH TIME ZONE,
    -- 工单关闭日期
    -- 分类与标识字段
    noti_category_id TEXT,
    -- 工单类别编号
    sys_eq_id TEXT,
    -- 设备编号
    noti_country_id TEXT,
    -- 工单国家简称
    sys_fl_id TEXT,
    -- 设备场地编号
    sys_mat_id TEXT,
    -- 设备物料号
    sys_serial_id TEXT,
    -- 设备序列号
    -- 趋势代码字段
    notification_trendcode_l1 TEXT,
    -- 工单趋势代码级别1
    notification_trendcode_l2 TEXT,
    -- 工单趋势代码级别2
    notification_trendcode_l3 TEXT,
    -- 工单趋势代码级别3
    -- 文本内容字段
    notification_medium_text TEXT,
    -- 工单保修短文本
    notification_text TEXT NOT NULL,
    -- 工单维修日志长文本（AI分析的主要文本）
    -- 系统字段
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    -- 记录创建时间
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() -- 记录更新时间
);
-- ============================================
-- AI提取数据表 (ai_extracted_data)
-- 存储从工单文本中AI提取的结构化信息
-- ============================================
CREATE TABLE IF NOT EXISTS ai_extracted_data (
    -- 主键
    id SERIAL PRIMARY KEY,
    -- 外键：引用通知工单
    notification_id TEXT NOT NULL REFERENCES notification_text(notification_id) ON DELETE CASCADE,
    -- AI提取的结构化字段
    modules_ai TEXT,
    -- 子故障模块
    component_ai TEXT,
    -- 故障部件
    fault_ai TEXT,
    -- 故障描述
    process_ai TEXT,
    -- 故障流程
    cause_ai TEXT,
    -- 根本原因
    resolution_ai JSONB,
    -- 解决步骤（结构化JSON）
    summary TEXT,
    -- 摘要总结
    -- 系统字段
    extracted_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    -- AI提取时间
    confidence_score DECIMAL(5, 4),
    -- AI提取置信度（0.0000-1.0000）
    model_version TEXT -- 使用的AI模型版本
);
-- ============================================
-- 语义嵌入表 (semantic_embeddings)
-- 存储工单文本的向量嵌入，用于语义搜索
-- ============================================
-- If pgvector is available, use vector type, otherwise fall back to bytea
DO $$ BEGIN IF EXISTS (
    SELECT 1
    FROM pg_extension
    WHERE extname = 'vector'
) THEN -- Use vector type when extension is available
IF NOT EXISTS (
    SELECT 1
    FROM information_schema.tables
    WHERE table_schema = 'public'
        AND table_name = 'semantic_embeddings'
) THEN EXECUTE $sql$ CREATE TABLE public.semantic_embeddings (
    -- 外键：引用通知工单
    notification_id TEXT NOT NULL REFERENCES notification_text(notification_id) ON DELETE CASCADE,
    -- 文本原文（用于调试和验证）
    source_text_ai TEXT NOT NULL,
    -- 向量嵌入
    vector vector(1536),
    -- 系统字段
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    -- 向量嵌入处理时间戳
    PRIMARY KEY (notification_id)
);
$sql$;
END IF;
ELSE -- Fallback: store embeddings as bytea when vector type unavailable
IF NOT EXISTS (
    SELECT 1
    FROM information_schema.tables
    WHERE table_schema = 'public'
        AND table_name = 'semantic_embeddings'
) THEN EXECUTE $sql$ CREATE TABLE public.semantic_embeddings (
    notification_id TEXT NOT NULL REFERENCES notification_text(notification_id) ON DELETE CASCADE,
    source_text_ai TEXT NOT NULL,
    vector_bytea BYTEA,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    PRIMARY KEY (notification_id)
);
$sql$;
END IF;
END IF;
END $$;
-- ============================================
-- 索引创建
-- ============================================
-- Text search indexes
CREATE INDEX IF NOT EXISTS notification_text_content_idx ON notification_text USING GIN (
    to_tsvector('english', coalesce(notification_text, ''))
);
CREATE INDEX IF NOT EXISTS ai_extracted_data_summary_idx ON ai_extracted_data USING GIN (to_tsvector('english', coalesce(summary, '')));
-- Vector indexes: attempt HNSW (pgvector 0.4+ supports ivfflat/hnsw depending on build)
DO $$ BEGIN IF EXISTS (
    SELECT 1
    FROM pg_extension
    WHERE extname = 'vector'
) THEN -- Try create HNSW index if supported
BEGIN EXECUTE 'CREATE INDEX IF NOT EXISTS semantic_embeddings_vector_hnsw_idx ON semantic_embeddings USING hnsw (vector)';
EXCEPTION
WHEN undefined_function
OR undefined_table
OR others THEN -- Try ivfflat as fallback
BEGIN EXECUTE 'CREATE INDEX IF NOT EXISTS semantic_embeddings_vector_ivfflat_idx ON semantic_embeddings USING ivfflat (vector) WITH (lists = 100)';
EXCEPTION
WHEN others THEN RAISE NOTICE 'Could not create vector index (extension missing functionality)';
END;
END;
END IF;
END $$;
-- ============================================
-- 辅助视图
-- ============================================
-- Provide a small helper view to inspect embedding storage mode
CREATE OR REPLACE VIEW public.semantic_embeddings_info AS
SELECT 'semantic_embeddings'::text as table_name,
    EXISTS (
        SELECT 1
        FROM pg_extension
        WHERE extname = 'vector'
    ) as has_vector;
-- ============================================
-- ETL元数据表 (从ddl_etl_metadata.sql合并)
-- ============================================
CREATE TABLE IF NOT EXISTS etl_metadata (
    id SERIAL PRIMARY KEY,
    table_name TEXT NOT NULL,
    last_sync_timestamp TIMESTAMP WITH TIME ZONE,
    rows_processed INTEGER DEFAULT 0,
    sync_status TEXT CHECK (
        sync_status IN ('pending', 'in_progress', 'completed', 'failed')
    ),
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    UNIQUE(table_name)
);
-- Index for efficient lookups
CREATE INDEX IF NOT EXISTS etl_metadata_table_name_idx ON etl_metadata(table_name);
CREATE INDEX IF NOT EXISTS etl_metadata_last_sync_idx ON etl_metadata(last_sync_timestamp);
-- END of init_schema.sql