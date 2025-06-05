# SiliconFlow API 配置指南

## 简介

[SiliconFlow](https://siliconflow.cn/) 是一个提供多种 AI 模型 API 的平台，我们使用它来调用 DeepSeek 模型。

## API 配置

### 1. 获取 API Key

1. 访问 [SiliconFlow 官网](https://siliconflow.cn/)
2. 注册账户并登录
3. 进入控制台，在 API 密钥页面创建新的密钥
4. 复制生成的 API 密钥

### 2. 设置环境变量

```bash
# 使用 Wrangler 设置密钥
wrangler secret put DEEPSEEK_API_KEY
# 粘贴你的 SiliconFlow API 密钥
```

## 可用模型

SiliconFlow 平台上的 DeepSeek 相关模型：

| 模型名称 | 模型ID | 特点 | 适用场景 |
|---------|-------|------|----------|
| DeepSeek Chat | `deepseek-chat` | 通用对话模型 | 日常聊天、角色扮演 |
| DeepSeek Coder | `deepseek-coder` | 编程专用模型 | 代码生成、技术问答 |

## 请求示例

### 基本聊天请求

```bash
curl -X POST "https://api.siliconflow.cn/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "model": "deepseek-chat",
    "messages": [
      {"role": "user", "content": "你好"}
    ],
    "temperature": 0.7,
    "max_tokens": 1000
  }'
```

### 响应格式

```json
{
  "id": "chatcmpl-...",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "deepseek-chat",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "你好！我是DeepSeek，很高兴为你服务。"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 20,
    "total_tokens": 30
  }
}
```

## 在项目中的使用

我们的聊天机器人代码会自动：

1. 检测模型名称，如果不是以 `deepseek` 开头，会默认使用 `deepseek-chat`
2. 发送请求到 SiliconFlow API 端点
3. 解析标准的 OpenAI 格式响应
4. 返回处理后的结果

## 费用说明

- SiliconFlow 提供一定的免费额度
- 按使用的 token 数量收费
- 具体定价请查看 [SiliconFlow 定价页面](https://siliconflow.cn/pricing)

## 限制和注意事项

1. **API 限制**: 遵守 SiliconFlow 的速率限制
2. **模型可用性**: 某些模型可能有地区限制
3. **响应时间**: 网络延迟可能影响响应速度
4. **错误处理**: 代码已包含完整的错误处理逻辑

## 故障排除

### 常见错误

1. **401 Unauthorized**: API 密钥错误或过期
2. **429 Too Many Requests**: 请求频率过高
3. **500 Internal Server Error**: SiliconFlow 服务暂时不可用

### 调试建议

```bash
# 查看 Workers 日志
wrangler tail

# 测试 API 连接
curl -H "Authorization: Bearer YOUR_API_KEY" \
     https://api.siliconflow.cn/v1/models
```

## 更多资源

- [SiliconFlow 官方文档](https://docs.siliconflow.cn/)
- [DeepSeek 模型介绍](https://deepseek.ai/)
- [OpenAI API 格式参考](https://platform.openai.com/docs/api-reference) 