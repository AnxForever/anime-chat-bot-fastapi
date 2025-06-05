"""
聊天处理器

处理聊天相关的API请求，包括发送消息、流式对话、角色管理等。
"""

import time
from typing import Dict, Any
from ..utils.http_utils import validate_json_request, sanitize_input
from ..utils.logger import get_logger
from ..services.llm_connector import LLMConnector
from ..data.characters import get_character_config, get_character_list

logger = get_logger(__name__)

class ChatHandler:
    """聊天API处理器"""
    
    def __init__(self):
        self.llm_connector = LLMConnector()
        logger.info("聊天处理器初始化完成")
    
    async def send_message(self, request_data: Dict[str, Any], env, ctx) -> Dict[str, Any]:
        """发送消息给角色"""
        start_time = time.time()
        
        try:
            # 验证请求数据
            validation_error = validate_json_request(
                request_data, 
                ["message", "character_id"]
            )
            if validation_error:
                raise ValueError(validation_error)
            
            json_data = request_data["json"]
            
            # 提取参数
            user_message = sanitize_input(json_data["message"], max_length=1000)
            character_id = json_data["character_id"]
            
            logger.info(f"处理聊天请求: character={character_id}")
            
            # 验证角色是否存在
            try:
                character_config = get_character_config(character_id)
            except KeyError:
                raise ValueError(f"角色 {character_id} 不存在")
            
            # 构建简化的提示词
            system_prompt = character_config["system_prompt"]["base_prompt"]
            full_prompt = f"{system_prompt}\n\n用户: {user_message}\n{character_config['name']}:"
            
            # 调用LLM生成回复
            llm_response = await self.llm_connector.generate_response(
                prompt=full_prompt,
                provider=character_config["llm_config"]["provider"],
                model=character_config["llm_config"]["model_name"],
                temperature=character_config["llm_config"]["temperature"],
                max_tokens=character_config["llm_config"]["max_tokens"]
            )
            
            # 构建响应
            response_data = {
                "message": llm_response["content"],
                "character_id": character_id,
                "character_name": character_config["name"],
                "processing_time": round(time.time() - start_time, 3),
                "tokens_used": llm_response.get("tokens_used", 0)
            }
            
            logger.info(f"聊天请求处理完成")
            return response_data
            
        except Exception as e:
            logger.error(f"聊天请求处理失败: {str(e)}")
            raise
    
    async def send_message_stream(self, request_data: Dict[str, Any], env, ctx) -> Dict[str, Any]:
        """流式发送消息"""
        # 目前使用普通响应
        response = await self.send_message(request_data, env, ctx)
        response["stream"] = True
        return response
    
    async def get_characters(self, request_data: Dict[str, Any], env, ctx) -> Dict[str, Any]:
        """获取所有可用角色列表"""
        try:
            characters = get_character_list()
            
            logger.info(f"返回 {len(characters)} 个角色")
            
            return {
                "characters": characters,
                "total": len(characters)
            }
            
        except Exception as e:
            logger.error(f"获取角色列表失败: {str(e)}")
            raise
    
    async def get_character(self, request_data: Dict[str, Any], env, ctx) -> Dict[str, Any]:
        """获取特定角色的详细信息"""
        try:
            character_id = request_data["path_params"]["character_id"]
            
            # 获取角色配置
            try:
                character_config = get_character_config(character_id)
            except KeyError:
                raise ValueError(f"角色 {character_id} 不存在")
            
            # 移除敏感信息
            public_config = {
                "id": character_config["id"],
                "name": character_config["name"],
                "description": character_config["description"],
                "character_type": character_config["character_type"],
                "tags": character_config["tags"],
                "basic_info": character_config["basic_info"],
                "personality": character_config["personality"],
                "is_active": character_config["is_active"]
            }
            
            logger.info(f"返回角色信息: {character_id}")
            
            return {
                "character": public_config
            }
            
        except Exception as e:
            logger.error(f"获取角色信息失败: {str(e)}")
            raise 