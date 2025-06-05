"""
LLM连接服务

提供统一的LLM API调用接口，支持Gemini和DeepSeek。
"""

import asyncio
import time
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, AsyncGenerator
import httpx
import google.generativeai as genai
from openai import AsyncOpenAI

from app.core import settings, LLMProviderError, LLMAPIError, LLMTimeoutError
from app.models import LLMProvider


class AbstractLLMProvider(ABC):
    """
    LLM提供商抽象基类
    
    定义所有LLM提供商必须实现的接口。
    """
    
    def __init__(self, provider_name: str):
        self.provider_name = provider_name
        self.max_retries = settings.max_retries
        self.timeout = settings.request_timeout_seconds
    
    @abstractmethod
    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.8,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Dict:
        """
        生成AI回复
        
        Args:
            messages: 消息历史列表
            temperature: 温度参数
            max_tokens: 最大token数
            **kwargs: 其他参数
            
        Returns:
            Dict: 包含回复内容和元数据的字典
        """
        pass
    
    @abstractmethod
    async def generate_stream_response(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.8,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        流式生成AI回复
        
        Args:
            messages: 消息历史列表
            temperature: 温度参数
            max_tokens: 最大token数
            **kwargs: 其他参数
            
        Yields:
            str: 回复内容片段
        """
        pass
    
    async def _retry_request(self, func, *args, **kwargs):
        """
        重试机制
        
        Args:
            func: 要重试的函数
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            函数执行结果
        """
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < self.max_retries:
                    # 指数退避
                    wait_time = (2 ** attempt) * 0.5
                    await asyncio.sleep(wait_time)
                    continue
                break
        
        # 所有重试都失败，抛出最后一个异常
        if last_exception:
            raise LLMAPIError(
                self.provider_name,
                f"重试{self.max_retries}次后仍然失败: {str(last_exception)}"
            )


class GeminiProvider(AbstractLLMProvider):
    """
    Gemini API提供商实现
    """
    
    def __init__(self):
        super().__init__("gemini")
        
        if not settings.gemini_api_key:
            raise LLMProviderError("gemini", "未提供Gemini API密钥")
        
        # 配置Gemini
        genai.configure(api_key=settings.gemini_api_key)
        self.model_name = settings.gemini_model
        
        # 创建模型实例
        self.model = genai.GenerativeModel(self.model_name)
    
    def _convert_messages_to_gemini_format(self, messages: List[Dict[str, str]]) -> List[Dict]:
        """
        将标准消息格式转换为Gemini格式
        
        Args:
            messages: 标准消息列表
            
        Returns:
            List[Dict]: Gemini格式的消息列表
        """
        gemini_messages = []
        
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            
            # Gemini的角色映射
            if role == "user":
                gemini_role = "user"
            elif role == "assistant":
                gemini_role = "model"
            else:  # system messages
                # Gemini没有system角色，将其合并到用户消息中
                gemini_role = "user"
                content = f"[系统消息]: {content}"
            
            gemini_messages.append({
                "role": gemini_role,
                "parts": [{"text": content}]
            })
        
        return gemini_messages
    
    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.8,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Dict:
        """
        生成AI回复
        """
        start_time = time.time()
        
        try:
            # 转换消息格式
            gemini_messages = self._convert_messages_to_gemini_format(messages)
            
            # 配置生成参数
            generation_config = genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens or settings.default_max_tokens,
            )
            
            # 准备对话历史（除了最后一条消息）
            if len(gemini_messages) > 1:
                history = gemini_messages[:-1]
                user_message = gemini_messages[-1]["parts"][0]["text"]
            else:
                history = []
                user_message = gemini_messages[0]["parts"][0]["text"]
            
            # 创建聊天会话
            chat = self.model.start_chat(history=history)
            
            # 发送消息并获取回复
            response = await asyncio.to_thread(
                chat.send_message,
                user_message,
                generation_config=generation_config
            )
            
            response_time = time.time() - start_time
            
            return {
                "content": response.text,
                "tokens_used": None,  # Gemini API可能不提供token计数
                "model": self.model_name,
                "provider": self.provider_name,
                "response_time": response_time
            }
            
        except Exception as e:
            raise LLMAPIError(self.provider_name, str(e))
    
    async def generate_stream_response(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.8,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        流式生成AI回复
        """
        try:
            # 转换消息格式
            gemini_messages = self._convert_messages_to_gemini_format(messages)
            
            # 配置生成参数
            generation_config = genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens or settings.default_max_tokens,
            )
            
            # 准备对话历史
            if len(gemini_messages) > 1:
                history = gemini_messages[:-1]
                user_message = gemini_messages[-1]["parts"][0]["text"]
            else:
                history = []
                user_message = gemini_messages[0]["parts"][0]["text"]
            
            # 创建聊天会话
            chat = self.model.start_chat(history=history)
            
            # 流式生成回复
            response_stream = await asyncio.to_thread(
                chat.send_message,
                user_message,
                generation_config=generation_config,
                stream=True
            )
            
            for chunk in response_stream:
                if chunk.text:
                    yield chunk.text
                    
        except Exception as e:
            raise LLMAPIError(self.provider_name, str(e))


