# 动漫角色聊天机器人 - Cloudflare Workers 版本

## 项目简介

这是动漫角色聊天机器人的 Cloudflare Workers 部署版本，将原本的 FastAPI 应用转换为适配 Workers 运行时环境的无服务器应用。

## 功能特性

- 🎭 **多角色支持**: 绫波丽、明日香、初音未来等经典动漫角色
- 🧠 **智能对话**: 基于 Gemini/DeepSeek API 的 AI 对话系统  
- 🚀 **无服务器**: 基于 Cloudflare Workers，自动伸缩，全球加速
- 💰 **成本优化**: 免费额度慷慨，按需付费
- 🛡️ **安全可靠**: 内置 DDoS 防护和安全机制

## 项目结构

```
workers/
├── src/                    # 源代码目录
│   ├── main.py            # 主入口文件
│   ├── router.py          # 路由映射器
│   ├── data/              # 内嵌数据
│   │   └── characters.py  # 角色配置数据
│   ├── handlers/          # API 处理器
│   │   ├── chat_handler.py    # 聊天处理器
│   │   ├── auth_handler.py    # 认证处理器
│   │   ├── session_handler.py # 会话处理器
│   │   └── memory_handler.py  # 记忆处理器
│   ├── services/          # 核心服务
│   │   └── llm_connector.py  # LLM 连接器
│   └── utils/             # 工具类
│       ├── http_utils.py  # HTTP 工具
│       └── logger.py      # 日志工具
├── package.json           # Node.js 配置
├── wrangler.toml         # Workers 部署配置
├── SETUP.md              # 安装指南
└── README.md             # 项目说明
```

## 部署指南

### 1. 环境准备

首先安装必要的工具：

```bash
# 安装 Node.js (版本 18+)
winget install OpenJS.NodeJS

# 安装 Wrangler CLI
npm install -g wrangler

# 验证安装
node --version
wrangler --version
```

### 2. 克隆并配置项目

```bash
# 进入 workers 目录
cd anime_chat_bot/workers

# 登录 Cloudflare
wrangler auth login
```

### 3. 配置 API 密钥

设置 LLM API 密钥：

```bash
# 设置 Gemini API 密钥
wrangler secret put GEMINI_API_KEY

# 设置 SiliconFlow API 密钥 (用于调用 DeepSeek 模型)
wrangler secret put DEEPSEEK_API_KEY

# 设置 JWT 密钥（可选）
wrangler secret put JWT_SECRET_KEY
```

### 4. 本地开发测试

```bash
# 启动本地开发服务器
wrangler dev

# 测试 API 端点
curl http://localhost:8787/health
curl http://localhost:8787/api/v1/characters
```

### 5. 部署到生产环境

```bash
# 部署到生产环境
wrangler deploy

# 查看部署状态
wrangler tail
```

## API 文档

### 基础端点

- `GET /` - 根路径信息
- `GET /health` - 健康检查

### 聊天相关

- `POST /api/v1/chat` - 发送消息
- `GET /api/v1/characters` - 获取角色列表
- `GET /api/v1/characters/{character_id}` - 获取角色详情

### 请求示例

**发送消息:**

```bash
curl -X POST https://your-worker.your-subdomain.workers.dev/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "你好，绫波丽",
    "character_id": "rei_ayanami"
  }'
```

**响应示例:**

```json
{
  "success": true,
  "data": {
    "message": "...你好。我是绫波丽。",
    "character_id": "rei_ayanami",
    "character_name": "绫波丽",
    "processing_time": 1.234,
    "tokens_used": 256
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## 支持的角色

| 角色ID | 角色名称 | 来源 | 特点 |
|--------|----------|------|------|
| rei_ayanami | 绫波丽 | 新世纪福音战士 | 冷淡、神秘、内向 |
| asuka_langley | 明日香·兰格雷 | 新世纪福音战士 | 自信、强势、傲娇 |
| miku_hatsune | 初音未来 | VOCALOID | 活泼、可爱、热爱音乐 |

## 性能优化

- **全球加速**: Cloudflare 的全球 CDN 网络
- **智能缓存**: 静态资源和 API 响应缓存
- **自动伸缩**: 根据流量自动调整计算资源
- **冷启动优化**: Workers 运行时优化，启动延迟极低

## 监控和日志

```bash
# 查看实时日志
wrangler tail

# 查看部署状态
wrangler list

# 查看使用统计
wrangler deployment list
```

## 故障排除

### 常见问题

1. **部署失败**
   - 检查 `wrangler.toml` 配置
   - 确认已登录 Cloudflare 账户
   - 验证 API 密钥设置

2. **API 调用失败**
   - 确认 LLM API 密钥已正确设置
   - 检查 API 额度是否充足
   - 查看 Workers 日志排错

3. **CORS 错误**
   - 检查前端请求头配置
   - 确认 Workers 已正确设置 CORS

### 获取帮助

- [Cloudflare Workers 文档](https://developers.cloudflare.com/workers/)
- [Wrangler CLI 文档](https://developers.cloudflare.com/workers/wrangler/)
- [项目 GitHub 仓库](https://github.com/your-repo/anime-chat-bot)

## 许可证

MIT License

---

**部署完成后，你将拥有一个全球可访问的动漫角色聊天机器人 API！** 🎉 