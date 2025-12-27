import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class SnowflakeConfig(BaseSettings):
    """Snowflake 连接配置"""

    account: str = Field(
        ..., description="Snowflake 账户 (例如: 'your-account.snowflakecomputing.com')"
    )
    user: str = Field(..., description="Snowflake 用户名")
    password: Optional[str] = Field(None, description="密码 (可选，如果使用 SSO)")
    authenticator: str = Field(
        "snowflake", description="认证方式: 'snowflake', 'externalbrowser', 'oauth'"
    )
    warehouse: str = Field(..., description="仓库名称")
    database: str = Field(..., description="数据库名称")
    schema: str = Field(..., description="模式名称")
    role: Optional[str] = Field(None, description="角色名称 (可选)")

    model_config = SettingsConfigDict(env_prefix="SNOWFLAKE_")


class PostgresConfig(BaseSettings):
    """PostgreSQL 连接配置"""

    host: str = Field("localhost", description="PostgreSQL 主机")
    port: int = Field(5432, description="PostgreSQL 端口")
    user: str = Field("postgres", description="PostgreSQL 用户名")
    password: str = Field(..., description="PostgreSQL 密码")
    database: str = Field("datalab", description="数据库名称")

    model_config = SettingsConfigDict(env_prefix="POSTGRES_")


class ETLConfig(BaseSettings):
    """ETL 配置"""

    batch_size: int = Field(1000, description="批处理大小")
    max_retries: int = Field(3, description="最大重试次数")
    retry_delay: int = Field(5, description="重试延迟(秒)")
    watermark_table: str = Field("etl_metadata", description="水位表名称")

    model_config = SettingsConfigDict(env_prefix="ETL_")


class Config(BaseSettings):
    """应用配置"""

    snowflake: SnowflakeConfig = Field(default_factory=SnowflakeConfig)
    postgres: PostgresConfig = Field(default_factory=PostgresConfig)
    etl: ETLConfig = Field(default_factory=ETLConfig)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",  # 忽略额外的环境变量
    )


def load_config() -> Config:
    """加载配置"""
    return Config()


def validate_config(config: Config) -> bool:
    """验证配置"""
    # 验证 Snowflake 配置
    if not config.snowflake.account:
        raise ValueError("SNOWFLAKE_ACCOUNT 必须设置")
    if not config.snowflake.user:
        raise ValueError("SNOWFLAKE_USER 必须设置")
    if not config.snowflake.warehouse:
        raise ValueError("SNOWFLAKE_WAREHOUSE 必须设置")
    if not config.snowflake.database:
        raise ValueError("SNOWFLAKE_DATABASE 必须设置")
    if not config.snowflake.schema:
        raise ValueError("SNOWFLAKE_SCHEMA 必须设置")

    # 验证 PostgreSQL 配置
    if not config.postgres.password:
        raise ValueError("POSTGRES_PASSWORD 必须设置")

    return True
