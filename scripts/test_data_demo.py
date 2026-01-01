#!/usr/bin/env python3
"""
测试数据演示脚本
展示如何使用部署的测试数据进行查询和分析
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import json
from datetime import datetime

def connect_to_db():
    """连接到PostgreSQL数据库"""
    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="datalab",
            user="postgres",
            password="password"
        )
        print("✅ 成功连接到数据库")
        return conn
    except Exception as e:
        print(f"❌ 连接数据库失败: {e}")
        return None

def demo_basic_queries(conn):
    """演示基本查询"""
    print("\n" + "="*60)
    print("1. 基本数据查询演示")
    print("="*60)

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        # 查询最新的5个工单
        cur.execute("""
            SELECT notification_id, noti_date, noti_issue_type,
                   LEFT(noti_text, 100) as text_preview
            FROM notification_text
            ORDER BY noti_date DESC
            LIMIT 5
        """)
        latest_tickets = cur.fetchall()

        print(f"\n📋 最新的5个工单:")
        for ticket in latest_tickets:
            print(f"  • ID: {ticket['notification_id']}")
            print(f"    日期: {ticket['noti_date']}")
            print(f"    问题类型: {ticket['noti_issue_type']}")
            print(f"    内容预览: {ticket['text_preview'][:80]}...")
            print()

def demo_ai_analysis(conn):
    """演示AI分析数据查询"""
    print("\n" + "="*60)
    print("2. AI分析数据查询演示")
    print("="*60)

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        # 查询AI提取的数据
        cur.execute("""
            SELECT nt.notification_id, nt.noti_issue_type,
                   aed.primary_symptom_ai, aed.root_cause_ai,
                   aed.solution_ai, aed.confidence_score_ai
            FROM notification_text nt
            JOIN ai_extracted_data aed ON nt.notification_id = aed.notification_id
            WHERE aed.confidence_score_ai >= 0.9
            ORDER BY aed.confidence_score_ai DESC
        """)
        high_confidence_ai = cur.fetchall()

        print(f"\n🤖 高置信度(≥0.9)的AI分析结果:")
        for analysis in high_confidence_ai:
            print(f"  • 工单ID: {analysis['notification_id']}")
            print(f"    问题类型: {analysis['noti_issue_type']}")
            print(f"    主要症状: {analysis['primary_symptom_ai']}")
            print(f"    根本原因: {analysis['root_cause_ai']}")
            print(f"    解决方案: {analysis['solution_ai']}")
            print(f"    置信度: {analysis['confidence_score_ai']:.3f}")
            print()

def demo_statistics(conn):
    """演示统计查询"""
    print("\n" + "="*60)
    print("3. 数据统计演示")
    print("="*60)

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        # 按问题类型统计
        cur.execute("""
            SELECT noti_issue_type, COUNT(*) as count,
                   ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage
            FROM notification_text
            GROUP BY noti_issue_type
            ORDER BY count DESC
        """)
        issue_stats = cur.fetchall()

        print(f"\n📊 问题类型分布:")
        for stat in issue_stats:
            print(f"  • {stat['noti_issue_type']}: {stat['count']} 个 ({stat['percentage']}%)")

        # AI提取覆盖率
        cur.execute("""
            SELECT
                COUNT(DISTINCT nt.notification_id) as total_tickets,
                COUNT(DISTINCT aed.notification_id) as ai_extracted_tickets,
                ROUND(COUNT(DISTINCT aed.notification_id) * 100.0 /
                      COUNT(DISTINCT nt.notification_id), 2) as coverage_percentage
            FROM notification_text nt
            LEFT JOIN ai_extracted_data aed ON nt.notification_id = aed.notification_id
        """)
        coverage = cur.fetchone()

        print(f"\n📈 AI提取覆盖率:")
        print(f"  • 总工单数: {coverage['total_tickets']}")
        print(f"  • AI提取工单数: {coverage['ai_extracted_tickets']}")
        print(f"  • 覆盖率: {coverage['coverage_percentage']}%")

def demo_etl_status(conn):
    """演示ETL状态查询"""
    print("\n" + "="*60)
    print("4. ETL状态查询演示")
    print("="*60)

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT table_name, sync_status, rows_processed,
                   total_records, processed_records, last_sync_timestamp
            FROM etl_metadata
            ORDER BY table_name
        """)
        etl_status = cur.fetchall()

        print(f"\n🔄 ETL同步状态:")
        for status in etl_status:
            print(f"  • 表名: {status['table_name']}")
            print(f"    状态: {status['sync_status']}")
            print(f"    处理行数: {status['rows_processed']}")
            print(f"    总记录数: {status['total_records']}")
            print(f"    已处理记录: {status['processed_records']}")
            print(f"    最后同步时间: {status['last_sync_timestamp']}")
            print()

