"""
WebSocket流式响应路由 - 支持实时对话
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from fastapi.websockets import WebSocketState
import json
import asyncio
import logging
from typing import Dict, List
from datetime import datetime

logger = logging.getLogger(__name__)

# WebSocket路由器
router = APIRouter()

# 连接管理器
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_sessions: Dict[str, str] = {}  # websocket_id -> user_id
    
    async def connect(self, websocket: WebSocket, session_id: str):
        """接受WebSocket连接"""
        await websocket.accept()
        self.active_connections[session_id] = websocket
        logger.info(f"WebSocket连接已建立: {session_id}")
    
    def disconnect(self, session_id: str):
        """断开WebSocket连接"""
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            if session_id in self.user_sessions:
                del self.user_sessions[session_id]
            logger.info(f"WebSocket连接已断开: {session_id}")
    
    async def send_message(self, session_id: str, message: dict):
        """发送消息到指定连接"""
        if session_id in self.active_connections:
            websocket = self.active_connections[session_id]
            if websocket.client_state == WebSocketState.CONNECTED:
                try:
                    await websocket.send_text(json.dumps(message, ensure_ascii=False))
                except Exception as e:
                    logger.error(f"发送消息失败: {e}")
                    self.disconnect(session_id)
    
    async def send_streaming_response(self, session_id: str, character_id: str, response_text: str):
        """发送流式响应"""
        if session_id not in self.active_connections:
            return
        
        # 发送开始信号
        await self.send_message(session_id, {
            "type": "response_start",
            "character_id": character_id,
            "timestamp": datetime.now().isoformat()
        })
        
        # 模拟逐字输出
        words = response_text.split()
        current_text = ""
        
        for i, word in enumerate(words):
            current_text += word + (" " if i < len(words) - 1 else "")
            
            # 发送当前文本块
            await self.send_message(session_id, {
                "type": "response_chunk",
                "character_id": character_id,
                "content": word + (" " if i < len(words) - 1 else ""),
                "full_content": current_text,
                "is_complete": False,
                "chunk_index": i,
                "timestamp": datetime.now().isoformat()
            })
            
            # 模拟打字延迟
            await asyncio.sleep(0.1)
        
        # 发送完成信号
        await self.send_message(session_id, {
            "type": "response_complete",
            "character_id": character_id,
            "full_message": response_text,
            "timestamp": datetime.now().isoformat(),
            "metadata": {
                "total_chunks": len(words),
                "response_time_ms": len(words) * 100,
                "character_mood": "neutral"
            }
        })

# 全局连接管理器
manager = ConnectionManager()

@router.websocket("/ws/chat/{session_id}")
async def websocket_chat_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket聊天端点"""
    await manager.connect(websocket, session_id)
    
    try:
        while True:
            # 接收客户端消息
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            message_type = message_data.get("type")
            
            if message_type == "user_message":
                await handle_user_message(session_id, message_data)
            elif message_type == "typing_start":
                await handle_typing_status(session_id, True)
            elif message_type == "typing_stop":
                await handle_typing_status(session_id, False)
            elif message_type == "ping":
                await manager.send_message(session_id, {"type": "pong", "timestamp": datetime.now().isoformat()})
            
    except WebSocketDisconnect:
        manager.disconnect(session_id)
        logger.info(f"WebSocket连接断开: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket错误: {e}")
        manager.disconnect(session_id)

async def handle_user_message(session_id: str, message_data: dict):
    """处理用户消息"""
    character_id = message_data.get("character_id")
    user_message = message_data.get("message")
    
    # 发送用户消息确认
    await manager.send_message(session_id, {
        "type": "user_message_received",
        "message": user_message,
        "timestamp": datetime.now().isoformat()
    })
    
    # 发送AI正在思考状态
    await manager.send_message(session_id, {
        "type": "ai_thinking",
        "character_id": character_id,
        "status": "thinking",
        "timestamp": datetime.now().isoformat()
    })
    
    # 模拟AI思考时间
    await asyncio.sleep(1.5)
    
    # 生成角色回复（这里应该调用AI服务）
    character_responses = {
        "rei_ayanami": f"...{user_message}。是吗。我明白了。",
        "asuka_langley": f"哈？{user_message}！你这家伙在说什么呢！",
        "miku_hatsune": f"哇！{user_message}♪ 这真是太棒了呢！我们一起来创作音乐吧！"
    }
    
    response_text = character_responses.get(character_id, "我现在无法回应...")
    
    # 发送流式响应
    await manager.send_streaming_response(session_id, character_id, response_text)

async def handle_typing_status(session_id: str, is_typing: bool):
    """处理打字状态"""
    await manager.send_message(session_id, {
        "type": "typing_status",
        "is_typing": is_typing,
        "timestamp": datetime.now().isoformat()
    })

@router.get("/ws/status")
async def get_websocket_status():
    """获取WebSocket连接状态"""
    return {
        "active_connections": len(manager.active_connections),
        "connections": list(manager.active_connections.keys()),
        "status": "healthy"
    } 