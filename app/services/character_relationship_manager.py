"""
角色关系网络管理器

管理不同角色之间的关系网络，处理角色互动、关系发展、冲突与协调等。
"""

import logging
from typing import Dict, List, Optional, Any, Tuple, Set
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass

from app.models import Character


class RelationshipType(Enum):
    """关系类型枚举"""
    NEUTRAL = "neutral"         # 中性关系
    FRIENDLY = "friendly"       # 友好关系
    ROMANTIC = "romantic"       # 浪漫关系
    RIVAL = "rival"            # 竞争关系
    ENEMY = "enemy"            # 敌对关系
    FAMILY = "family"          # 家庭关系
    COLLEAGUE = "colleague"    # 同事关系
    MENTOR = "mentor"          # 师生关系


class InteractionType(Enum):
    """互动类型枚举"""
    CONVERSATION = "conversation"   # 对话
    COOPERATION = "cooperation"     # 合作
    CONFLICT = "conflict"          # 冲突
    SUPPORT = "support"            # 支援
    TEACHING = "teaching"          # 教导
    COMPETITION = "competition"    # 竞争


@dataclass
class CharacterRelationship:
    """角色关系数据结构"""
    character_a_id: str
    character_b_id: str
    relationship_type: RelationshipType
    affinity_score: float  # 亲密度分数 (-100 到 100)
    trust_level: float     # 信任度 (0 到 100)
    interaction_count: int
    positive_interactions: int
    negative_interactions: int
    last_interaction: datetime
    relationship_notes: List[str]
    created_at: datetime
    updated_at: datetime


@dataclass
class InteractionRecord:
    """互动记录数据结构"""
    id: str
    character_a_id: str
    character_b_id: str
    interaction_type: InteractionType
    context: str
    outcome: str  # positive, negative, neutral
    impact_score: float  # 对关系的影响分数
    timestamp: datetime


