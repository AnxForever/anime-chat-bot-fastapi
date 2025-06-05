"""
测试API接口
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
import json

from anime_chat_bot.app.main import app
from app.models import Character, CharacterType, LLMProvider
from app.models.character import Personality, BehaviorRules, LLMConfig, ContextConfig

client = TestClient(app)

class TestRootEndpoints:
    """测试根路径端点"""
    
    def test_root(self):
        """测试根路径"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert data["status"] == "运行中 ✅"
    
    def test_health_check(self):
        """测试健康检查"""
        with patch('app.services.CharacterLoader.list_characters', new_callable=AsyncMock) as mock_list:
            mock_list.return_value = [{"id": "test", "name": "测试角色"}]
            response = client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "健康"
            assert "characters_loaded" in data
    
    def test_version(self):
        """测试版本信息"""
        response = client.get("/version")
        assert response.status_code == 200
        data = response.json()
        assert data["application"] == "动漫角色聊天机器人"
        assert data["version"] == "1.0.0"
        assert "features" in data

class TestCharactersAPI:
    """测试角色API"""
    
    @patch('app.services.CharacterLoader.list_characters', new_callable=AsyncMock)
    def test_list_characters(self, mock_list):
        """测试获取角色列表"""
        mock_list.return_value = [
            {
                "id": "rei_ayanami",
                "name": "绫波丽",
                "description": "EVA驾驶员",
                "character_type": "ANIME",
                "tags": ["EVA", "冷淡"]
            },
            {
                "id": "asuka_langley", 
                "name": "明日香·兰格雷",
                "description": "天才驾驶员",
                "character_type": "ANIME",
                "tags": ["EVA", "骄傲"]
            }
        ]
        
        response = client.get("/api/characters/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["id"] == "rei_ayanami"
        assert data[1]["id"] == "asuka_langley"
    
    @patch('app.services.CharacterLoader.get_character', new_callable=AsyncMock)
    def test_get_character(self, mock_get):
        """测试获取单个角色"""
        mock_character = Character(
            id="rei_ayanami",
            name="绫波丽",
            description="EVA驾驶员",
            character_type=CharacterType.ANIME,
            personality=Personality(),
            behavior_rules=BehaviorRules(),
            llm_config=LLMConfig(),
            context_config=ContextConfig(),
            system_prompt={"base_prompt": "测试"}
        )
        mock_get.return_value = mock_character
        
        response = client.get("/api/characters/rei_ayanami")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "rei_ayanami"
        assert data["name"] == "绫波丽"
        assert data["character_type"] == "ANIME"
    
    @patch('app.services.CharacterLoader.get_character', new_callable=AsyncMock)
    def test_get_character_not_found(self, mock_get):
        """测试获取不存在的角色"""
        mock_get.return_value = None
        
        response = client.get("/api/characters/nonexistent")
        assert response.status_code == 404
        data = response.json()
        assert "角色" in data["detail"]
        assert "不存在" in data["detail"]
    
    @patch('app.services.CharacterLoader.get_character', new_callable=AsyncMock)
    def test_get_character_preview(self, mock_get):
        """测试获取角色预览"""
        mock_character = Character(
            id="rei_ayanami",
            name="绫波丽",
            description="EVA驾驶员",
            character_type=CharacterType.ANIME,
            personality=Personality(
                traits=["冷静", "神秘"],
                interests=["阅读", "思考"]
            ),
            behavior_rules=BehaviorRules(),
            llm_config=LLMConfig(),
            context_config=ContextConfig(),
            system_prompt={
                "greeting": "...你好",
                "sample_responses": ["...是吗"]
            }
        )
        mock_get.return_value = mock_character
        
        response = client.get("/api/characters/rei_ayanami/preview")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "rei_ayanami"
        assert "personality_summary" in data
        assert "greeting" in data
    
    def test_get_character_types(self):
        """测试获取角色类型"""
        response = client.get("/api/characters/types/")
        assert response.status_code == 200
        data = response.json()
        assert "character_types" in data
        assert len(data["character_types"]) > 0
    
    @patch('app.services.CharacterLoader.list_characters', new_callable=AsyncMock)
    def test_get_popular_tags(self, mock_list):
        """测试获取热门标签"""
        mock_list.return_value = [
            {"tags": ["EVA", "冷淡", "神秘"]},
            {"tags": ["EVA", "骄傲", "天才"]},
            {"tags": ["音乐", "活泼", "甜美"]}
        ]
        
        response = client.get("/api/characters/tags/")
        assert response.status_code == 200
        data = response.json()
        assert "tags" in data
        assert "total_tags" in data

class TestChatAPI:
    """测试聊天API"""
    
    @patch('app.services.CharacterLoader.get_character', new_callable=AsyncMock)
    @patch('app.services.SessionManager.get_session', new_callable=AsyncMock)
    @patch('app.services.SessionManager.create_session', new_callable=AsyncMock)
    @patch('app.services.LLMConnector.generate_response', new_callable=AsyncMock)
    @patch('app.services.PromptBuilder.build_character_prompt', new_callable=AsyncMock)
    @patch('app.services.PromptBuilder.build_conversation_context', new_callable=AsyncMock)
    @patch('app.core.security.ContentFilter.is_content_safe', new_callable=AsyncMock)
    @patch('app.core.security.RateLimiter.check_rate_limit', new_callable=AsyncMock)
    def test_send_message(self, mock_rate_limit, mock_content_filter, 
                         mock_build_context, mock_build_prompt, mock_llm,
                         mock_create_session, mock_get_session, mock_get_character):
        """测试发送消息"""
        # 设置模拟返回值
        mock_rate_limit.return_value = True
        mock_content_filter.return_value = True
        
        mock_character = Character(
            id="rei_ayanami",
            name="绫波丽",
            description="EVA驾驶员",
            character_type=CharacterType.ANIME,
            personality=Personality(),
            behavior_rules=BehaviorRules(),
            llm_config=LLMConfig(provider=LLMProvider.GEMINI),
            context_config=ContextConfig(),
            system_prompt={"base_prompt": "测试"}
        )
        mock_get_character.return_value = mock_character
        
        mock_session = AsyncMock()
        mock_session.add_message = AsyncMock()
        mock_message = AsyncMock()
        mock_message.id = "msg_123"
        mock_message.timestamp = "2024-01-01T00:00:00Z"
        mock_session.add_message.return_value = mock_message
        mock_get_session.return_value = None
        mock_create_session.return_value = mock_session
        
        mock_build_prompt.return_value = "角色提示词"
        mock_build_context.return_value = "对话上下文"
        mock_llm.return_value = "...你好"
        
        # 发送请求
        request_data = {
            "character_id": "rei_ayanami",
            "user_message": "你好",
            "session_id": "test_session",
            "user_id": "test_user"
        }
        
        response = client.post("/api/chat/send", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert data["character_id"] == "rei_ayanami"
        assert data["assistant_message"] == "...你好"
        assert "session_id" in data
    
    @patch('app.core.security.ContentFilter.is_content_safe', new_callable=AsyncMock)
    def test_send_message_content_filter(self, mock_content_filter):
        """测试内容过滤"""
        mock_content_filter.return_value = False
        
        request_data = {
            "character_id": "rei_ayanami",
            "user_message": "不当内容",
            "user_id": "test_user"
        }
        
        response = client.post("/api/chat/send", json=request_data)
        assert response.status_code == 400
        assert "内容不当" in response.json()["detail"]
    
    @patch('app.services.SessionManager.get_session', new_callable=AsyncMock)
    def test_get_session_info(self, mock_get_session):
        """测试获取会话信息"""
        mock_session = AsyncMock()
        mock_session.session_id = "test_session"
        mock_session.character_id = "rei_ayanami"
        mock_session.user_id = "test_user"
        mock_session.created_at = "2024-01-01T00:00:00Z"
        mock_session.updated_at = "2024-01-01T00:00:00Z"
        mock_session.messages = []
        mock_session.status.value = "ACTIVE"
        mock_get_session.return_value = mock_session
        
        response = client.get("/api/chat/sessions/test_session")
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "test_session"
        assert data["character_id"] == "rei_ayanami"
        assert data["message_count"] == 0
    
    @patch('app.services.SessionManager.get_session', new_callable=AsyncMock)
    def test_get_session_not_found(self, mock_get_session):
        """测试获取不存在的会话"""
        mock_get_session.return_value = None
        
        response = client.get("/api/chat/sessions/nonexistent")
        assert response.status_code == 404
        assert "会话不存在" in response.json()["detail"]
    
    @patch('app.services.SessionManager.delete_session', new_callable=AsyncMock)
    def test_delete_session(self, mock_delete):
        """测试删除会话"""
        mock_delete.return_value = True
        
        response = client.delete("/api/chat/sessions/test_session")
        assert response.status_code == 200
        data = response.json()
        assert "已删除" in data["message"]
        assert data["session_id"] == "test_session"
    
    @patch('app.services.SessionManager.get_session', new_callable=AsyncMock)
    def test_get_session_messages(self, mock_get_session):
        """测试获取会话消息"""
        mock_session = AsyncMock()
        mock_messages = [
            AsyncMock(id="msg1", role=AsyncMock(value="user"), content="你好", 
                     timestamp="2024-01-01T00:00:00Z", status=AsyncMock(value="sent"), metadata={}),
            AsyncMock(id="msg2", role=AsyncMock(value="assistant"), content="...你好", 
                     timestamp="2024-01-01T00:01:00Z", status=AsyncMock(value="sent"), metadata={})
        ]
        mock_session.messages = mock_messages
        mock_get_session.return_value = mock_session
        
        response = client.get("/api/chat/sessions/test_session/messages?limit=10&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert "messages" in data
        assert data["total"] == 2
        assert data["limit"] == 10
        assert data["offset"] == 0 