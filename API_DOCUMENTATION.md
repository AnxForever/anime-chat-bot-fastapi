# 动漫角色聊天机器人 API 文档

## 📋 基础配置

### 1. **服务器信息**
```
开发环境: http://localhost:8000
生产环境: https://your-domain.com
API 基础路径: /api/v1
WebSocket: ws://localhost:8000/ws
```

### 2. **认证方式**
```
认证类型: JWT Bearer Token
请求头: Authorization: Bearer <token>
会话管理: Redis/内存存储
```

### 3. **请求/响应格式**
```
Content-Type: application/json
字符编码: UTF-8
时间格式: ISO 8601
```

---

## 🤖 角色管理 API

### GET /api/v1/characters
获取所有可用角色列表

**响应示例:**
```json
{
  "success": true,
  "data": [
    {
      "id": "rei_ayanami",
      "name": "绫波零",
      "description": "沉默寡言的EVA驾驶员",
      "avatar_url": "/static/avatars/rei.png",
      "source": "新世纪福音战士",
      "personality_traits": ["冷淡", "神秘", "忠诚"],
      "available": true
    }
  ]
}
```

### GET /api/v1/characters/{character_id}
获取角色详细信息

**响应示例:**
```json
{
  "success": true,
  "data": {
    "id": "rei_ayanami",
    "name": "绫波零",
    "description": "沉默寡言的EVA驾驶员",
    "avatar_url": "/static/avatars/rei.png",
    "personality_deep": {
      "core_traits": ["冷淡", "神秘莫测", "忠诚"],
      "big_five_personality": {
        "openness": 4,
        "conscientiousness": 9,
        "extraversion": 2,
        "agreeableness": 6,
        "neuroticism": 7
      }
    },
    "behavioral_constraints": {
      "forbidden_words": ["开心死了", "超级"],
      "preferred_expressions": ["...", "是吗", "司令"],
      "must_do": ["对司令保持忠诚"],
      "must_not_do": ["表现过度情感", "质疑命令"]
    },
    "few_shot_examples": [
      {
        "user": "你好，零！",
        "assistant": "...你好。有什么事吗？"
      }
    ]
  }
}
```

---

## 💬 对话系统 API

### POST /api/v1/chat
发送消息并获取AI回复

**请求体:**
```json
{
  "character_id": "rei_ayanami",
  "message": "今天天气很好呢！",
  "user_id": "user_123",
  "session_id": "session_456"
}
```

**响应示例:**
```json
{
  "success": true,
  "data": {
    "message": "是吗...天气确实不错。",
    "character_id": "rei_ayanami", 
    "timestamp": "2024-01-01T10:01:00Z",
    "metadata": {
      "emotion_detected": "neutral",
      "response_time_ms": 1250,
      "confidence_score": 0.85
    }
  }
}
```

### POST /api/v1/chat/stream
流式对话（WebSocket 或 SSE）

**WebSocket 连接:**
```javascript
ws://localhost:8000/ws/chat/{session_id}

// 发送消息
{
  "type": "user_message",
  "character_id": "rei_ayanami",
  "message": "你今天心情怎么样？"
}

// 接收流式响应
{
  "type": "character_response_chunk",
  "content": "今天",
  "is_complete": false
}
{
  "type": "character_response_chunk", 
  "content": "的心情...",
  "is_complete": false
}
{
  "type": "character_response_complete",
  "full_message": "今天的心情...还算正常吧。",
  "metadata": {...}
}
```

### GET /api/v1/conversations/{session_id}/messages
获取对话历史

**查询参数:**
```
page: 页码 (默认: 1)
limit: 每页数量 (默认: 50, 最大: 100)
before: 时间戳 (获取该时间之前的消息)
```

**响应示例:**
```json
{
  "success": true,
  "data": {
    "messages": [
      {
        "id": "msg_001",
        "role": "user",
        "content": "你好",
        "timestamp": "2024-01-01T10:00:00Z",
        "user_id": "user_123"
      },
      {
        "id": "msg_002", 
        "role": "assistant",
        "content": "...你好。",
        "timestamp": "2024-01-01T10:00:05Z",
        "character_id": "rei_ayanami",
        "metadata": {
          "emotion": "neutral",
          "confidence": 0.92
        }
      }
    ],
    "pagination": {
      "current_page": 1,
      "total_pages": 3,
      "total_messages": 150,
      "has_next": true
    }
  }
}
```

---

## 🧠 记忆系统 API

### GET /api/v1/memory/{character_id}/{session_id}
获取角色记忆

**响应示例:**
```json
{
  "success": true,
  "data": {
    "memories": [
      {
        "id": "mem_001",
        "type": "factual",
        "importance": "high",
        "content": "用户说他喜欢音乐",
        "keywords": ["音乐", "喜欢"],
        "emotions": ["happy"],
        "created_at": "2024-01-01T10:00:00Z",
        "access_count": 3
      }
    ],
    "statistics": {
      "total_memories": 25,
      "by_type": {
        "factual": 10,
        "emotional": 8,
        "preference": 5,
        "relationship": 2
      },
      "by_importance": {
        "critical": 2,
        "high": 8, 
        "medium": 10,
        "low": 5
      }
    }
  }
}
```

