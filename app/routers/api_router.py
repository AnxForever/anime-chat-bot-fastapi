"""
API 路由器 - 提供完整的RESTful API接口
"""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from app.models import Character, Message, Session
from app.services.character_loader import CharacterLoader
from app.services.prompt_builder import PromptBuilder
from app.services.emotion_manager import EmotionManager
from app.services.character_state_manager import CharacterStateManager
from app.services.memory_manager import MemoryManager
from app.services.character_relationship_manager import CharacterRelationshipManager
from app.services.context_aware_adjuster import ContextAwareAdjuster
from app.services.response_validator import ResponseValidator

# 初始化路由器
router = APIRouter(prefix="/api/v1", tags=["API v1"])
security = HTTPBearer()
logger = logging.getLogger(__name__)

# 初始化服务
character_loader = CharacterLoader()
prompt_builder = PromptBuilder()
emotion_manager = EmotionManager()
state_manager = CharacterStateManager()
memory_manager = MemoryManager()
relationship_manager = CharacterRelationshipManager()
context_adjuster = ContextAwareAdjuster(
    emotion_manager, state_manager, memory_manager, relationship_manager
)
response_validator = ResponseValidator()

# 请求/响应模型
from pydantic import BaseModel

class ApiResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None
    timestamp: str = datetime.now().isoformat()

class ChatRequest(BaseModel):
    character_id: str
    message: str
    user_id: Optional[str] = "anonymous"
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    message: str
    character_id: str
    timestamp: str
    metadata: Optional[Dict[str, Any]] = None

class CharacterStateResponse(BaseModel):
    relationship_level: str
    familiarity_score: float
    mood: str
    energy_level: float
    trust_level: float
    interaction_count: int
    positive_interactions: int
    negative_interactions: int
    topic_preferences: Dict[str, float]
    special_memories: List[str]
    last_interaction: str

class MemoryResponse(BaseModel):
    memories: List[Dict[str, Any]]
    statistics: Dict[str, Any]

# 认证依赖
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """获取当前用户（简化版本）"""
    # 这里应该实现真正的JWT验证
    # 目前为了简化，直接返回用户ID
    return "user_123"

# 错误处理函数
def create_error_response(code: str, message: str, details: Any = None) -> ApiResponse:
    """创建错误响应"""
    return ApiResponse(
        success=False,
        error={
            "code": code,
            "message": message,
            "details": details
        }
    )

def create_success_response(data: Any) -> ApiResponse:
    """创建成功响应"""
    return ApiResponse(success=True, data=data)

# === 角色管理 API ===

@router.get("/characters")
async def get_characters():
    """获取所有可用角色列表"""
    try:
        characters_data = []
        
        # 获取所有角色
        character_files = ["rei_ayanami", "asuka_langley", "miku_hatsune"]
        
        for char_id in character_files:
            try:
                character = character_loader.load_character(char_id)
                config_data = getattr(character, '_config_data', {})
                
                character_info = {
                    "id": character.id,
                    "name": character.name,
                    "description": character.description,
                    "avatar_url": f"/static/avatars/{char_id}.png",
                    "source": config_data.get('basic_info', {}).get('source', '未知'),
                    "personality_traits": config_data.get('personality_deep', {}).get('core_traits', []),
                    "available": True
                }
                characters_data.append(character_info)
                
            except Exception as e:
                logger.warning(f"Failed to load character {char_id}: {e}")
                continue
        
        return create_success_response(characters_data)
        
    except Exception as e:
        logger.error(f"Error getting characters: {e}")
        return create_error_response("SYS_001", "系统内部错误", str(e))

@router.get("/characters/{character_id}")
async def get_character_detail(character_id: str):
    """获取角色详细信息"""
    try:
        character = character_loader.load_character(character_id)
        if not character:
            return create_error_response("CHAR_001", "角色不存在", {"character_id": character_id})
        
        config_data = getattr(character, '_config_data', {})
        
        character_detail = {
            "id": character.id,
            "name": character.name,
            "description": character.description,
            "avatar_url": f"/static/avatars/{character_id}.png",
            "personality_deep": config_data.get('personality_deep', {}),
            "behavioral_constraints": config_data.get('behavioral_constraints', {}),
            "few_shot_examples": config_data.get('few_shot_examples', [])
        }
        
        return create_success_response(character_detail)
        
    except Exception as e:
        logger.error(f"Error getting character detail: {e}")
        return create_error_response("CHAR_002", "角色配置错误", str(e))

# === 对话系统 API ===

