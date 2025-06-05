"""
数据模型包

包含所有的Pydantic数据模型和枚举类型。
"""

from enum import Enum


class CharacterType(str, Enum):
    """角色类型枚举"""
    ANIME = "anime"
    GAME = "game"
    NOVEL = "novel"
    ORIGINAL = "original"


class MessageRole(str, Enum):
    """消息角色枚举"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class MessageStatus(str, Enum):
    """消息状态枚举"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class SessionStatus(str, Enum):
    """会话状态枚举"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class LLMProvider(str, Enum):
    """LLM提供商枚举"""
    GEMINI = "gemini"
    DEEPSEEK = "deepseek"


# 导入所有数据模型
from .character import Character, CharacterSummary
from .message import Message, ChatRequest, ChatResponse, StreamChatResponse
from .session import Session, SessionSummary, SessionCreate

# 公开导出的模型和枚举
__all__ = [
    # 枚举类型
    "CharacterType",
    "MessageRole", 
    "MessageStatus",
    "SessionStatus",
    "LLMProvider",
    
    # 角色模型
    "Character",
    "CharacterSummary",
    
    # 消息模型
    "Message",
    "ChatRequest", 
    "ChatResponse",
    "StreamChatResponse",
    
    # 会话模型
    "Session",
    "SessionSummary",
    "SessionCreate",
] 