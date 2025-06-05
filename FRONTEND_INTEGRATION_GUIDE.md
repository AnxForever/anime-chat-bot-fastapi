# 前端集成指南

## 🚀 快速开始

### 1. 启动后端服务

```bash
# 安装依赖
pip install -r requirements.txt

# 启动服务器
python run.py
```

服务将在 `http://localhost:8000` 启动

### 2. API 基础信息

- **基础URL**: `http://localhost:8000/api/v1`
- **文档地址**: `http://localhost:8000/docs`
- **认证方式**: JWT Bearer Token（可选）

## 📋 核心接口示例

### 获取角色列表

```javascript
// GET /api/v1/characters
const getCharacters = async () => {
  const response = await fetch('http://localhost:8000/api/v1/characters');
  const data = await response.json();
  return data.data; // 角色数组
};
```

**响应格式:**
```json
{
  "success": true,
  "data": [
    {
      "id": "rei_ayanami",
      "name": "绫波零", 
      "description": "沉默寡言的EVA驾驶员",
      "avatar_url": "/static/avatars/rei.png",
      "personality_traits": ["冷淡", "神秘", "忠诚"]
    }
  ]
}
```

### 发送聊天消息

```javascript
// POST /api/v1/chat
const sendMessage = async (characterId, message, sessionId = null) => {
  const response = await fetch('http://localhost:8000/api/v1/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      character_id: characterId,
      message: message,
      session_id: sessionId || `session_${Date.now()}`
    })
  });
  
  const data = await response.json();
  return data.data;
};
```

**响应格式:**
```json
{
  "success": true,
  "data": {
    "message": "是吗...天气确实不错。",
    "character_id": "rei_ayanami",
    "timestamp": "2024-01-01T10:01:00Z",
    "metadata": {
      "emotion_detected": "neutral",
      "response_time_ms": 800,
      "confidence_score": 0.85
    }
  }
}
```

### 获取对话历史

```javascript
// GET /api/v1/conversations/{session_id}/messages
const getHistory = async (sessionId, page = 1, limit = 50) => {
  const url = `http://localhost:8000/api/v1/conversations/${sessionId}/messages?page=${page}&limit=${limit}`;
  const response = await fetch(url);
  const data = await response.json();
  return data.data;
};
```

## 🎨 React 组件示例

### 角色选择组件

```jsx
import React, { useState, useEffect } from 'react';