### POST /api/v1/memory/{character_id}/{session_id}/extract
从对话中提取记忆

**请求体:**
```json
{
  "user_message": "我最喜欢的歌手是初音未来！",
  "character_response": "是吗...我知道了。"
}
```

---

## 📊 角色状态 API

### GET /api/v1/character-state/{character_id}/{session_id}
获取角色当前状态

**响应示例:**
```json
{
  "success": true,
  "data": {
    "relationship_level": "friend",
    "familiarity_score": 65.5,
    "mood": "good",
    "energy_level": 80.0,
    "trust_level": 72.5,
    "interaction_count": 45,
    "positive_interactions": 38,
    "negative_interactions": 2,
    "topic_preferences": {
      "音乐": 8.5,
      "日常": 6.2,
      "EVA": 9.1
    },
    "special_memories": [
      "用户第一次说喜欢我",
      "一起讨论了EVA驾驶的感受"
    ],
    "last_interaction": "2024-01-01T10:00:00Z"
  }
}
```

### POST /api/v1/character-state/{character_id}/{session_id}/update
更新角色状态

**请求体:**
```json
{
  "interaction_type": "conversation",
  "user_message": "你今天看起来很开心！",
  "character_response": "...是吗？谢谢你。",
  "interaction_quality": 0.8
}
```

---

## 🤝 关系管理 API

### GET /api/v1/relationships/{character_id}
获取角色关系网络

**响应示例:**
```json
{
  "success": true,
  "data": {
    "relationships": [
      {
        "character_a": "rei_ayanami",
        "character_b": "asuka_langley", 
        "relationship_type": "rival",
        "affinity_score": -10,
        "trust_level": 30,
        "interaction_count": 15,
        "last_interaction": "2024-01-01T09:00:00Z",
        "notes": ["同为EVA驾驶员", "性格差异导致的微妙竞争关系"]
      }
    ],
    "network_summary": {
      "total_relationships": 3,
      "relationship_types": {
        "rival": 1,
        "neutral": 1, 
        "friendly": 1
      }
    }
  }
}
```

### POST /api/v1/relationships/simulate
模拟角色互动

**请求体:**
```json
{
  "character_a_id": "rei_ayanami",
  "character_b_id": "asuka_langley",
  "topic": "EVA驾驶技巧",
  "context": "training_scenario"
}
```

---

## 🎯 上下文分析 API

### POST /api/v1/context/analyze
分析对话上下文

**请求体:**
```json
{
  "character_id": "rei_ayanami",
  "session_id": "session_456",
  "user_message": "我今天心情不太好...",
  "conversation_history": [...]
}
```

**响应示例:**
```json
{
  "success": true,
  "data": {
    "emotional_context": {
      "user_emotion": "sad",
      "emotion_intensity": 0.7,
      "emotion_trend": "declining"
    },
    "relational_context": {
      "relationship_level": "friend",
      "familiarity_score": 65.5
    },
    "adjustment_instructions": [
      "语调调整：表现得更加同情和温柔(强度: 0.7)",
      "亲密度调整：增加关怀表达(程度: 0.6)"
    ]
  }
}
```

---

## ✅ 验证系统 API

### POST /api/v1/validation/response
验证生成的回应

**请求体:**
```json
{
  "character_id": "rei_ayanami",
  "user_message": "你好！",
  "character_response": "开心死了！今天天气超级好！",
  "context": {...}
}
```

**响应示例:**
```json
{
  "success": true,
  "data": {
    "overall_score": 0.3,
    "overall_passed": false,
    "requires_regeneration": true,
    "major_issues": [
      "使用了角色禁用词汇: '开心死了'",
      "使用了角色禁用词汇: '超级'"
    ],
    "recommendations": [
      "移除或替换词汇 '开心死了'",
      "使用更符合角色的语言模式"
    ],
    "validation_results": [
      {
        "category": "character_consistency",
        "passed": false,
        "score": 0.4,
        "severity": "high"
      }
    ]
  }
}
```

---

## 🔐 认证与用户系统

### POST /api/v1/auth/login
用户登录

**请求体:**
```json
{
  "username": "user123",
  "password": "password123"
}
```

**响应示例:**
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "dGhpc2lzYXJlZnJlc2h0b2tlbg...",
    "expires_in": 3600,
    "user": {
      "id": "user_123",
      "username": "user123",
      "created_at": "2024-01-01T00:00:00Z"
    }
  }
}
```

### GET /api/v1/auth/me
获取当前用户信息

**响应示例:**
```json
{
  "success": true,
  "data": {
    "id": "user_123",
    "username": "user123",
    "sessions": [
      {
        "session_id": "session_456",
        "character_id": "rei_ayanami",
        "created_at": "2024-01-01T10:00:00Z",
        "message_count": 25
      }
    ]
  }
}
```

---

## 📈 统计与监控 API

### GET /api/v1/stats/overview
获取系统概览统计

**响应示例:**
```json
{
  "success": true,
  "data": {
    "total_users": 1250,
    "active_sessions": 45,
    "total_messages": 125000,
    "average_response_time": 1.2,
    "character_popularity": {
      "rei_ayanami": 45,
      "asuka_langley": 38,
      "miku_hatsune": 42
    }
  }
}
```

---

## 🔧 数据结构定义

### TypeScript 接口
```typescript
interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: ApiError;
  timestamp: string;
}

