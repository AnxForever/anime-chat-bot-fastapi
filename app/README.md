# 动漫角色聊天机器人 - Vercel FastAPI 部署指南

## 1. 目录结构

```
anime_chat_bot/
  app/
    main.py
    requirements.txt
    vercel.json
    ...
```

## 2. 推送到 GitHub/GitLab/Bitbucket

- 推荐只推送 app/ 目录为一个独立仓库，或在 Vercel 选择 app/ 作为根目录

## 3. Vercel 配置

- 新建 Vercel 项目，选择 app/ 目录为根目录
- 自动检测 Python 项目
- 自动安装 requirements.txt 依赖

## 4. 添加环境变量

在 Vercel 项目设置中添加：

- GEMINI_API_KEY
- DEEPSEEK_API_KEY
- JWT_SECRET_KEY（如有）

## 5. 访问 API

- 部署完成后，Vercel 会分配一个域名
- 访问 `https://your-vercel-domain.vercel.app/health` 检查服务
- 访问 `https://your-vercel-domain.vercel.app/api/v1/chat` 进行聊天

## 6. 常见问题

- 依赖安装失败：检查 requirements.txt
- 入口文件错误：确保 main.py 有 `app = FastAPI()`
- 环境变量未生效：检查 Vercel 设置

---

如需自定义路径或入口文件，请相应修改 vercel.json 的 "src" 和 "dest" 字段。 