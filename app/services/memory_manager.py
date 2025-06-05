"""
会话记忆管理器

提供智能的会话记忆管理，包括重要信息提取、长期记忆存储、上下文相关性分析等。
"""

import logging
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, asdict
import re

from app.models import Character, Message, Session


class MemoryType(Enum):
    """记忆类型枚举"""
    FACTUAL = "factual"         # 事实性记忆
    EMOTIONAL = "emotional"     # 情感记忆
    BEHAVIORAL = "behavioral"   # 行为记忆
    PREFERENCE = "preference"   # 偏好记忆
    RELATIONSHIP = "relationship"  # 关系记忆


class MemoryImportance(Enum):
    """记忆重要性枚举"""
    CRITICAL = "critical"       # 关键记忆
    HIGH = "high"              # 高重要性
    MEDIUM = "medium"          # 中等重要性
    LOW = "low"                # 低重要性


@dataclass
class MemoryItem:
    """记忆项数据结构"""
    id: str
    character_id: str
    session_id: str
    memory_type: MemoryType
    importance: MemoryImportance
    content: str
    context: str
    keywords: List[str]
    related_emotions: List[str]
    access_count: int
    created_at: datetime
    last_accessed: datetime
    expires_at: Optional[datetime] = None


class MemoryManager:
    """会话记忆管理器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # 存储记忆数据
        self._memories: Dict[str, List[MemoryItem]] = {}
        
        # 重要性关键词
        self.importance_keywords = {
            MemoryImportance.CRITICAL: [
                "我爱你", "我恨你", "生日", "死了", "结婚", "分手",
                "秘密", "永远", "承诺", "重要", "特别"
            ],
            MemoryImportance.HIGH: [
                "喜欢", "讨厌", "害怕", "担心", "梦想", "希望",
                "家人", "朋友", "工作", "学习", "目标"
            ],
            MemoryImportance.MEDIUM: [
                "兴趣", "爱好", "电影", "音乐", "书", "游戏",
                "旅行", "美食", "运动", "计划"
            ]
        }
        
        # 情感关键词
        self.emotion_keywords = {
            "开心": ["开心", "高兴", "快乐", "兴奋", "满足", "喜悦"],
            "难过": ["难过", "伤心", "痛苦", "失落", "沮丧", "哭"],
            "生气": ["生气", "愤怒", "恼火", "烦躁", "讨厌", "气"],
            "害怕": ["害怕", "恐惧", "担心", "紧张", "焦虑", "怕"],
            "惊讶": ["惊讶", "震惊", "意外", "吃惊", "不敢相信"]
        }
        
        # 记忆保留策略
        self.retention_periods = {
            MemoryImportance.CRITICAL: timedelta(days=365),  # 1年
            MemoryImportance.HIGH: timedelta(days=90),      # 3个月
            MemoryImportance.MEDIUM: timedelta(days=30),    # 1个月
            MemoryImportance.LOW: timedelta(days=7)         # 1周
        }
    
    def extract_memories_from_conversation(
        self,
        character_id: str,
        session_id: str,
        user_message: str,
        character_response: str
    ) -> List[MemoryItem]:
        """
        从对话中提取记忆
        
        Args:
            character_id: 角色ID
            session_id: 会话ID  
            user_message: 用户消息
            character_response: 角色回复
            
        Returns:
            List[MemoryItem]: 提取的记忆列表
        """
        memories = []
        now = datetime.now()
        
        # 分析用户消息
        user_memories = self._analyze_message_for_memories(
            user_message, character_id, session_id, "user", now
        )
        memories.extend(user_memories)
        
        # 分析角色回复
        character_memories = self._analyze_message_for_memories(
            character_response, character_id, session_id, "character", now
        )
        memories.extend(character_memories)
        
        # 存储记忆
        session_key = f"{character_id}_{session_id}"
        if session_key not in self._memories:
            self._memories[session_key] = []
        
        self._memories[session_key].extend(memories)
        
        # 清理过期记忆
        self._cleanup_expired_memories(session_key)
        
        return memories
    
    def _analyze_message_for_memories(
        self,
        message: str,
        character_id: str,
        session_id: str,
        source: str,
        timestamp: datetime
    ) -> List[MemoryItem]:
        """分析消息提取记忆"""
        memories = []
        
        # 检测重要性
        importance = self._determine_importance(message)
        
        # 检测记忆类型
        memory_types = self._classify_memory_types(message)
        
        # 提取关键词
        keywords = self._extract_keywords(message)
        
        # 检测情感
        emotions = self._detect_emotions(message)
        
        # 为每种记忆类型创建记忆项
        for memory_type in memory_types:
            memory_id = f"{character_id}_{session_id}_{timestamp.timestamp()}_{memory_type.value}"
            
            # 计算过期时间
            expires_at = timestamp + self.retention_periods.get(importance, timedelta(days=7))
            
            memory = MemoryItem(
                id=memory_id,
                character_id=character_id,
                session_id=session_id,
                memory_type=memory_type,
                importance=importance,
                content=message[:200],  # 限制长度
                context=f"来自{source}的消息",
                keywords=keywords,
                related_emotions=emotions,
                access_count=0,
                created_at=timestamp,
                last_accessed=timestamp,
                expires_at=expires_at
            )
            
            memories.append(memory)
        
        return memories
    
    def _determine_importance(self, message: str) -> MemoryImportance:
        """确定消息重要性"""
        message_lower = message.lower()
        
        # 检查关键词
        for importance, keywords in self.importance_keywords.items():
            for keyword in keywords:
                if keyword in message_lower:
                    return importance
        
        # 检查特殊标记
        if any(marker in message_lower for marker in ["!", "！", "?", "？"]):
            if len([c for c in message if c in "!！"]) > 2:
                return MemoryImportance.HIGH
        
        # 检查长度（长消息通常包含更多信息）
        if len(message) > 100:
            return MemoryImportance.MEDIUM
        
        return MemoryImportance.LOW
    
    def _classify_memory_types(self, message: str) -> List[MemoryType]:
        """分类记忆类型"""
        types = []
        message_lower = message.lower()
        
        # 情感记忆
        if any(emotion_words for emotion_words in self.emotion_keywords.values() 
               if any(word in message_lower for word in emotion_words)):
            types.append(MemoryType.EMOTIONAL)
        
        # 偏好记忆
        preference_indicators = ["喜欢", "不喜欢", "爱好", "兴趣", "最喜欢", "讨厌"]
        if any(indicator in message_lower for indicator in preference_indicators):
            types.append(MemoryType.PREFERENCE)
        
        # 事实性记忆
        factual_indicators = ["是", "在", "有", "会", "能", "做", "工作", "学习", "家"]
        if any(indicator in message_lower for indicator in factual_indicators):
            types.append(MemoryType.FACTUAL)
        
        # 关系记忆
        relationship_indicators = ["朋友", "家人", "同事", "恋人", "我们", "一起"]
        if any(indicator in message_lower for indicator in relationship_indicators):
            types.append(MemoryType.RELATIONSHIP)
        
        # 如果没有匹配，默认为事实性记忆
        if not types:
            types.append(MemoryType.FACTUAL)
        
        return types
    
    def _extract_keywords(self, message: str) -> List[str]:
        """提取关键词"""
        # 简单的关键词提取（可以用更复杂的NLP方法）
        keywords = []
        
        # 移除标点符号，分割单词
        words = re.findall(r'\w+', message.lower())
        
        # 过滤停用词
        stop_words = {"的", "了", "在", "是", "我", "你", "他", "她", "它", "这", "那", "有", "和", "与"}
        keywords = [word for word in words if word not in stop_words and len(word) > 1]
        
        # 保留前10个关键词
        return keywords[:10]
    
    def _detect_emotions(self, message: str) -> List[str]:
        """检测情感"""
        detected_emotions = []
        message_lower = message.lower()
        
        for emotion, keywords in self.emotion_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                detected_emotions.append(emotion)
        
        return detected_emotions
    
    def get_relevant_memories(
        self,
        character_id: str,
        session_id: str,
        current_message: str,
        max_memories: int = 5
    ) -> List[MemoryItem]:
        """
        获取与当前消息相关的记忆
        
        Args:
            character_id: 角色ID
            session_id: 会话ID
            current_message: 当前消息
            max_memories: 最大记忆数量
            
        Returns:
            List[MemoryItem]: 相关记忆列表
        """
        session_key = f"{character_id}_{session_id}"
        if session_key not in self._memories:
            return []
        
        memories = self._memories[session_key]
        current_keywords = self._extract_keywords(current_message)
        current_emotions = self._detect_emotions(current_message)
        
        # 计算相关性分数
        scored_memories = []
        for memory in memories:
            score = self._calculate_relevance_score(
                memory, current_keywords, current_emotions
            )
            if score > 0:
                # 更新访问记录
                memory.access_count += 1
                memory.last_accessed = datetime.now()
                scored_memories.append((memory, score))
        
        # 按分数排序
        scored_memories.sort(key=lambda x: x[1], reverse=True)
        
        # 返回前N个最相关的记忆
        return [memory for memory, score in scored_memories[:max_memories]]
    
    def _calculate_relevance_score(
        self,
        memory: MemoryItem,
        current_keywords: List[str],
        current_emotions: List[str]
    ) -> float:
        """计算记忆相关性分数"""
        score = 0.0
        
        # 关键词匹配分数
        keyword_matches = len(set(memory.keywords) & set(current_keywords))
        score += keyword_matches * 10
        
        # 情感匹配分数
        emotion_matches = len(set(memory.related_emotions) & set(current_emotions))
        score += emotion_matches * 15
        
        # 重要性权重
        importance_weights = {
            MemoryImportance.CRITICAL: 50,
            MemoryImportance.HIGH: 30,
            MemoryImportance.MEDIUM: 20,
            MemoryImportance.LOW: 10
        }
        score += importance_weights.get(memory.importance, 10)
        
        # 访问频率权重（经常访问的记忆更重要）
        score += min(memory.access_count * 5, 25)
        
        # 时间衰减（最近的记忆权重更高）
        days_ago = (datetime.now() - memory.created_at).days
        time_weight = max(0, 30 - days_ago)
        score += time_weight
        
        return score
    
    def _cleanup_expired_memories(self, session_key: str):
        """清理过期记忆"""
        if session_key not in self._memories:
            return
        
        now = datetime.now()
        valid_memories = []
        
        for memory in self._memories[session_key]:
            if memory.expires_at is None or memory.expires_at > now:
                valid_memories.append(memory)
        
        self._memories[session_key] = valid_memories
        
        # 如果记忆过多，保留最重要的记忆
        max_memories_per_session = 100
        if len(self._memories[session_key]) > max_memories_per_session:
            # 按重要性和访问频率排序
            self._memories[session_key].sort(
                key=lambda m: (m.importance.value, m.access_count), 
                reverse=True
            )
            self._memories[session_key] = self._memories[session_key][:max_memories_per_session]
    
    def get_memory_summary_for_prompt(
        self,
        character_id: str,
        session_id: str,
        current_message: str
    ) -> str:
        """
        获取用于提示词的记忆摘要
        
        Args:
            character_id: 角色ID
            session_id: 会话ID
            current_message: 当前消息
            
        Returns:
            str: 记忆摘要文本
        """
        relevant_memories = self.get_relevant_memories(
            character_id, session_id, current_message, max_memories=3
        )
        
        if not relevant_memories:
            return ""
        
        memory_texts = []
        for memory in relevant_memories:
            memory_text = f"记忆({memory.memory_type.value}): {memory.content}"
            memory_texts.append(memory_text)
        
        return f"\n\n<relevant_memories>\n{chr(10).join(memory_texts)}\n</relevant_memories>"
    
    def get_memory_statistics(
        self,
        character_id: str,
        session_id: str
    ) -> Dict[str, Any]:
        """获取记忆统计信息"""
        session_key = f"{character_id}_{session_id}"
        if session_key not in self._memories:
            return {"total_memories": 0}
        
        memories = self._memories[session_key]
        
        # 按类型统计
        type_counts = {}
        for memory in memories:
            type_name = memory.memory_type.value
            type_counts[type_name] = type_counts.get(type_name, 0) + 1
        
        # 按重要性统计
        importance_counts = {}
        for memory in memories:
            importance_name = memory.importance.value
            importance_counts[importance_name] = importance_counts.get(importance_name, 0) + 1
        
        return {
            "total_memories": len(memories),
            "by_type": type_counts,
            "by_importance": importance_counts,
            "most_accessed": max(memories, key=lambda m: m.access_count).content if memories else None,
            "average_access_count": sum(m.access_count for m in memories) / len(memories) if memories else 0
        }
    
    def clear_session_memories(self, character_id: str, session_id: str):
        """清除会话记忆"""
        session_key = f"{character_id}_{session_id}"
        if session_key in self._memories:
            del self._memories[session_key] 