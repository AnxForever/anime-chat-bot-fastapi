"""
角色数据模型

定义动漫角色的配置结构和验证规则。
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from . import CharacterType


class Character(BaseModel):
    """
    角色模型
    
    定义动漫角色的完整配置信息，包括基础信息、性格特征、
    语言风格、行为约束和LLM配置参数。
    """
    
    # 基础标识信息
    id: str = Field(..., description="角色唯一标识符", min_length=1, max_length=50)
    name: str = Field(..., description="角色名称", min_length=1, max_length=100)
    type: CharacterType = Field(default=CharacterType.ANIME, description="角色类型")
    
    # 外观和描述
    avatar_url: Optional[str] = Field(None, description="头像URL")
    description: str = Field(..., description="角色简介", min_length=10, max_length=500)
    personality: str = Field(..., description="性格特征", min_length=10, max_length=1000)
    background: Optional[str] = Field(None, description="背景故事", max_length=2000)
    
    # 语言风格配置
    speech_patterns: List[str] = Field(
        default_factory=list, 
        description="语言模式和说话习惯",
        max_items=10
    )
    catchphrases: List[str] = Field(
        default_factory=list, 
        description="角色的口头禅和常用语",
        max_items=10
    )
    tone: str = Field(
        default="friendly", 
        description="基本语调风格",
        max_length=50
    )
    
    # 角色扮演核心设置
    system_prompt: str = Field(
        ..., 
        description="系统提示词模板",
        min_length=50,
        max_length=4000
    )
    example_dialogues: List[Dict[str, str]] = Field(
        default_factory=list, 
        description="示例对话片段",
        max_items=5
    )
    
    # 行为约束和规则
    forbidden_topics: List[str] = Field(
        default_factory=list, 
        description="禁止讨论的话题",
        max_items=20
    )
    behavioral_rules: List[str] = Field(
        default_factory=list, 
        description="角色行为准则",
        max_items=15
    )
    
    # LLM配置参数
    max_context_length: int = Field(
        default=4000, 
        description="最大上下文长度",
        ge=1000,
        le=8000
    )
    temperature: float = Field(
        default=0.8, 
        description="LLM温度参数，控制回复的创造性",
        ge=0.0,
        le=2.0
    )
    max_tokens: int = Field(
        default=1000,
        description="单次回复的最大token数",
        ge=100,
        le=2000
    )
    
    # 元数据
    created_at: Optional[str] = Field(None, description="创建时间")
    updated_at: Optional[str] = Field(None, description="更新时间")
    tags: List[str] = Field(
        default_factory=list, 
        description="角色标签，用于分类和搜索",
        max_items=10
    )
    
    # 扩展配置
    metadata: Dict[str, Any] = Field(
        default_factory=dict, 
        description="扩展元数据"
    )
    
    class Config:
        """Pydantic配置"""
        json_schema_extra = {
            "example": {
                "id": "tsundere_alice",
                "name": "艾莉丝",
                "type": "anime",
                "description": "傲娇魔法少女，外表冷淡但内心温柔，是学院中实力强大的魔法师。",
                "personality": "傲娇、毒舌、内心温柔、容易害羞、好胜心强、对朋友很忠诚",
                "background": "来自魔法世界的贵族家庭，从小接受严格的魔法训练...",
                "speech_patterns": [
                    "经常使用反问句", 
                    "说话时常有停顿", 
                    "害羞时会结巴",
                    "生气时语调会变高"
                ],
                "catchphrases": [
                    "哼！才不是为了你呢！", 
                    "别、别误会了！",
                    "这种事情我才不在乎呢..."
                ],
                "tone": "傲娇",
                "system_prompt": "你是艾莉丝，一个傲娇的魔法少女...",
                "temperature": 0.8,
                "max_tokens": 800,
                "tags": ["傲娇", "魔法少女", "学院", "贵族"]
            }
        }


class CharacterSummary(BaseModel):
    """
    角色摘要模型
    
    用于角色列表显示，只包含基本信息。
    """
    
    id: str = Field(..., description="角色ID")
    name: str = Field(..., description="角色名称")
    type: CharacterType = Field(..., description="角色类型")
    description: str = Field(..., description="角色简介")
    avatar_url: Optional[str] = Field(None, description="头像URL")
    tags: List[str] = Field(default_factory=list, description="标签") 