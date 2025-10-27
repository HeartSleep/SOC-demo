from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer
import asyncio
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.logging import setup_logging, get_logger
from app.core.database_simple import init_database, close_database
from app.api.endpoints import auth, settings as settings_endpoints, system
from app.api.endpoints import vulnerabilities_simple as vulnerabilities, users_simple as users, assets_simple as assets, tasks_real as tasks, reports_simple as reports
from app.api.endpoints import vulnerability_rules

logger = get_logger(__name__)

# Security
security = HTTPBearer()


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("启动 SOC 安全平台 (本地开发模式)...")

    # 初始化简化数据库
    try:
        await init_database()
        logger.info("数据库已初始化 (内存模式)")
    except Exception as e:
        logger.warning(f"数据库初始化失败: {e}")

    yield

    # 清理
    try:
        await close_database()
        logger.info("SOC 安全平台已停止")
    except Exception as e:
        logger.warning(f"数据库清理失败: {e}")


# 创建 FastAPI 应用
app = FastAPI(
    title="SOC 安全平台",
    version="1.0.0",
    description="企业级安全运营中心平台 (本地开发版)",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*.localdomain"],
)

# 健康检查
@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "version": "1.0.0",
        "mode": "local_development"
    }

# API 路由
app.include_router(
    auth.router,
    prefix="/api/v1/auth",
    tags=["authentication"]
)

app.include_router(
    assets.router,
    prefix="/api/v1/assets",
    tags=["assets"]
)

app.include_router(
    tasks.router,
    prefix="/api/v1/tasks",
    tags=["tasks"]
)

app.include_router(
    vulnerabilities.router,
    prefix="/api/v1/vulnerabilities",
    tags=["vulnerabilities"]
)

app.include_router(
    reports.router,
    prefix="/api/v1/reports",
    tags=["reports"]
)

app.include_router(
    users.router,
    prefix="/api/v1/users",
    tags=["users"]
)

app.include_router(
    settings_endpoints.router,
    prefix="/api/v1/settings",
    tags=["settings"]
)

app.include_router(
    system.router,
    prefix="/api/v1/system",
    tags=["system"]
)

app.include_router(
    vulnerability_rules.router,
    prefix="/api/v1/vulnerability-rules",
    tags=["vulnerability-rules"]
)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main_local:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
