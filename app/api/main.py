
"""Main FastAPI application."""

import logging
from contextlib import asynccontextmanager
import time

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import redis. asyncio as redis

from app.config. settings import settings
from app.core.storage. redis_store import RedisContextStore
from app.core.storage.task_store import TaskStore

# 配置日志
logging.basicConfig(
    level=settings.log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 全局变量（生命周期管理）
redis_client = None
context_store = None
task_store = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    global redis_client, context_store, task_store
    
    logger.info("🚀 Starting Multi-Agent Coding Assistant...")
    
    # 初始化 Redis
    try:
        redis_client = redis.from_url(
            settings.redis_url,
            decode_responses=True,
            max_connections=settings.redis_max_connections
        )
        await redis_client.ping()
        logger.info("✅ Redis connected")
        
        # 初始化存储层
        context_store = RedisContextStore(redis_client)
        task_store = TaskStore(redis_client)
        logger.info("✅ Storage layers initialized")
        
    except Exception as e: 
        logger.error(f"❌ Failed to initialize Redis: {e}")
        raise
    
    logger.info(f"✅ Application started on {settings.api_prefix}")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down...")
    if redis_client:
        await redis_client.close()
        logger.info("✅ Redis connection closed")


# 创建 FastAPI 应用
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    lifespan=lifespan,
    docs_url=f"{settings.api_prefix}/docs",
    openapi_url=f"{settings. api_prefix}/openapi.json"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================
# 依赖注入
# ============================================

def get_context_store() -> RedisContextStore:
    """Get context store dependency."""
    if context_store is None:
        raise HTTPException(status_code=503, detail="Context store not available")
    return context_store


def get_task_store() -> TaskStore:
    """Get task store dependency."""
    if task_store is None:
        raise HTTPException(status_code=503, detail="Task store not available")
    return task_store


# ============================================
# 路由
# ============================================

from app.api.routes import tasks, contexts

app.include_router(
    tasks.router,
    prefix=f"{settings.api_prefix}/tasks",
    tags=["tasks"]
)

app.include_router(
    contexts.router,
    prefix=f"{settings.api_prefix}/contexts",
    tags=["contexts"]
)


# ============================================
# 根路由
# ============================================

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": settings.api_title,
        "version": settings.api_version,
        "docs":  f"{settings.api_prefix}/docs",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    from app.api.schemas.response import HealthResponse
    
    redis_status = "disconnected"
    
    try:
        if redis_client:
            await redis_client.ping()
            redis_status = "connected"
    except Exception as e:
        logger.error(f"Health check failed: {e}")
    
    return HealthResponse(
        status="healthy" if redis_status == "connected" else "unhealthy",
        redis=redis_status,
        timestamp=time.time()
    )
