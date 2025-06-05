"""
情感状态管理器

管理角色的情感状态，提供动态的情感响应和状态跟踪。
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum

from app.models import Character, Message


class EmotionalState(Enum):
    """情感状态枚举"""
    NEUTRAL = "neutral"
    PLEASED = "pleased"
    CONFUSED = "confused"
    SAD = "sad"
    ANGRY = "angry"
    CARING = "caring"
    EXCITED = "excited"
    DISAPPOINTED = "disappointed"


class EmotionManager:
    """
    情感状态管理器
    
    根据对话内容和角色设定动态调整情感状态
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # 存储每个会话的情感状态历史
        self._session_emotions: Dict[str, List[Dict[str, Any]]] = {}
        
        # 情感触发词典
        self.emotion_triggers = {
            EmotionalState.PLEASED: [
                "谢谢", "太好了", "厉害", "棒", "喜欢", "开心", "高兴"
            ],
            EmotionalState.SAD: [
                "难过", "伤心", "失落", "沮丧", "痛苦", "哭", "眼泪"
            ],
            EmotionalState.ANGRY: [
                "生气", "愤怒", "讨厌", "烦", "恨", "气死了", "受不了"
            ],
            EmotionalState.CONFUSED: [
                "不明白", "困惑", "奇怪", "为什么", "怎么回事", "搞不懂"
            ]
        }
    
    def analyze_user_message_emotion(self, message: str) -> EmotionalState:
        """
        分析用户消息的情感倾向
        
        Args:
            message: 用户消息
            
        Returns:
            EmotionalState: 检测到的情感状态
        """
        message_lower = message.lower()
        
        # 情感得分统计
        emotion_scores = {state: 0 for state in EmotionalState}
        
        for emotion, triggers in self.emotion_triggers.items():
            for trigger in triggers:
                if trigger.lower() in message_lower:
                    emotion_scores[emotion] += 1
        
        # 特殊情况：问号多表示困惑
        if message.count('?') > 1 or message.count('？') > 1:
            emotion_scores[EmotionalState.CONFUSED] += 1
        
        # 感叹号多表示激动
        if message.count('!') > 2 or message.count('！') > 2:
            emotion_scores[EmotionalState.EXCITED] += 1
        
        # 找到得分最高的情感
        max_emotion = max(emotion_scores.items(), key=lambda x: x[1])
        
        return max_emotion[0] if max_emotion[1] > 0 else EmotionalState.NEUTRAL
    
    def get_character_emotional_response(
        self, 
        character: Character, 
        user_emotion: EmotionalState,
        session_id: str
    ) -> EmotionalState:
        """
        根据用户情感和角色特性决定角色的情感响应
        
        Args:
            character: 角色对象
            user_emotion: 用户情感状态
            session_id: 会话ID
            
        Returns:
            EmotionalState: 角色应该表现的情感状态
        """
        try:
            config_data = getattr(character, '_config_data', {})
            personality_deep = config_data.get('personality_deep', {})
            core_traits = personality_deep.get('core_traits', [])
            
            # 获取角色历史情感状态
            recent_emotions = self._get_recent_emotions(session_id)
            
            # 根据角色特性和用户情感决定响应
            if user_emotion == EmotionalState.SAD:
                # 用户难过时
                if any(trait in ['温柔', '关怀', '善良'] for trait in core_traits):
                    return EmotionalState.CARING
                elif any(trait in ['冷淡', '疏离'] for trait in core_traits):
                    return EmotionalState.CONFUSED
                else:
                    return EmotionalState.CARING
            
            elif user_emotion == EmotionalState.PLEASED:
                # 用户开心时
                if any(trait in ['骄傲', '自信', '强势'] for trait in core_traits):
                    return EmotionalState.PLEASED
                elif any(trait in ['活泼', '开朗'] for trait in core_traits):
                    return EmotionalState.EXCITED
                else:
                    return EmotionalState.PLEASED
            
            elif user_emotion == EmotionalState.ANGRY:
                # 用户生气时
                if any(trait in ['强势', '好胜'] for trait in core_traits):
                    return EmotionalState.ANGRY
                elif any(trait in ['温柔', '冷淡'] for trait in core_traits):
                    return EmotionalState.CONFUSED
                else:
                    return EmotionalState.NEUTRAL
            
            elif user_emotion == EmotionalState.CONFUSED:
                # 用户困惑时
                if any(trait in ['聪明', '知性'] for trait in core_traits):
                    return EmotionalState.CARING
                else:
                    return EmotionalState.CONFUSED
                    
            elif user_emotion == EmotionalState.EXCITED:
                # 用户兴奋时
                if any(trait in ['活泼', '开朗'] for trait in core_traits):
                    return EmotionalState.EXCITED
                elif any(trait in ['冷淡', '内敛'] for trait in core_traits):
                    return EmotionalState.CONFUSED
                else:
                    return EmotionalState.PLEASED
            
            # 默认根据角色基础性格
            if any(trait in ['活泼', '开朗', '热情'] for trait in core_traits):
                return EmotionalState.PLEASED
            elif any(trait in ['冷淡', '神秘', '内敛'] for trait in core_traits):
                return EmotionalState.NEUTRAL
            else:
                return EmotionalState.NEUTRAL
                
        except Exception as e:
            self.logger.error(f"确定角色情感响应时出错: {e}")
            return EmotionalState.NEUTRAL
    
    def update_emotion_history(
        self, 
        session_id: str, 
        user_emotion: EmotionalState, 
        character_emotion: EmotionalState
    ) -> None:
        """
        更新会话的情感历史
        
        Args:
            session_id: 会话ID
            user_emotion: 用户情感
            character_emotion: 角色情感
        """
        if session_id not in self._session_emotions:
            self._session_emotions[session_id] = []
        
        emotion_record = {
            'timestamp': datetime.now(),
            'user_emotion': user_emotion.value,
            'character_emotion': character_emotion.value
        }
        
        self._session_emotions[session_id].append(emotion_record)
        
        # 保持最近20条记录
        if len(self._session_emotions[session_id]) > 20:
            self._session_emotions[session_id] = self._session_emotions[session_id][-20:]
    
    def _get_recent_emotions(self, session_id: str, hours: int = 1) -> List[Dict[str, Any]]:
        """
        获取最近的情感状态记录
        
        Args:
            session_id: 会话ID
            hours: 获取几小时内的记录
            
        Returns:
            List[Dict]: 情感记录列表
        """
        if session_id not in self._session_emotions:
            return []
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_emotions = [
            record for record in self._session_emotions[session_id]
            if record['timestamp'] > cutoff_time
        ]
        
        return recent_emotions
    
    def get_emotion_consistency_modifier(
        self, 
        character: Character, 
        target_emotion: EmotionalState,
        session_id: str
    ) -> str:
        """
        获取情感一致性修饰符，确保角色情感变化合理
        
        Args:
            character: 角色对象
            target_emotion: 目标情感状态
            session_id: 会话ID
            
        Returns:
            str: 情感修饰提示
        """
        try:
            recent_emotions = self._get_recent_emotions(session_id, hours=0.5)
            
            if not recent_emotions:
                return ""
            
            last_emotion = recent_emotions[-1]['character_emotion']
            
            # 检查情感变化是否过于剧烈
            emotion_intensity = {
                EmotionalState.NEUTRAL.value: 0,
                EmotionalState.PLEASED.value: 2,
                EmotionalState.CONFUSED.value: 1,
                EmotionalState.SAD.value: -2,
                EmotionalState.ANGRY.value: -3,
                EmotionalState.CARING.value: 1,
                EmotionalState.EXCITED.value: 3
            }
            
            last_intensity = emotion_intensity.get(last_emotion, 0)
            target_intensity = emotion_intensity.get(target_emotion.value, 0)
            
            intensity_diff = abs(target_intensity - last_intensity)
            
            if intensity_diff > 3:
                # 情感变化过大，需要过渡
                return f"\n请注意：你的情感状态从{last_emotion}逐渐转向{target_emotion.value}，变化应该自然而不突兀。"
            
            return ""
            
        except Exception as e:
            self.logger.error(f"生成情感一致性修饰符时出错: {e}")
            return ""
    
    def clear_session_emotions(self, session_id: str) -> None:
        """
        清除指定会话的情感历史
        
        Args:
            session_id: 会话ID
        """
        if session_id in self._session_emotions:
            del self._session_emotions[session_id]
    
    def get_emotion_statistics(self, session_id: str) -> Dict[str, Any]:
        """
        获取会话的情感统计信息
        
        Args:
            session_id: 会话ID
            
        Returns:
            Dict: 情感统计信息
        """
        if session_id not in self._session_emotions:
            return {'total_interactions': 0, 'emotion_distribution': {}}
        
        emotions = self._session_emotions[session_id]
        total = len(emotions)
        
        # 统计角色情感分布
        character_emotions = [e['character_emotion'] for e in emotions]
        emotion_counts = {}
        for emotion in character_emotions:
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
        
        # 计算百分比
        emotion_distribution = {
            emotion: (count / total) * 100 
            for emotion, count in emotion_counts.items()
        }
        
        return {
            'total_interactions': total,
            'emotion_distribution': emotion_distribution,
            'recent_trend': character_emotions[-5:] if len(character_emotions) >= 5 else character_emotions
        } 