@router.post("/chat")
async def chat_with_character(
    request: ChatRequest,
    current_user: str = Depends(get_current_user)
):
    """发送消息并获取AI回复"""
    try:
        # 验证输入
        if not request.message.strip():
            return create_error_response("CHAT_001", "消息内容为空")
        
        # 加载角色
        character = character_loader.load_character(request.character_id)
        if not character:
            return create_error_response("CHAR_001", "角色不存在", {"character_id": request.character_id})
        
        # 生成会话ID（如果没有提供）
        session_id = request.session_id or f"session_{current_user}_{request.character_id}"
        
        # 分析情感
        user_emotion = emotion_manager.analyze_emotion(request.message)
        
        # 获取角色状态
        char_state = state_manager.get_character_state(character.id, session_id)
        
        # 获取相关记忆
        relevant_memories = memory_manager.get_relevant_memories(
            character.id, session_id, request.message, max_memories=3
        )
        
        # 获取上下文调整指令
        conversation_history = []  # 这里应该从数据库获取历史对话
        adjustment_instructions = context_adjuster.generate_adjustment_instructions(
            character, session_id, request.message, conversation_history
        )
        
        # 构建提示词
        system_prompt = prompt_builder.build_system_prompt(character)
        
        # 添加状态修饰符
        state_modifiers = state_manager.get_state_modifiers_for_prompt(character, session_id)
        
        # 添加记忆摘要
        memory_summary = memory_manager.get_memory_summary_for_prompt(
            character.id, session_id, request.message
        )
        
        # 组合完整提示词
        full_prompt = system_prompt + state_modifiers + memory_summary + adjustment_instructions
        
        # 这里应该调用AI服务生成回复
        # 目前为演示，返回模拟回复
        character_response = f"[{character.name}] 这是一个基于完整系统生成的回复，回应: {request.message}"
        
        # 验证回应质量
        validation_result = response_validator.validate_response(
            character, request.message, character_response, {
                "emotion": user_emotion,
                "state": char_state
            }
        )
        
        # 如果回应需要重新生成
        if validation_result.requires_regeneration:
            character_response = f"[{character.name}] 经过验证优化的回复: {request.message}"
        
        # 更新角色状态
        interaction_quality = 0.8 if validation_result.overall_passed else 0.4
        updated_state = state_manager.update_state_after_interaction(
            character, session_id, request.message, character_response, interaction_quality
        )
        
        # 提取和存储记忆
        extracted_memories = memory_manager.extract_memories_from_conversation(
            character.id, session_id, request.message, character_response
        )
        
        # 构建响应
        response_data = {
            "message": character_response,
            "character_id": character.id,
            "timestamp": datetime.now().isoformat(),
            "metadata": {
                "emotion_detected": user_emotion.value if hasattr(user_emotion, 'value') else str(user_emotion),
                "response_time_ms": 1200,  # 模拟响应时间
                "confidence_score": validation_result.overall_score,
                "character_state": {
                    "mood": updated_state.mood.value,
                    "energy_level": updated_state.energy_level,
                    "relationship_level": updated_state.relationship_level.value,
                    "familiarity_score": updated_state.familiarity_score
                },
                "validation_passed": validation_result.overall_passed,
                "memories_extracted": len(extracted_memories)
            }
        }
        
        return create_success_response(response_data)
        
    except Exception as e:
        logger.error(f"Error in chat: {e}")
        return create_error_response("CHAT_003", "AI服务暂时不可用", str(e))

@router.get("/conversations/{session_id}/messages")
async def get_conversation_history(
    session_id: str,
    page: int = 1,
    limit: int = 50,
    current_user: str = Depends(get_current_user)
):
    """获取对话历史"""
    try:
        # 这里应该从数据库获取真实的对话历史
        # 目前返回模拟数据
        messages = [
            {
                "id": f"msg_{i}",
                "role": "user" if i % 2 == 0 else "assistant",
                "content": f"消息内容 {i}",
                "timestamp": datetime.now().isoformat(),
                "user_id": current_user if i % 2 == 0 else None,
                "character_id": "rei_ayanami" if i % 2 == 1 else None
            }
            for i in range(1, min(limit + 1, 21))
        ]
        
        response_data = {
            "messages": messages,
            "pagination": {
                "current_page": page,
                "total_pages": 5,
                "total_messages": 100,
                "has_next": page < 5
            }
        }
        
        return create_success_response(response_data)
        
    except Exception as e:
        logger.error(f"Error getting conversation history: {e}")
        return create_error_response("CHAT_002", "会话不存在", str(e))

# === 角色状态 API ===

