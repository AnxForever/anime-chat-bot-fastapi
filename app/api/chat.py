"""
聊天API路由
提供与角色对话的接口
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
import json
import asyncio
from typing import Optional, Dict, Any
import uuid

from ..models import ChatRequest, ChatResponse, StreamChatResponse, MessageRole, MessageStatus
from ..services import CharacterLoader, SessionManager, LLMConnector, PromptBuilder
from ..core.exceptions import CharacterNotFoundError, SessionNotFoundError, LLMError, ValidationError
from ..core.security import ContentFilter, RateLimiter
from ..core.config import get_settings

router = APIRouter(prefix="/api/chat", tags=["chat"])

# 依赖注入
def get_character_loader():
    return CharacterLoader()

def get_session_manager():
    return SessionManager()

def get_llm_connector():
    return LLMConnector()

def get_prompt_builder():
    return PromptBuilder()

def get_content_filter():
    return ContentFilter()

def get_rate_limiter():
    return RateLimiter()

@router.post("/send", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    character_loader: CharacterLoader = Depends(get_character_loader),
    session_manager: SessionManager = Depends(get_session_manager),
    llm_connector: LLMConnector = Depends(get_llm_connector),
    prompt_builder: PromptBuilder = Depends(get_prompt_builder),
    content_filter: ContentFilter = Depends(get_content_filter),
    rate_limiter: RateLimiter = Depends(get_rate_limiter)
):
    """
    发送消息给角色并获取回复
    
    Args:
        request: 聊天请求，包含角色ID、用户消息和会话ID（可选）
        
    Returns:
        ChatResponse: 包含角色回复的响应
        
    Raises:
        HTTPException: 当角色不存在、内容不当或达到速率限制时
    """
    try:
        # 内容过滤
        if not await content_filter.is_content_safe(request.user_message):
            raise HTTPException(status_code=400, detail="消息内容不当，请修改后重试")
        
        # 速率限制检查
        if not await rate_limiter.check_rate_limit(request.session_id or "anonymous"):
            raise HTTPException(status_code=429, detail="请求过于频繁，请稍后重试")
        
        # 加载角色
        character = await character_loader.get_character(request.character_id)
        if not character:
            raise HTTPException(status_code=404, detail=f"角色 {request.character_id} 不存在")
        
        # 获取或创建会话
        session_id = request.session_id or str(uuid.uuid4())
        session = await session_manager.get_session(session_id)
        if not session:
            session = await session_manager.create_session(
                session_id=session_id,
                character_id=request.character_id,
                user_id=request.user_id
            )
        
        # 添加用户消息到会话
        user_message = await session.add_message(
            role=MessageRole.USER,
            content=request.user_message,
            metadata={"timestamp": request.timestamp}
        )
        
        # 构建提示词
        system_prompt = await prompt_builder.build_character_prompt(character)
        conversation_context = await prompt_builder.build_conversation_context(session)
        
        # 调用LLM获取回复
        assistant_content = await llm_connector.generate_response(
            character=character,
            system_prompt=system_prompt,
            conversation_context=conversation_context,
            user_message=request.user_message
        )
        
        # 添加助手消息到会话
        assistant_message = await session.add_message(
            role=MessageRole.ASSISTANT,
            content=assistant_content,
            metadata={"model": character.llm_config.provider.value}
        )
        
        # 保存会话状态
        await session_manager.save_session(session)
        
        # 后台任务：更新会话统计
        background_tasks.add_task(
            session_manager.update_session_stats, 
            session_id, 
            len(request.user_message), 
            len(assistant_content)
        )
        
        return ChatResponse(
            character_id=request.character_id,
            session_id=session_id,
            assistant_message=assistant_content,
            message_id=assistant_message.id,
            timestamp=assistant_message.timestamp
        )
        
    except CharacterNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except LLMError as e:
        raise HTTPException(status_code=503, detail=f"AI服务暂时不可用: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {str(e)}")


@router.post("/stream", response_class=StreamingResponse)
async def stream_message(
    request: ChatRequest,
    character_loader: CharacterLoader = Depends(get_character_loader),
    session_manager: SessionManager = Depends(get_session_manager),
    llm_connector: LLMConnector = Depends(get_llm_connector),
    prompt_builder: PromptBuilder = Depends(get_prompt_builder),
    content_filter: ContentFilter = Depends(get_content_filter),
    rate_limiter: RateLimiter = Depends(get_rate_limiter)
):
    """
    流式发送消息给角色并获取实时回复
    
    Args:
        request: 聊天请求
        
    Returns:
        StreamingResponse: 服务器发送事件流
    """
    
    async def generate_stream():
        try:
            # 内容过滤和速率限制
            if not await content_filter.is_content_safe(request.user_message):
                yield f"data: {json.dumps({'error': '消息内容不当，请修改后重试'})}\n\n"
                return
            
            if not await rate_limiter.check_rate_limit(request.session_id or "anonymous"):
                yield f"data: {json.dumps({'error': '请求过于频繁，请稍后重试'})}\n\n"
                return
            
            # 加载角色和会话
            character = await character_loader.get_character(request.character_id)
            if not character:
                yield f"data: {json.dumps({'error': f'角色 {request.character_id} 不存在'})}\n\n"
                return
            
            session_id = request.session_id or str(uuid.uuid4())
            session = await session_manager.get_session(session_id)
            if not session:
                session = await session_manager.create_session(
                    session_id=session_id,
                    character_id=request.character_id,
                    user_id=request.user_id
                )
            
            # 添加用户消息
            user_message = await session.add_message(
                role=MessageRole.USER,
                content=request.user_message
            )
            
            # 构建提示词
            system_prompt = await prompt_builder.build_character_prompt(character)
            conversation_context = await prompt_builder.build_conversation_context(session)
            
            # 发送开始事件
            yield f"data: {json.dumps(StreamChatResponse(type='start', session_id=session_id).dict())}\n\n"
            
            # 流式生成回复
            full_content = ""
            async for chunk in llm_connector.stream_response(
                character=character,
                system_prompt=system_prompt,
                conversation_context=conversation_context,
                user_message=request.user_message
            ):
                if chunk:
                    full_content += chunk
                    response = StreamChatResponse(
                        type="chunk",
                        session_id=session_id,
                        content=chunk,
                        full_content=full_content
                    )
                    yield f"data: {json.dumps(response.dict())}\n\n"
            
            # 添加完整的助手消息到会话
            assistant_message = await session.add_message(
                role=MessageRole.ASSISTANT,
                content=full_content,
                metadata={"model": character.llm_config.provider.value}
            )
            
            # 保存会话
            await session_manager.save_session(session)
            
            # 发送结束事件
            end_response = StreamChatResponse(
                type="end",
                session_id=session_id,
                message_id=assistant_message.id,
                full_content=full_content
            )
            yield f"data: {json.dumps(end_response.dict())}\n\n"
            
        except Exception as e:
            error_response = StreamChatResponse(
                type="error",
                session_id=request.session_id or "",
                error=str(e)
            )
            yield f"data: {json.dumps(error_response.dict())}\n\n"
    
    return EventSourceResponse(generate_stream())


@router.get("/sessions/{session_id}")
async def get_session_info(
    session_id: str,
    session_manager: SessionManager = Depends(get_session_manager)
):
    """
    获取会话信息
    
    Args:
        session_id: 会话ID
        
    Returns:
        dict: 会话信息
    """
    try:
        session = await session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="会话不存在")
        
        return {
            "session_id": session.session_id,
            "character_id": session.character_id,
            "user_id": session.user_id,
            "created_at": session.created_at,
            "updated_at": session.updated_at,
            "message_count": len(session.messages),
            "status": session.status.value
        }
        
    except SessionNotFoundError:
        raise HTTPException(status_code=404, detail="会话不存在")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    session_manager: SessionManager = Depends(get_session_manager)
):
    """
    删除会话
    
    Args:
        session_id: 会话ID
        
    Returns:
        dict: 删除结果
    """
    try:
        success = await session_manager.delete_session(session_id)
        if not success:
            raise HTTPException(status_code=404, detail="会话不存在")
        
        return {"message": "会话已删除", "session_id": session_id}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/messages")
async def get_session_messages(
    session_id: str,
    limit: Optional[int] = 50,
    offset: Optional[int] = 0,
    session_manager: SessionManager = Depends(get_session_manager)
):
    """
    获取会话消息历史
    
    Args:
        session_id: 会话ID
        limit: 返回消息数量限制
        offset: 偏移量
        
    Returns:
        dict: 消息列表和分页信息
    """
    try:
        session = await session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="会话不存在")
        
        # 获取消息子集
        total_messages = len(session.messages)
        start_idx = max(0, total_messages - offset - limit)
        end_idx = total_messages - offset
        
        messages = [
            {
                "id": msg.id,
                "role": msg.role.value,
                "content": msg.content,
                "timestamp": msg.timestamp,
                "status": msg.status.value,
                "metadata": msg.metadata
            }
            for msg in session.messages[start_idx:end_idx]
        ]
        
        return {
            "messages": messages,
            "total": total_messages,
            "limit": limit,
            "offset": offset,
            "has_more": offset + limit < total_messages
        }
        
    except SessionNotFoundError:
        raise HTTPException(status_code=404, detail="会话不存在")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 