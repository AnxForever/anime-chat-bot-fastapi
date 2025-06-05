#!/usr/bin/env python3
"""启动脚本"""

import uvicorn

if __name__ == "__main__":
    print("🚀 启动动漫角色聊天机器人...")
    print("📖 API文档: http://localhost:8000/docs")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 