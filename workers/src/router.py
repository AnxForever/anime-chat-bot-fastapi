"""
路由映射器

将 HTTP 请求路由到对应的处理函数，替代 FastAPI 的路由系统。
"""

import re
import json
from urllib.parse import urlparse, parse_qs
from typing import Dict, Any, Callable, Optional, List, Tuple
from js import Response, Request

from .handlers.chat_handler import ChatHandler
from .handlers.auth_handler import AuthHandler  
from .handlers.memory_handler import MemoryHandler
from .handlers.session_handler import SessionHandler
from .utils.http_utils import create_response, create_error_response
from .utils.logger import get_logger

logger = get_logger(__name__)


class Route:
    """路由定义类"""
    
    def __init__(self, method: str, pattern: str, handler: Callable, auth_required: bool = False):
        self.method = method.upper()
        self.pattern = pattern
        self.handler = handler
        self.auth_required = auth_required
        self.regex = self._compile_pattern(pattern)
    
    def _compile_pattern(self, pattern: str) -> re.Pattern:
        """将路径模式编译为正则表达式"""
        # 替换路径参数 {param} 为正则表达式
        pattern = pattern.replace("{", "(?P<").replace("}", ">[^/]+)")
        # 添加行开始和结束锚点
        pattern = f"^{pattern}/?$"
        return re.compile(pattern)
    
    def match(self, method: str, path: str) -> Optional[Dict[str, str]]:
        """检查请求是否匹配此路由"""
        if method.upper() != self.method:
            return None
        
        match = self.regex.match(path)
        if match:
            return match.groupdict()
        return None


