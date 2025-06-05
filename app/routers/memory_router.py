"""
记忆管理路由 - 支持高级记忆功能
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from enum import Enum
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/memory", tags=["记忆管理"])

class MemoryType(str, Enum):
    FACTUAL = "factual"           # 事实信息
    EMOTIONAL = "emotional"       # 情感记忆  
    PREFERENCE = "preference"     # 偏好记忆
    RELATIONSHIP = "relationship" # 关系记忆
    EVENT = "event"              # 事件记忆

class MemoryImportance(str, Enum):
    CRITICAL = "critical"  # 极重要
    HIGH = "high"         # 重要
    MEDIUM = "medium"     # 一般
    LOW = "low"           # 不重要

class Memory(BaseModel):
    id: str
    type: MemoryType
    importance: MemoryImportance
    content: str
    keywords: List[str]
    emotions: List[str]
    context: Dict[str, Any]
    created_at: str
    last_accessed: str
    access_count: int
    related_memories: List[str]

class MemoryCreate(BaseModel):
    type: MemoryType
    content: str
    keywords: Optional[List[str]] = []
    emotions: Optional[List[str]] = []
    context: Optional[Dict[str, Any]] = {}
    importance: Optional[MemoryImportance] = MemoryImportance.MEDIUM

class MemoryUpdate(BaseModel):
    content: Optional[str] = None
    keywords: Optional[List[str]] = None
    emotions: Optional[List[str]] = None
    importance: Optional[MemoryImportance] = None

class MemorySearch(BaseModel):
    query: str
    types: Optional[List[MemoryType]] = None
    importance_levels: Optional[List[MemoryImportance]] = None
    date_range: Optional[Dict[str, str]] = None

# 模拟记忆数据库
memories_db: Dict[str, Dict[str, Memory]] = {}  # character_id -> session_id -> memories

def generate_memory_id() -> str:
    """生成记忆ID"""
    import secrets
    return f"mem_{secrets.token_hex(8)}"

def extract_keywords(text: str) -> List[str]:
    """从文本中提取关键词"""
    # 简单的关键词提取（实际应用中可使用NLP技术）
    common_words = {"的", "了", "在", "是", "我", "你", "他", "她", "它", "们", "和", "与"}
    words = text.split()
    keywords = [word for word in words if len(word) > 1 and word not in common_words]
    return keywords[:5]  # 返回前5个关键词

@router.post("/extract/{character_id}/{session_id}")
async def extract_memories_from_conversation(
    character_id: str,
    session_id: str,
    conversation_data: Dict[str, Any]
):
    """从对话中提取记忆"""
    user_message = conversation_data.get("user_message", "")
    character_response = conversation_data.get("character_response", "")
    
    extracted_memories = []
    
    # 初始化角色记忆存储
    if character_id not in memories_db:
        memories_db[character_id] = {}
    if session_id not in memories_db[character_id]:
        memories_db[character_id][session_id] = {}
    
    # 分析用户消息中的信息
    user_keywords = extract_keywords(user_message)
    
    # 提取事实信息
    if any(keyword in user_message for keyword in ["我是", "我叫", "我的", "我在", "我喜欢"]):
        memory_id = generate_memory_id()
        factual_memory = Memory(
            id=memory_id,
            type=MemoryType.FACTUAL,
            importance=MemoryImportance.HIGH,
            content=f"用户说: {user_message}",
            keywords=user_keywords,
            emotions=["neutral"],
            context={
                "conversation_context": character_response,
                "extraction_method": "keyword_matching"
            },
            created_at=datetime.now().isoformat(),
            last_accessed=datetime.now().isoformat(),
            access_count=1,
            related_memories=[]
        )
        memories_db[character_id][session_id][memory_id] = factual_memory
        extracted_memories.append(factual_memory)
    
    # 提取情感信息
    emotion_indicators = {
        "开心": ["高兴", "开心", "快乐", "兴奋"],
        "难过": ["难过", "伤心", "沮丧", "失望"],
        "愤怒": ["生气", "愤怒", "烦躁", "讨厌"],
        "紧张": ["紧张", "焦虑", "担心", "害怕"]
    }
    
    detected_emotions = []
    for emotion, indicators in emotion_indicators.items():
        if any(indicator in user_message for indicator in indicators):
            detected_emotions.append(emotion)
    
    if detected_emotions:
        memory_id = generate_memory_id()
        emotional_memory = Memory(
            id=memory_id,
            type=MemoryType.EMOTIONAL,
            importance=MemoryImportance.MEDIUM,
            content=f"用户表现出{'/'.join(detected_emotions)}的情绪: {user_message}",
            keywords=user_keywords,
            emotions=detected_emotions,
            context={
                "emotional_context": character_response,
                "detected_emotions": detected_emotions
            },
            created_at=datetime.now().isoformat(),
            last_accessed=datetime.now().isoformat(),
            access_count=1,
            related_memories=[]
        )
        memories_db[character_id][session_id][memory_id] = emotional_memory
        extracted_memories.append(emotional_memory)
    
    # 提取偏好信息
    if any(keyword in user_message for keyword in ["喜欢", "讨厌", "最爱", "最恨", "偏爱"]):
        memory_id = generate_memory_id()
        preference_memory = Memory(
            id=memory_id,
            type=MemoryType.PREFERENCE,
            importance=MemoryImportance.HIGH,
            content=f"用户偏好: {user_message}",
            keywords=user_keywords,
            emotions=["neutral"],
            context={
                "preference_context": character_response,
                "extraction_confidence": 0.8
            },
            created_at=datetime.now().isoformat(),
            last_accessed=datetime.now().isoformat(),
            access_count=1,
            related_memories=[]
        )
        memories_db[character_id][session_id][memory_id] = preference_memory
        extracted_memories.append(preference_memory)
    
    return {
        "success": True,
        "extracted_memories": [mem.dict() for mem in extracted_memories],
        "total_extracted": len(extracted_memories)
    }

@router.get("/list/{character_id}/{session_id}")
async def get_character_memories(
    character_id: str,
    session_id: str,
    memory_type: Optional[MemoryType] = None,
    importance: Optional[MemoryImportance] = None,
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0)
):
    """获取角色记忆列表"""
    if character_id not in memories_db or session_id not in memories_db[character_id]:
        return {"success": True, "memories": [], "total": 0}
    
    memories = list(memories_db[character_id][session_id].values())
    
    # 应用筛选条件
    if memory_type:
        memories = [m for m in memories if m.type == memory_type]
    if importance:
        memories = [m for m in memories if m.importance == importance]
    
    # 按创建时间排序
    memories.sort(key=lambda x: x.created_at, reverse=True)
    
    # 分页
    total = len(memories)
    memories = memories[offset:offset + limit]
    
    return {
        "success": True,
        "memories": [mem.dict() for mem in memories],
        "total": total,
        "pagination": {
            "limit": limit,
            "offset": offset,
            "has_more": offset + limit < total
        }
    }

@router.post("/search/{character_id}/{session_id}")
async def search_memories(
    character_id: str,
    session_id: str,
    search_data: MemorySearch
):
    """搜索记忆"""
    if character_id not in memories_db or session_id not in memories_db[character_id]:
        return {"success": True, "memories": [], "total": 0}
    
    memories = list(memories_db[character_id][session_id].values())
    query_lower = search_data.query.lower()
    
    # 搜索匹配
    matching_memories = []
    for memory in memories:
        score = 0
        
        # 内容匹配
        if query_lower in memory.content.lower():
            score += 2
        
        # 关键词匹配
        for keyword in memory.keywords:
            if query_lower in keyword.lower():
                score += 1
        
        # 情感匹配
        for emotion in memory.emotions:
            if query_lower in emotion.lower():
                score += 1
        
        if score > 0:
            memory_dict = memory.dict()
            memory_dict["relevance_score"] = score
            matching_memories.append(memory_dict)
    
    # 按相关性排序
    matching_memories.sort(key=lambda x: x["relevance_score"], reverse=True)
    
    return {
        "success": True,
        "memories": matching_memories,
        "total": len(matching_memories),
        "query": search_data.query
    }

@router.get("/statistics/{character_id}/{session_id}")
async def get_memory_statistics(character_id: str, session_id: str):
    """获取记忆统计信息"""
    if character_id not in memories_db or session_id not in memories_db[character_id]:
        return {
            "success": True,
            "statistics": {
                "total_memories": 0,
                "by_type": {},
                "by_importance": {},
                "recent_activity": [],
                "top_keywords": [],
                "emotion_distribution": {}
            }
        }
    
    memories = list(memories_db[character_id][session_id].values())
    
    # 按类型统计
    by_type = {}
    for memory in memories:
        by_type[memory.type.value] = by_type.get(memory.type.value, 0) + 1
    
    # 按重要性统计
    by_importance = {}
    for memory in memories:
        by_importance[memory.importance.value] = by_importance.get(memory.importance.value, 0) + 1
    
    # 近期活动
    recent_memories = sorted(memories, key=lambda x: x.created_at, reverse=True)[:10]
    recent_activity = [
        {
            "date": mem.created_at,
            "type": mem.type.value,
            "content": mem.content[:50] + "..." if len(mem.content) > 50 else mem.content
        }
        for mem in recent_memories
    ]
    
    # 热门关键词
    keyword_count = {}
    for memory in memories:
        for keyword in memory.keywords:
            keyword_count[keyword] = keyword_count.get(keyword, 0) + 1
    
    top_keywords = sorted(keyword_count.items(), key=lambda x: x[1], reverse=True)[:10]
    
    # 情感分布
    emotion_count = {}
    for memory in memories:
        for emotion in memory.emotions:
            emotion_count[emotion] = emotion_count.get(emotion, 0) + 1
    
    return {
        "success": True,
        "statistics": {
            "total_memories": len(memories),
            "by_type": by_type,
            "by_importance": by_importance,
            "recent_activity": recent_activity,
            "top_keywords": [{"keyword": k, "count": v} for k, v in top_keywords],
            "emotion_distribution": emotion_count
        }
    }

@router.get("/timeline/{character_id}/{session_id}")
async def get_memory_timeline(
    character_id: str,
    session_id: str,
    days: int = Query(30, le=365)
):
    """获取记忆时间线"""
    if character_id not in memories_db or session_id not in memories_db[character_id]:
        return {"success": True, "timeline": []}
    
    memories = list(memories_db[character_id][session_id].values())
    
    # 按日期分组
    timeline_data = {}
    for memory in memories:
        date_str = memory.created_at[:10]  # YYYY-MM-DD
        if date_str not in timeline_data:
            timeline_data[date_str] = []
        
        timeline_data[date_str].append({
            "id": memory.id,
            "type": memory.type.value,
            "importance": memory.importance.value,
            "content": memory.content,
            "time": memory.created_at,
            "keywords": memory.keywords,
            "emotions": memory.emotions
        })
    
    # 转换为时间线格式
    timeline = []
    for date, day_memories in sorted(timeline_data.items(), reverse=True):
        timeline.append({
            "date": date,
            "memories": sorted(day_memories, key=lambda x: x["time"], reverse=True),
            "count": len(day_memories)
        })
    
    return {
        "success": True,
        "timeline": timeline[:days],
        "total_days": len(timeline)
    }

@router.get("/insights/{character_id}/{session_id}")
async def get_memory_insights(character_id: str, session_id: str):
    """获取记忆洞察分析"""
    if character_id not in memories_db or session_id not in memories_db[character_id]:
        return {"success": True, "insights": {}}
    
    memories = list(memories_db[character_id][session_id].values())
    
    # 分析用户画像
    user_profile = {
        "interests": [],
        "personality_traits": [],
        "emotional_patterns": [],
        "communication_style": ""
    }
    
    # 提取兴趣爱好
    interest_keywords = []
    for memory in memories:
        if memory.type == MemoryType.PREFERENCE:
            interest_keywords.extend(memory.keywords)
    
    from collections import Counter
    interest_counter = Counter(interest_keywords)
    user_profile["interests"] = [{"interest": k, "frequency": v} for k, v in interest_counter.most_common(10)]
    
    # 分析情感模式
    emotion_timeline = []
    for memory in memories:
        if memory.emotions:
            emotion_timeline.append({
                "date": memory.created_at,
                "emotions": memory.emotions
            })
    
    user_profile["emotional_patterns"] = emotion_timeline[-20:]  # 最近20次情感记录
    
    # 记忆质量评估
    quality_metrics = {
        "completeness": min(len(memories) / 50.0, 1.0),  # 记忆完整性
        "diversity": len(set(mem.type for mem in memories)) / len(MemoryType),  # 记忆多样性
        "recency": sum(1 for mem in memories if (datetime.now() - datetime.fromisoformat(mem.created_at.replace('Z', '+00:00'))).days <= 7) / max(len(memories), 1),  # 记忆新鲜度
        "depth": sum(1 for mem in memories if mem.importance in [MemoryImportance.HIGH, MemoryImportance.CRITICAL]) / max(len(memories), 1)  # 记忆深度
    }
    
    return {
        "success": True,
        "insights": {
            "user_profile": user_profile,
            "quality_metrics": quality_metrics,
            "recommendations": [
                "多了解用户的兴趣爱好",
                "注意用户的情感变化",
                "记录更多具体的生活细节",
                "关注用户的价值观和信念"
            ],
            "memory_health": {
                "total_score": sum(quality_metrics.values()) / len(quality_metrics),
                "strong_areas": [k for k, v in quality_metrics.items() if v > 0.7],
                "improvement_areas": [k for k, v in quality_metrics.items() if v < 0.3]
            }
        }
    } 