interface ApiError {
  code: string;
  message: string;
  details?: any;
}

interface Character {
  id: string;
  name: string;
  description: string;
  avatar_url: string;
  source: string;
  personality_traits: string[];
  available: boolean;
}

interface CharacterState {
  relationship_level: RelationshipLevel;
  familiarity_score: number;
  mood: CharacterMood;
  energy_level: number;
  trust_level: number;
  interaction_count: number;
  positive_interactions: number;
  negative_interactions: number;
  topic_preferences: Record<string, number>;
  special_memories: string[];
  last_interaction: string;
}

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  user_id?: string;
  character_id?: string;
  metadata?: MessageMetadata;
}

interface MessageMetadata {
  emotion_detected?: string;
  response_time_ms?: number;
  confidence_score?: number;
  character_state?: Partial<CharacterState>;
}

interface Memory {
  id: string;
  type: MemoryType;
  importance: MemoryImportance;
  content: string;
  keywords: string[];
  emotions: string[];
  created_at: string;
  access_count: number;
}

enum RelationshipLevel {
  STRANGER = 'stranger',
  ACQUAINTANCE = 'acquaintance', 
  FRIEND = 'friend',
  CLOSE_FRIEND = 'close_friend',
  SPECIAL = 'special'
}

enum CharacterMood {
  GREAT = 'great',
  GOOD = 'good',
  NEUTRAL = 'neutral',
  BAD = 'bad',
  TERRIBLE = 'terrible'
}

enum MemoryType {
  FACTUAL = 'factual',
  EMOTIONAL = 'emotional',
  BEHAVIORAL = 'behavioral',
  PREFERENCE = 'preference',
  RELATIONSHIP = 'relationship'
}

enum MemoryImportance {
  CRITICAL = 'critical',
  HIGH = 'high',
  MEDIUM = 'medium',
  LOW = 'low'
}
```

---

## 🚀 错误处理

### 错误码定义

```json
{
  "AUTH_001": "无效的访问令牌",
  "AUTH_002": "令牌已过期", 
  "AUTH_003": "权限不足",
  "CHAR_001": "角色不存在",
  "CHAR_002": "角色配置错误",
  "CHAT_001": "消息内容为空",
  "CHAT_002": "会话不存在",
  "CHAT_003": "AI服务暂时不可用",
  "MEM_001": "记忆提取失败",
  "VAL_001": "回应验证失败",
  "SYS_001": "系统内部错误",
  "RATE_001": "请求频率超限"
}
```

### 错误响应格式

```json
{
  "success": false,
  "error": {
    "code": "CHAR_001",
    "message": "角色不存在",
    "details": {
      "character_id": "invalid_character",
      "available_characters": ["rei_ayanami", "asuka_langley", "miku_hatsune"]
    }
  },
  "timestamp": "2024-01-01T10:00:00Z"
}
```

---

## 🛠️ 环境配置

### 环境变量示例

```bash
# 基础配置
APP_ENV=development
APP_PORT=8000
API_VERSION=v1

# 数据库
DATABASE_URL=postgresql://user:pass@localhost:5432/chatbot
REDIS_URL=redis://localhost:6379

# AI 服务
GEMINI_API_KEY=your_gemini_api_key
DEEPSEEK_API_KEY=your_deepseek_api_key

# JWT 配置
JWT_SECRET=your_jwt_secret
JWT_EXPIRE_HOURS=24

# CORS 配置
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com

# 文件上传
UPLOAD_PATH=/uploads
MAX_FILE_SIZE=10MB
```

### CORS 配置

```python
# 允许的源
CORS_ORIGINS = [
    "http://localhost:3000",  # React开发服务器
    "http://localhost:5173",  # Vite开发服务器
    "https://yourdomain.com"  # 生产域名
]

# 允许的方法
CORS_METHODS = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]

# 允许的头部
CORS_HEADERS = ["Content-Type", "Authorization"]
```

---

## 📊 性能优化建议

### 1. **缓存策略**
- 角色配置：Redis缓存，TTL: 1小时
- 对话历史：内存缓存最近50条
- 用户状态：Redis缓存，TTL: 30分钟

### 2. **请求限制**
- 对话API：每用户每分钟60次
- 记忆API：每用户每分钟20次
- 认证API：每IP每分钟10次

### 3. **响应优化**
- 启用Gzip压缩
- 静态资源CDN
- 数据库连接池
- 异步处理长时间任务

---

*这份API文档涵盖了所有核心功能，你可以根据前端需求进行调整！* 