class CharacterRelationshipManager:
    """角色关系网络管理器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # 存储角色关系
        self._relationships: Dict[str, CharacterRelationship] = {}
        # 存储互动记录
        self._interactions: List[InteractionRecord] = []
        
        # 预定义的角色关系（基于动漫设定）
        self.predefined_relationships = {
            ("rei_ayanami", "asuka_langley"): {
                "type": RelationshipType.RIVAL,
                "affinity": -10,
                "trust": 30,
                "notes": ["同为EVA驾驶员", "性格差异导致的微妙竞争关系"]
            },
            ("rei_ayanami", "miku_hatsune"): {
                "type": RelationshipType.NEUTRAL,
                "affinity": 5,
                "trust": 50,
                "notes": ["来自不同世界", "缺乏直接交集"]
            },
            ("asuka_langley", "miku_hatsune"): {
                "type": RelationshipType.FRIENDLY,
                "affinity": 15,
                "trust": 60,
                "notes": ["都很有活力", "可能会因为音乐话题产生共鸣"]
            }
        }
        
        # 关系影响因子
        self.relationship_factors = {
            RelationshipType.RIVAL: {
                "competitive_bonus": 10,
                "trust_penalty": -5,
                "conflict_amplifier": 1.5
            },
            RelationshipType.FRIENDLY: {
                "cooperation_bonus": 15,
                "trust_bonus": 5,
                "support_amplifier": 1.3
            },
            RelationshipType.ROMANTIC: {
                "intimacy_bonus": 20,
                "jealousy_factor": 2.0,
                "emotional_amplifier": 1.8
            }
        }
    
    def initialize_predefined_relationships(self):
        """初始化预定义的角色关系"""
        now = datetime.now()
        
        for (char_a, char_b), config in self.predefined_relationships.items():
            relationship_key = self._get_relationship_key(char_a, char_b)
            
            if relationship_key not in self._relationships:
                self._relationships[relationship_key] = CharacterRelationship(
                    character_a_id=char_a,
                    character_b_id=char_b,
                    relationship_type=config["type"],
                    affinity_score=config["affinity"],
                    trust_level=config["trust"],
                    interaction_count=0,
                    positive_interactions=0,
                    negative_interactions=0,
                    last_interaction=now,
                    relationship_notes=config["notes"],
                    created_at=now,
                    updated_at=now
                )
    
    def _get_relationship_key(self, char_a_id: str, char_b_id: str) -> str:
        """生成关系键值（确保一致性）"""
        return f"{min(char_a_id, char_b_id)}_{max(char_a_id, char_b_id)}"
    
    def get_relationship(
        self, 
        character_a_id: str, 
        character_b_id: str
    ) -> Optional[CharacterRelationship]:
        """获取两个角色之间的关系"""
        if character_a_id == character_b_id:
            return None  # 不允许自我关系
        
        relationship_key = self._get_relationship_key(character_a_id, character_b_id)
        return self._relationships.get(relationship_key)
    
    def create_or_update_relationship(
        self,
        character_a_id: str,
        character_b_id: str,
        interaction_type: InteractionType,
        context: str,
        outcome: str = "neutral",
        impact_score: float = 0.0
    ) -> CharacterRelationship:
        """
        创建或更新角色关系
        
        Args:
            character_a_id: 角色A的ID
            character_b_id: 角色B的ID
            interaction_type: 互动类型
            context: 互动上下文
            outcome: 互动结果 (positive, negative, neutral)
            impact_score: 影响分数
            
        Returns:
            CharacterRelationship: 更新后的关系
        """
        relationship_key = self._get_relationship_key(character_a_id, character_b_id)
        now = datetime.now()
        
        # 记录互动
        interaction_id = f"{character_a_id}_{character_b_id}_{now.timestamp()}"
        interaction = InteractionRecord(
            id=interaction_id,
            character_a_id=character_a_id,
            character_b_id=character_b_id,
            interaction_type=interaction_type,
            context=context,
            outcome=outcome,
            impact_score=impact_score,
            timestamp=now
        )
        self._interactions.append(interaction)
        
        # 获取或创建关系
        if relationship_key in self._relationships:
            relationship = self._relationships[relationship_key]
        else:
            # 创建新关系
            relationship = CharacterRelationship(
                character_a_id=character_a_id,
                character_b_id=character_b_id,
                relationship_type=RelationshipType.NEUTRAL,
                affinity_score=0.0,
                trust_level=50.0,
                interaction_count=0,
                positive_interactions=0,
                negative_interactions=0,
                last_interaction=now,
                relationship_notes=[],
                created_at=now,
                updated_at=now
            )
            self._relationships[relationship_key] = relationship
        
        # 更新关系数据
        relationship.interaction_count += 1
        relationship.last_interaction = now
        relationship.updated_at = now
        
        # 根据互动结果更新关系
        if outcome == "positive":
            relationship.positive_interactions += 1
            relationship.affinity_score = min(100.0, relationship.affinity_score + abs(impact_score))
            relationship.trust_level = min(100.0, relationship.trust_level + abs(impact_score) * 0.5)
        elif outcome == "negative":
            relationship.negative_interactions += 1
            relationship.affinity_score = max(-100.0, relationship.affinity_score - abs(impact_score))
            relationship.trust_level = max(0.0, relationship.trust_level - abs(impact_score) * 0.3)
        
        # 根据亲密度调整关系类型
        relationship.relationship_type = self._determine_relationship_type(relationship)
        
        return relationship
    
    def _determine_relationship_type(self, relationship: CharacterRelationship) -> RelationshipType:
        """根据关系数据确定关系类型"""
        affinity = relationship.affinity_score
        trust = relationship.trust_level
        positive_ratio = (
            relationship.positive_interactions / 
            max(1, relationship.interaction_count)
        )
        
        # 检查是否有特殊关系（基于预定义）
        rel_key = self._get_relationship_key(
            relationship.character_a_id, 
            relationship.character_b_id
        )
        
        if (relationship.character_a_id, relationship.character_b_id) in self.predefined_relationships:
            base_type = self.predefined_relationships[
                (relationship.character_a_id, relationship.character_b_id)
            ]["type"]
        elif (relationship.character_b_id, relationship.character_a_id) in self.predefined_relationships:
            base_type = self.predefined_relationships[
                (relationship.character_b_id, relationship.character_a_id)
            ]["type"]
        else:
            base_type = RelationshipType.NEUTRAL
        
        # 根据互动调整关系类型
        if affinity > 70 and trust > 80:
            if base_type == RelationshipType.FRIENDLY:
                return RelationshipType.ROMANTIC
            else:
                return RelationshipType.FRIENDLY
        elif affinity < -50:
            if base_type == RelationshipType.RIVAL:
                return RelationshipType.ENEMY
            else:
                return RelationshipType.RIVAL
        elif affinity > 30 and positive_ratio > 0.7:
            return RelationshipType.FRIENDLY
        elif affinity < -20 and positive_ratio < 0.3:
            return RelationshipType.RIVAL
        else:
            return base_type
    
    def get_character_relationships(self, character_id: str) -> List[CharacterRelationship]:
        """获取某个角色的所有关系"""
        relationships = []
        
        for relationship in self._relationships.values():
            if (relationship.character_a_id == character_id or 
                relationship.character_b_id == character_id):
                relationships.append(relationship)
        
        return relationships
    
    def get_relationship_context_for_prompt(
        self,
        primary_character_id: str,
        mentioned_characters: List[str]
    ) -> str:
        """
        获取用于提示词的关系上下文
        
        Args:
            primary_character_id: 主要角色ID
            mentioned_characters: 提到的其他角色ID列表
            
        Returns:
            str: 关系上下文文本
        """
        context_parts = []
        
        for other_char_id in mentioned_characters:
            if other_char_id == primary_character_id:
                continue
            
            relationship = self.get_relationship(primary_character_id, other_char_id)
            if relationship:
                # 确定从主要角色视角的关系描述
                if relationship.character_a_id == primary_character_id:
                    other_char = relationship.character_b_id
                else:
                    other_char = relationship.character_a_id
                
                relationship_desc = self._get_relationship_description(
                    relationship, primary_character_id
                )
                context_parts.append(f"与{other_char}的关系: {relationship_desc}")
        
        if context_parts:
            return f"\n\n<character_relationships>\n{chr(10).join(context_parts)}\n</character_relationships>"
        
        return ""
    
    def _get_relationship_description(
        self, 
        relationship: CharacterRelationship, 
        perspective_character_id: str
    ) -> str:
        """获取关系描述"""
        rel_type = relationship.relationship_type
        affinity = relationship.affinity_score
        trust = relationship.trust_level
        
        type_descriptions = {
            RelationshipType.NEUTRAL: "一般关系",
            RelationshipType.FRIENDLY: "友好关系",
            RelationshipType.ROMANTIC: "亲密关系",
            RelationshipType.RIVAL: "竞争关系",
            RelationshipType.ENEMY: "敌对关系",
            RelationshipType.FAMILY: "家人关系",
            RelationshipType.COLLEAGUE: "同事关系",
            RelationshipType.MENTOR: "师生关系"
        }
        
        base_desc = type_descriptions.get(rel_type, "未知关系")
        
        # 添加亲密度和信任度信息
        if affinity > 50:
            affinity_desc = "很亲近"
        elif affinity > 0:
            affinity_desc = "比较亲近"
        elif affinity > -30:
            affinity_desc = "有些疏远"
        else:
            affinity_desc = "很疏远"
        
        if trust > 70:
            trust_desc = "高度信任"
        elif trust > 40:
            trust_desc = "一般信任"
        else:
            trust_desc = "缺乏信任"
        
        return f"{base_desc}({affinity_desc}, {trust_desc})"
    
    def simulate_character_interaction(
        self,
        character_a: Character,
        character_b: Character,
        topic: str
    ) -> Dict[str, Any]:
        """
        模拟两个角色之间的互动
        
        Args:
            character_a: 角色A
            character_b: 角色B
            topic: 互动话题
            
        Returns:
            Dict: 互动模拟结果
        """
        relationship = self.get_relationship(character_a.id, character_b.id)
        
        # 获取角色配置数据
        config_a = getattr(character_a, '_config_data', {})
        config_b = getattr(character_b, '_config_data', {})
        
        personality_a = config_a.get('personality_deep', {}).get('core_traits', [])
        personality_b = config_b.get('personality_deep', {}).get('core_traits', [])
        
        # 计算兼容性
        compatibility = self._calculate_personality_compatibility(personality_a, personality_b)
        
        # 预测互动结果
        if relationship:
            base_affinity = relationship.affinity_score
        else:
            base_affinity = 0
        
        interaction_score = (compatibility * 0.4 + base_affinity * 0.6) / 100
        
        # 生成互动建议
        suggestions = self._generate_interaction_suggestions(
            character_a, character_b, topic, interaction_score
        )
        
        return {
            "characters": [character_a.name, character_b.name],
            "topic": topic,
            "predicted_outcome": "positive" if interaction_score > 0.3 else 
                                "negative" if interaction_score < -0.3 else "neutral",
            "compatibility_score": compatibility,
            "current_affinity": base_affinity,
            "interaction_suggestions": suggestions,
            "potential_conflicts": self._identify_potential_conflicts(
                personality_a, personality_b
            )
        }
    
    def _calculate_personality_compatibility(
        self, 
        traits_a: List[str], 
        traits_b: List[str]
    ) -> float:
        """计算性格兼容性"""
        # 兼容性矩阵（简化版）
        compatibility_matrix = {
            "活泼开朗": {"冷淡": -20, "内敛": -10, "活泼开朗": 30, "温柔": 20},
            "冷淡": {"活泼开朗": -20, "强势": -15, "冷淡": 10, "神秘": 15},
            "强势好胜": {"温柔": 10, "强势好胜": -10, "冷淡": -5, "活泼开朗": 15},
            "温柔": {"强势好胜": 10, "冷淡": 5, "温柔": 25, "活泼开朗": 20},
            "神秘莫测": {"冷淡": 15, "神秘莫测": 5, "活泼开朗": -10}
        }
        
        total_score = 0
        comparisons = 0
        
        for trait_a in traits_a:
            for trait_b in traits_b:
                if trait_a in compatibility_matrix:
                    score = compatibility_matrix[trait_a].get(trait_b, 0)
                    total_score += score
                    comparisons += 1
        
        return total_score / max(1, comparisons)
    
    def _generate_interaction_suggestions(
        self,
        character_a: Character,
        character_b: Character,
        topic: str,
        interaction_score: float
    ) -> List[str]:
        """生成互动建议"""
        suggestions = []
        
        if interaction_score > 0.3:
            suggestions.extend([
                f"{character_a.name}可以主动与{character_b.name}分享{topic}相关的想法",
                f"两人可以就{topic}进行深入的讨论",
                f"鼓励合作和相互支持"
            ])
        elif interaction_score < -0.3:
            suggestions.extend([
                f"{character_a.name}在谈论{topic}时应该保持谨慎",
                f"避免触及敏感话题，保持礼貌距离",
                f"寻找共同点来缓解紧张关系"
            ])
        else:
            suggestions.extend([
                f"可以围绕{topic}进行轻松的交流",
                f"保持友好但不过分亲近的态度",
                f"观察对方的反应来调整互动方式"
            ])
        
        return suggestions
    
    def _identify_potential_conflicts(
        self, 
        traits_a: List[str], 
        traits_b: List[str]
    ) -> List[str]:
        """识别潜在冲突点"""
        conflicts = []
        
        conflict_combinations = [
            (["强势好胜", "骄傲"], ["强势好胜", "骄傲"], "双方都很强势，可能产生竞争冲突"),
            (["冷淡", "疏离"], ["活泼开朗", "热情"], "性格反差较大，可能产生理解困难"),
            (["固执", "倔强"], ["固执", "倔强"], "双方都很固执，容易产生意见分歧")
        ]
        
        for traits_x, traits_y, conflict_desc in conflict_combinations:
            if (any(t in traits_a for t in traits_x) and any(t in traits_b for t in traits_y)) or \
               (any(t in traits_b for t in traits_x) and any(t in traits_a for t in traits_y)):
                conflicts.append(conflict_desc)
        
        return conflicts
    
    def get_relationship_network_summary(self) -> Dict[str, Any]:
        """获取关系网络摘要"""
        total_relationships = len(self._relationships)
        
        # 按类型统计
        type_counts = {}
        for rel in self._relationships.values():
            rel_type = rel.relationship_type.value
            type_counts[rel_type] = type_counts.get(rel_type, 0) + 1
        
        # 找出最活跃的关系
        most_interactive = max(
            self._relationships.values(),
            key=lambda r: r.interaction_count,
            default=None
        )
        
        return {
            "total_relationships": total_relationships,
            "relationship_types": type_counts,
            "most_interactive_pair": (
                f"{most_interactive.character_a_id} & {most_interactive.character_b_id}"
                if most_interactive else None
            ),
            "total_interactions": len(self._interactions),
            "network_density": total_relationships / max(1, (3 * 2 / 2))  # 假设3个角色的完全图
        } 