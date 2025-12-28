"""测试AI管道集成到历史数据处理中"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, date

from src.etl.historical_processor import HistoricalProcessor, BackfillConfig
from src.utils.config import SnowflakeConfig, PostgresConfig


class TestAIIntegration:
    """测试AI管道集成"""

    def setup_method(self):
        """设置测试环境"""
        self.snowflake_config = SnowflakeConfig(
            account="test_account",
            user="test_user",
            password="test_password",
            warehouse="test_warehouse",
            database="test_database",
            schema="test_schema",
        )

        self.postgres_config = PostgresConfig(
            host="localhost",
            port=5432,
            database="test_db",
            user="test_user",
            password="test_password",
        )

        self.backfill_config = BackfillConfig(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
            batch_size=10,
            enable_ai_processing=True,
            enable_embeddings=True,
            dry_run=False,
        )

        self.processor = HistoricalProcessor(
            snowflake_config=self.snowflake_config,
            postgres_config=self.postgres_config,
            backfill_config=self.backfill_config,
        )

    @patch("src.etl.historical_processor.SnowflakeClient")
    @patch("src.etl.historical_processor.PostgresWriter")
    @patch("src.etl.historical_processor.AzureOpenAIClient")
    @patch("src.etl.historical_processor.EmbeddingPipeline")
    def test_ai_components_initialization(
        self, mock_embedding, mock_openai, mock_postgres, mock_snowflake
    ):
        """测试AI组件初始化"""
        # 模拟连接成功
        mock_snowflake_instance = Mock()
        mock_snowflake_instance.connect.return_value = True
        mock_snowflake.return_value = mock_snowflake_instance

        mock_postgres_instance = Mock()
        mock_postgres_instance.connect.return_value = True
        mock_postgres.return_value = mock_postgres_instance

        # 模拟配置加载
        with patch("src.utils.config.load_config") as mock_load_config:
            mock_load_config.return_value = {
                "azure_openai": {
                    "endpoint": "https://test.openai.azure.com/",
                    "api_key": "test_key",
                    "api_version": "2024-02-01",
                    "chat_deployment": "gpt-4",
                    "embed_deployment": "text-embedding-ada-002",
                }
            }

            # 模拟CostTracker
            with patch("src.etl.historical_processor.CostTracker") as mock_cost_tracker:
                mock_cost_tracker_instance = Mock()
                mock_cost_tracker.return_value = mock_cost_tracker_instance

                # 初始化处理器
                result = self.processor.initialize()

                # 验证初始化成功
                assert result is True
                assert self.processor.openai_client is not None
                assert self.processor.embedding_pipeline is not None

    def test_process_batch_with_ai_extraction(self):
        """测试AI提取批次处理"""
        # 模拟OpenAI客户端
        mock_openai = Mock()
        self.processor.openai_client = mock_openai

        # 模拟PostgresWriter
        mock_postgres = Mock()
        self.processor.postgres_writer = mock_postgres

        # 模拟analyze_text函数
        with patch("src.etl.historical_processor.analyze_text") as mock_analyze:
            # 模拟成功的AI分析结果
            mock_analyze.return_value = {
                "success": True,
                "data": {
                    "notification_id": "test_001",
                    "main_component_ai": "Pump Assembly",
                    "primary_symptom_ai": "Leakage detected",
                    "root_cause_ai": "Worn seal",
                    "summary_ai": "Pump leaking due to worn seal",
                    "solution_ai": "Replace seal and test",
                    "keywords_ai": ["pump", "leak", "seal"],
                    "extraction_timestamp": datetime.now(),
                    "confidence_score": 0.85,
                },
            }

            # 测试数据
            test_batch = [
                {
                    "notification_id": "test_001",
                    "notification_text": "Pump leaking from seal area",
                    "created_at": datetime.now(),
                }
            ]

            # 调用AI提取方法
            results = self.processor._process_batch_with_ai_extraction(test_batch)

            # 验证结果
            assert len(results) == 1
            assert results[0]["notification_id"] == "test_001"
            assert results[0]["main_component_ai"] == "Pump Assembly"

            # 验证函数调用
            mock_analyze.assert_called_once()

    def test_process_batch_with_embeddings(self):
        """测试嵌入生成批次处理"""
        # 模拟EmbeddingPipeline
        mock_embedding = Mock()
        mock_embedding.embed_deployment = "text-embedding-ada-002"
        mock_embedding.batch_generate.return_value = [[0.1] * 1536]  # 模拟嵌入向量
        self.processor.embedding_pipeline = mock_embedding

        # 测试数据
        test_batch = [
            {
                "notification_id": "test_001",
                "notification_text": "Pump leaking from seal area",
                "created_at": datetime.now(),
            }
        ]

        # 调用嵌入生成方法
        results = self.processor._process_batch_with_embeddings(test_batch)

        # 验证结果
        assert len(results) == 1
        assert results[0]["notification_id"] == "test_001"
        assert len(results[0]["embedding_vector"]) == 1536
        assert results[0]["embedding_model"] == "text-embedding-ada-002"

        # 验证函数调用
        mock_embedding.batch_generate.assert_called_once_with(
            ["Pump leaking from seal area"]
        )

    def test_validate_ai_quality(self):
        """测试AI质量验证"""
        # 测试数据
        ai_results = [
            {
                "notification_id": "test_001",
                "main_component_ai": "Pump Assembly",
                "primary_symptom_ai": "Leakage detected",
                "summary_ai": "Pump leaking due to worn seal. Need to replace the seal immediately.",
                "keywords_ai": ["pump", "leak", "seal"],
                "extraction_timestamp": datetime.now(),
                "confidence_score": 0.85,
            },
            {
                "notification_id": "test_002",
                "main_component_ai": None,  # 缺少必填字段
                "primary_symptom_ai": "Error",
                "summary_ai": "Short",  # 摘要太短
                "keywords_ai": [],  # 没有关键词
                "extraction_timestamp": datetime.now(),
                "confidence_score": 0.85,
            },
        ]

        # 调用质量验证方法
        quality_report = self.processor._validate_ai_quality(ai_results)

        # 验证报告
        assert quality_report["total"] == 2
        assert quality_report["valid"] == 1  # 只有第一个是有效的
        assert quality_report["invalid"] == 1
        assert 0.5 <= quality_report["quality_score"] <= 0.7

        # 验证质量分布
        distribution = quality_report["quality_distribution"]
        assert (
            distribution["excellent"]
            + distribution["good"]
            + distribution["fair"]
            + distribution["poor"]
            == 2
        )

    def test_empty_batch_handling(self):
        """测试空批次处理"""
        # 模拟PostgresWriter
        mock_postgres = Mock()
        self.processor.postgres_writer = mock_postgres

        # 测试空批次
        empty_batch = []

        # 调用处理方法
        result = self.processor._process_batch_with_ai(empty_batch)

        # 验证处理成功（空批次应该成功）
        assert result is True

        # 验证没有调用数据库写入
        mock_postgres.upsert_notification_text.assert_not_called()

    @patch("src.etl.historical_processor.analyze_text")
    def test_ai_processing_with_errors(self, mock_analyze):
        """测试AI处理错误处理"""
        # 模拟PostgresWriter
        mock_postgres = Mock()
        self.processor.postgres_writer = mock_postgres

        # 模拟OpenAI客户端
        mock_openai = Mock()
        self.processor.openai_client = mock_openai

        # 模拟analyze_text抛出异常
        mock_analyze.side_effect = Exception("API Error")

        # 测试数据
        test_batch = [
            {
                "notification_id": "test_001",
                "notification_text": "Pump leaking",
                "created_at": datetime.now(),
            }
        ]

        # 调用AI提取方法
        results = self.processor._process_batch_with_ai_extraction(test_batch)

        # 验证结果为空（因为出错）
        assert len(results) == 0

        # 验证失败记录计数
        assert self.processor.failed_records == 1

    def test_dry_run_mode(self):
        """测试干运行模式"""
        # 启用干运行模式
        self.processor.backfill_config.dry_run = True

        # 模拟PostgresWriter
        mock_postgres = Mock()
        self.processor.postgres_writer = mock_postgres

        # 模拟OpenAI客户端
        mock_openai = Mock()
        self.processor.openai_client = mock_openai

        # 模拟EmbeddingPipeline
        mock_embedding = Mock()
        self.processor.embedding_pipeline = mock_embedding

        # 测试数据
        test_batch = [
            {
                "notification_id": "test_001",
                "notification_text": "Test notification",
                "created_at": datetime.now(),
            }
        ]

        # 调用处理方法
        result = self.processor._process_batch_with_ai(test_batch)

        # 验证处理成功
        assert result is True

        # 验证没有实际写入数据库（干运行模式）
        mock_postgres.upsert_notification_text.assert_not_called()
        mock_postgres.upsert_ai_extracted_data.assert_not_called()
        mock_postgres.upsert_semantic_embeddings.assert_not_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
