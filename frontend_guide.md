# 前端集成指南

## 🚀 快速开始

### 启动后端服务
```bash
# 安装依赖
pip install -r requirements.txt

# 启动服务器  
python run.py
```

服务地址: `http://localhost:8000`
API文档: `http://localhost:8000/docs`

## 📋 核心接口

### 1. 获取角色列表
```javascript
// GET /api/v1/characters
const getCharacters = async () => {
  const response = await fetch('http://localhost:8000/api/v1/characters');
  const data = await response.json();
  return data.data;
};
```

### 2. 发送聊天消息
```javascript  
// POST /api/v1/chat
const sendMessage = async (characterId, message) => {
  const response = await fetch('http://localhost:8000/api/v1/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      character_id: characterId,
      message: message,
      session_id: `session_${Date.now()}`
    })
  });
  return response.json();
};
```

### 3. 获取对话历史
```javascript
// GET /api/v1/conversations/{session_id}/messages  
const getHistory = async (sessionId) => {
  const response = await fetch(`http://localhost:8000/api/v1/conversations/${sessionId}/messages`);
  return response.json();
};
```

## 🎨 React 组件示例

### 角色选择器
```jsx
const CharacterSelector = ({ onSelect }) => {
  const [characters, setCharacters] = useState([]);

  useEffect(() => {
    getCharacters().then(setCharacters);
  }, []);

  return (
    <div className="character-grid">
      {characters.map(char => (
        <div key={char.id} onClick={() => onSelect(char)}>
          <img src={char.avatar_url} alt={char.name} />
          <h3>{char.name}</h3>
          <p>{char.description}</p>
        </div>
      ))}
    </div>
  );
};
```

### 聊天界面
```jsx
const ChatInterface = ({ character }) => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');

  const handleSend = async () => {
    const userMsg = { role: 'user', content: input };
    setMessages(prev => [...prev, userMsg]);
    
    const response = await sendMessage(character.id, input);
    const aiMsg = { role: 'assistant', content: response.data.message };
    setMessages(prev => [...prev, aiMsg]);
    
    setInput('');
  };

  return (
    <div className="chat-container">
      <div className="messages">
        {messages.map((msg, i) => (
          <div key={i} className={`message ${msg.role}`}>
            {msg.content}
          </div>
        ))}
      </div>
      <div className="input-area">
        <input 
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyPress={e => e.key === 'Enter' && handleSend()}
        />
        <button onClick={handleSend}>发送</button>
      </div>
    </div>
  );
};
```

## 🎯 TypeScript 类型

```typescript
interface Character {
  id: string;
  name: string;
  description: string;
  avatar_url: string;
  personality_traits: string[];
}

interface ChatResponse {
  success: boolean;
  data: {
    message: string;
    character_id: string;
    timestamp: string;
    metadata: any;
  };
}
```

## ⚡ 使用建议

1. 为每个会话生成唯一 session_id
2. 实现错误处理和重试机制  
3. 缓存角色列表提升性能
4. 添加加载状态提升用户体验
5. 适配移动端界面 