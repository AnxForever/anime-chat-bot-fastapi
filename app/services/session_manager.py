"""
会话管理服务

提供会话的创建、管理、缓存和自动清理功能。
"""

import uuid
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import OrderedDict

from app.core import (
    settings, 
    SessionNotFoundError, 
    SessionExpiredError, 
    SessionLimitExceededError
)
from app.models import Session, SessionSummary, SessionCreate, Message


class SessionManager:
    """
    会话管理器
    
    基于内存的会话管理，支持LRU淘汰和自动过期清理。
    """
    
    def __init__(self):
        self.max_sessions = settings.max_sessions_in_memory
        self.session_timeout = settings.session_timeout_hours
        
        # 使用OrderedDict实现LRU
        self._sessions: OrderedDict[str, Session] = OrderedDict()
        
        # 后台清理任务
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False
        
        # 启动后台清理
        self._start_cleanup_task()
    
    def _start_cleanup_task(self):
        """启动后台清理任务"""
        if not self._cleanup_task or self._cleanup_task.done():
            self._running = True
            self._cleanup_task = asyncio.create_task(self._cleanup_expired_sessions())
    
    async def _cleanup_expired_sessions(self):
        """后台清理过期会话"""
        while self._running:
            try:
                await self._clean_expired_sessions()
                # 每5分钟清理一次
                await asyncio.sleep(300)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"会话清理出错: {e}")
                await asyncio.sleep(60)  # 出错后等待1分钟再试
    
    async def _clean_expired_sessions(self):
        """清理过期的会话"""
        expired_sessions = []
        current_time = datetime.now()
        
        for session_id, session in self._sessions.items():
            # 检查是否过期
            if session.auto_archive_after:
                hours_since_active = (current_time - session.last_active_at).total_seconds() / 3600
                if hours_since_active > session.auto_archive_after:
                    expired_sessions.append(session_id)
        
        # 移除过期会话
        for session_id in expired_sessions:
            if session_id in self._sessions:
                self._sessions[session_id].status = "archived"
                del self._sessions[session_id]
                print(f"清理过期会话: {session_id}")
    
    def _ensure_capacity(self):
        """确保会话数量不超过限制"""
        while len(self._sessions) >= self.max_sessions:
            # 移除最旧的会话（LRU）
            oldest_session_id, oldest_session = self._sessions.popitem(last=False)
            oldest_session.status = "archived"
            print(f"会话容量已满，归档最旧会话: {oldest_session_id}")
    
    def _touch_session(self, session_id: str):
        """更新会话的访问时间（LRU）"""
        if session_id in self._sessions:
            # 移到末尾（最新）
            session = self._sessions.pop(session_id)
            self._sessions[session_id] = session
    
    def _generate_session_id(self) -> str:
        """生成唯一的会话ID"""
        return f"session_{uuid.uuid4().hex[:12]}"
    
    async def create_session(
        self, 
        character_id: str,
        session_create: Optional[SessionCreate] = None
    ) -> Session:
        """
        创建新会话
        
        Args:
            character_id: 角色ID
            session_create: 会话创建配置
            
        Returns:
            Session: 新创建的会话
            
        Raises:
            SessionLimitExceededError: 会话数量超出限制
        """
        # 检查会话数量限制
        if len(self._sessions) >= self.max_sessions:
            self._ensure_capacity()
        
        # 生成会话ID
        session_id = self._generate_session_id()
        while session_id in self._sessions:
            session_id = self._generate_session_id()
        
        # 创建会话对象
        session_data = {
            "id": session_id,
            "character_id": character_id,
        }
        
        if session_create:
            session_data.update({
                "max_messages": session_create.max_messages,
                "auto_archive_after": session_create.auto_archive_after,
            })
        
        session = Session(**session_data)
        
        # 添加到会话字典
        self._sessions[session_id] = session
        
        return session
    
    async def get_session(self, session_id: str) -> Session:
        """
        获取会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            Session: 会话对象
            
        Raises:
            SessionNotFoundError: 会话不存在
            SessionExpiredError: 会话已过期
        """
        if session_id not in self._sessions:
            raise SessionNotFoundError(session_id)
        
        session = self._sessions[session_id]
        
        # 检查是否过期
        if session.is_expired():
            # 移除过期会话
            del self._sessions[session_id]
            session.status = "archived"
            raise SessionExpiredError(session_id)
        
        # 更新LRU顺序
        self._touch_session(session_id)
        
        return session
    
    async def update_session(self, session: Session) -> Session:
        """
        更新会话
        
        Args:
            session: 会话对象
            
        Returns:
            Session: 更新后的会话
            
        Raises:
            SessionNotFoundError: 会话不存在
        """
        if session.id not in self._sessions:
            raise SessionNotFoundError(session.id)
        
        # 更新会话
        self._sessions[session.id] = session
        
        # 更新LRU顺序
        self._touch_session(session.id)
        
        return session
    
    async def add_message_to_session(self, session_id: str, message: Message) -> Session:
        """
        向会话添加消息
        
        Args:
            session_id: 会话ID
            message: 消息对象
            
        Returns:
            Session: 更新后的会话
            
        Raises:
            SessionNotFoundError: 会话不存在
            SessionExpiredError: 会话已过期
        """
        session = await self.get_session(session_id)
        
        # 添加消息
        session.add_message(message)
        
        # 更新会话
        return await self.update_session(session)
    
    async def delete_session(self, session_id: str) -> bool:
        """
        删除会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            bool: 是否成功删除
        """
        if session_id in self._sessions:
            session = self._sessions[session_id]
            session.status = "archived"
            del self._sessions[session_id]
            return True
        return False
    
    async def get_user_sessions(self, character_id: Optional[str] = None) -> List[SessionSummary]:
        """
        获取用户会话列表
        
        Args:
            character_id: 可选的角色ID过滤
            
        Returns:
            List[SessionSummary]: 会话摘要列表
        """
        summaries = []
        
        for session in self._sessions.values():
            # 角色过滤
            if character_id and session.character_id != character_id:
                continue
            
            # 获取最后一条消息预览
            last_message_preview = None
            if session.messages:
                last_msg = session.messages[-1]
                preview_length = 50
                last_message_preview = (
                    last_msg.content[:preview_length] + "..." 
                    if len(last_msg.content) > preview_length 
                    else last_msg.content
                )
            
            summary = SessionSummary(
                id=session.id,
                character_id=session.character_id,
                character_name=None,  # 可以从character_loader获取
                status=session.status,
                created_at=session.created_at,
                last_active_at=session.last_active_at,
                total_messages=session.total_messages,
                last_message_preview=last_message_preview
            )
            summaries.append(summary)
        
        # 按最后活跃时间排序（最新的在前）
        summaries.sort(key=lambda x: x.last_active_at, reverse=True)
        
        return summaries
    
    async def archive_session(self, session_id: str) -> bool:
        """
        归档会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            bool: 是否成功归档
        """
        if session_id in self._sessions:
            session = self._sessions[session_id]
            session.status = "archived"
            del self._sessions[session_id]
            return True
        return False
    
    async def activate_session(self, session_id: str) -> Session:
        """
        激活会话（更新最后活跃时间）
        
        Args:
            session_id: 会话ID
            
        Returns:
            Session: 激活后的会话
            
        Raises:
            SessionNotFoundError: 会话不存在
        """
        session = await self.get_session(session_id)
        session.last_active_at = datetime.now()
        return await self.update_session(session)
    
    def get_session_stats(self) -> Dict:
        """
        获取会话统计信息
        
        Returns:
            Dict: 统计信息
        """
        active_sessions = len(self._sessions)
        total_messages = sum(session.total_messages for session in self._sessions.values())
        
        # 按角色统计
        character_stats = {}
        for session in self._sessions.values():
            char_id = session.character_id
            if char_id not in character_stats:
                character_stats[char_id] = {"sessions": 0, "messages": 0}
            character_stats[char_id]["sessions"] += 1
            character_stats[char_id]["messages"] += session.total_messages
        
        return {
            "active_sessions": active_sessions,
            "max_sessions": self.max_sessions,
            "total_messages": total_messages,
            "character_stats": character_stats,
            "memory_usage_percent": (active_sessions / self.max_sessions) * 100
        }
    
    async def cleanup_all_sessions(self):
        """清理所有会话（用于关闭应用时）"""
        self._running = False
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        # 归档所有会话
        for session in self._sessions.values():
            session.status = "archived"
        
        self._sessions.clear()


# 全局实例
session_manager = SessionManager() 