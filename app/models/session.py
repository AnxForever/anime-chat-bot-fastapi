"""
会话数据模型

定义聊天会话的数据结构和状态管理。
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from .message import Message
from . import SessionStatus


class Session(BaseModel):
    """
    会话模型
    
    管理用户与特定角色的完整对话会话，包含消息历史、
    状态信息和统计数据。
    """
    
    # 基础标识
    id: str = Field(..., description="会话唯一标识符")
    character_id: str = Field(..., description="当前会话的角色ID")
    
    # 会话状态
    status: SessionStatus = Field(default=SessionStatus.ACTIVE, description="会话状态")
    created_at: datetime = Field(default_factory=datetime.now, description="会话创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="最后更新时间")
    last_active_at: datetime = Field(default_factory=datetime.now, description="最后活跃时间")
    
    # 消息历史
    messages: List[Message] = Field(default_factory=list, description="会话消息历史")
    
    # 统计信息
    total_messages: int = Field(default=0, description="总消息数量")
    user_messages: int = Field(default=0, description="用户消息数量")
    assistant_messages: int = Field(default=0, description="助手消息数量")
    total_tokens: int = Field(default=0, description="总token使用量")
    total_response_time: float = Field(default=0.0, description="累计响应时间")
    
    # 配置选项
    max_messages: int = Field(
        default=50, 
        description="最大消息历史长度",
        ge=10,
        le=200
    )
    auto_archive_after: Optional[int] = Field(
        default=24, 
        description="自动归档时间（小时）",
        ge=1,
        le=168  # 一周
    )
    
    # 扩展数据
    metadata: Dict[str, Any] = Field(default_factory=dict, description="会话扩展元数据")
    
    def add_message(self, message: Message) -> None:
        """
        添加消息到会话
        
        Args:
            message: 要添加的消息对象
        """
        self.messages.append(message)
        self.total_messages += 1
        self.updated_at = datetime.now()
        self.last_active_at = datetime.now()
        
        # 更新统计信息
        if message.role.value == "user":
            self.user_messages += 1
        elif message.role.value == "assistant":
            self.assistant_messages += 1
            
        if message.tokens_used:
            self.total_tokens += message.tokens_used
            
        if message.response_time:
            self.total_response_time += message.response_time
        
        # 限制消息历史长度
        if len(self.messages) > self.max_messages:
            # 保留最新的消息，删除最旧的（但保留第一条系统消息）
            system_messages = [msg for msg in self.messages if msg.role.value == "system"]
            other_messages = [msg for msg in self.messages if msg.role.value != "system"]
            
            # 保留系统消息和最新的非系统消息
            keep_count = self.max_messages - len(system_messages)
            if keep_count > 0:
                self.messages = system_messages + other_messages[-keep_count:]
            else:
                self.messages = system_messages[:self.max_messages]
    
    def get_context_messages(self, max_tokens: int = 4000) -> List[Dict[str, str]]:
        """
        获取适合LLM的上下文消息列表
        
        Args:
            max_tokens: 最大token限制
            
        Returns:
            格式化的消息列表
        """
        context_messages = []
        estimated_tokens = 0
        
        # 从最新消息开始倒序处理
        for message in reversed(self.messages):
            # 粗略估算token数（中文字符约等于1.5个token）
            estimated_msg_tokens = len(message.content) * 1.5
            
            if estimated_tokens + estimated_msg_tokens > max_tokens:
                break
                
            context_messages.insert(0, {
                "role": message.role.value,
                "content": message.content
            })
            estimated_tokens += estimated_msg_tokens
        
        return context_messages
    
    def is_expired(self) -> bool:
        """
        检查会话是否已过期
        
        Returns:
            是否过期
        """
        if not self.auto_archive_after:
            return False
            
        hours_since_active = (datetime.now() - self.last_active_at).total_seconds() / 3600
        return hours_since_active > self.auto_archive_after
    
    class Config:
        """Pydantic配置"""
        json_schema_extra = {
            "example": {
                "id": "session_67890",
                "character_id": "tsundere_alice",
                "status": "active",
                "total_messages": 10,
                "user_messages": 5,
                "assistant_messages": 5,
                "total_tokens": 450,
                "total_response_time": 12.5,
                "max_messages": 50,
                "auto_archive_after": 24
            }
        }


class SessionSummary(BaseModel):
    """
    会话摘要模型
    
    用于会话列表显示，只包含基本信息。
    """
    
    id: str = Field(..., description="会话ID")
    character_id: str = Field(..., description="角色ID")
    character_name: Optional[str] = Field(None, description="角色名称")
    status: SessionStatus = Field(..., description="会话状态")
    created_at: datetime = Field(..., description="创建时间")
    last_active_at: datetime = Field(..., description="最后活跃时间")
    total_messages: int = Field(..., description="总消息数")
    last_message_preview: Optional[str] = Field(None, description="最后一条消息预览")


class SessionCreate(BaseModel):
    """
    创建会话请求模型
    """
    
    character_id: str = Field(..., description="角色ID", min_length=1, max_length=50)
    max_messages: Optional[int] = Field(
        default=50,
        description="最大消息数",
        ge=10,
        le=200
    )
    auto_archive_after: Optional[int] = Field(
        default=24,
        description="自动归档时间（小时）",
        ge=1,
        le=168
    ) 