class Router:
    """路由器"""
    
    def __init__(self):
        self.routes: List[Route] = []
        self.handlers = {
            'chat': ChatHandler(),
            'auth': AuthHandler(),
            'memory': MemoryHandler(),
            'session': SessionHandler()
        }
        
        # 注册所有路由
        self._register_routes()
    
    def _register_routes(self):
        """注册所有 API 路由"""
        
        # ====== 基础路由 ======
        self.add_route("GET", "/", self._handle_root)
        self.add_route("GET", "/health", self._handle_health)
        
        # ====== 聊天相关路由 ======
        self.add_route("POST", "/api/v1/chat", self.handlers['chat'].send_message)
        self.add_route("POST", "/api/v1/chat/stream", self.handlers['chat'].send_message_stream)
        self.add_route("GET", "/api/v1/characters", self.handlers['chat'].get_characters)
        self.add_route("GET", "/api/v1/characters/{character_id}", self.handlers['chat'].get_character)
        
        # ====== 会话管理路由 ======
        self.add_route("POST", "/api/v1/sessions", self.handlers['session'].create_session)
        self.add_route("GET", "/api/v1/sessions", self.handlers['session'].get_sessions)
        self.add_route("GET", "/api/v1/sessions/{session_id}", self.handlers['session'].get_session)
        self.add_route("DELETE", "/api/v1/sessions/{session_id}", self.handlers['session'].delete_session)
        
        # ====== 记忆管理路由 ======
        self.add_route("GET", "/api/v1/sessions/{session_id}/memories", self.handlers['memory'].get_memories)
        self.add_route("POST", "/api/v1/sessions/{session_id}/memories", self.handlers['memory'].add_memory)
        self.add_route("DELETE", "/api/v1/sessions/{session_id}/memories/{memory_id}", self.handlers['memory'].delete_memory)
        
        # ====== 认证路由 ======
        self.add_route("POST", "/api/v1/auth/token", self.handlers['auth'].create_token)
        self.add_route("POST", "/api/v1/auth/refresh", self.handlers['auth'].refresh_token, auth_required=True)
        self.add_route("GET", "/api/v1/auth/me", self.handlers['auth'].get_current_user, auth_required=True)
        
        # ====== 统计分析路由 ======
        self.add_route("GET", "/api/v1/stats/overview", self.handlers['session'].get_stats)
        self.add_route("GET", "/api/v1/stats/sessions", self.handlers['session'].get_session_stats)
        
        logger.info(f"已注册 {len(self.routes)} 个路由")
    
    def add_route(self, method: str, pattern: str, handler: Callable, auth_required: bool = False):
        """添加路由"""
        route = Route(method, pattern, handler, auth_required)
        self.routes.append(route)
    
    async def handle_request(self, request: Request, env, ctx) -> Response:
        """处理 HTTP 请求"""
        try:
            # 解析请求 URL
            url = urlparse(request.url)
            path = url.path
            method = request.method
            
            logger.info(f"路由匹配: {method} {path}")
            
            # 查找匹配的路由
            for route in self.routes:
                path_params = route.match(method, path)
                if path_params is not None:
                    logger.info(f"匹配到路由: {route.pattern}")
                    
                    # 解析请求数据
                    request_data = await self._parse_request_data(request, url, path_params)
                    
                    # 检查认证
                    if route.auth_required:
                        auth_result = await self._check_authentication(request_data)
                        if not auth_result['valid']:
                            return create_error_response(
                                error_code="AUTH_001",
                                message="认证失败",
                                details=auth_result['error'],
                                status_code=401
                            )
                        request_data['user'] = auth_result['user']
                    
                    # 调用处理函数
                    try:
                        result = await route.handler(request_data, env, ctx)
                        return create_response(result)
                    except Exception as handler_error:
                        logger.error(f"处理器执行出错: {str(handler_error)}")
                        return create_error_response(
                            error_code="HANDLER_001", 
                            message="请求处理失败",
                            details=str(handler_error),
                            status_code=500
                        )
            
            # 没有匹配的路由
            logger.warning(f"未找到匹配的路由: {method} {path}")
            return create_error_response(
                error_code="ROUTE_001",
                message="未找到对应的 API 端点",
                details=f"路径 {path} 不存在",
                status_code=404
            )
            
        except Exception as e:
            logger.error(f"路由处理出错: {str(e)}")
            return create_error_response(
                error_code="ROUTER_001",
                message="路由处理失败", 
                details=str(e),
                status_code=500
            )
    
    async def _parse_request_data(self, request: Request, url, path_params: Dict[str, str]) -> Dict[str, Any]:
        """解析请求数据"""
        data = {
            'method': request.method,
            'url': request.url,
            'path': url.path,
            'path_params': path_params,
            'query_params': parse_qs(url.query),
            'headers': dict(request.headers)
        }
        
        # 解析请求体
        if request.method in ['POST', 'PUT', 'PATCH']:
            try:
                content_type = request.headers.get('content-type', '')
                if 'application/json' in content_type:
                    body_text = await request.text()
                    if body_text:
                        data['json'] = json.loads(body_text)
                else:
                    data['text'] = await request.text()
            except Exception as e:
                logger.warning(f"请求体解析失败: {str(e)}")
                data['json'] = {}
        
        return data
    
    async def _check_authentication(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """检查用户认证"""
        try:
            # 从请求头获取 Authorization token
            auth_header = request_data.get('headers', {}).get('authorization', '')
            if not auth_header or not auth_header.startswith('Bearer '):
                return {'valid': False, 'error': '缺少认证令牌'}
            
            token = auth_header[7:]  # 移除 'Bearer ' 前缀
            
            # 验证 token（这里可以调用 AuthHandler 的验证方法）
            auth_handler = self.handlers['auth']
            user_data = await auth_handler.verify_token(token)
            
            return {'valid': True, 'user': user_data}
            
        except Exception as e:
            return {'valid': False, 'error': str(e)}
    
    # ====== 内置处理函数 ======
    
    async def _handle_root(self, request_data: Dict[str, Any], env, ctx) -> Dict[str, Any]:
        """根路径处理"""
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
    
    async def _handle_health(self, request_data: Dict[str, Any], env, ctx) -> Dict[str, Any]:
        """健康检查处理"""
        return {
            "status": "healthy",
            "service": "动漫角色聊天机器人",
            "version": "1.0.0-workers",
            "timestamp": str(request_data.get('timestamp', 'unknown')),
            "environment": "cloudflare-workers",
            "services": {
                "api": "running",
                "llm_services": "available",
                "memory": "active"
            }
        } 