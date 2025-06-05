"""
统计分析路由 - 支持对话质量分析和用户行为统计
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import random

router = APIRouter(prefix="/api/v1/analytics", tags=["统计分析"])

class QualityAnalysis(BaseModel):
    conversation_quality: float      # 对话质量 (0-100)
    relationship_development: float  # 关系发展 (0-100)
    emotional_interaction: float     # 情绪互动 (0-100)
    activity_pattern: float         # 活动模式 (0-100)
    topic_diversity: float          # 话题多样性 (0-100)
    overall_score: float            # 总体评分 (0-100)

class ConversationStats(BaseModel):
    total_messages: int
    average_message_length: float
    conversation_duration_minutes: float
    character_response_rate: float
    user_engagement_score: float

class RelationshipProgress(BaseModel):
    current_level: str
    progress_percentage: float
    milestones_achieved: List[str]
    next_milestone: str
    relationship_history: List[Dict[str, Any]]

@router.get("/quality/{character_id}/{session_id}")
async def get_conversation_quality(character_id: str, session_id: str):
    """获取对话质量分析"""
    
    # 模拟质量分析数据
    quality_scores = {
        "conversation_quality": random.uniform(70, 95),
        "relationship_development": random.uniform(60, 90),
        "emotional_interaction": random.uniform(65, 88),
        "activity_pattern": random.uniform(55, 85),
        "topic_diversity": random.uniform(70, 92)
    }
    
    # 计算总体评分
    overall_score = sum(quality_scores.values()) / len(quality_scores)
    quality_scores["overall_score"] = overall_score
    
    # 生成改进建议
    suggestions = []
    if quality_scores["relationship_development"] < 70:
        suggestions.append({
            "category": "关系发展",
            "suggestion": "尝试分享更多个人经历和感受",
            "priority": "high"
        })
    
    if quality_scores["topic_diversity"] < 75:
        suggestions.append({
            "category": "话题多样性",
            "suggestion": "探讨不同类型的话题，如兴趣、梦想、日常生活",
            "priority": "medium"
        })
    
    if quality_scores["emotional_interaction"] < 70:
        suggestions.append({
            "category": "情绪互动",
            "suggestion": "更多地表达自己的情感和感受",
            "priority": "high"
        })
    
    return {
        "success": True,
        "quality_analysis": quality_scores,
        "suggestions": suggestions,
        "analysis_date": datetime.now().isoformat()
    }

@router.get("/conversation-stats/{character_id}/{session_id}")
async def get_conversation_statistics(
    character_id: str, 
    session_id: str,
    days: int = 7
):
    """获取对话统计信息"""
    
    # 模拟统计数据
    stats = {
        "total_messages": random.randint(50, 200),
        "user_messages": random.randint(25, 100),
        "character_messages": random.randint(25, 100),
        "average_message_length": random.uniform(20, 80),
        "conversation_duration_minutes": random.uniform(30, 180),
        "character_response_rate": random.uniform(0.85, 0.98),
        "user_engagement_score": random.uniform(70, 95),
        "peak_activity_hours": [19, 20, 21],  # 晚上7-9点
        "conversation_frequency": {
            "daily_average": random.uniform(5, 20),
            "weekly_total": random.randint(30, 100),
            "monthly_trend": "increasing"
        }
    }
    
    # 每日活动分布
    daily_distribution = []
    for i in range(24):
        activity_level = random.uniform(0, 1)
        if i in [19, 20, 21]:  # 晚上活跃度更高
            activity_level = random.uniform(0.7, 1.0)
        elif i in range(0, 7):  # 凌晨活跃度较低
            activity_level = random.uniform(0, 0.3)
            
        daily_distribution.append({
            "hour": i,
            "activity_level": activity_level,
            "message_count": int(activity_level * 20)
        })
    
    stats["daily_distribution"] = daily_distribution
    
    return {
        "success": True,
        "statistics": stats,
        "period_days": days,
        "generated_at": datetime.now().isoformat()
    }

@router.get("/relationship-progress/{character_id}/{session_id}")
async def get_relationship_progress(character_id: str, session_id: str):
    """获取关系发展进度"""
    
    # 关系等级定义
    relationship_levels = [
        "stranger", "acquaintance", "friend", 
        "close_friend", "best_friend", "special"
    ]
    
    current_level_index = random.randint(1, 4)
    current_level = relationship_levels[current_level_index]
    
    # 模拟关系进度数据
    progress_data = {
        "current_level": current_level,
        "progress_percentage": random.uniform(30, 90),
        "milestones_achieved": [
            "第一次对话",
            "分享个人信息",
            "情感交流",
            "建立信任"
        ][:current_level_index + 1],
        "next_milestone": "深入了解彼此" if current_level_index < len(relationship_levels) - 1 else "维持特殊关系",
        "relationship_score": random.uniform(60, 95),
        "interaction_count": random.randint(20, 150),
        "positive_interactions": random.randint(18, 140),
        "negative_interactions": random.randint(0, 5)
    }
    
    # 关系历史
    relationship_history = []
    for i in range(1, current_level_index + 2):
        if i < len(relationship_levels):
            relationship_history.append({
                "level": relationship_levels[i],
                "achieved_date": (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat(),
                "key_event": f"达成{relationship_levels[i]}关系"
            })
    
    progress_data["relationship_history"] = relationship_history
    
    return {
        "success": True,
        "relationship_progress": progress_data,
        "updated_at": datetime.now().isoformat()
    }

@router.get("/emotion-analysis/{character_id}/{session_id}")
async def get_emotion_analysis(
    character_id: str, 
    session_id: str,
    days: int = 30
):
    """获取情绪分析"""
    
    emotions = ["happy", "sad", "excited", "angry", "neutral", "confused"]
    
    # 情绪分布
    emotion_distribution = {}
    for emotion in emotions:
        emotion_distribution[emotion] = random.uniform(5, 25)
    
    # 归一化到100%
    total = sum(emotion_distribution.values())
    emotion_distribution = {k: (v/total)*100 for k, v in emotion_distribution.items()}
    
    # 情绪时间线
    emotion_timeline = []
    for i in range(days):
        date = (datetime.now() - timedelta(days=i)).date()
        dominant_emotion = random.choice(emotions)
        emotion_timeline.append({
            "date": date.isoformat(),
            "dominant_emotion": dominant_emotion,
            "intensity": random.uniform(0.3, 1.0),
            "stability": random.uniform(0.5, 1.0)
        })
    
    # 情绪洞察
    insights = {
        "dominant_emotion": max(emotion_distribution.items(), key=lambda x: x[1])[0],
        "emotional_stability": random.uniform(0.6, 0.9),
        "positive_ratio": (emotion_distribution.get("happy", 0) + emotion_distribution.get("excited", 0)) / 100,
        "improvement_trend": random.choice(["improving", "stable", "declining"])
    }
    
    return {
        "success": True,
        "emotion_analysis": {
            "distribution": emotion_distribution,
            "timeline": emotion_timeline[-7:],  # 最近7天
            "insights": insights,
            "recommendations": [
                "保持积极的对话氛围",
                "注意用户的情绪变化",
                "在用户情绪低落时给予支持"
            ]
        },
        "analysis_period": f"{days} days",
        "generated_at": datetime.now().isoformat()
    }

@router.get("/topic-analysis/{character_id}/{session_id}")
async def get_topic_analysis(character_id: str, session_id: str):
    """获取话题分析"""
    
    # 话题分类
    topics = {
        "日常生活": random.uniform(20, 35),
        "兴趣爱好": random.uniform(15, 30),
        "工作学习": random.uniform(10, 25),
        "情感交流": random.uniform(10, 20),
        "娱乐游戏": random.uniform(5, 15),
        "其他": random.uniform(5, 10)
    }
    
    # 归一化到100%
    total = sum(topics.values())
    topics = {k: (v/total)*100 for k, v in topics.items()}
    
    # 话题趋势
    topic_trends = []
    for topic, percentage in topics.items():
        trend = random.choice(["increasing", "stable", "decreasing"])
        topic_trends.append({
            "topic": topic,
            "percentage": percentage,
            "trend": trend,
            "engagement_level": random.uniform(0.6, 1.0)
        })
    
    # 推荐新话题
    recommended_topics = [
        "尝试讨论未来的梦想和计划",
        "分享有趣的童年回忆",
        "聊聊最近看的电影或书籍",
        "讨论对某个社会话题的看法"
    ]
    
    return {
        "success": True,
        "topic_analysis": {
            "distribution": topics,
            "trends": topic_trends,
            "diversity_score": len([t for t in topics.values() if t > 5]) / len(topics),
            "recommended_topics": recommended_topics,
            "insights": {
                "most_discussed": max(topics.items(), key=lambda x: x[1])[0],
                "least_discussed": min(topics.items(), key=lambda x: x[1])[0],
                "balance_score": 1.0 - (max(topics.values()) - min(topics.values())) / 100
            }
        },
        "generated_at": datetime.now().isoformat()
    }

@router.get("/improvement-suggestions/{character_id}/{session_id}")
async def get_improvement_suggestions(character_id: str, session_id: str):
    """获取改进建议"""
    
    suggestions = [
        {
            "category": "对话深度",
            "title": "增加情感共鸣",
            "description": "尝试分享更多个人感受和内心想法",
            "priority": "high",
            "estimated_impact": "显著提升关系质量",
            "action_steps": [
                "分享今天的心情",
                "询问对方的感受",
                "表达理解和同情"
            ],
            "progress": 0.3
        },
        {
            "category": "话题多样性",
            "title": "探索新领域",
            "description": "尝试讨论之前未涉及的话题",
            "priority": "medium",
            "estimated_impact": "增加对话趣味性",
            "action_steps": [
                "询问对方的兴趣爱好",
                "分享自己的新发现",
                "讨论时事或流行文化"
            ],
            "progress": 0.6
        },
        {
            "category": "互动频率",
            "title": "保持定期联系",
            "description": "建立稳定的对话节奏",
            "priority": "medium",
            "estimated_impact": "维持关系稳定性",
            "action_steps": [
                "设定固定的聊天时间",
                "主动发起话题",
                "回应对方的消息"
            ],
            "progress": 0.8
        }
    ]
    
    return {
        "success": True,
        "suggestions": suggestions,
        "overall_progress": sum(s["progress"] for s in suggestions) / len(suggestions),
        "next_focus": "对话深度",
        "generated_at": datetime.now().isoformat()
    } 