const CharacterSelector = ({ onCharacterSelect }) => {
  const [characters, setCharacters] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchCharacters = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/v1/characters');
        const data = await response.json();
        setCharacters(data.data);
      } catch (error) {
        console.error('获取角色失败:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchCharacters();
  }, []);

  if (loading) return <div>加载中...</div>;

  return (
    <div className="character-selector">
      <h3>选择角色</h3>
      <div className="character-grid">
        {characters.map(character => (
          <div 
            key={character.id}
            className="character-card"
            onClick={() => onCharacterSelect(character)}
          >
            <img src={character.avatar_url} alt={character.name} />
            <h4>{character.name}</h4>
            <p>{character.description}</p>
            <div className="traits">
              {character.personality_traits.map(trait => (
                <span key={trait} className="trait">{trait}</span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
```

### 聊天组件

```jsx
import React, { useState } from 'react';

const ChatInterface = ({ character }) => {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId] = useState(`session_${Date.now()}`);

  const sendMessage = async () => {
    if (!inputValue.trim() || loading) return;

    const userMessage = {
      role: 'user',
      content: inputValue,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setLoading(true);
    setInputValue('');

    try {
      const response = await fetch('http://localhost:8000/api/v1/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          character_id: character.id,
          message: inputValue,
          session_id: sessionId
        })
      });

      const data = await response.json();
      
      if (data.success) {
        const characterMessage = {
          role: 'assistant',
          content: data.data.message,
          timestamp: data.data.timestamp,
          metadata: data.data.metadata
        };
        setMessages(prev => [...prev, characterMessage]);
      }
    } catch (error) {
      console.error('发送消息失败:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chat-interface">
      <div className="chat-header">
        <img src={character.avatar_url} alt={character.name} />
        <h3>{character.name}</h3>
      </div>
      
      <div className="messages">
        {messages.map((message, index) => (
          <div key={index} className={`message ${message.role}`}>
            <div className="content">{message.content}</div>
            <div className="timestamp">
              {new Date(message.timestamp).toLocaleTimeString()}
            </div>
          </div>
        ))}
        {loading && <div className="message assistant loading">正在输入...</div>}
      </div>
      
      <div className="input-area">
        <input
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
          placeholder="输入消息..."
          disabled={loading}
        />
        <button onClick={sendMessage} disabled={loading || !inputValue.trim()}>
          发送
        </button>
      </div>
    </div>
  );
};
```

## 🎯 TypeScript 类型定义

```typescript
// types.ts
export interface Character {
  id: string;
  name: string;
  description: string;
  avatar_url: string;
  source: string;
  personality_traits: string[];
  available: boolean;
}

export interface ChatMessage {
  message: string;
  character_id: string;
  timestamp: string;
  metadata?: {
    emotion_detected?: string;
    response_time_ms?: number;
    confidence_score?: number;
    character_state?: {
      mood: string;
      energy_level: number;
      relationship_level: string;
    };
  };
}

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: {
    code: string;
    message: string;
    details?: any;
  };
  timestamp: string;
}

export interface ChatRequest {
  character_id: string;
  message: string;
  user_id?: string;
  session_id?: string;
}
```

## 🛠️ API 客户端封装

```typescript
// api-client.ts
class ChatBotAPI {
  private baseUrl: string;

  constructor(baseUrl = 'http://localhost:8000/api/v1') {
    this.baseUrl = baseUrl;
  }

  async getCharacters(): Promise<Character[]> {
    const response = await fetch(`${this.baseUrl}/characters`);
    const data: ApiResponse<Character[]> = await response.json();
    
    if (!data.success) {
      throw new Error(data.error?.message || '获取角色失败');
    }
    
    return data.data || [];
  }

  async sendMessage(request: ChatRequest): Promise<ChatMessage> {
    const response = await fetch(`${this.baseUrl}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request)
    });

    const data: ApiResponse<ChatMessage> = await response.json();
    
    if (!data.success) {
      throw new Error(data.error?.message || '发送消息失败');
    }
    
    return data.data!;
  }

  async getConversationHistory(
    sessionId: string, 
    page = 1, 
    limit = 50
  ): Promise<any> {
    const url = `${this.baseUrl}/conversations/${sessionId}/messages?page=${page}&limit=${limit}`;
    const response = await fetch(url);
    const data = await response.json();
    
    if (!data.success) {
      throw new Error(data.error?.message || '获取历史失败');
    }
    
    return data.data;
  }
}

// 使用示例
const api = new ChatBotAPI();

// 获取角色
const characters = await api.getCharacters();

// 发送消息
const response = await api.sendMessage({
  character_id: 'rei_ayanami',
  message: '你好！',
  session_id: 'my-session'
});
```

## 🎨 CSS 样式建议

```css
/* 角色卡片样式 */
.character-card {
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 16px;
  text-align: center;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.character-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}

.character-card img {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  object-fit: cover;
}

.traits {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  justify-content: center;
  margin-top: 8px;
}

.trait {
  background: #f0f0f0;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
}

/* 聊天界面样式 */
.chat-interface {
  display: flex;
  flex-direction: column;
  height: 600px;
  border: 1px solid #ddd;
  border-radius: 8px;
}

.chat-header {
  display: flex;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid #eee;
  background: #f8f9fa;
}

.chat-header img {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  margin-right: 12px;
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.message {
  margin-bottom: 12px;
  max-width: 70%;
}

.message.user {
  margin-left: auto;
  text-align: right;
}

.message.user .content {
  background: #007bff;
  color: white;
  padding: 8px 12px;
  border-radius: 18px 18px 4px 18px;
}

.message.assistant .content {
  background: #f1f3f4;
  padding: 8px 12px;
  border-radius: 18px 18px 18px 4px;
}

.message.loading .content {
  background: #f1f3f4;
  padding: 8px 12px;
  border-radius: 18px;
  font-style: italic;
  opacity: 0.7;
}

.timestamp {
  font-size: 11px;
  color: #666;
  margin-top: 4px;
}

.input-area {
  display: flex;
  padding: 16px;
  border-top: 1px solid #eee;
  background: #f8f9fa;
}

.input-area input {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 20px;
  margin-right: 8px;
  outline: none;
}

.input-area input:focus {
  border-color: #007bff;
}

.input-area button {
  padding: 8px 16px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 20px;
  cursor: pointer;
}

.input-area button:disabled {
  background: #ccc;
  cursor: not-allowed;
}
```

## ⚠️ 错误处理

```javascript
// 错误处理示例
const handleApiError = (error) => {
  if (error.code === 'CHAR_001') {
    alert('角色不存在，请重新选择');
  } else if (error.code === 'CHAT_003') {
    alert('AI服务暂时不可用，请稍后重试');
  } else {
    alert('发生未知错误：' + error.message);
  }
};

// 在API调用中使用
try {
  const response = await api.sendMessage(request);
  // 处理成功响应
} catch (error) {
  handleApiError(error);
}
```

## 🔧 开发建议

1. **会话管理**: 为每个用户创建唯一的 session_id
2. **状态管理**: 使用 Redux/Zustand 管理聊天状态  
3. **错误重试**: 实现自动重试机制
4. **缓存策略**: 缓存角色列表和历史消息
5. **响应式设计**: 适配移动端界面
6. **实时通信**: 后续可升级为 WebSocket

## 📱 移动端适配

```css
@media (max-width: 768px) {
  .character-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .chat-interface {
    height: calc(100vh - 100px);
  }
  
  .message {
    max-width: 85%;
  }
}
```

这份指南提供了完整的前端集成方案，帅哥你可以根据实际需求进行调整！ 