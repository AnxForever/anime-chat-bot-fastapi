"""
测试数据模型
"""
import pytest
from datetime import datetime
from app.models import Character, CharacterType, Message, MessageRole, MessageStatus, Session, SessionStatus, LLMProvider
from app.models.character import Personality, BehaviorRules, LLMConfig, ContextConfig

class TestCharacter:
    """测试角色模型"""
    
    def test_character_creation(self):
        """测试角色创建"""
        personality = Personality(
            traits=["冷静", "理性"],
            speech_style=["简洁", "直接"],
            emotional_range=["平静", "困惑"],
            interests=["阅读", "思考"],
            background="测试角色背景"
        )
        
        behavior_rules = BehaviorRules(
            forbidden_topics=["暴力"],
            response_guidelines=["保持冷静"],
            interaction_style="理性",
            content_filters=["violence_strict"]
        )
        
        llm_config = LLMConfig(
            provider=LLMProvider.GEMINI,
            model_name="gemini-pro",
            temperature=0.7
        )
        
        context_config = ContextConfig()
        
        character = Character(
            id="test_character",
            name="测试角色",
            description="用于测试的角色",
            character_type=CharacterType.ORIGINAL,
            personality=personality,
            behavior_rules=behavior_rules,
            llm_config=llm_config,
            context_config=context_config,
            system_prompt={"base_prompt": "你是一个测试角色"}
        )
        
        assert character.id == "test_character"
        assert character.name == "测试角色"
        assert character.character_type == CharacterType.ORIGINAL
        assert character.is_active is True
        assert len(character.personality.traits) == 2

    def test_character_validation(self):
        """测试角色验证"""
        with pytest.raises(ValueError):
            # 空名称应该抛出错误
            Character(
                id="test",
                name="",
                description="测试",
                character_type=CharacterType.ORIGINAL,
                personality=Personality(),
                behavior_rules=BehaviorRules(),
                llm_config=LLMConfig(),
                context_config=ContextConfig(),
                system_prompt={}
            )

class TestMessage:
    """测试消息模型"""
    
    def test_message_creation(self):
        """测试消息创建"""
        message = Message(
            role=MessageRole.USER,
            content="你好"
        )
        
        assert message.role == MessageRole.USER
        assert message.content == "你好"
        assert message.status == MessageStatus.SENT
        assert message.id is not None
        assert message.timestamp is not None

    def test_message_validation(self):
        """测试消息验证"""
        with pytest.raises(ValueError):
            # 空内容应该抛出错误
            Message(
                role=MessageRole.USER,
                content=""
            )

class TestSession:
    """测试会话模型"""
    
    @pytest.mark.asyncio
    async def test_session_creation(self):
        """测试会话创建"""
        session = Session(
            session_id="test_session",
            character_id="test_character",
            user_id="test_user"
        )
        
        assert session.session_id == "test_session"
        assert session.character_id == "test_character"
        assert session.user_id == "test_user"
        assert session.status == SessionStatus.ACTIVE
        assert len(session.messages) == 0
        
    @pytest.mark.asyncio
    async def test_add_message(self):
        """测试添加消息"""
        session = Session(
            session_id="test_session",
            character_id="test_character",
            user_id="test_user"
        )
        
        message = await session.add_message(
            role=MessageRole.USER,
            content="你好"
        )
        
        assert len(session.messages) == 1
        assert message.role == MessageRole.USER
        assert message.content == "你好"
        assert session.messages[0] == message
    
    @pytest.mark.asyncio
    async def test_get_recent_messages(self):
        """测试获取最近消息"""
        session = Session(
            session_id="test_session",
            character_id="test_character",
            user_id="test_user"
        )
        
        # 添加多条消息
        for i in range(5):
            await session.add_message(
                role=MessageRole.USER,
                content=f"消息 {i}"
            )
        
        recent_messages = session.get_recent_messages(3)
        assert len(recent_messages) == 3
        assert recent_messages[0].content == "消息 2"  # 最近3条从第2条开始
        assert recent_messages[-1].content == "消息 4"  # 最后一条是第4条
    
    @pytest.mark.asyncio
    async def test_session_context(self):
        """测试会话上下文生成"""
        session = Session(
            session_id="test_session",
            character_id="test_character",
            user_id="test_user"
        )
        
        await session.add_message(MessageRole.USER, "你好")
        await session.add_message(MessageRole.ASSISTANT, "你好！")
        await session.add_message(MessageRole.USER, "今天天气如何？")
        
        context = session.get_conversation_context()
        assert "你好" in context
        assert "今天天气如何？" in context
        
        # 测试限制长度的上下文
        limited_context = session.get_conversation_context(max_length=10)
        assert len(limited_context) <= 10

class TestEnums:
    """测试枚举类型"""
    
    def test_character_type_enum(self):
        """测试角色类型枚举"""
        assert CharacterType.ANIME.value == "ANIME"
        assert CharacterType.GAME.value == "GAME"
        assert CharacterType.ORIGINAL.value == "ORIGINAL"
    
    def test_message_role_enum(self):
        """测试消息角色枚举"""
        assert MessageRole.USER.value == "user"
        assert MessageRole.ASSISTANT.value == "assistant"
        assert MessageRole.SYSTEM.value == "system"
    
    def test_llm_provider_enum(self):
        """测试LLM提供商枚举"""
        assert LLMProvider.GEMINI.value == "GEMINI"
        assert LLMProvider.DEEPSEEK.value == "DEEPSEEK" 