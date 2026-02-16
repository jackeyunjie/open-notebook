"""Living Knowledge System API with PostgreSQL Persistence

FastAPI application with PostgreSQL backend for production use.
"""

import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from open_notebook.skills.living.api_endpoints import router
from open_notebook.skills.living.database.postgresql import PostgreSQLDatabase

# Global database instance
db: PostgreSQLDatabase = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global db
    
    # Startup
    logger.info("Starting Living Knowledge System API with PostgreSQL...")
    
    # Initialize PostgreSQL connection
    db = PostgreSQLDatabase(
        host=os.getenv("LIVING_DB_HOST", "localhost"),
        port=int(os.getenv("LIVING_DB_PORT", "5433")),
        database=os.getenv("LIVING_DB_NAME", "living_system"),
        user=os.getenv("LIVING_DB_USER", "living"),
        password=os.getenv("LIVING_DB_PASSWORD", "living"),
    )
    
    try:
        await db.connect()
        logger.info("✅ PostgreSQL connected successfully")
        
        # Check system health
        health = await db.get_system_health()
        logger.info(f"System health: {health['status']}")
        
    except Exception as e:
        logger.error(f"❌ Failed to connect to PostgreSQL: {e}")
        logger.warning("⚠️ Running in memory-only mode (data will not persist)")
    
    yield
    
    # Shutdown
    if db:
        await db.disconnect()
        logger.info("PostgreSQL disconnected")


# Create FastAPI app with lifespan
app = FastAPI(
    title="Living Knowledge System API (PostgreSQL)",
    description="""
    活体知识系统 API - 五层认知架构 (PostgreSQL 持久化版本)
    
    ## 架构层次
    
    ### P0 - 感知层 (Perception)
    收集市场情报：痛点扫描、情感监控、趋势发现、场景识别
    
    ### P1 - 判断层 (Judgment)
    四维度价值评估：价值、热度、可信度、效用
    
    ### P2 - 关系层 (Relationship)
    知识图谱构建：实体链接、语义聚类、时序编织、交叉引用
    
    ### P3 - 进化层 (Evolution)
    自我改进：策略进化、反馈循环、模式识别、参数调优
    
    ### P4 - 数据层 (Data)
    生命周期管理：数据生成、流量监控、质量检查、归档管理
    
    ## 数据库
    - PostgreSQL 15+ (核心数据)
    - TimescaleDB (时序指标)
    - 端口: 5433 (避免与现有 PostgreSQL 冲突)
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include router
app.include_router(router)


@app.get("/")
async def root():
    """Root endpoint."""
    db_status = "connected" if db and db.pool else "disconnected"
    
    return {
        "name": "Living Knowledge System API (PostgreSQL)",
        "version": "1.0.0",
        "description": "五层活体知识系统 - 生产就绪版本",
        "database": {
            "type": "PostgreSQL + TimescaleDB",
            "status": db_status,
            "host": os.getenv("LIVING_DB_HOST", "localhost"),
            "port": int(os.getenv("LIVING_DB_PORT", "5433")),
            "database": os.getenv("LIVING_DB_NAME", "living_system"),
        },
        "layers": {
            "p0": "感知层 - Perception",
            "p1": "判断层 - Judgment",
            "p2": "关系层 - Relationship",
            "p3": "进化层 - Evolution",
            "p4": "数据层 - Data Management"
        },
        "docs": "/docs",
        "health": "/living-knowledge/status"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint with database status."""
    db_healthy = False
    
    if db and db.pool:
        try:
            health = await db.get_system_health()
            db_healthy = health.get("status") == "healthy"
        except:
            pass
    
    return {
        "status": "healthy" if db_healthy else "degraded",
        "database": "connected" if db_healthy else "disconnected",
        "timestamp": __import__("datetime").datetime.now().isoformat()
    }


@app.get("/db/status")
async def database_status():
    """Get detailed database status."""
    if not db or not db.pool:
        return {
            "status": "disconnected",
            "error": "Database not connected"
        }
    
    try:
        health = await db.get_system_health()
        return {
            "status": health.get("status", "unknown"),
            "storage": {
                "total_gb": health.get("storage_gb", 0),
                "by_tier": health.get("storage_by_tier", {})
            },
            "metrics": {
                "cell_states": health.get("cell_states", 0),
                "agent_states": health.get("agent_states", 0),
                "lineage_records": health.get("lineage_records", 0)
            },
            "timestamp": __import__("datetime").datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


def main():
    """Run the API server."""
    host = os.getenv("LIVING_HOST", "0.0.0.0")
    port = int(os.getenv("LIVING_PORT", "8000"))
    
    logger.info(f"Starting server on {host}:{port}")
    
    uvicorn.run(
        "open_notebook.skills.living.api_postgres:app",
        host=host,
        port=port,
        reload=False,
        log_level="info"
    )


if __name__ == "__main__":
    main()
