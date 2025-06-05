"""
消息数据模型

定义聊天消息、请求和响应的数据结构。
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from . import MessageRole, MessageStatus


class Message(BaseModel):
    """
    消息模型
    
    表示聊天系统中的单条消息，包含消息内容、元数据和统计信息。
    """
    
    # 基础标识
    id: str = Field(..., description="消息唯一标识符")
    session_id: str = Field(..., description="所属会话ID")
    character_id: Optional[str] = Field(None, description="关联的角色ID")
    
    # 消息内容
    role: MessageRole = Field(..., description="消息角色（用户/助手/系统）")
    content: str = Field(..., description="消息内容", min_length=1, max_length=5000)
    
    # 时间和状态
    timestamp: datetime = Field(default_factory=datetime.now, description="消息时间戳")
    status: MessageStatus = Field(default=MessageStatus.COMPLETED, description="消息状态")
    
    # LLM相关统计
    tokens_used: Optional[int] = Field(None, description="使用的token数量", ge=0)
    response_time: Optional[float] = Field(None, description="响应时间（秒）", ge=0.0)
    model_used: Optional[str] = Field(None, description="使用的LLM模型名称")
    provider_used: Optional[str] = Field(None, description="使用的LLM提供商")
    
    # 扩展数据
    metadata: Dict[str, Any] = Field(default_factory=dict, description="扩展元数据")
    
    class Config:
        """Pydantic配置"""
        json_schema_extra = {
            "example": {
                "id": "msg_12345",
                "session_id": "session_67890",
                "character_id": "tsundere_alice",
                "role": "assistant",
                "content": "哼！你终于来找我了？才不是因为担心你呢...",
                "status": "completed",
                "tokens_used": 45,
                "response_time": 1.2,
                "model_used": "gemini-1.5-pro",
                "provider_used": "gemini"
            }
        }


class ChatRequest(BaseModel):
    """
    聊天请求模型
    
    用户发送消息的请求格式。
    """
    
    message: str = Field(
        ..., 
        description="用户消息内容",
        min_length=1, 
        max_length=2000
    )
    character_id: str = Field(
        ..., 
        description="要对话的角色ID",
        min_length=1,
        max_length=50
    )
    session_id: Optional[str] = Field(
        None, 
        description="会话ID，不提供则创建新会话"
    )
    
    # 可选的LLM参数覆盖
    temperature: Optional[float] = Field(
        None, 
        description="覆盖角色默认的温度参数",
        ge=0.0,
        le=2.0
    )
    max_tokens: Optional[int] = Field(
        None,
        description="覆盖角色默认的最大token数",
        ge=50,
        le=2000
    )
    
    class Config:
        """Pydantic配置"""
        json_schema_extra = {
            "example": {
                "message": "艾莉丝，今天过得怎么样？",
                "character_id": "tsundere_alice",
                "session_id": "session_67890"
            }
        }


class ChatResponse(BaseModel):
    """
    聊天响应模型
    
    AI回复消息的响应格式。
    """
    
    # 基础响应信息
    message_id: str = Field(..., description="生成的消息ID")
    session_id: str = Field(..., description="会话ID")
    content: str = Field(..., description="AI回复内容")
    
    # 角色信息
    character_id: str = Field(..., description="回复的角色ID")
    character_name: str = Field(..., description="角色名称")
    
    # 时间和统计
    timestamp: datetime = Field(..., description="回复生成时间")
    tokens_used: Optional[int] = Field(None, description="使用的token数量")
    response_time: Optional[float] = Field(None, description="响应时间（秒）")
    
    # LLM信息
    model_used: Optional[str] = Field(None, description="使用的模型")
    provider_used: Optional[str] = Field(None, description="使用的提供商")
    
    class Config:
        """Pydantic配置"""
        json_schema_extra = {
            "example": {
                "message_id": "msg_12345",
                "session_id": "session_67890",
                "content": "哼！你终于来找我了？才不是因为担心你呢...",
                "character_id": "tsundere_alice",
                "character_name": "艾莉丝",
                "tokens_used": 45,
                "response_time": 1.2,
                "model_used": "gemini-1.5-pro",
                "provider_used": "gemini"
            }
        }


class StreamChatResponse(BaseModel):
    """
    流式聊天响应模型
    
    用于流式返回AI回复的数据块。
    """
    
    session_id: str = Field(..., description="会话ID")
    character_id: str = Field(..., description="角色ID")
    content_delta: str = Field(..., description="本次传输的内容增量")
    is_complete: bool = Field(default=False, description="是否是完整响应的最后一块")
    
    # 仅在最后一块中包含的统计信息
    total_tokens: Optional[int] = Field(None, description="总token使用量")
    total_response_time: Optional[float] = Field(None, description="总响应时间")
    
    class Config:
        """Pydantic配置"""
        json_schema_extra = {
            "example": {
                "session_id": "session_67890",
                "character_id": "tsundere_alice",
                "content_delta": "哼！你终于",
                "is_complete": False
            }
        } 