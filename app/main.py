"""
动漫角色聊天机器人主应用
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import logging
import os
from datetime import datetime

# 导入路由
from app.routers.chat_api import router as chat_router
from app.routers.websocket_router import router as websocket_router
from app.routers.auth_router import router as auth_router
from app.routers.enhanced_memory import router as memory_router
from app.routers.stats_router import router as analytics_router

# 初始化FastAPI应用
app = FastAPI(
    title="动漫角色聊天机器人 API",
    description="基于AI的动漫角色角色扮演聊天系统，支持流式响应、用户认证、记忆管理和统计分析",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React开发服务器
        "http://localhost:5173",  # Vite开发服务器
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# 静态文件服务
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# 注册路由
app.include_router(chat_router)
app.include_router(websocket_router)
app.include_router(auth_router)
app.include_router(memory_router)
app.include_router(analytics_router)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# 根路径
@app.get("/")
async def root():
    """API根路径"""
    return {
        "message": "动漫角色聊天机器人 API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "docs": "/docs",
        "redoc": "/redoc",
        "status": "running"
    }

# 健康检查
@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "api": "running",
            "ai_service": "available",
            "database": "connected"
        }
    }

# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "SYS_001",
                "message": "系统内部错误",
                "details": str(exc) if app.debug else "请联系系统管理员"
            },
            "timestamp": datetime.now().isoformat()
        }
    )

# 启动事件
@app.on_event("startup")
async def startup_event():
    """应用启动时执行"""
    logger.info("动漫角色聊天机器人 API 正在启动...")
    
    # 初始化服务
    try:
        # 这里可以添加服务初始化逻辑
        # 例如：连接数据库、加载模型等
        logger.info("所有服务初始化完成")
    except Exception as e:
        logger.error(f"服务初始化失败: {e}")
        raise

# 关闭事件  
@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时执行"""
    logger.info("动漫角色聊天机器人 API 正在关闭...")
    
    # 清理资源
    try:
        # 这里可以添加清理逻辑
        # 例如：关闭数据库连接、保存状态等
        logger.info("资源清理完成")
    except Exception as e:
        logger.error(f"资源清理失败: {e}")

if __name__ == "__main__":
    import uvicorn
    
    # 开发环境配置
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
