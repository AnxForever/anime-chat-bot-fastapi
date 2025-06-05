"""
角色加载服务

负责从JSON文件加载、缓存和管理动漫角色配置。
"""

import os
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path
import aiofiles

from app.core import settings, CharacterNotFoundError, CharacterLoadError
from app.models import Character, CharacterSummary


class CharacterLoader:
    """
    角色加载器
    
    提供角色配置的加载、缓存和管理功能。
    """
    
    def __init__(self):
        self.characters_dir = Path(settings.characters_dir)
        self.cache_enabled = settings.enable_character_cache
        self.cache_ttl = settings.character_cache_ttl
        
        # 角色缓存
        self._character_cache: Dict[str, Character] = {}
        self._cache_timestamps: Dict[str, datetime] = {}
        self._character_list_cache: Optional[List[CharacterSummary]] = None
        self._list_cache_timestamp: Optional[datetime] = None
        
        # 确保角色目录存在
        self.characters_dir.mkdir(parents=True, exist_ok=True)
    
    def _is_cache_valid(self, character_id: str) -> bool:
        """
        检查角色缓存是否有效
        
        Args:
            character_id: 角色ID
            
        Returns:
            bool: 缓存是否有效
        """
        if not self.cache_enabled:
            return False
        
        if character_id not in self._cache_timestamps:
            return False
        
        cache_time = self._cache_timestamps[character_id]
        expiry_time = cache_time + timedelta(seconds=self.cache_ttl)
        
        return datetime.now() < expiry_time
    
    def _is_list_cache_valid(self) -> bool:
        """
        检查角色列表缓存是否有效
        
        Returns:
            bool: 缓存是否有效
        """
        if not self.cache_enabled or not self._list_cache_timestamp:
            return False
        
        expiry_time = self._list_cache_timestamp + timedelta(seconds=self.cache_ttl)
        return datetime.now() < expiry_time
    
    def _get_character_file_path(self, character_id: str) -> Path:
        """
        获取角色配置文件路径
        
        Args:
            character_id: 角色ID
            
        Returns:
            Path: 文件路径
        """
        return self.characters_dir / f"{character_id}.json"
    
    async def _load_character_from_file(self, character_id: str) -> Character:
        """
        从文件加载角色配置
        
        Args:
            character_id: 角色ID
            
        Returns:
            Character: 角色对象
            
        Raises:
            CharacterNotFoundError: 角色文件不存在
            CharacterLoadError: 角色加载失败
        """
        file_path = self._get_character_file_path(character_id)
        
        # 检查文件是否存在
        if not file_path.exists():
            raise CharacterNotFoundError(character_id)
        
        try:
            # 异步读取文件
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
            
            # 解析JSON
            character_data = json.loads(content)
            
            # 验证和创建Character对象
            character = Character(**character_data)
            
            # 保存原始配置数据用于增强的提示词构建
            character._config_data = character_data
            
            # 设置时间戳（如果没有的话）
            if not character.created_at:
                stat = file_path.stat()
                character.created_at = datetime.fromtimestamp(stat.st_ctime).isoformat()
            
            if not character.updated_at:
                stat = file_path.stat()
                character.updated_at = datetime.fromtimestamp(stat.st_mtime).isoformat()
            
            return character
            
        except json.JSONDecodeError as e:
            raise CharacterLoadError(character_id, f"JSON解析错误: {e}")
        except Exception as e:
            raise CharacterLoadError(character_id, f"文件读取错误: {e}")
    
    async def get_character(self, character_id: str) -> Character:
        """
        获取角色配置
        
        Args:
            character_id: 角色ID
            
        Returns:
            Character: 角色对象
            
        Raises:
            CharacterNotFoundError: 角色不存在
            CharacterLoadError: 角色加载失败
        """
        # 检查缓存
        if self._is_cache_valid(character_id):
            return self._character_cache[character_id]
        
        # 从文件加载
        character = await self._load_character_from_file(character_id)
        
        # 更新缓存
        if self.cache_enabled:
            self._character_cache[character_id] = character
            self._cache_timestamps[character_id] = datetime.now()
        
        return character
    
    async def get_character_list(self) -> List[CharacterSummary]:
        """
        获取所有角色摘要列表
        
        Returns:
            List[CharacterSummary]: 角色摘要列表
        """
        # 检查列表缓存
        if self._is_list_cache_valid() and self._character_list_cache:
            return self._character_list_cache
        
        character_summaries = []
        
        # 遍历角色目录
        if self.characters_dir.exists():
            for file_path in self.characters_dir.glob("*.json"):
                character_id = file_path.stem
                
                try:
                    # 尝试从缓存获取
                    if self._is_cache_valid(character_id):
                        character = self._character_cache[character_id]
                    else:
                        character = await self._load_character_from_file(character_id)
                        
                        # 更新缓存
                        if self.cache_enabled:
                            self._character_cache[character_id] = character
                            self._cache_timestamps[character_id] = datetime.now()
                    
                    # 创建摘要
                    summary = CharacterSummary(
                        id=character.id,
                        name=character.name,
                        type=character.type,
                        description=character.description,
                        avatar_url=character.avatar_url,
                        tags=character.tags
                    )
                    character_summaries.append(summary)
                    
                except Exception as e:
                    # 记录错误但不中断整个列表加载
                    print(f"加载角色 {character_id} 时出错: {e}")
                    continue
        
        # 按名称排序
        character_summaries.sort(key=lambda x: x.name)
        
        # 更新列表缓存
        if self.cache_enabled:
            self._character_list_cache = character_summaries
            self._list_cache_timestamp = datetime.now()
        
        return character_summaries
    
    async def character_exists(self, character_id: str) -> bool:
        """
        检查角色是否存在
        
        Args:
            character_id: 角色ID
            
        Returns:
            bool: 角色是否存在
        """
        # 先检查缓存
        if character_id in self._character_cache and self._is_cache_valid(character_id):
            return True
        
        # 检查文件是否存在
        file_path = self._get_character_file_path(character_id)
        return file_path.exists()
    
    async def save_character(self, character: Character) -> None:
        """
        保存角色配置到文件
        
        Args:
            character: 角色对象
            
        Raises:
            CharacterLoadError: 保存失败
        """
        file_path = self._get_character_file_path(character.id)
        
        try:
            # 更新时间戳
            character.updated_at = datetime.now().isoformat()
            
            # 转换为字典
            character_data = character.dict()
            
            # 异步写入文件
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(character_data, ensure_ascii=False, indent=2))
            
            # 更新缓存
            if self.cache_enabled:
                self._character_cache[character.id] = character
                self._cache_timestamps[character.id] = datetime.now()
                
                # 清除列表缓存，因为可能有新角色
                self._character_list_cache = None
                self._list_cache_timestamp = None
                
        except Exception as e:
            raise CharacterLoadError(character.id, f"保存失败: {e}")
    
    async def delete_character(self, character_id: str) -> bool:
        """
        删除角色配置
        
        Args:
            character_id: 角色ID
            
        Returns:
            bool: 是否成功删除
        """
        file_path = self._get_character_file_path(character_id)
        
        try:
            if file_path.exists():
                file_path.unlink()
            
            # 清除缓存
            if character_id in self._character_cache:
                del self._character_cache[character_id]
            if character_id in self._cache_timestamps:
                del self._cache_timestamps[character_id]
            
            # 清除列表缓存
            self._character_list_cache = None
            self._list_cache_timestamp = None
            
            return True
            
        except Exception as e:
            print(f"删除角色 {character_id} 时出错: {e}")
            return False
    
    def clear_cache(self, character_id: Optional[str] = None) -> None:
        """
        清除缓存
        
        Args:
            character_id: 指定角色ID，None则清除所有缓存
        """
        if character_id:
            # 清除指定角色缓存
            if character_id in self._character_cache:
                del self._character_cache[character_id]
            if character_id in self._cache_timestamps:
                del self._cache_timestamps[character_id]
        else:
            # 清除所有缓存
            self._character_cache.clear()
            self._cache_timestamps.clear()
            self._character_list_cache = None
            self._list_cache_timestamp = None
    
    def get_cache_info(self) -> Dict:
        """
        获取缓存信息
        
        Returns:
            Dict: 缓存统计信息
        """
        return {
            "cache_enabled": self.cache_enabled,
            "cache_ttl": self.cache_ttl,
            "cached_characters": len(self._character_cache),
            "character_ids": list(self._character_cache.keys()),
            "list_cached": self._character_list_cache is not None,
            "last_list_update": self._list_cache_timestamp.isoformat() if self._list_cache_timestamp else None
        }


# 全局实例
character_loader = CharacterLoader() 