"""
用户认证路由 - 支持用户注册、登录、会话管理
"""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import jwt
import hashlib
import secrets
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["认证"])
security = HTTPBearer()

# JWT配置
JWT_SECRET_KEY = "your-super-secret-jwt-key-here"
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

# 模拟用户数据库
users_db: Dict[str, Dict[str, Any]] = {}
sessions_db: Dict[str, Dict[str, Any]] = {}

class UserRegister(BaseModel):
    username: str
    email: Optional[EmailStr] = None
    password: str
    display_name: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: Dict[str, Any]

class UserProfile(BaseModel):
    id: str
    username: str
    email: Optional[str]
    display_name: Optional[str]
    created_at: str
    last_login: Optional[str]
    settings: Dict[str, Any]

def hash_password(password: str) -> str:
    """密码哈希"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    """验证密码"""
    return hash_password(password) == hashed

def create_access_token(user_id: str, username: str) -> str:
    """创建JWT访问令牌"""
    expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    payload = {
        "user_id": user_id,
        "username": username,
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

def verify_token(token: str) -> Dict[str, Any]:
    """验证JWT令牌"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="令牌已过期"
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的令牌"
        )

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """获取当前用户"""
    token = credentials.credentials
    payload = verify_token(token)
    user_id = payload.get("user_id")
    
    if user_id not in users_db:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在"
        )
    
    return users_db[user_id]

@router.post("/register", response_model=TokenResponse)
async def register_user(user_data: UserRegister):
    """用户注册"""
    # 检查用户名是否已存在
    for user in users_db.values():
        if user["username"] == user_data.username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已存在"
            )
    
    # 创建新用户
    user_id = f"user_{secrets.token_hex(8)}"
    hashed_password = hash_password(user_data.password)
    
    new_user = {
        "id": user_id,
        "username": user_data.username,
        "email": user_data.email,
        "display_name": user_data.display_name or user_data.username,
        "password_hash": hashed_password,
        "created_at": datetime.now().isoformat(),
        "last_login": None,
        "settings": {
            "theme": "default",
            "language": "zh-CN",
            "notifications": True,
            "auto_save": True
        },
        "statistics": {
            "total_conversations": 0,
            "total_messages": 0,
            "favorite_characters": [],
            "joined_days": 0
        }
    }
    
    users_db[user_id] = new_user
    
    # 生成访问令牌
    access_token = create_access_token(user_id, user_data.username)
    
    # 移除密码哈希后返回用户信息
    user_response = {k: v for k, v in new_user.items() if k != "password_hash"}
    
    logger.info(f"新用户注册: {user_data.username}")
    
    return TokenResponse(
        access_token=access_token,
        expires_in=ACCESS_TOKEN_EXPIRE_HOURS * 3600,
        user=user_response
    )

@router.post("/login", response_model=TokenResponse)
async def login_user(login_data: UserLogin):
    """用户登录"""
    # 查找用户
    user = None
    for u in users_db.values():
        if u["username"] == login_data.username:
            user = u
            break
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )
    
    # 验证密码
    if not verify_password(login_data.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )
    
    # 更新最后登录时间
    user["last_login"] = datetime.now().isoformat()
    
    # 生成访问令牌
    access_token = create_access_token(user["id"], user["username"])
    
    # 移除密码哈希后返回用户信息
    user_response = {k: v for k, v in user.items() if k != "password_hash"}
    
    logger.info(f"用户登录: {login_data.username}")
    
    return TokenResponse(
        access_token=access_token,
        expires_in=ACCESS_TOKEN_EXPIRE_HOURS * 3600,
        user=user_response
    )

@router.get("/me", response_model=UserProfile)
async def get_user_profile(current_user: Dict[str, Any] = Depends(get_current_user)):
    """获取当前用户资料"""
    user_response = {k: v for k, v in current_user.items() if k != "password_hash"}
    return UserProfile(**user_response)

@router.put("/me")
async def update_user_profile(
    profile_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """更新用户资料"""
    user_id = current_user["id"]
    
    # 可更新的字段
    updatable_fields = ["display_name", "email", "settings"]
    
    for field in updatable_fields:
        if field in profile_data:
            users_db[user_id][field] = profile_data[field]
    
    users_db[user_id]["updated_at"] = datetime.now().isoformat()
    
    # 返回更新后的用户信息
    user_response = {k: v for k, v in users_db[user_id].items() if k != "password_hash"}
    
    return {"success": True, "user": user_response}

@router.post("/logout")
async def logout_user(current_user: Dict[str, Any] = Depends(get_current_user)):
    """用户登出"""
    # 在实际应用中，这里可以将令牌加入黑名单
    logger.info(f"用户登出: {current_user['username']}")
    
    return {"success": True, "message": "登出成功"}

@router.get("/sessions")
async def get_user_sessions(current_user: Dict[str, Any] = Depends(get_current_user)):
    """获取用户会话列表"""
    user_id = current_user["id"]
    
    # 模拟用户会话数据
    sessions = [
        {
            "session_id": f"session_{user_id}_rei",
            "character_id": "rei_ayanami",
            "character_name": "绫波零",
            "created_at": "2024-01-01T10:00:00Z",
            "last_message_at": "2024-01-01T12:00:00Z",
            "message_count": 25,
            "relationship_level": "friend"
        },
        {
            "session_id": f"session_{user_id}_asuka",
            "character_id": "asuka_langley",
            "character_name": "明日香·兰格雷",
            "created_at": "2024-01-01T11:00:00Z",
            "last_message_at": "2024-01-01T11:30:00Z",
            "message_count": 15,
            "relationship_level": "acquaintance"
        }
    ]
    
    return {"success": True, "sessions": sessions}

@router.delete("/sessions/{session_id}")
async def delete_user_session(
    session_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """删除用户会话"""
    # 这里应该删除会话相关的所有数据
    logger.info(f"删除会话: {session_id} for user: {current_user['username']}")
    
    return {"success": True, "message": "会话已删除"}

@router.get("/verify")
async def verify_token_endpoint(current_user: Dict[str, Any] = Depends(get_current_user)):
    """验证令牌有效性"""
    return {
        "valid": True,
        "user_id": current_user["id"],
        "username": current_user["username"],
        "expires_at": "检查令牌过期时间"
    } 