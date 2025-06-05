"""
角色管理API路由
提供角色信息查询和管理的接口
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any

from ..models import Character, CharacterType
from ..services import CharacterLoader
from ..core.exceptions import CharacterNotFoundError, ValidationError

router = APIRouter(prefix="/api/characters", tags=["characters"])

# 依赖注入
def get_character_loader():
    return CharacterLoader()


@router.get("/", response_model=List[Dict[str, Any]])
async def list_characters(
    character_type: Optional[CharacterType] = Query(None, description="按角色类型筛选"),
    search: Optional[str] = Query(None, description="搜索角色名称或描述"),
    limit: Optional[int] = Query(20, ge=1, le=100, description="返回数量限制"),
    offset: Optional[int] = Query(0, ge=0, description="偏移量"),
    character_loader: CharacterLoader = Depends(get_character_loader)
):
    """
    获取角色列表
    
    Args:
        character_type: 角色类型筛选
        search: 搜索关键词
        limit: 返回数量限制
        offset: 偏移量
        
    Returns:
        List[Dict]: 角色列表
    """
    try:
        # 获取所有角色
        all_characters = await character_loader.list_characters()
        
        # 应用筛选条件
        filtered_characters = []
        for char_info in all_characters:
            # 类型筛选
            if character_type and char_info.get("character_type") != character_type.value:
                continue
            
            # 搜索筛选
            if search:
                search_lower = search.lower()
                name_match = search_lower in char_info.get("name", "").lower()
                desc_match = search_lower in char_info.get("description", "").lower()
                if not (name_match or desc_match):
                    continue
            
            filtered_characters.append(char_info)
        
        # 分页
        total = len(filtered_characters)
        start = offset
        end = offset + limit
        paginated_characters = filtered_characters[start:end]
        
        # 为每个角色添加分页信息
        result = []
        for char_info in paginated_characters:
            result.append({
                **char_info,
                "total": total,
                "limit": limit,
                "offset": offset,
                "has_more": end < total
            })
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取角色列表失败: {str(e)}")


@router.get("/{character_id}", response_model=Dict[str, Any])
async def get_character(
    character_id: str,
    include_config: bool = Query(False, description="是否包含详细配置信息"),
    character_loader: CharacterLoader = Depends(get_character_loader)
):
    """
    获取指定角色的详细信息
    
    Args:
        character_id: 角色ID
        include_config: 是否包含详细配置
        
    Returns:
        Dict: 角色详细信息
    """
    try:
        character = await character_loader.get_character(character_id)
        if not character:
            raise HTTPException(status_code=404, detail=f"角色 {character_id} 不存在")
        
        # 基础信息
        result = {
            "id": character.id,
            "name": character.name,
            "description": character.description,
            "character_type": character.character_type.value,
            "tags": character.tags,
            "avatar_url": character.avatar_url,
            "is_active": character.is_active,
            "created_at": character.created_at,
            "updated_at": character.updated_at
        }
        
        # 详细配置信息（可选）
        if include_config:
            result.update({
                "personality": {
                    "traits": character.personality.traits,
                    "speech_style": character.personality.speech_style,
                    "emotional_range": character.personality.emotional_range,
                    "interests": character.personality.interests,
                    "background": character.personality.background
                },
                "behavior_rules": {
                    "forbidden_topics": character.behavior_rules.forbidden_topics,
                    "response_guidelines": character.behavior_rules.response_guidelines,
                    "interaction_style": character.behavior_rules.interaction_style,
                    "content_filters": character.behavior_rules.content_filters
                },
                "llm_config": {
                    "provider": character.llm_config.provider.value,
                    "model_name": character.llm_config.model_name,
                    "temperature": character.llm_config.temperature,
                    "max_tokens": character.llm_config.max_tokens,
                    "top_p": character.llm_config.top_p,
                    "frequency_penalty": character.llm_config.frequency_penalty,
                    "presence_penalty": character.llm_config.presence_penalty
                },
                "context_config": {
                    "max_context_length": character.context_config.max_context_length,
                    "context_window_size": character.context_config.context_window_size,
                    "memory_summary_threshold": character.context_config.memory_summary_threshold,
                    "important_memory_weight": character.context_config.important_memory_weight
                }
            })
        
        return result
        
    except CharacterNotFoundError:
        raise HTTPException(status_code=404, detail=f"角色 {character_id} 不存在")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取角色信息失败: {str(e)}")


@router.get("/{character_id}/preview")
async def get_character_preview(
    character_id: str,
    character_loader: CharacterLoader = Depends(get_character_loader)
):
    """
    获取角色预览信息（用于聊天界面显示）
    
    Args:
        character_id: 角色ID
        
    Returns:
        Dict: 角色预览信息
    """
    try:
        character = await character_loader.get_character(character_id)
        if not character:
            raise HTTPException(status_code=404, detail=f"角色 {character_id} 不存在")
        
        return {
            "id": character.id,
            "name": character.name,
            "description": character.description,
            "avatar_url": character.avatar_url,
            "character_type": character.character_type.value,
            "tags": character.tags,
            "personality_summary": {
                "main_traits": character.personality.traits[:3],  # 主要特征
                "speech_style": character.personality.speech_style,
                "interests": character.personality.interests[:5]  # 主要兴趣
            },
            "greeting": character.system_prompt.get("greeting", "你好！我是 " + character.name),
            "sample_responses": character.system_prompt.get("sample_responses", [])
        }
        
    except CharacterNotFoundError:
        raise HTTPException(status_code=404, detail=f"角色 {character_id} 不存在")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取角色预览失败: {str(e)}")


@router.get("/types/")
async def get_character_types():
    """
    获取所有可用的角色类型
    
    Returns:
        Dict: 角色类型列表和描述
    """
    return {
        "character_types": [
            {
                "value": char_type.value,
                "name": char_type.value,
                "description": _get_character_type_description(char_type)
            }
            for char_type in CharacterType
        ]
    }


@router.get("/tags/")
async def get_popular_tags(
    limit: int = Query(20, ge=1, le=50, description="返回标签数量"),
    character_loader: CharacterLoader = Depends(get_character_loader)
):
    """
    获取热门标签
    
    Args:
        limit: 返回标签数量
        
    Returns:
        Dict: 标签列表和使用次数
    """
    try:
        all_characters = await character_loader.list_characters()
        
        # 统计标签使用频率
        tag_counts = {}
        for char_info in all_characters:
            for tag in char_info.get("tags", []):
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        # 按使用频率排序
        sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
        
        return {
            "tags": [
                {"name": tag, "count": count}
                for tag, count in sorted_tags[:limit]
            ],
            "total_tags": len(tag_counts)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取标签失败: {str(e)}")


@router.post("/{character_id}/validate")
async def validate_character(
    character_id: str,
    character_loader: CharacterLoader = Depends(get_character_loader)
):
    """
    验证角色配置是否有效
    
    Args:
        character_id: 角色ID
        
    Returns:
        Dict: 验证结果
    """
    try:
        character = await character_loader.get_character(character_id)
        if not character:
            raise HTTPException(status_code=404, detail=f"角色 {character_id} 不存在")
        
        # 执行各种验证
        validation_results = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "details": {}
        }
        
        # 基础信息验证
        if not character.name or len(character.name.strip()) == 0:
            validation_results["errors"].append("角色名称不能为空")
            validation_results["is_valid"] = False
        
        if not character.description or len(character.description.strip()) < 10:
            validation_results["warnings"].append("角色描述过短，建议至少10个字符")
        
        # 个性配置验证
        if not character.personality.traits:
            validation_results["errors"].append("角色特征不能为空")
            validation_results["is_valid"] = False
        
        if len(character.personality.traits) > 10:
            validation_results["warnings"].append("角色特征过多，建议控制在10个以内")
        
        # LLM配置验证
        if character.llm_config.temperature < 0 or character.llm_config.temperature > 2:
            validation_results["errors"].append("temperature参数应在0-2之间")
            validation_results["is_valid"] = False
        
        if character.llm_config.max_tokens < 1 or character.llm_config.max_tokens > 4096:
            validation_results["errors"].append("max_tokens参数应在1-4096之间")
            validation_results["is_valid"] = False
        
        # 上下文配置验证
        if character.context_config.max_context_length < 100:
            validation_results["warnings"].append("最大上下文长度过短，可能影响对话质量")
        
        # 系统提示词验证
        if not character.system_prompt.get("base_prompt"):
            validation_results["errors"].append("基础系统提示词不能为空")
            validation_results["is_valid"] = False
        
        # 添加验证详细信息
        validation_results["details"] = {
            "character_id": character_id,
            "name": character.name,
            "validation_time": "现在",  # 实际应用中使用datetime.now()
            "config_completeness": _calculate_config_completeness(character)
        }
        
        return validation_results
        
    except CharacterNotFoundError:
        raise HTTPException(status_code=404, detail=f"角色 {character_id} 不存在")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"验证角色配置失败: {str(e)}")


def _get_character_type_description(char_type: CharacterType) -> str:
    """获取角色类型的描述"""
    descriptions = {
        CharacterType.ANIME: "动漫角色，通常来自日本动画作品",
        CharacterType.GAME: "游戏角色，来自各种电子游戏",
        CharacterType.NOVEL: "小说角色，来自文学作品",
        CharacterType.ORIGINAL: "原创角色，独特的虚拟人物",
        CharacterType.HISTORICAL: "历史人物，真实存在的历史角色",
        CharacterType.CELEBRITY: "名人角色，现实中的知名人物"
    }
    return descriptions.get(char_type, "未知类型")


def _calculate_config_completeness(character: Character) -> float:
    """计算角色配置的完整度"""
    total_fields = 0
    completed_fields = 0
    
    # 基础信息
    total_fields += 4
    if character.name: completed_fields += 1
    if character.description: completed_fields += 1
    if character.avatar_url: completed_fields += 1
    if character.tags: completed_fields += 1
    
    # 个性配置
    total_fields += 5
    if character.personality.traits: completed_fields += 1
    if character.personality.speech_style: completed_fields += 1
    if character.personality.emotional_range: completed_fields += 1
    if character.personality.interests: completed_fields += 1
    if character.personality.background: completed_fields += 1
    
    # 行为规则
    total_fields += 4
    if character.behavior_rules.forbidden_topics: completed_fields += 1
    if character.behavior_rules.response_guidelines: completed_fields += 1
    if character.behavior_rules.interaction_style: completed_fields += 1
    if character.behavior_rules.content_filters: completed_fields += 1
    
    # 系统提示词
    total_fields += 2
    if character.system_prompt.get("base_prompt"): completed_fields += 1
    if character.system_prompt.get("greeting"): completed_fields += 1
    
    return round((completed_fields / total_fields) * 100, 1) 