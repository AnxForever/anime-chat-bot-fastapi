# anime-chat-bot-fastapi
动漫角色聊天机器人 FastAPI 版本，支持 Gemini/DeepSeek API，可一键部署到 Vercel。

## 🚀 部署说明

### Vercel 部署配置

本项目使用优化的 `vercel.json` 配置来确保 FastAPI 应用在 Vercel 上正确运行：

```json
{
  "version": 2,
  "functions": {
    "main.py": {
      "runtime": "@vercel/python",
      "memory": 1024,
      "maxDuration": 10
    }
  },
  "routes": [
    {
      "src": "/(.*)",
      "dest": "main.py"
    }
  ]
}
```

**配置说明：**
- 使用 `functions` 而非 `builds`，明确指定 `main.py` 为 Serverless Function 入口
- 设置内存为 1024MB，最大执行时间为 10 秒
- 确保 Python 包导入（如 `app.routers`）在 Vercel 环境中正常工作

### 部署步骤

1. 将代码推送到 GitHub 仓库
2. 在 Vercel 中连接该仓库
3. 配置环境变量（如 API 密钥）
4. 部署完成后，API 文档可通过 `/docs` 访问
