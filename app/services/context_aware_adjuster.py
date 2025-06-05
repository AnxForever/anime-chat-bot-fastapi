"""
上下文感知回应调整器

基于多维度上下文信息（情感状态、角色状态、记忆、关系等）动态调整角色回应。
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import re

from app.models import Character
from app.services.emotion_manager import EmotionManager, EmotionalState
from app.services.character_state_manager import CharacterStateManager, CharacterMood
from app.services.memory_manager import MemoryManager
from app.services.character_relationship_manager import CharacterRelationshipManager


class ContextType(Enum):
    """上下文类型枚举"""
    EMOTIONAL = "emotional"       # 情感上下文
    TEMPORAL = "temporal"         # 时间上下文
    RELATIONAL = "relational"     # 关系上下文
    TOPICAL = "topical"          # 话题上下文
    BEHAVIORAL = "behavioral"     # 行为上下文


class AdjustmentType(Enum):
    """调整类型枚举"""
    TONE = "tone"                # 语调调整
    FORMALITY = "formality"      # 正式程度调整
    ENTHUSIASM = "enthusiasm"    # 热情度调整
    INTIMACY = "intimacy"        # 亲密度调整
    DIRECTNESS = "directness"    # 直接程度调整


class ContextAwareAdjuster:
    """上下文感知回应调整器"""
    
    def __init__(
        self,
        emotion_manager: EmotionManager,
        state_manager: CharacterStateManager,
        memory_manager: MemoryManager,
        relationship_manager: CharacterRelationshipManager
    ):
        self.logger = logging.getLogger(__name__)
        self.emotion_manager = emotion_manager
        self.state_manager = state_manager
        self.memory_manager = memory_manager
        self.relationship_manager = relationship_manager
        
        # 上下文权重配置
        self.context_weights = {
            ContextType.EMOTIONAL: 0.3,
            ContextType.TEMPORAL: 0.15,
            ContextType.RELATIONAL: 0.25,
            ContextType.TOPICAL: 0.2,
            ContextType.BEHAVIORAL: 0.1
        }
        
        # 调整策略配置
        self.adjustment_strategies = {
            "high_emotion": {
                AdjustmentType.TONE: "更加情感化",
                AdjustmentType.ENTHUSIASM: "提高热情度",
                AdjustmentType.DIRECTNESS: "更加直接表达"
            },
            "close_relationship": {
                AdjustmentType.INTIMACY: "增加亲密感",
                AdjustmentType.FORMALITY: "降低正式程度",
                AdjustmentType.TONE: "更加温暖"
            },
            "formal_context": {
                AdjustmentType.FORMALITY: "提高正式程度",
                AdjustmentType.DIRECTNESS: "保持适当距离",
                AdjustmentType.TONE: "更加中性"
            },
            "negative_mood": {
                AdjustmentType.TONE: "更加谨慎",
                AdjustmentType.ENTHUSIASM: "降低热情度",
                AdjustmentType.INTIMACY: "保持适当距离"
            }
        }
    
    def analyze_context(
        self,
        character: Character,
        session_id: str,
        user_message: str,
        conversation_history: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        分析多维度上下文
        
        Args:
            character: 角色对象
            session_id: 会话ID
            user_message: 用户消息
            conversation_history: 对话历史
            
        Returns:
            Dict: 上下文分析结果
        """
        context_analysis = {}
        
        # 情感上下文分析
        emotional_context = self._analyze_emotional_context(
            character, session_id, user_message
        )
        context_analysis[ContextType.EMOTIONAL] = emotional_context
        
        # 时间上下文分析
        temporal_context = self._analyze_temporal_context(
            character, session_id, conversation_history
        )
        context_analysis[ContextType.TEMPORAL] = temporal_context
        
        # 关系上下文分析
        relational_context = self._analyze_relational_context(
            character, session_id, user_message
        )
        context_analysis[ContextType.RELATIONAL] = relational_context
        
        # 话题上下文分析
        topical_context = self._analyze_topical_context(
            character, session_id, user_message, conversation_history
        )
        context_analysis[ContextType.TOPICAL] = topical_context
        
        # 行为上下文分析
        behavioral_context = self._analyze_behavioral_context(
            character, session_id, conversation_history
        )
        context_analysis[ContextType.BEHAVIORAL] = behavioral_context
        
        return context_analysis
    
    def _analyze_emotional_context(
        self, 
        character: Character, 
        session_id: str, 
        user_message: str
    ) -> Dict[str, Any]:
        """分析情感上下文"""
        # 获取当前情感状态
        current_emotion = self.emotion_manager.analyze_emotion(user_message)
        emotion_history = self.emotion_manager.get_emotion_history(
            character.id, session_id
        )
        
        # 计算情感强度
        emotion_intensity = self._calculate_emotion_intensity(user_message)
        
        # 情感变化趋势
        emotion_trend = self._analyze_emotion_trend(emotion_history)
        
        return {
            "current_emotion": current_emotion,
            "emotion_intensity": emotion_intensity,
            "emotion_trend": emotion_trend,
            "emotion_stability": len(set(emotion_history[-3:])) <= 1 if emotion_history else True
        }
    
    def _analyze_temporal_context(
        self,
        character: Character,
        session_id: str,
        conversation_history: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """分析时间上下文"""
        now = datetime.now()
        
        # 会话持续时间
        session_duration = self._estimate_session_duration(conversation_history)
        
        # 响应节奏
        response_pace = self._analyze_response_pace(conversation_history)
        
        # 时间敏感性
        time_sensitive = self._detect_time_sensitivity(conversation_history)
        
        return {
            "session_duration": session_duration,
            "response_pace": response_pace,
            "time_sensitive": time_sensitive,
            "conversation_length": len(conversation_history)
        }
    
    def _analyze_relational_context(
        self,
        character: Character,
        session_id: str,
        user_message: str
    ) -> Dict[str, Any]:
        """分析关系上下文"""
        # 获取角色状态
        char_state = self.state_manager.get_character_state(character.id, session_id)
        
        # 提及的其他角色
        mentioned_characters = self._extract_mentioned_characters(user_message)
        
        # 关系上下文
        relationship_context = ""
        if mentioned_characters:
            relationship_context = self.relationship_manager.get_relationship_context_for_prompt(
                character.id, mentioned_characters
            )
        
        return {
            "relationship_level": char_state.relationship_level,
            "familiarity_score": char_state.familiarity_score,
            "trust_level": char_state.trust_level,
            "mentioned_characters": mentioned_characters,
            "relationship_context": relationship_context
        }
    
    def _analyze_topical_context(
        self,
        character: Character,
        session_id: str,
        user_message: str,
        conversation_history: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """分析话题上下文"""
        # 当前话题
        current_topic = self._extract_topic(user_message)
        
        # 话题历史
        topic_history = [
            self._extract_topic(msg.get("content", ""))
            for msg in conversation_history[-5:]
        ]
        
        # 话题转换
        topic_shift = self._detect_topic_shift(topic_history)
        
        # 敏感话题检测
        sensitive_topic = self._detect_sensitive_topic(user_message, character)
        
        return {
            "current_topic": current_topic,
            "topic_history": topic_history,
            "topic_shift": topic_shift,
            "sensitive_topic": sensitive_topic
        }
    
    def _analyze_behavioral_context(
        self,
        character: Character,
        session_id: str,
        conversation_history: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """分析行为上下文"""
        # 用户行为模式
        user_patterns = self._analyze_user_patterns(conversation_history)
        
        # 角色一致性检查
        consistency_score = self._check_character_consistency(
            character, conversation_history
        )
        
        return {
            "user_patterns": user_patterns,
            "consistency_score": consistency_score,
            "interaction_quality": self._assess_interaction_quality(conversation_history)
        }
    
    def generate_adjustment_instructions(
        self,
        character: Character,
        session_id: str,
        user_message: str,
        conversation_history: List[Dict[str, str]]
    ) -> str:
        """
        生成调整指令
        
        Args:
            character: 角色对象
            session_id: 会话ID
            user_message: 用户消息
            conversation_history: 对话历史
            
        Returns:
            str: 调整指令文本
        """
        # 分析上下文
        context_analysis = self.analyze_context(
            character, session_id, user_message, conversation_history
        )
        
        # 确定需要的调整
        required_adjustments = self._determine_required_adjustments(context_analysis)
        
        # 生成调整指令
        adjustment_instructions = []
        
        for adjustment_type, adjustment_details in required_adjustments.items():
            instruction = self._generate_specific_adjustment_instruction(
                adjustment_type, adjustment_details, character
            )
            if instruction:
                adjustment_instructions.append(instruction)
        
        if adjustment_instructions:
            return f"\n\n<response_adjustments>\n{chr(10).join(adjustment_instructions)}\n</response_adjustments>"
        
        return ""
    
    def _determine_required_adjustments(
        self, 
        context_analysis: Dict[str, Any]
    ) -> Dict[AdjustmentType, Dict[str, Any]]:
        """确定需要的调整"""
        required_adjustments = {}
        
        emotional_ctx = context_analysis.get(ContextType.EMOTIONAL, {})
        relational_ctx = context_analysis.get(ContextType.RELATIONAL, {})
        topical_ctx = context_analysis.get(ContextType.TOPICAL, {})
        behavioral_ctx = context_analysis.get(ContextType.BEHAVIORAL, {})
        
        # 基于情感状态的调整
        if emotional_ctx.get("emotion_intensity", 0) > 0.7:
            required_adjustments[AdjustmentType.TONE] = {
                "direction": "emotional",
                "intensity": emotional_ctx.get("emotion_intensity", 0.5),
                "emotion": emotional_ctx.get("current_emotion", EmotionalState.NEUTRAL)
            }
        
        # 基于关系状态的调整
        familiarity = relational_ctx.get("familiarity_score", 0)
        if familiarity > 70:
            required_adjustments[AdjustmentType.INTIMACY] = {
                "direction": "increase",
                "level": familiarity / 100
            }
            required_adjustments[AdjustmentType.FORMALITY] = {
                "direction": "decrease",
                "level": 0.3
            }
        elif familiarity < 20:
            required_adjustments[AdjustmentType.FORMALITY] = {
                "direction": "increase",
                "level": 0.7
            }
        
        # 基于敏感话题的调整
        if topical_ctx.get("sensitive_topic"):
            required_adjustments[AdjustmentType.DIRECTNESS] = {
                "direction": "decrease",
                "level": 0.3
            }
        
        # 基于用户模式的调整
        user_patterns = behavioral_ctx.get("user_patterns", {})
        if user_patterns.get("formality_preference") == "casual":
            required_adjustments[AdjustmentType.FORMALITY] = {
                "direction": "decrease",
                "level": 0.4
            }
        
        return required_adjustments
    
    def _generate_specific_adjustment_instruction(
        self,
        adjustment_type: AdjustmentType,
        adjustment_details: Dict[str, Any],
        character: Character
    ) -> str:
        """生成具体的调整指令"""
        direction = adjustment_details.get("direction", "neutral")
        level = adjustment_details.get("intensity", adjustment_details.get("level", 0.5))
        
        if adjustment_type == AdjustmentType.TONE:
            emotion = adjustment_details.get("emotion", EmotionalState.NEUTRAL)
            if emotion == EmotionalState.PLEASED:
                return f"语调调整：表现得更加愉悦和积极(强度: {level:.1f})"
            elif emotion == EmotionalState.SAD:
                return f"语调调整：表现得更加同情和温柔(强度: {level:.1f})"
            elif emotion == EmotionalState.ANGRY:
                return f"语调调整：控制情绪，保持角色特有的表达方式(强度: {level:.1f})"
        
        elif adjustment_type == AdjustmentType.FORMALITY:
            if direction == "increase":
                return f"正式度调整：使用更正式和礼貌的表达(程度: {level:.1f})"
            elif direction == "decrease":
                return f"正式度调整：使用更轻松和随意的表达(程度: {level:.1f})"
        
        elif adjustment_type == AdjustmentType.INTIMACY:
            if direction == "increase":
                return f"亲密度调整：表现得更加亲近和关怀(程度: {level:.1f})"
            elif direction == "decrease":
                return f"亲密度调整：保持适当的距离感(程度: {level:.1f})"
        
        elif adjustment_type == AdjustmentType.ENTHUSIASM:
            if direction == "increase":
                return f"热情度调整：表现得更加积极和兴奋(程度: {level:.1f})"
            elif direction == "decrease":
                return f"热情度调整：保持冷静和克制(程度: {level:.1f})"
        
        elif adjustment_type == AdjustmentType.DIRECTNESS:
            if direction == "increase":
                return f"直接度调整：更加直白和明确地表达(程度: {level:.1f})"
            elif direction == "decrease":
                return f"直接度调整：使用更加委婉和含蓄的表达(程度: {level:.1f})"
        
        return ""
    
    def _calculate_emotion_intensity(self, message: str) -> float:
        """计算情感强度"""
        # 简单的情感强度计算
        intensity_indicators = {
            "!": 0.2, "！": 0.2,
            "?": 0.1, "？": 0.1,
            "...": 0.15, "。。。": 0.15,
            "啊": 0.1, "呀": 0.1, "哦": 0.1
        }
        
        intensity = 0.0
        for indicator, value in intensity_indicators.items():
            count = message.count(indicator)
            intensity += count * value
        
        # 检查大写字母比例（如果有）
        if any(c.isupper() for c in message):
            intensity += 0.1
        
        return min(1.0, intensity)
    
    def _analyze_emotion_trend(self, emotion_history: List[EmotionalState]) -> str:
        """分析情感趋势"""
        if len(emotion_history) < 2:
            return "stable"
        
        recent_emotions = emotion_history[-3:]
        if len(set(recent_emotions)) == 1:
            return "stable"
        elif len(set(recent_emotions)) == len(recent_emotions):
            return "volatile"
        else:
            return "changing"
    
    def _estimate_session_duration(self, conversation_history: List[Dict[str, str]]) -> float:
        """估算会话持续时间（小时）"""
        # 简化计算：假设每轮对话2分钟
        return len(conversation_history) * 2 / 60
    
    def _analyze_response_pace(self, conversation_history: List[Dict[str, str]]) -> str:
        """分析响应节奏"""
        msg_count = len(conversation_history)
        if msg_count > 20:
            return "fast"
        elif msg_count > 10:
            return "moderate"
        else:
            return "slow"
    
    def _detect_time_sensitivity(self, conversation_history: List[Dict[str, str]]) -> bool:
        """检测时间敏感性"""
        time_keywords = ["现在", "立刻", "马上", "快", "急", "等不及"]
        recent_messages = conversation_history[-3:] if conversation_history else []
        
        for msg in recent_messages:
            content = msg.get("content", "").lower()
            if any(keyword in content for keyword in time_keywords):
                return True
        
        return False
    
    def _extract_mentioned_characters(self, message: str) -> List[str]:
        """提取提及的角色"""
        character_names = {
            "绫波零": "rei_ayanami",
            "明日香": "asuka_langley", 
            "初音未来": "miku_hatsune",
            "零": "rei_ayanami",
            "未来": "miku_hatsune"
        }
        
        mentioned = []
        for name, char_id in character_names.items():
            if name in message:
                mentioned.append(char_id)
        
        return mentioned
    
    def _extract_topic(self, message: str) -> str:
        """提取话题"""
        topic_keywords = {
            "学习": "education",
            "工作": "work", 
            "音乐": "music",
            "电影": "entertainment",
            "爱好": "hobbies",
            "感情": "relationships",
            "家人": "family",
            "EVA": "eva",
            "驾驶": "eva",
            "歌曲": "music"
        }
        
        for keyword, topic in topic_keywords.items():
            if keyword in message:
                return topic
        
        return "general"
    
    def _detect_topic_shift(self, topic_history: List[str]) -> bool:
        """检测话题转换"""
        if len(topic_history) < 2:
            return False
        
        return topic_history[-1] != topic_history[-2]
    
    def _detect_sensitive_topic(self, message: str, character: Character) -> bool:
        """检测敏感话题"""
        config_data = getattr(character, '_config_data', {})
        behavioral_constraints = config_data.get('behavioral_constraints', {})
        forbidden_topics = behavioral_constraints.get('forbidden_topics', [])
        
        message_lower = message.lower()
        return any(topic.lower() in message_lower for topic in forbidden_topics)
    
    def _analyze_user_patterns(self, conversation_history: List[Dict[str, str]]) -> Dict[str, Any]:
        """分析用户模式"""
        user_messages = [
            msg.get("content", "") for msg in conversation_history 
            if msg.get("role") == "user"
        ]
        
        if not user_messages:
            return {}
        
        # 分析正式程度偏好
        formal_indicators = ["您", "请", "谢谢", "不好意思"]
        casual_indicators = ["哈哈", "嗯", "哦", "吧"]
        
        formal_count = sum(
            sum(indicator in msg for indicator in formal_indicators)
            for msg in user_messages
        )
        casual_count = sum(
            sum(indicator in msg for indicator in casual_indicators) 
            for msg in user_messages
        )
        
        formality_preference = "formal" if formal_count > casual_count else "casual"
        
        return {
            "formality_preference": formality_preference,
            "average_message_length": sum(len(msg) for msg in user_messages) / len(user_messages),
            "question_frequency": sum("?" in msg or "？" in msg for msg in user_messages) / len(user_messages)
        }
    
    def _check_character_consistency(
        self, 
        character: Character, 
        conversation_history: List[Dict[str, str]]
    ) -> float:
        """检查角色一致性"""
        # 简化的一致性检查
        char_messages = [
            msg.get("content", "") for msg in conversation_history
            if msg.get("role") == "assistant"
        ]
        
        if not char_messages:
            return 1.0
        
        config_data = getattr(character, '_config_data', {})
        preferred_words = config_data.get('behavioral_constraints', {}).get('preferred_expressions', [])
        forbidden_words = config_data.get('behavioral_constraints', {}).get('forbidden_words', [])
        
        consistency_score = 1.0
        
        # 检查是否使用了禁用词汇
        for msg in char_messages:
            for forbidden in forbidden_words:
                if forbidden in msg:
                    consistency_score -= 0.1
        
        return max(0.0, consistency_score)
    
    def _assess_interaction_quality(self, conversation_history: List[Dict[str, str]]) -> float:
        """评估互动质量"""
        if len(conversation_history) < 2:
            return 0.5
        
        # 简化的质量评估
        user_messages = [msg for msg in conversation_history if msg.get("role") == "user"]
        
        # 基于消息长度和频率评估
        avg_length = sum(len(msg.get("content", "")) for msg in user_messages) / len(user_messages)
        
        if avg_length > 20:
            return min(1.0, 0.7 + (avg_length - 20) / 100)
        else:
            return 0.5 