@router.get("/character-state/{character_id}/{session_id}")
async def get_character_state(
    character_id: str,
    session_id: str,
    current_user: str = Depends(get_current_user)
):
    """获取角色当前状态"""
    try:
        character = character_loader.load_character(character_id)
        if not character:
            return create_error_response("CHAR_001", "角色不存在")
        
        state = state_manager.get_character_state(character_id, session_id)
        
        state_data = {
            "relationship_level": state.relationship_level.value,
            "familiarity_score": state.familiarity_score,
            "mood": state.mood.value,
            "energy_level": state.energy_level,
            "trust_level": state.trust_level,
            "interaction_count": state.interaction_count,
            "positive_interactions": state.positive_interactions,
            "negative_interactions": state.negative_interactions,
            "topic_preferences": state.topic_preferences,
            "special_memories": state.special_memories,
            "last_interaction": state.last_interaction.isoformat()
        }
        
        return create_success_response(state_data)
        
    except Exception as e:
        logger.error(f"Error getting character state: {e}")
        return create_error_response("SYS_001", "系统内部错误", str(e))

# === 记忆系统 API ===

@router.get("/memory/{character_id}/{session_id}")
async def get_character_memory(
    character_id: str,
    session_id: str,
    current_user: str = Depends(get_current_user)
):
    """获取角色记忆"""
    try:
        # 获取记忆统计
        memory_stats = memory_manager.get_memory_statistics(character_id, session_id)
        
        # 模拟记忆数据
        memories_data = {
            "memories": [
                {
                    "id": "mem_001",
                    "type": "factual",
                    "importance": "high",
                    "content": "用户说他喜欢音乐",
                    "keywords": ["音乐", "喜欢"],
                    "emotions": ["happy"],
                    "created_at": datetime.now().isoformat(),
                    "access_count": 3
                }
            ],
            "statistics": memory_stats
        }
        
        return create_success_response(memories_data)
        
    except Exception as e:
        logger.error(f"Error getting memory: {e}")
        return create_error_response("MEM_001", "记忆提取失败", str(e))

# === 关系管理 API ===

@router.get("/relationships/{character_id}")
async def get_character_relationships(
    character_id: str,
    current_user: str = Depends(get_current_user)
):
    """获取角色关系网络"""
    try:
        relationships = relationship_manager.get_character_relationships(character_id)
        network_summary = relationship_manager.get_relationship_network_summary()
        
        relationships_data = []
        for rel in relationships:
            relationships_data.append({
                "character_a": rel.character_a_id,
                "character_b": rel.character_b_id,
                "relationship_type": rel.relationship_type.value,
                "affinity_score": rel.affinity_score,
                "trust_level": rel.trust_level,
                "interaction_count": rel.interaction_count,
                "last_interaction": rel.last_interaction.isoformat(),
                "notes": rel.relationship_notes
            })
        
        response_data = {
            "relationships": relationships_data,
            "network_summary": network_summary
        }
        
        return create_success_response(response_data)
        
    except Exception as e:
        logger.error(f"Error getting relationships: {e}")
        return create_error_response("SYS_001", "系统内部错误", str(e))

# === 验证系统 API ===

@router.post("/validation/response")
async def validate_response(
    request: Dict[str, Any],
    current_user: str = Depends(get_current_user)
):
    """验证生成的回应"""
    try:
        character_id = request.get("character_id")
        user_message = request.get("user_message")
        character_response = request.get("character_response")
        context = request.get("context", {})
        
        character = character_loader.load_character(character_id)
        if not character:
            return create_error_response("CHAR_001", "角色不存在")
        
        validation_result = response_validator.validate_response(
            character, user_message, character_response, context
        )
        
        result_data = {
            "overall_score": validation_result.overall_score,
            "overall_passed": validation_result.overall_passed,
            "requires_regeneration": validation_result.requires_regeneration,
            "major_issues": validation_result.major_issues,
            "recommendations": validation_result.recommendations,
            "validation_results": [
                {
                    "category": result.category.value,
                    "passed": result.passed,
                    "score": result.score,
                    "severity": result.severity
                }
                for result in validation_result.validation_results
            ]
        }
        
        return create_success_response(result_data)
        
    except Exception as e:
        logger.error(f"Error validating response: {e}")
        return create_error_response("VAL_001", "回应验证失败", str(e))

# === 统计与监控 API ===

@router.get("/stats/overview")
async def get_system_stats(current_user: str = Depends(get_current_user)):
    """获取系统概览统计"""
    try:
        # 模拟统计数据
        stats_data = {
            "total_users": 1250,
            "active_sessions": 45,
            "total_messages": 125000,
            "average_response_time": 1.2,
            "character_popularity": {
                "rei_ayanami": 45,
                "asuka_langley": 38,
                "miku_hatsune": 42
            },
            "system_health": {
                "ai_service_status": "healthy",
                "database_status": "healthy",
                "memory_usage": "normal"
            }
        }
        
        return create_success_response(stats_data)
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return create_error_response("SYS_001", "系统内部错误", str(e)) 