def demo_complete_workflow(conn):
    """演示完整的工作流程查询"""
    print("\n" + "="*60)
    print("5. 完整工作流程演示")
    print("="*60)

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        # 查询一个完整的工单处理流程
        cur.execute("""
            SELECT
                nt.notification_id,
                nt.noti_date,
                nt.noti_issue_type,
                nt.noti_text as original_text,
                aed.keywords_ai,
                aed.primary_symptom_ai,
                aed.root_cause_ai,
                aed.summary_ai,
                aed.solution_ai,
                aed.solution_type_ai,
                aed.confidence_score_ai,
                em.sync_status as etl_status,
                em.last_sync_timestamp
            FROM notification_text nt
            LEFT JOIN ai_extracted_data aed ON nt.notification_id = aed.notification_id
            LEFT JOIN etl_metadata em ON em.table_name = 'notification_text'
            WHERE nt.notification_id LIKE 'TEST%'
            ORDER BY nt.noti_date DESC
            LIMIT 1
        """)
        workflow = cur.fetchone()

        if workflow:
            print(f"\n🔧 完整的工单处理流程示例:")
            print(f"  工单ID: {workflow['notification_id']}")
            print(f"  创建时间: {workflow['noti_date']}")
            print(f"  问题类型: {workflow['noti_issue_type']}")
            print(f"\n  原始文本摘要:")
            print(f"    {workflow['original_text'][:200]}...")

            if workflow['keywords_ai']:
                # keywords_ai已经是JSONB格式，直接使用
                keywords = workflow['keywords_ai']
                if isinstance(keywords, list):
                    print(f"\n  AI提取的关键词: {', '.join(keywords)}")
                else:
                    print(f"\n  AI提取的关键词: {keywords}")

            print(f"\n  AI分析结果:")
            print(f"    主要症状: {workflow['primary_symptom_ai']}")
            print(f"    根本原因: {workflow['root_cause_ai']}")
            print(f"    摘要: {workflow['summary_ai']}")
            print(f"    解决方案: {workflow['solution_ai']}")
            print(f"    解决方案类型: {workflow['solution_type_ai']}")
            print(f"    置信度: {workflow['confidence_score_ai']:.3f}")

            print(f"\n  ETL状态:")
            print(f"    同步状态: {workflow['etl_status']}")
            print(f"    最后同步时间: {workflow['last_sync_timestamp']}")

def main():
    """主函数"""
    print("🚀 测试数据演示脚本")
    print("="*60)

    # 连接到数据库
    conn = connect_to_db()
    if not conn:
        return

    try:
        # 执行各个演示
        demo_basic_queries(conn)
        demo_ai_analysis(conn)
        demo_statistics(conn)
        demo_etl_status(conn)
        demo_complete_workflow(conn)

        print("\n" + "="*60)
        print("✅ 测试数据演示完成!")
        print("="*60)
        print("\n📋 总结:")
        print("  • 已成功部署少量生产数据进行测试")
        print("  • 数据包含完整的工单处理流程")
        print("  • 支持AI分析、统计查询和ETL状态监控")
        print("  • 可用于功能测试、性能测试和集成测试")

    finally:
        conn.close()
        print("\n🔌 数据库连接已关闭")

if __name__ == "__main__":
    main()