"""
LLM 连接器 - Workers 版本

适配 Cloudflare Workers 环境的 LLM API 调用服务。
使用 Workers 原生 fetch API 替代 aiohttp。
"""

import json
import os
import asyncio
from typing import Dict, Any, Optional
from js import fetch, Headers

from ..utils.logger import get_logger

logger = get_logger(__name__)

class LLMConnector:
    """LLM API 连接器"""
    
    def __init__(self):
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
        
        logger.info("LLM连接器初始化完成")
    
    async def generate_response(
        self,
        prompt: str,
        provider: str = "GEMINI",
        model: str = "gemini-pro",
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> Dict[str, Any]:
        """
        生成AI回复
        
        Args:
            prompt: 提示词
            provider: LLM提供商
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大token数
            
        Returns:
            Dict[str, Any]: 生成的回复
        """
        if provider.upper() == "GEMINI":
            return await self._call_gemini_api(prompt, model, temperature, max_tokens)
        elif provider.upper() == "DEEPSEEK":
            return await self._call_deepseek_api(prompt, model, temperature, max_tokens)
        else:
            raise ValueError(f"不支持的LLM提供商: {provider}")
    
    async def _call_gemini_api(
        self,
        prompt: str,
        model: str,
        temperature: float,
        max_tokens: int
    ) -> Dict[str, Any]:
        """调用 Gemini API"""
        if not self.gemini_api_key:
            raise ValueError("Gemini API密钥未配置")
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.gemini_api_key}"
        
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
                "topP": 0.8,
                "topK": 40
            }
        }
        
        headers = Headers()
        headers.set("Content-Type", "application/json")
        
        try:
            response = await fetch(url, {
                "method": "POST",
                "headers": headers,
                "body": json.dumps(payload)
            })
            
            if not response.ok:
                error_text = await response.text()
                raise Exception(f"Gemini API调用失败: {response.status} - {error_text}")
            
            result = await response.json()
            
            # 解析Gemini响应
            if "candidates" in result and len(result["candidates"]) > 0:
                content = result["candidates"][0]["content"]["parts"][0]["text"]
                
                return {
                    "content": content.strip(),
                    "provider": "GEMINI",
                    "model": model,
                    "tokens_used": len(content) * 1.2  # 粗略估算
                }
            else:
                raise Exception("Gemini API返回了空响应")
                
        except Exception as e:
            logger.error(f"Gemini API调用出错: {str(e)}")
            raise
    
    async def _call_deepseek_api(
        self,
        prompt: str,
        model: str,
        temperature: float,
        max_tokens: int
    ) -> Dict[str, Any]:
        """调用 SiliconFlow API (DeepSeek 模型)"""
        if not self.deepseek_api_key:
            raise ValueError("SiliconFlow API密钥未配置")
        
        # SiliconFlow API 端点
        url = "https://api.siliconflow.cn/v1/chat/completions"
        
        # 确保模型名称格式正确
        if not model.startswith("deepseek"):
            model = "deepseek-chat"  # SiliconFlow 上的 DeepSeek 模型名称
        
        payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": 0.9,
            "stream": False
        }
        
        headers = Headers()
        headers.set("Content-Type", "application/json")
        headers.set("Authorization", f"Bearer {self.deepseek_api_key}")
        
        try:
            response = await fetch(url, {
                "method": "POST",
                "headers": headers,
                "body": json.dumps(payload)
            })
            
            if not response.ok:
                error_text = await response.text()
                raise Exception(f"SiliconFlow API调用失败: {response.status} - {error_text}")
            
            result = await response.json()
            
            # 解析SiliconFlow响应（格式与OpenAI兼容）
            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0]["message"]["content"]
                tokens_used = result.get("usage", {}).get("total_tokens", 0)
                
                return {
                    "content": content.strip(),
                    "provider": "SILICONFLOW",
                    "model": model,
                    "tokens_used": tokens_used
                }
            else:
                raise Exception("SiliconFlow API返回了空响应")
                
        except Exception as e:
            logger.error(f"SiliconFlow API调用出错: {str(e)}")
            raise 