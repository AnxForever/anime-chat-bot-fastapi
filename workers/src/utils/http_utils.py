"""
HTTP 工具类

提供 HTTP 请求/响应处理的工具函数，替代 FastAPI 的响应机制。
"""

import json
from datetime import datetime
from typing import Dict, Any, Optional, Union
from js import Response, Headers

def create_response(
    data: Any, 
    status_code: int = 200,
    headers: Optional[Dict[str, str]] = None
) -> Response:
    """
    创建标准 JSON 响应
    
    Args:
        data: 响应数据
        status_code: HTTP 状态码
        headers: 额外的响应头
        
    Returns:
        Response: Cloudflare Workers Response 对象
    """
    # 构建响应数据
    response_data = {
        "success": True,
        "data": data,
        "timestamp": datetime.now().isoformat()
    }
    
    # 创建响应头
    response_headers = Headers()
    response_headers.set("Content-Type", "application/json; charset=utf-8")
    
    # 添加额外的响应头
    if headers:
        for key, value in headers.items():
            response_headers.set(key, value)
    
    # 序列化数据
    json_body = json.dumps(response_data, ensure_ascii=False, indent=2)
    
    return Response(
        json_body,
        {
            "status": status_code,
            "headers": response_headers
        }
    )

def create_error_response(
    error_code: str,
    message: str,
    details: Optional[str] = None,
    status_code: int = 400,
    headers: Optional[Dict[str, str]] = None
) -> Response:
    """
    创建错误响应
    
    Args:
        error_code: 错误代码
        message: 错误消息
        details: 错误详情
        status_code: HTTP 状态码
        headers: 额外的响应头
        
    Returns:
        Response: 错误响应对象
    """
    # 构建错误响应数据
    error_data = {
        "success": False,
        "error": {
            "code": error_code,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
    }
    
    # 添加错误详情（仅在调试模式下）
    if details:
        error_data["error"]["details"] = details
    
    # 创建响应头
    response_headers = Headers()
    response_headers.set("Content-Type", "application/json; charset=utf-8")
    
    # 添加额外的响应头
    if headers:
        for key, value in headers.items():
            response_headers.set(key, value)
    
    # 序列化数据
    json_body = json.dumps(error_data, ensure_ascii=False, indent=2)
    
    return Response(
        json_body,
        {
            "status": status_code,
            "headers": response_headers
        }
    )

def create_stream_response(
    content: str,
    headers: Optional[Dict[str, str]] = None
) -> Response:
    """
    创建流式响应（用于聊天流式输出）
    
    Args:
        content: 流式内容
        headers: 额外的响应头
        
    Returns:
        Response: 流式响应对象
    """
    # 创建响应头
    response_headers = Headers()
    response_headers.set("Content-Type", "text/event-stream")
    response_headers.set("Cache-Control", "no-cache")
    response_headers.set("Connection", "keep-alive")
    
    # 添加额外的响应头
    if headers:
        for key, value in headers.items():
            response_headers.set(key, value)
    
    return Response(
        content,
        {
            "status": 200,
            "headers": response_headers
        }
    )

def handle_cors() -> Response:
    """
    处理 CORS 预检请求
    
    Returns:
        Response: CORS 预检响应
    """
    headers = Headers()
    headers.set("Access-Control-Allow-Origin", "*")
    headers.set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
    headers.set("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With")
    headers.set("Access-Control-Max-Age", "86400")
    
    return Response("", {
        "status": 204,
        "headers": headers
    })

def parse_query_params(query_string: str) -> Dict[str, str]:
    """
    解析查询参数
    
    Args:
        query_string: 查询字符串
        
    Returns:
        Dict[str, str]: 解析后的参数字典
    """
    params = {}
    
    if not query_string:
        return params
    
    for param in query_string.split('&'):
        if '=' in param:
            key, value = param.split('=', 1)
            # URL 解码
            key = key.replace('%20', ' ').replace('+', ' ')
            value = value.replace('%20', ' ').replace('+', ' ')
            params[key] = value
        else:
            params[param] = ''
    
    return params

def extract_bearer_token(authorization_header: str) -> Optional[str]:
    """
    从 Authorization 头中提取 Bearer token
    
    Args:
        authorization_header: Authorization 头的值
        
    Returns:
        Optional[str]: 提取的 token，如果没有则返回 None
    """
    if not authorization_header:
        return None
    
    if authorization_header.startswith('Bearer '):
        return authorization_header[7:]  # 移除 'Bearer ' 前缀
    
    return None

def format_sse_message(data: Dict[str, Any], event_type: str = "message") -> str:
    """
    格式化 Server-Sent Events (SSE) 消息
    
    Args:
        data: 要发送的数据
        event_type: 事件类型
        
    Returns:
        str: 格式化的 SSE 消息
    """
    json_data = json.dumps(data, ensure_ascii=False)
    return f"event: {event_type}\ndata: {json_data}\n\n"

def validate_json_request(request_data: Dict[str, Any], required_fields: list) -> Optional[str]:
    """
    验证 JSON 请求数据
    
    Args:
        request_data: 请求数据
        required_fields: 必需的字段列表
        
    Returns:
        Optional[str]: 验证错误消息，如果验证通过则返回 None
    """
    json_data = request_data.get('json', {})
    
    if not json_data:
        return "请求体必须包含有效的 JSON 数据"
    
    missing_fields = []
    for field in required_fields:
        if field not in json_data:
            missing_fields.append(field)
    
    if missing_fields:
        return f"缺少必需的字段: {', '.join(missing_fields)}"
    
    return None

def get_client_ip(request_data: Dict[str, Any]) -> str:
    """
    获取客户端 IP 地址
    
    Args:
        request_data: 请求数据
        
    Returns:
        str: 客户端 IP 地址
    """
    headers = request_data.get('headers', {})
    
    # 尝试从不同的头中获取真实 IP
    ip_headers = [
        'cf-connecting-ip',  # Cloudflare
        'x-forwarded-for',
        'x-real-ip',
        'x-client-ip'
    ]
    
    for header in ip_headers:
        ip = headers.get(header)
        if ip:
            # 如果是逗号分隔的多个 IP，取第一个
            return ip.split(',')[0].strip()
    
    return 'unknown'

def sanitize_input(text: str, max_length: int = 1000) -> str:
    """
    清理和验证用户输入
    
    Args:
        text: 输入文本
        max_length: 最大长度限制
        
    Returns:
        str: 清理后的文本
    """
    if not text:
        return ""
    
    # 移除前后空白
    text = text.strip()
    
    # 长度限制
    if len(text) > max_length:
        text = text[:max_length]
    
    # 移除可能的恶意字符（基础清理）
    dangerous_chars = ['<', '>', '"', "'", '&']
    for char in dangerous_chars:
        text = text.replace(char, '')
    
    return text 