"""
客户端使用示例
演示如何使用动漫聊天机器人API
"""
import asyncio
import aiohttp
import json
from typing import Optional

class AnimeChatbotClient:
    """动漫聊天机器人客户端"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session_id: Optional[str] = None
    
    async def get_characters(self) -> list:
        """获取可用角色列表"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/api/characters/") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"获取角色列表失败: {response.status}")
    
    async def get_character_preview(self, character_id: str) -> dict:
        """获取角色预览信息"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/api/characters/{character_id}/preview") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"获取角色预览失败: {response.status}")
    
    async def send_message(self, character_id: str, message: str, user_id: str = "demo_user") -> dict:
        """发送消息给角色"""
        payload = {
            "character_id": character_id,
            "user_message": message,
            "user_id": user_id
        }
        
        if self.session_id:
            payload["session_id"] = self.session_id
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/chat/send",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    # 保存会话ID以便后续对话
                    self.session_id = result.get("session_id")
                    return result
                else:
                    error_detail = await response.text()
                    raise Exception(f"发送消息失败: {response.status} - {error_detail}")
    
    async def stream_message(self, character_id: str, message: str, user_id: str = "demo_user"):
        """流式发送消息"""
        payload = {
            "character_id": character_id,
            "user_message": message,
            "user_id": user_id
        }
        
        if self.session_id:
            payload["session_id"] = self.session_id
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/chat/stream",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    async for line in response.content:
                        if line:
                            line_str = line.decode('utf-8').strip()
                            if line_str.startswith('data: '):
                                data_str = line_str[6:]  # 移除 'data: ' 前缀
                                try:
                                    data = json.loads(data_str)
                                    yield data
                                    # 保存会话ID
                                    if data.get("session_id"):
                                        self.session_id = data["session_id"]
                                except json.JSONDecodeError:
                                    continue
                else:
                    error_detail = await response.text()
                    raise Exception(f"流式消息失败: {response.status} - {error_detail}")
    
    async def get_session_info(self) -> dict:
        """获取当前会话信息"""
        if not self.session_id:
            raise Exception("没有活跃的会话")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/api/chat/sessions/{self.session_id}") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"获取会话信息失败: {response.status}")
    
    async def get_conversation_history(self, limit: int = 10) -> dict:
        """获取对话历史"""
        if not self.session_id:
            raise Exception("没有活跃的会话")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/api/chat/sessions/{self.session_id}/messages?limit={limit}"
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"获取对话历史失败: {response.status}")


async def demo_conversation():
    """演示对话流程"""
    client = AnimeChatbotClient()
    
    print("🎭 动漫聊天机器人演示")
    print("=" * 50)
    
    # 获取可用角色
    print("📋 获取可用角色...")
    characters = await client.get_characters()
    print(f"✅ 找到 {len(characters)} 个角色:")
    for char in characters[:3]:  # 只显示前3个
        print(f"  - {char.get('name')} ({char.get('id')})")
    
    # 选择绫波丽进行对话
    character_id = "rei_ayanami"
    print(f"\n🎯 选择角色: {character_id}")
    
    # 获取角色预览
    preview = await client.get_character_preview(character_id)
    print(f"📝 角色描述: {preview.get('description')}")
    print(f"💬 问候语: {preview.get('greeting')}")
    
    print("\n" + "=" * 50)
    print("开始对话 (输入 'quit' 退出)")
    print("=" * 50)
    
    # 模拟对话
    conversation = [
        "你好，绫波丽",
        "你今天过得怎么样？",
        "你对EVA有什么看法？"
    ]
    
    for message in conversation:
        print(f"\n👤 用户: {message}")
        
        # 发送消息并获取回复
        response = await client.send_message(character_id, message)
        print(f"🤖 {preview.get('name')}: {response.get('assistant_message')}")
        
        # 短暂停顿，模拟真实对话
        await asyncio.sleep(1)
    
    # 显示会话信息
    print("\n" + "=" * 50)
    print("📊 会话统计")
    session_info = await client.get_session_info()
    print(f"会话ID: {session_info.get('session_id')}")
    print(f"消息数量: {session_info.get('message_count')}")
    print(f"角色: {session_info.get('character_id')}")
    
    # 获取对话历史
    history = await client.get_conversation_history()
    print(f"\n📜 对话历史 (最近{len(history.get('messages', []))}条):")
    for msg in history.get('messages', []):
        role = "👤" if msg['role'] == 'user' else "🤖"
        print(f"  {role} {msg['content']}")


async def demo_streaming():
    """演示流式对话"""
    client = AnimeChatbotClient()
    
    print("\n🌊 流式对话演示")
    print("=" * 50)
    
    character_id = "miku_hatsune"
    message = "你好，未来！能为我唱首歌吗？"
    
    print(f"👤 用户: {message}")
    print("🤖 初音未来: ", end="", flush=True)
    
    full_response = ""
    async for chunk_data in client.stream_message(character_id, message):
        if chunk_data.get("type") == "chunk":
            content = chunk_data.get("content", "")
            print(content, end="", flush=True)
            full_response += content
        elif chunk_data.get("type") == "end":
            print(f"\n\n✅ 完整回复接收完成，共 {len(full_response)} 个字符")


async def main():
    """主函数"""
    try:
        print("🚀 正在启动演示...")
        
        # 检查服务是否可用
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get("http://localhost:8000/health") as response:
                    if response.status != 200:
                        print("❌ 服务不可用，请确保后端服务正在运行")
                        print("💡 启动命令: uv run python main.py")
                        return
            except aiohttp.ClientConnectorError:
                print("❌ 无法连接到后端服务")
                print("💡 请确保后端服务在 http://localhost:8000 运行")
                return
        
        # 运行演示
        await demo_conversation()
        await demo_streaming()
        
        print("\n🎉 演示完成！")
        
    except Exception as e:
        print(f"❌ 演示过程中出现错误: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main()) 