class DeepSeekProvider(AbstractLLMProvider):
    """
    DeepSeek API提供商实现
    """
    
    def __init__(self):
        super().__init__("deepseek")
        
        if not settings.deepseek_api_key:
            raise LLMProviderError("deepseek", "未提供DeepSeek API密钥")
        
        # 创建OpenAI兼容的客户端
        self.client = AsyncOpenAI(
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url
        )
        self.model_name = settings.deepseek_model
    
    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.8,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Dict:
        """
        生成AI回复
        """
        start_time = time.time()
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens or settings.default_max_tokens,
                timeout=self.timeout
            )
            
            response_time = time.time() - start_time
            
            return {
                "content": response.choices[0].message.content,
                "tokens_used": response.usage.total_tokens if response.usage else None,
                "model": self.model_name,
                "provider": self.provider_name,
                "response_time": response_time
            }
            
        except Exception as e:
            raise LLMAPIError(self.provider_name, str(e))
    
    async def generate_stream_response(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.8,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        流式生成AI回复
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens or settings.default_max_tokens,
                stream=True,
                timeout=self.timeout
            )
            
            async for chunk in response:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            raise LLMAPIError(self.provider_name, str(e))


class LLMConnector:
    """
    LLM连接器主类
    
    提供统一的LLM调用接口，支持多个提供商。
    """
    
    def __init__(self):
        self.providers: Dict[str, AbstractLLMProvider] = {}
        self.default_provider = settings.default_llm_provider
        
        # 初始化提供商
        self._initialize_providers()
    
    def _initialize_providers(self):
        """初始化所有可用的LLM提供商"""
        # 初始化Gemini
        if settings.gemini_api_key:
            try:
                self.providers[LLMProvider.GEMINI] = GeminiProvider()
            except Exception as e:
                print(f"Gemini初始化失败: {e}")
        
        # 初始化DeepSeek
        if settings.deepseek_api_key:
            try:
                self.providers[LLMProvider.DEEPSEEK] = DeepSeekProvider()
            except Exception as e:
                print(f"DeepSeek初始化失败: {e}")
        
        if not self.providers:
            raise LLMProviderError("none", "没有可用的LLM提供商")
        
        # 确保默认提供商可用
        if self.default_provider not in self.providers:
            self.default_provider = list(self.providers.keys())[0]
            print(f"默认LLM提供商不可用，切换到: {self.default_provider}")
    
    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        provider: Optional[str] = None,
        temperature: float = 0.8,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Dict:
        """
        生成AI回复
        
        Args:
            messages: 消息历史列表
            provider: 指定的提供商，None则使用默认
            temperature: 温度参数
            max_tokens: 最大token数
            **kwargs: 其他参数
            
        Returns:
            Dict: 包含回复内容和元数据的字典
        """
        provider = provider or self.default_provider
        
        if provider not in self.providers:
            # 尝试回退到可用的提供商
            available_providers = list(self.providers.keys())
            if available_providers:
                provider = available_providers[0]
                print(f"指定的提供商不可用，回退到: {provider}")
            else:
                raise LLMProviderError(provider, "没有可用的LLM提供商")
        
        try:
            return await self.providers[provider]._retry_request(
                self.providers[provider].generate_response,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
        except Exception as e:
            # 如果主提供商失败，尝试其他提供商
            for fallback_provider in self.providers:
                if fallback_provider != provider:
                    try:
                        print(f"主提供商{provider}失败，尝试{fallback_provider}")
                        return await self.providers[fallback_provider].generate_response(
                            messages=messages,
                            temperature=temperature,
                            max_tokens=max_tokens,
                            **kwargs
                        )
                    except Exception:
                        continue
            
            # 所有提供商都失败
            raise e
    
    async def generate_stream_response(
        self,
        messages: List[Dict[str, str]],
        provider: Optional[str] = None,
        temperature: float = 0.8,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        流式生成AI回复
        
        Args:
            messages: 消息历史列表
            provider: 指定的提供商，None则使用默认
            temperature: 温度参数
            max_tokens: 最大token数
            **kwargs: 其他参数
            
        Yields:
            str: 回复内容片段
        """
        provider = provider or self.default_provider
        
        if provider not in self.providers:
            available_providers = list(self.providers.keys())
            if available_providers:
                provider = available_providers[0]
            else:
                raise LLMProviderError(provider, "没有可用的LLM提供商")
        
        async for chunk in self.providers[provider].generate_stream_response(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        ):
            yield chunk
    
    def get_available_providers(self) -> List[str]:
        """获取可用的提供商列表"""
        return list(self.providers.keys())
    
    def get_provider_info(self, provider: str) -> Dict:
        """获取提供商信息"""
        if provider not in self.providers:
            raise LLMProviderError(provider, "提供商不存在")
        
        provider_obj = self.providers[provider]
        return {
            "name": provider,
            "model": getattr(provider_obj, 'model_name', 'unknown'),
            "available": True
        } 