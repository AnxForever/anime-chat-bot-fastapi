"""
日志工具类

适配 Cloudflare Workers 环境的日志记录器。
"""

import json
from datetime import datetime
from typing import Any, Dict, Optional
from enum import Enum

class LogLevel(Enum):
    """日志级别枚举"""
    DEBUG = "DEBUG"
    INFO = "INFO" 
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class WorkersLogger:
    """Workers 环境日志记录器"""
    
    def __init__(self, name: str, level: LogLevel = LogLevel.INFO):
        self.name = name
        self.level = level
        
        # 日志级别优先级
        self.level_priority = {
            LogLevel.DEBUG: 10,
            LogLevel.INFO: 20,
            LogLevel.WARNING: 30,
            LogLevel.ERROR: 40,
            LogLevel.CRITICAL: 50
        }
    
    def _should_log(self, level: LogLevel) -> bool:
        """检查是否应该记录此级别的日志"""
        return self.level_priority[level] >= self.level_priority[self.level]
    
    def _format_message(self, level: LogLevel, message: str, extra: Optional[Dict[str, Any]] = None) -> str:
        """格式化日志消息"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level.value,
            "logger": self.name,
            "message": message
        }
        
        if extra:
            log_entry["extra"] = extra
        
        return json.dumps(log_entry, ensure_ascii=False)
    
    def _output(self, formatted_message: str, level: LogLevel):
        """输出日志消息"""
        # 在 Cloudflare Workers 中，console.log 是主要的日志输出方式
        if level in [LogLevel.ERROR, LogLevel.CRITICAL]:
            print(f"ERROR: {formatted_message}")
        elif level == LogLevel.WARNING:
            print(f"WARN: {formatted_message}")
        else:
            print(formatted_message)
    
    def debug(self, message: str, **kwargs):
        """记录调试信息"""
        if self._should_log(LogLevel.DEBUG):
            formatted = self._format_message(LogLevel.DEBUG, message, kwargs if kwargs else None)
            self._output(formatted, LogLevel.DEBUG)
    
    def info(self, message: str, **kwargs):
        """记录信息"""
        if self._should_log(LogLevel.INFO):
            formatted = self._format_message(LogLevel.INFO, message, kwargs if kwargs else None)
            self._output(formatted, LogLevel.INFO)
    
    def warning(self, message: str, **kwargs):
        """记录警告"""
        if self._should_log(LogLevel.WARNING):
            formatted = self._format_message(LogLevel.WARNING, message, kwargs if kwargs else None)
            self._output(formatted, LogLevel.WARNING)
    
    def error(self, message: str, **kwargs):
        """记录错误"""
        if self._should_log(LogLevel.ERROR):
            formatted = self._format_message(LogLevel.ERROR, message, kwargs if kwargs else None)
            self._output(formatted, LogLevel.ERROR)
    
    def critical(self, message: str, **kwargs):
        """记录严重错误"""
        if self._should_log(LogLevel.CRITICAL):
            formatted = self._format_message(LogLevel.CRITICAL, message, kwargs if kwargs else None)
            self._output(formatted, LogLevel.CRITICAL)
    
    def exception(self, message: str, exc_info: Optional[Exception] = None, **kwargs):
        """记录异常信息"""
        extra_data = kwargs.copy() if kwargs else {}
        
        if exc_info:
            extra_data["exception_type"] = type(exc_info).__name__
            extra_data["exception_message"] = str(exc_info)
        
        self.error(message, **extra_data)

# 全局日志器实例
_loggers: Dict[str, WorkersLogger] = {}

def get_logger(name: str, level: LogLevel = LogLevel.INFO) -> WorkersLogger:
    """
    获取日志器实例
    
    Args:
        name: 日志器名称
        level: 日志级别
        
    Returns:
        WorkersLogger: 日志器实例
    """
    if name not in _loggers:
        _loggers[name] = WorkersLogger(name, level)
    
    return _loggers[name]

def set_global_log_level(level: LogLevel):
    """
    设置全局日志级别
    
    Args:
        level: 新的日志级别
    """
    for logger in _loggers.values():
        logger.level = level

def log_request_info(request_data: Dict[str, Any], logger: WorkersLogger):
    """
    记录请求信息
    
    Args:
        request_data: 请求数据
        logger: 日志器实例
    """
    logger.info(
        "处理请求",
        method=request_data.get('method'),
        path=request_data.get('path'),
        user_agent=request_data.get('headers', {}).get('user-agent'),
        client_ip=_get_client_ip_from_headers(request_data.get('headers', {}))
    )

def log_response_info(status_code: int, processing_time: float, logger: WorkersLogger):
    """
    记录响应信息
    
    Args:
        status_code: HTTP 状态码
        processing_time: 处理时间（秒）
        logger: 日志器实例
    """
    logger.info(
        "响应完成",
        status_code=status_code,
        processing_time_ms=round(processing_time * 1000, 2)
    )

def log_llm_request(provider: str, model: str, tokens_used: int, response_time: float, logger: WorkersLogger):
    """
    记录 LLM 请求信息
    
    Args:
        provider: LLM 提供商
        model: 使用的模型
        tokens_used: 使用的 token 数量
        response_time: 响应时间
        logger: 日志器实例
    """
    logger.info(
        "LLM 请求完成",
        provider=provider,
        model=model,
        tokens_used=tokens_used,
        response_time_ms=round(response_time * 1000, 2)
    )

def log_error_with_context(error: Exception, context: Dict[str, Any], logger: WorkersLogger):
    """
    记录带上下文的错误信息
    
    Args:
        error: 异常对象
        context: 错误上下文
        logger: 日志器实例
    """
    logger.exception(
        f"发生错误: {str(error)}",
        exc_info=error,
        **context
    )

def _get_client_ip_from_headers(headers: Dict[str, str]) -> str:
    """从请求头中获取客户端 IP"""
    ip_headers = [
        'cf-connecting-ip',
        'x-forwarded-for', 
        'x-real-ip',
        'x-client-ip'
    ]
    
    for header in ip_headers:
        ip = headers.get(header)
        if ip:
            return ip.split(',')[0].strip()
    
    return 'unknown' 