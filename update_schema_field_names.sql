-- 数据库字段名更新脚本
-- 将 notification_* 字段更新为 noti_* 以保持一致性

-- 1. 首先创建备份表
CREATE TABLE IF NOT EXISTS notification_text_backup AS SELECT * FROM notification_text;

-- 2. 重命名字段（如果表存在且字段名不同）
DO $$ 
BEGIN
    -- 检查表是否存在
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'notification_text') THEN
        -- 重命名 notification_date 到 noti_date
        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'notification_text' AND column_name = 'notification_date') THEN
            ALTER TABLE notification_text RENAME COLUMN notification_date TO noti_date;
        END IF;
        
        -- 重命名 notification_assigned_date 到 noti_assigned_date
        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'notification_text' AND column_name = 'notification_assigned_date') THEN
            ALTER TABLE notification_text RENAME COLUMN notification_assigned_date TO noti_assigned_date;
        END IF;
        
        -- 重命名 notification_closed_date 到 noti_closed_date
        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'notification_text' AND column_name = 'notification_closed_date') THEN
            ALTER TABLE notification_text RENAME COLUMN notification_closed_date TO noti_closed_date;
        END IF;
        
        -- 重命名 notification_text 到 noti_text
        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'notification_text' AND column_name = 'notification_text') THEN
            ALTER TABLE notification_text RENAME COLUMN notification_text TO noti_text;
        END IF;
        
        -- 重命名 notification_medium_text 到 noti_medium_text
        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'notification_text' AND column_name = 'notification_medium_text') THEN
            ALTER TABLE notification_text RENAME COLUMN notification_medium_text TO noti_medium_text;
        END IF;
        
        -- 重命名 notification_issue_type 到 noti_issue_type
        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'notification_text' AND column_name = 'notification_issue_type') THEN
            ALTER TABLE notification_text RENAME COLUMN notification_issue_type TO noti_issue_type;
        END IF;
        
        -- 重命名 notification_trendcode_l1 到 noti_trendcode_l1
        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'notification_text' AND column_name = 'notification_trendcode_l1') THEN
            ALTER TABLE notification_text RENAME COLUMN notification_trendcode_l1 TO noti_trendcode_l1;
        END IF;
        
        -- 重命名 notification_trendcode_l2 到 noti_trendcode_l2
        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'notification_text' AND column_name = 'notification_trendcode_l2') THEN
            ALTER TABLE notification_text RENAME COLUMN notification_trendcode_l2 TO noti_trendcode_l2;
        END IF;
        
        -- 重命名 notification_trendcode_l3 到 noti_trendcode_l3
        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'notification_text' AND column_name = 'notification_trendcode_l3') THEN
            ALTER TABLE notification_text RENAME COLUMN notification_trendcode_l3 TO noti_trendcode_l3;
        END IF;
    END IF;
END $$;

-- 3. 更新 init_schema.sql 文件中的字段名（手动执行）
-- 此脚本用于实际数据库更新，init_schema.sql 文件需要手动更新以保持一致性
