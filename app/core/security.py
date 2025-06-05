"""
安全配置模块

提供API安全、内容过滤和请求验证功能。
"""

import re
import hashlib
import time
from typing import List, Optional, Dict, Any
from collections import defaultdict, deque
from .config import settings
from .exceptions import ContentFilterError, RateLimitExceededError, MessageTooLongError


class ContentFilter:
    """
    内容过滤器
    
    提供基础的内容安全过滤功能。
    """
    
    def __init__(self):
        # 敏感词列表（可根据需要扩展）
        self.forbidden_words = [
            # 基础敏感词示例
            "暴力", "色情", "赌博", "毒品",
            # 可以根据实际需求添加更多
        ]
        
        # 敏感模式（正则表达式）
        self.forbidden_patterns = [
            r"\b(?:攻击|伤害|杀害)\b",  # 暴力相关
            r"\b(?:18禁|成人|色情)\b",  # 成人内容
        ]
    
    def is_content_safe(self, content: str) -> tuple[bool, Optional[str]]:
        """
        检查内容是否安全
        
        Args:
            content: 要检查的内容
            
        Returns:
            tuple: (是否安全, 违规原因)
        """
        if not settings.enable_content_filter:
            return True, None
        
        # 检查消息长度
        if len(content) > settings.max_message_length:
            return False, f"消息长度超出限制({len(content)} > {settings.max_message_length})"
        
        # 检查敏感词
        content_lower = content.lower()
        for word in self.forbidden_words:
            if word in content_lower:
                return False, f"包含敏感词: {word}"
        
        # 检查敏感模式
        for pattern in self.forbidden_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return False, f"匹配敏感模式: {pattern}"
        
        return True, None
    
    def filter_content(self, content: str) -> str:
        """
        过滤并清理内容
        
        Args:
            content: 原始内容
            
        Returns:
            str: 过滤后的内容
            
        Raises:
            ContentFilterError: 内容不安全时抛出
        """
        is_safe, reason = self.is_content_safe(content)
        if not is_safe:
            raise ContentFilterError(reason)
        
        return content.strip()


class RateLimiter:
    """
    请求频率限制器
    
    基于内存的简单频率限制实现。
    """
    
    def __init__(self):
        # 存储每个客户端的请求时间戳
        self.client_requests: Dict[str, deque] = defaultdict(lambda: deque())
        self.cleanup_interval = 60  # 清理间隔（秒）
        self.last_cleanup = time.time()
    
    def _get_client_id(self, request) -> str:
        """
        获取客户端标识符
        
        Args:
            request: FastAPI请求对象
            
        Returns:
            str: 客户端标识符
        """
        # 优先使用IP地址作为客户端标识
        if hasattr(request, 'client') and request.client:
            return request.client.host
        return "unknown"
    
    def _cleanup_old_requests(self):
        """清理过期的请求记录"""
        current_time = time.time()
        if current_time - self.last_cleanup < self.cleanup_interval:
            return
        
        cutoff_time = current_time - 60  # 只保留最近一分钟的记录
        
        for client_id in list(self.client_requests.keys()):
            requests = self.client_requests[client_id]
            
            # 移除过期的请求记录
            while requests and requests[0] < cutoff_time:
                requests.popleft()
            
            # 如果队列为空，删除该客户端记录
            if not requests:
                del self.client_requests[client_id]
        
        self.last_cleanup = current_time
    
    def check_rate_limit(self, request) -> bool:
        """
        检查是否超出频率限制
        
        Args:
            request: FastAPI请求对象
            
        Returns:
            bool: 是否允许请求
            
        Raises:
            RateLimitExceededError: 超出频率限制时抛出
        """
        self._cleanup_old_requests()
        
        client_id = self._get_client_id(request)
        current_time = time.time()
        requests = self.client_requests[client_id]
        
        # 计算最近一分钟的请求数
        cutoff_time = current_time - 60
        recent_requests = sum(1 for req_time in requests if req_time > cutoff_time)
        
        # 检查是否超出限制
        if recent_requests >= settings.rate_limit_per_minute:
            raise RateLimitExceededError(settings.rate_limit_per_minute)
        
        # 记录本次请求
        requests.append(current_time)
        
        return True


class APIKeyValidator:
    """
    API密钥验证器
    
    提供可选的API密钥验证功能。
    """
    
    def __init__(self):
        self.api_key_header = settings.api_key_header
        self.valid_api_keys = set()  # 可以从配置或数据库加载
    
    def validate_api_key(self, request) -> bool:
        """
        验证API密钥
        
        Args:
            request: FastAPI请求对象
            
        Returns:
            bool: 是否验证通过
        """
        if not self.api_key_header:
            # 如果未配置API密钥验证，则跳过
            return True
        
        api_key = request.headers.get(self.api_key_header)
        if not api_key:
            return False
        
        # 这里可以实现更复杂的验证逻辑
        # 例如从数据库查询、密钥加密验证等
        return api_key in self.valid_api_keys
    
    def add_api_key(self, api_key: str):
        """添加有效的API密钥"""
        self.valid_api_keys.add(api_key)
    
    def remove_api_key(self, api_key: str):
        """移除API密钥"""
        self.valid_api_keys.discard(api_key)


class SecurityUtils:
    """
    安全工具类
    
    提供各种安全相关的工具函数。
    """
    
    @staticmethod
    def hash_string(text: str) -> str:
        """
        对字符串进行SHA256哈希
        
        Args:
            text: 要哈希的文本
            
        Returns:
            str: 哈希值
        """
        return hashlib.sha256(text.encode('utf-8')).hexdigest()
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        清理文件名，移除危险字符
        
        Args:
            filename: 原始文件名
            
        Returns:
            str: 清理后的文件名
        """
        # 移除或替换危险字符
        dangerous_chars = r'[<>:"/\\|?*]'
        safe_filename = re.sub(dangerous_chars, '_', filename)
        
        # 移除开头和结尾的空格和点
        safe_filename = safe_filename.strip('. ')
        
        # 限制长度
        if len(safe_filename) > 100:
            safe_filename = safe_filename[:100]
        
        return safe_filename
    
    @staticmethod
    def validate_character_id(character_id: str) -> bool:
        """
        验证角色ID格式
        
        Args:
            character_id: 角色ID
            
        Returns:
            bool: 是否有效
        """
        # 角色ID应该只包含字母、数字、下划线和连字符
        pattern = r'^[a-zA-Z0-9_-]{1,50}$'
        return bool(re.match(pattern, character_id))
    
    @staticmethod
    def validate_session_id(session_id: str) -> bool:
        """
        验证会话ID格式
        
        Args:
            session_id: 会话ID
            
        Returns:
            bool: 是否有效
        """
        # 会话ID通常是UUID格式或类似的标识符
        pattern = r'^[a-zA-Z0-9_-]{8,64}$'
        return bool(re.match(pattern, session_id))


# 全局实例
content_filter = ContentFilter()
rate_limiter = RateLimiter()
api_key_validator = APIKeyValidator()
security_utils = SecurityUtils() 