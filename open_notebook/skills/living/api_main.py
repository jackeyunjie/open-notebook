"""Living Knowledge System API Server

FastAPI application for the five-layer living knowledge system.
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from open_notebook.skills.living.api_endpoints import router

# Create FastAPI app
app = FastAPI(
    title="Living Knowledge System API",
    description="""
    活体知识系统 API - 五层认知架构
    
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
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
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
    return {
        "name": "Living Knowledge System API",
        "version": "1.0.0",
        "description": "五层活体知识系统",
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
    """Health check endpoint."""
    return {"status": "healthy"}


def main():
    """Run the API server."""
    uvicorn.run(
        "open_notebook.skills.living.api_main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )


if __name__ == "__main__":
    main()
