"""
应用配置管理

基于Pydantic Settings的配置管理，支持环境变量和配置验证。
"""

import os
from typing import List, Optional
from pydantic import BaseSettings, Field, validator
from functools import lru_cache


class Settings(BaseSettings):
    """
    应用配置类
    
    自动从环境变量加载配置，提供默认值和验证。
    """
    
    # ============================================================================
    # 应用基础配置
    # ============================================================================
    
    app_name: str = Field(default="动漫角色扮演聊天机器人", description="应用名称")
    app_version: str = Field(default="0.1.0", description="应用版本")
    environment: str = Field(default="development", description="运行环境")
    debug: bool = Field(default=False, description="调试模式")
    
    # 服务器配置
    host: str = Field(default="127.0.0.1", description="服务器主机")
    port: int = Field(default=8000, description="服务器端口", ge=1, le=65535)
    
    # 日志配置
    log_level: str = Field(default="INFO", description="日志级别")
    
    # ============================================================================
    # LLM API 配置
    # ============================================================================
    
    # Gemini配置
    gemini_api_key: Optional[str] = Field(default=None, description="Gemini API密钥")
    gemini_model: str = Field(default="gemini-1.5-pro", description="Gemini模型名称")
    
    # DeepSeek配置
    deepseek_api_key: Optional[str] = Field(default=None, description="DeepSeek API密钥")
    deepseek_base_url: str = Field(
        default="https://api.deepseek.com/v1", 
        description="DeepSeek API基础URL"
    )
    deepseek_model: str = Field(default="deepseek-chat", description="DeepSeek模型名称")
    
    # LLM通用配置
    default_llm_provider: str = Field(default="gemini", description="默认LLM提供商")
    default_temperature: float = Field(
        default=0.8, 
        description="默认温度参数",
        ge=0.0,
        le=2.0
    )
    default_max_tokens: int = Field(
        default=1000,
        description="默认最大token数",
        ge=50,
        le=4000
    )
    request_timeout_seconds: int = Field(
        default=30,
        description="请求超时时间（秒）",
        ge=5,
        le=120
    )
    max_retries: int = Field(
        default=3,
        description="最大重试次数",
        ge=0,
        le=10
    )
    
    # ============================================================================
    # 聊天机器人配置
    # ============================================================================
    
    # 会话管理
    max_sessions_in_memory: int = Field(
        default=100,
        description="内存中最大会话数",
        ge=10,
        le=1000
    )
    session_timeout_hours: int = Field(
        default=24,
        description="会话超时时间（小时）",
        ge=1,
        le=168
    )
    max_messages_per_session: int = Field(
        default=50,
        description="每个会话最大消息数",
        ge=10,
        le=200
    )
    
    # 角色配置
    characters_dir: str = Field(default="data/characters", description="角色配置目录")
    enable_character_cache: bool = Field(default=True, description="启用角色缓存")
    character_cache_ttl: int = Field(
        default=3600,
        description="角色缓存TTL（秒）",
        ge=60,
        le=86400
    )
    
    # ============================================================================
    # 安全和限制配置
    # ============================================================================
    
    # 内容过滤
    enable_content_filter: bool = Field(default=True, description="启用内容过滤")
    max_message_length: int = Field(
        default=2000,
        description="最大消息长度",
        ge=50,
        le=5000
    )
    
    # API安全
    api_key_header: Optional[str] = Field(default=None, description="API密钥请求头")
    allowed_origins: List[str] = Field(
        default_factory=lambda: ["*"],
        description="允许的CORS源"
    )
    
    # 性能限制
    max_concurrent_requests: int = Field(
        default=10,
        description="最大并发请求数",
        ge=1,
        le=100
    )
    rate_limit_per_minute: int = Field(
        default=60,
        description="每分钟请求限制",
        ge=1,
        le=1000
    )
    
    # ============================================================================
    # 缓存配置
    # ============================================================================
    
    enable_response_cache: bool = Field(default=False, description="启用响应缓存")
    cache_ttl_seconds: int = Field(
        default=300,
        description="缓存TTL（秒）",
        ge=30,
        le=3600
    )
    
    # ============================================================================
    # 验证器
    # ============================================================================
    
    @validator("default_llm_provider")
    def validate_llm_provider(cls, v):
        """验证LLM提供商"""
        valid_providers = ["gemini", "deepseek"]
        if v.lower() not in valid_providers:
            raise ValueError(f"LLM提供商必须是: {', '.join(valid_providers)}")
        return v.lower()
    
    @validator("log_level")
    def validate_log_level(cls, v):
        """验证日志级别"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"日志级别必须是: {', '.join(valid_levels)}")
        return v.upper()
    
    @validator("environment")
    def validate_environment(cls, v):
        """验证运行环境"""
        valid_envs = ["development", "staging", "production"]
        if v.lower() not in valid_envs:
            raise ValueError(f"运行环境必须是: {', '.join(valid_envs)}")
        return v.lower()
    
    @validator("characters_dir")
    def validate_characters_dir(cls, v):
        """验证角色配置目录"""
        if not os.path.exists(v):
            # 如果目录不存在，尝试创建
            try:
                os.makedirs(v, exist_ok=True)
            except Exception as e:
                raise ValueError(f"无法创建角色配置目录 {v}: {e}")
        return v
    
    def validate_llm_config(self) -> None:
        """验证LLM配置完整性"""
        if self.default_llm_provider == "gemini" and not self.gemini_api_key:
            raise ValueError("使用Gemini时必须提供GEMINI_API_KEY")
        if self.default_llm_provider == "deepseek" and not self.deepseek_api_key:
            raise ValueError("使用DeepSeek时必须提供DEEPSEEK_API_KEY")
    
    class Config:
        """Pydantic配置"""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        
        # 环境变量前缀（可选）
        env_prefix = ""
        
        # 字段别名映射
        fields = {
            "gemini_api_key": {"env": "GEMINI_API_KEY"},
            "deepseek_api_key": {"env": "DEEPSEEK_API_KEY"},
            "deepseek_base_url": {"env": "DEEPSEEK_BASE_URL"},
        }


@lru_cache()
def get_settings() -> Settings:
    """
    获取应用配置实例（单例模式）
    
    使用lru_cache装饰器确保配置只加载一次。
    
    Returns:
        Settings: 配置实例
    """
    settings = Settings()
    
    # 验证LLM配置
    try:
        settings.validate_llm_config()
    except ValueError as e:
        print(f"配置验证警告: {e}")
    
    return settings


# 全局配置实例
settings = get_settings() 