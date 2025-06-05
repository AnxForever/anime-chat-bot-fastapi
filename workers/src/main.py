"""
动漫角色聊天机器人 - Cloudflare Workers 主入口

基于 Cloudflare Workers 的动漫角色扮演聊天机器人后端服务
"""

import json
import asyncio
from js import Response, Request, Headers
from typing import Dict, Any, Optional

# 导入路由处理器
from .router import Router
from .utils.http_utils import create_response, handle_cors, create_error_response
from .utils.logger import get_logger

# 初始化日志
logger = get_logger(__name__)

# 创建全局路由器实例
router = Router()

async def fetch(request, env, ctx) -> Response:
    """
    Cloudflare Workers 主要处理函数
    
    Args:
        request: HTTP 请求对象
        env: 环境变量和绑定
        ctx: 执行上下文
        
    Returns:
        Response: HTTP 响应对象
    """
    try:
        # 解析请求
        url = request.url
        method = request.method
        
        # 记录请求日志
        logger.info(f"收到请求: {method} {url}")
        
        # 处理 CORS 预检请求
        if method == "OPTIONS":
            return handle_cors()
        
        # 设置环境变量到全局上下文
        _setup_environment(env)
        
        # 路由分发
        response = await router.handle_request(request, env, ctx)
        
        # 添加 CORS 头
        response = _add_cors_headers(response)
        
        logger.info(f"请求处理完成: {response.status}")
        return response
        
    except Exception as e:
        logger.error(f"请求处理出错: {str(e)}")
        
        # 返回统一的错误响应
        error_response = create_error_response(
            error_code="SYS_001",
            message="系统内部错误",
            details=str(e),
            status_code=500
        )
        
        return _add_cors_headers(error_response)

def _setup_environment(env) -> None:
    """
    设置全局环境变量
    
    Args:
        env: Cloudflare Workers 环境对象
    """
    import os
    
    # 设置 API 密钥
    if hasattr(env, 'GEMINI_API_KEY'):
        os.environ['GEMINI_API_KEY'] = env.GEMINI_API_KEY
    if hasattr(env, 'DEEPSEEK_API_KEY'):
        os.environ['DEEPSEEK_API_KEY'] = env.DEEPSEEK_API_KEY
    if hasattr(env, 'JWT_SECRET_KEY'):
        os.environ['JWT_SECRET_KEY'] = env.JWT_SECRET_KEY
    
    # 设置应用配置
    os.environ['APP_ENV'] = getattr(env, 'APP_ENV', 'production')
    os.environ['APP_NAME'] = getattr(env, 'APP_NAME', '动漫角色聊天机器人')
    os.environ['API_VERSION'] = getattr(env, 'API_VERSION', 'v1')
    os.environ['CORS_ORIGINS'] = getattr(env, 'CORS_ORIGINS', '*')

def _add_cors_headers(response: Response) -> Response:
    """
    为响应添加 CORS 头
    
    Args:
        response: 原始响应对象
        
    Returns:
        Response: 添加了 CORS 头的响应对象
    """
    # 创建新的响应头
    headers = Headers(response.headers)
    
    # 添加 CORS 头
    headers.set("Access-Control-Allow-Origin", "*")
    headers.set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
    headers.set("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With")
    headers.set("Access-Control-Max-Age", "86400")
    
    # 创建新的响应对象
    return Response(
        response.body,
        {
            "status": response.status,
            "statusText": response.statusText,
            "headers": headers
        }
    )

# 健康检查端点（内置）
async def health_check() -> Dict[str, Any]:
    """健康检查"""
    return {
        "status": "healthy",
        "service": "动漫角色聊天机器人",
        "version": "1.0.0-workers",
        "timestamp": str(asyncio.get_event_loop().time()),
        "environment": "cloudflare-workers"
    }

# 根路径端点（内置）
async def root_info() -> Dict[str, Any]:
    """根路径信息"""
    return {
        "message": "动漫角色聊天机器人 API - Cloudflare Workers 版本",
        "version": "1.0.0",
        "docs": "https://github.com/your-repo/anime-chat-bot",
        "endpoints": {
            "chat": "/api/v1/chat",
            "characters": "/api/v1/characters",
            "sessions": "/api/v1/sessions",
            "health": "/health"
        },
        "status": "running",
        "platform": "cloudflare-workers"
    }

# 导出 fetch 函数供 Workers 运行时调用
__all__ = ["fetch"] 