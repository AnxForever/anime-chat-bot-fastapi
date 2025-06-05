"""
自定义异常类

定义项目中使用的各种业务异常，提供清晰的错误处理机制。
"""

from typing import Optional, Dict, Any


class AnimeChaBotException(Exception):
    """
    聊天机器人基础异常类
    
    所有业务异常的基类，提供统一的异常处理接口。
    """
    
    def __init__(
        self, 
        message: str, 
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}


class CharacterNotFoundError(AnimeChaBotException):
    """角色未找到异常"""
    
    def __init__(self, character_id: str):
        super().__init__(
            message=f"角色未找到: {character_id}",
            error_code="CHARACTER_NOT_FOUND",
            details={"character_id": character_id}
        )


class CharacterLoadError(AnimeChaBotException):
    """角色加载异常"""
    
    def __init__(self, character_id: str, reason: str):
        super().__init__(
            message=f"角色加载失败: {character_id} - {reason}",
            error_code="CHARACTER_LOAD_ERROR",
            details={"character_id": character_id, "reason": reason}
        )


class SessionNotFoundError(AnimeChaBotException):
    """会话未找到异常"""
    
    def __init__(self, session_id: str):
        super().__init__(
            message=f"会话未找到: {session_id}",
            error_code="SESSION_NOT_FOUND",
            details={"session_id": session_id}
        )


class SessionExpiredError(AnimeChaBotException):
    """会话过期异常"""
    
    def __init__(self, session_id: str):
        super().__init__(
            message=f"会话已过期: {session_id}",
            error_code="SESSION_EXPIRED",
            details={"session_id": session_id}
        )


class LLMProviderError(AnimeChaBotException):
    """LLM提供商异常"""
    
    def __init__(self, provider: str, reason: str):
        super().__init__(
            message=f"LLM提供商错误 ({provider}): {reason}",
            error_code="LLM_PROVIDER_ERROR",
            details={"provider": provider, "reason": reason}
        )


class LLMAPIError(AnimeChaBotException):
    """LLM API调用异常"""
    
    def __init__(self, provider: str, api_error: str, status_code: Optional[int] = None):
        super().__init__(
            message=f"LLM API调用失败 ({provider}): {api_error}",
            error_code="LLM_API_ERROR",
            details={
                "provider": provider, 
                "api_error": api_error,
                "status_code": status_code
            }
        )


class LLMTimeoutError(AnimeChaBotException):
    """LLM请求超时异常"""
    
    def __init__(self, provider: str, timeout_seconds: int):
        super().__init__(
            message=f"LLM请求超时 ({provider}): {timeout_seconds}秒",
            error_code="LLM_TIMEOUT_ERROR",
            details={"provider": provider, "timeout_seconds": timeout_seconds}
        )


class ContentFilterError(AnimeChaBotException):
    """内容过滤异常"""
    
    def __init__(self, reason: str):
        super().__init__(
            message=f"内容被过滤: {reason}",
            error_code="CONTENT_FILTERED",
            details={"reason": reason}
        )


class MessageTooLongError(AnimeChaBotException):
    """消息过长异常"""
    
    def __init__(self, message_length: int, max_length: int):
        super().__init__(
            message=f"消息长度超出限制: {message_length} > {max_length}",
            error_code="MESSAGE_TOO_LONG",
            details={"message_length": message_length, "max_length": max_length}
        )


class SessionLimitExceededError(AnimeChaBotException):
    """会话数量超出限制异常"""
    
    def __init__(self, current_sessions: int, max_sessions: int):
        super().__init__(
            message=f"会话数量超出限制: {current_sessions} >= {max_sessions}",
            error_code="SESSION_LIMIT_EXCEEDED",
            details={"current_sessions": current_sessions, "max_sessions": max_sessions}
        )


class RateLimitExceededError(AnimeChaBotException):
    """请求频率超出限制异常"""
    
    def __init__(self, limit_per_minute: int):
        super().__init__(
            message=f"请求频率超出限制: 每分钟最多 {limit_per_minute} 次",
            error_code="RATE_LIMIT_EXCEEDED",
            details={"limit_per_minute": limit_per_minute}
        )


class ConfigurationError(AnimeChaBotException):
    """配置错误异常"""
    
    def __init__(self, config_name: str, reason: str):
        super().__init__(
            message=f"配置错误 ({config_name}): {reason}",
            error_code="CONFIGURATION_ERROR",
            details={"config_name": config_name, "reason": reason}
        )


class PromptBuildError(AnimeChaBotException):
    """提示词构建异常"""
    
    def __init__(self, character_id: str, reason: str):
        super().__init__(
            message=f"提示词构建失败 ({character_id}): {reason}",
            error_code="PROMPT_BUILD_ERROR",
            details={"character_id": character_id, "reason": reason}
        )


class ValidationError(AnimeChaBotException):
    """数据验证异常"""
    
    def __init__(self, field: str, value: Any, reason: str):
        super().__init__(
            message=f"数据验证失败 ({field}): {reason}",
            error_code="VALIDATION_ERROR",
            details={"field": field, "value": str(value), "reason": reason}
        ) 