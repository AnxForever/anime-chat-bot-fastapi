# Cloudflare Workers 部署设置指南

## 前置要求

### 1. 安装 Node.js 和 npm
```bash
# Windows (使用 winget)
winget install OpenJS.NodeJS

# 或者访问 https://nodejs.org/ 下载安装包
```

### 2. 安装 Wrangler CLI
```bash
npm install -g wrangler
```

### 3. 验证安装
```bash
node --version  # 应该显示 v18+ 
npm --version   # 应该显示 9+
wrangler --version  # 应该显示 3+
```

## Cloudflare 账户配置

### 1. 登录 Cloudflare
```bash
wrangler auth login
```

### 2. 设置 API 密钥
```bash
# 设置 Gemini API 密钥
wrangler secret put GEMINI_API_KEY

# 设置 SiliconFlow API 密钥 (用于调用 DeepSeek 模型)
wrangler secret put DEEPSEEK_API_KEY

# 设置 JWT 密钥
wrangler secret put JWT_SECRET_KEY
```

## 开发和部署

### 本地开发
```bash
cd workers
wrangler dev
```

### 部署到生产环境
```bash
cd workers
wrangler deploy
```

### 部署到测试环境
```bash
cd workers  
wrangler deploy --env staging
```

## 故障排除

### 常见问题
1. **认证失败**: 确保已通过 `wrangler auth login` 登录
2. **部署失败**: 检查 wrangler.toml 配置文件
3. **API 调用失败**: 确认已设置所有必要的 secret 变量

### 获取帮助
- Cloudflare Workers 文档: https://developers.cloudflare.com/workers/
- Wrangler CLI 文档: https://developers.cloudflare.com/workers/wrangler/ 