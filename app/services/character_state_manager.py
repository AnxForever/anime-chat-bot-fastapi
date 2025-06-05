"""
角色状态管理器

管理角色在对话过程中的动态状态变化，包括熟悉度、情绪历史、关系发展等。
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass

from app.models import Character, Message, Session


class RelationshipLevel(Enum):
    """关系级别枚举"""
    STRANGER = "stranger"           # 陌生人
    ACQUAINTANCE = "acquaintance"   # 认识
    FRIEND = "friend"               # 朋友
    CLOSE_FRIEND = "close_friend"   # 密友
    SPECIAL = "special"             # 特殊关系


class CharacterMood(Enum):
    """角色心情枚举"""
    GREAT = "great"         # 很好
    GOOD = "good"           # 好
    NEUTRAL = "neutral"     # 一般
    BAD = "bad"             # 不好
    TERRIBLE = "terrible"   # 很糟


@dataclass
class CharacterState:
    """角色状态数据结构"""
    character_id: str
    session_id: str
    relationship_level: RelationshipLevel
    familiarity_score: float  # 0-100 熟悉度分数
    mood: CharacterMood
    energy_level: float  # 0-100 活力值
    last_interaction: datetime
    interaction_count: int
    positive_interactions: int
    negative_interactions: int
    trust_level: float  # 0-100 信任度
    topic_preferences: Dict[str, float]  # 话题偏好分数
    special_memories: List[str]  # 特殊记忆
    created_at: datetime
    updated_at: datetime


class CharacterStateManager:
    """角色状态管理器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # 存储各会话的角色状态
        self._character_states: Dict[str, CharacterState] = {}
        
        # 关系发展阈值
        self.relationship_thresholds = {
            RelationshipLevel.ACQUAINTANCE: 10,  # 10次互动成为认识
            RelationshipLevel.FRIEND: 30,        # 30次互动成为朋友
            RelationshipLevel.CLOSE_FRIEND: 80,  # 80次互动成为密友
            RelationshipLevel.SPECIAL: 150      # 150次互动达到特殊关系
        }
        
        # 话题分类词典
        self.topic_keywords = {
            "日常": ["吃饭", "睡觉", "天气", "工作", "学习", "今天"],
            "情感": ["喜欢", "讨厌", "爱", "恨", "感情", "心情"],
            "兴趣": ["音乐", "电影", "游戏", "书", "运动", "爱好"],
            "私人": ["家人", "朋友", "秘密", "梦想", "过去", "未来"],
            "角色相关": ["EVA", "驾驶", "司令", "真嵌", "歌曲", "表演"]
        }
    
    def get_character_state(self, character_id: str, session_id: str) -> CharacterState:
        """获取角色状态"""
        state_key = f"{character_id}_{session_id}"
        
        if state_key not in self._character_states:
            # 创建新的角色状态
            now = datetime.now()
            self._character_states[state_key] = CharacterState(
                character_id=character_id,
                session_id=session_id,
                relationship_level=RelationshipLevel.STRANGER,
                familiarity_score=0.0,
                mood=CharacterMood.NEUTRAL,
                energy_level=75.0,  # 初始活力值
                last_interaction=now,
                interaction_count=0,
                positive_interactions=0,
                negative_interactions=0,
                trust_level=50.0,   # 初始信任度
                topic_preferences={},
                special_memories=[],
                created_at=now,
                updated_at=now
            )
        
        return self._character_states[state_key]
    
    def update_state_after_interaction(
        self, 
        character: Character,
        session_id: str,
        user_message: str,
        character_response: str,
        interaction_quality: float = 0.5
    ) -> CharacterState:
        """
        交互后更新角色状态
        
        Args:
            character: 角色对象
            session_id: 会话ID
            user_message: 用户消息
            character_response: 角色回复
            interaction_quality: 交互质量 (0-1)
            
        Returns:
            CharacterState: 更新后的状态
        """
        state = self.get_character_state(character.id, session_id)
        
        # 更新基础计数
        state.interaction_count += 1
        state.last_interaction = datetime.now()
        state.updated_at = datetime.now()
        
        # 根据交互质量更新正负面计数
        if interaction_quality > 0.6:
            state.positive_interactions += 1
            # 提升心情和信任度
            state.mood = self._improve_mood(state.mood)
            state.trust_level = min(100.0, state.trust_level + 2.0)
        elif interaction_quality < 0.4:
            state.negative_interactions += 1
            # 降低心情和信任度
            state.mood = self._worsen_mood(state.mood)
            state.trust_level = max(0.0, state.trust_level - 1.0)
        
        # 更新熟悉度分数
        familiarity_gain = interaction_quality * 2.0
        state.familiarity_score = min(100.0, state.familiarity_score + familiarity_gain)
        
        # 更新关系级别
        state.relationship_level = self._calculate_relationship_level(state)
        
        # 分析和更新话题偏好
        self._update_topic_preferences(state, user_message)
        
        # 检查是否有特殊记忆值得保存
        self._check_special_memory(state, user_message, character_response)
        
        # 更新活力值（随时间和交互变化）
        self._update_energy_level(state, character)
        
        return state
    
    def _improve_mood(self, current_mood: CharacterMood) -> CharacterMood:
        """改善心情"""
        mood_levels = [
            CharacterMood.TERRIBLE,
            CharacterMood.BAD,
            CharacterMood.NEUTRAL,
            CharacterMood.GOOD,
            CharacterMood.GREAT
        ]
        
        current_index = mood_levels.index(current_mood)
        if current_index < len(mood_levels) - 1:
            return mood_levels[current_index + 1]
        return current_mood
    
    def _worsen_mood(self, current_mood: CharacterMood) -> CharacterMood:
        """恶化心情"""
        mood_levels = [
            CharacterMood.TERRIBLE,
            CharacterMood.BAD,
            CharacterMood.NEUTRAL,
            CharacterMood.GOOD,
            CharacterMood.GREAT
        ]
        
        current_index = mood_levels.index(current_mood)
        if current_index > 0:
            return mood_levels[current_index - 1]
        return current_mood
    
    def _calculate_relationship_level(self, state: CharacterState) -> RelationshipLevel:
        """计算关系级别"""
        score = state.familiarity_score + (state.positive_interactions * 2) - state.negative_interactions
        
        if score >= self.relationship_thresholds[RelationshipLevel.SPECIAL]:
            return RelationshipLevel.SPECIAL
        elif score >= self.relationship_thresholds[RelationshipLevel.CLOSE_FRIEND]:
            return RelationshipLevel.CLOSE_FRIEND
        elif score >= self.relationship_thresholds[RelationshipLevel.FRIEND]:
            return RelationshipLevel.FRIEND
        elif score >= self.relationship_thresholds[RelationshipLevel.ACQUAINTANCE]:
            return RelationshipLevel.ACQUAINTANCE
        else:
            return RelationshipLevel.STRANGER
    
    def _update_topic_preferences(self, state: CharacterState, user_message: str):
        """更新话题偏好"""
        message_lower = user_message.lower()
        
        for topic, keywords in self.topic_keywords.items():
            score_change = 0
            for keyword in keywords:
                if keyword in message_lower:
                    score_change += 0.5
            
            if score_change > 0:
                current_score = state.topic_preferences.get(topic, 0.0)
                state.topic_preferences[topic] = min(10.0, current_score + score_change)
    
    def _check_special_memory(
        self, 
        state: CharacterState, 
        user_message: str, 
        character_response: str
    ):
        """检查是否有特殊记忆需要保存"""
        special_indicators = [
            "我喜欢你", "我爱你", "生日", "重要", "秘密", 
            "第一次", "特别", "难忘", "永远", "承诺"
        ]
        
        for indicator in special_indicators:
            if indicator in user_message.lower():
                memory = f"用户说: {user_message[:50]}..."
                if memory not in state.special_memories:
                    state.special_memories.append(memory)
                    # 保持最多10个特殊记忆
                    if len(state.special_memories) > 10:
                        state.special_memories.pop(0)
                break
    
    def _update_energy_level(self, state: CharacterState, character: Character):
        """更新活力值"""
        config_data = getattr(character, '_config_data', {})
        personality_deep = config_data.get('personality_deep', {})
        
        # 根据角色特性调整活力变化
        base_energy = personality_deep.get('big_five_personality', {}).get('extraversion', 5) * 10
        
        # 时间衰减
        time_since_last = datetime.now() - state.last_interaction
        if time_since_last.total_seconds() > 3600:  # 超过1小时
            state.energy_level = max(30.0, state.energy_level - 5.0)
        
        # 根据心情调整
        mood_modifiers = {
            CharacterMood.GREAT: 10,
            CharacterMood.GOOD: 5,
            CharacterMood.NEUTRAL: 0,
            CharacterMood.BAD: -5,
            CharacterMood.TERRIBLE: -10
        }
        
        target_energy = base_energy + mood_modifiers.get(state.mood, 0)
        
        # 渐进调整到目标值
        if state.energy_level < target_energy:
            state.energy_level = min(100.0, state.energy_level + 2.0)
        elif state.energy_level > target_energy:
            state.energy_level = max(0.0, state.energy_level - 1.0)
    
    def get_state_modifiers_for_prompt(
        self, 
        character: Character, 
        session_id: str
    ) -> str:
        """
        获取用于提示词的状态修饰符
        
        Args:
            character: 角色对象
            session_id: 会话ID
            
        Returns:
            str: 状态修饰提示
        """
        state = self.get_character_state(character.id, session_id)
        
        modifiers = []
        
        # 关系状态修饰
        relationship_texts = {
            RelationshipLevel.STRANGER: "这是你们的初次相遇，保持适当的距离和礼貌。",
            RelationshipLevel.ACQUAINTANCE: "你们已经认识了，可以稍微亲近一些。",
            RelationshipLevel.FRIEND: "你们已经是朋友了，可以更加自在和亲密。",
            RelationshipLevel.CLOSE_FRIEND: "你们是很好的朋友，可以分享更多私人想法。",
            RelationshipLevel.SPECIAL: "你们有着特殊的关系，可以表现出更深层的情感连接。"
        }
        
        if state.relationship_level in relationship_texts:
            modifiers.append(relationship_texts[state.relationship_level])
        
        # 心情状态修饰
        mood_texts = {
            CharacterMood.GREAT: "你今天心情特别好，更加活泼和积极。",
            CharacterMood.GOOD: "你心情不错，比平时稍微开朗一些。",
            CharacterMood.NEUTRAL: "",  # 不添加修饰
            CharacterMood.BAD: "你心情有些不好，可能稍微冷淡或沉默一些。",
            CharacterMood.TERRIBLE: "你心情很糟糕，表现得更加内向或易怒。"
        }
        
        if state.mood in mood_texts and mood_texts[state.mood]:
            modifiers.append(mood_texts[state.mood])
        
        # 活力值修饰
        if state.energy_level > 80:
            modifiers.append("你精力充沛，表现得更加有活力。")
        elif state.energy_level < 30:
            modifiers.append("你感觉有些疲惫，可能不太有精神。")
        
        # 话题偏好提示
        preferred_topics = [topic for topic, score in state.topic_preferences.items() if score > 5.0]
        if preferred_topics:
            modifiers.append(f"你比较喜欢聊{', '.join(preferred_topics[:2])}相关的话题。")
        
        # 特殊记忆提示
        if state.special_memories:
            modifiers.append(f"记住这些重要的对话：{'; '.join(state.special_memories[-2:])}")
        
        if modifiers:
            return f"\n\n<character_state>\n{chr(10).join(modifiers)}\n</character_state>"
        
        return ""
    
    def get_interaction_suggestions(
        self, 
        character: Character, 
        session_id: str
    ) -> List[str]:
        """
        获取交互建议
        
        Args:
            character: 角色对象
            session_id: 会话ID
            
        Returns:
            List[str]: 建议列表
        """
        state = self.get_character_state(character.id, session_id)
        suggestions = []
        
        # 根据关系级别建议
        if state.relationship_level == RelationshipLevel.STRANGER:
            suggestions.append("尝试进行自我介绍")
            suggestions.append("询问对方的基本信息")
        elif state.relationship_level == RelationshipLevel.FRIEND:
            suggestions.append("分享一些个人想法")
            suggestions.append("询问对方的兴趣爱好")
        
        # 根据话题偏好建议
        if "角色相关" in state.topic_preferences and state.topic_preferences["角色相关"] > 3:
            suggestions.append("聊聊角色相关的话题")
        
        return suggestions
    
    def reset_session_state(self, character_id: str, session_id: str):
        """重置会话状态"""
        state_key = f"{character_id}_{session_id}"
        if state_key in self._character_states:
            del self._character_states[state_key]
    
    def get_state_summary(self, character_id: str, session_id: str) -> Dict[str, Any]:
        """获取状态摘要"""
        state = self.get_character_state(character_id, session_id)
        
        return {
            "relationship_level": state.relationship_level.value,
            "familiarity_score": state.familiarity_score,
            "mood": state.mood.value,
            "energy_level": state.energy_level,
            "trust_level": state.trust_level,
            "interaction_count": state.interaction_count,
            "positive_ratio": (
                state.positive_interactions / max(1, state.interaction_count) * 100
            ),
            "preferred_topics": list(state.topic_preferences.keys())[:3],
            "special_memories_count": len(state.special_memories),
            "days_since_creation": (datetime.now() - state.created_at).days
        } 