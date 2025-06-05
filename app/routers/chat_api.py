"""
聊天API路由 - 核心对话功能接口
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

# 初始化路由器
router = APIRouter(prefix="/api/v1", tags=["Chat API"])
logger = logging.getLogger(__name__)

# 请求/响应模型
class ChatRequest(BaseModel):
    character_id: str
    message: str
    user_id: Optional[str] = "anonymous"
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    success: bool
    data: Dict[str, Any]
    timestamp: str = datetime.now().isoformat()

class CharacterListResponse(BaseModel):
    success: bool
    data: List[Dict[str, Any]]
    timestamp: str = datetime.now().isoformat()

@router.get("/characters")
async def get_characters() -> CharacterListResponse:
    """获取所有可用角色列表"""
    characters_data = [
        {
            "id": "rei_ayanami",
            "name": "绫波零",
            "description": "沉默寡言的EVA驾驶员",
            "avatar_url": "/static/avatars/rei.png",
            "source": "新世纪福音战士",
            "personality_traits": ["冷淡", "神秘", "忠诚"],
            "available": True
        },
        {
            "id": "asuka_langley",
            "name": "明日香·兰格雷", 
            "description": "自信强势的德国EVA驾驶员",
            "avatar_url": "/static/avatars/asuka.png",
            "source": "新世纪福音战士",
            "personality_traits": ["强势", "骄傲", "活泼"],
            "available": True
        },
        {
            "id": "miku_hatsune",
            "name": "初音未来",
            "description": "充满活力的虚拟歌姬",
            "avatar_url": "/static/avatars/miku.png", 
            "source": "VOCALOID",
            "personality_traits": ["活泼", "乐观", "音乐"],
            "available": True
        }
    ]
    
    return CharacterListResponse(success=True, data=characters_data)

@router.post("/chat")
async def chat_with_character(request: ChatRequest) -> ChatResponse:
    """发送消息并获取AI回复"""
    
    # 模拟AI回复逻辑
    character_responses = {
        "rei_ayanami": f"...{request.message}。是吗。",
        "asuka_langley": f"哈？{request.message}！你说什么呢！",
        "miku_hatsune": f"哇！{request.message}♪ 听起来很棒呢！"
    }
    
    character_response = character_responses.get(
        request.character_id, 
        "抱歉，我现在无法回应。"
    )
    
    response_data = {
        "message": character_response,
        "character_id": request.character_id,
        "timestamp": datetime.now().isoformat(),
        "metadata": {
            "emotion_detected": "neutral",
            "response_time_ms": 800,
            "confidence_score": 0.85,
            "character_state": {
                "mood": "neutral",
                "energy_level": 75,
                "relationship_level": "acquaintance"
            }
        }
    }
    
    return ChatResponse(success=True, data=response_data)

@router.get("/conversations/{session_id}/messages")
async def get_conversation_history(
    session_id: str,
    page: int = 1,
    limit: int = 50
):
    """获取对话历史"""
    
    # 模拟对话历史数据
    messages = [
        {
            "id": f"msg_{i}",
            "role": "user" if i % 2 == 0 else "assistant",
            "content": f"这是第{i}条消息",
            "timestamp": datetime.now().isoformat(),
            "character_id": "rei_ayanami" if i % 2 == 1 else None
        }
        for i in range(1, min(limit + 1, 11))
    ]
    
    response_data = {
        "messages": messages,
        "pagination": {
            "current_page": page,
            "total_pages": 3,
            "total_messages": 30,
            "has_next": page < 3
        }
    }
    
    return {"success": True, "data": response_data} 