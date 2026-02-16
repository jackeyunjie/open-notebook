"""FastAPI server for Living Knowledge System.

Provides RESTful endpoints for:
- System health and status
- Organ management
- Trigger activation
- Meridian monitoring
- Data lifecycle management

Port: 8888 (default)
"""

import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from loguru import logger

from open_notebook.skills.living import (
    LivingSkill,
    AgentTissue,
    TriggerRegistry,
    TriggerType,
    MeridianSystem,
)
from open_notebook.skills.living.database.abstract import (
    CellState,
    AgentState,
    DataTier,
)
from open_notebook.skills.living.database.postgresql import (
    create_postgresql_database,
    PostgreSQLDatabase,
)
from open_notebook.skills.living.p4_data_agent import P4DataAgent


# ============================================================================
# Pydantic Models
# ============================================================================

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str = "1.0.0"
    components: Dict[str, Any]


class CellInfo(BaseModel):
    skill_id: str
    name: str
    state: str
    run_count: int
    success_rate: float
    last_run: Optional[str]
    next_run: Optional[str]


class AgentInfo(BaseModel):
    agent_id: str
    name: str
    status: str
    energy_level: float
    stress_level: float
    skill_count: int
    tasks_completed: int


class TriggerActivationRequest(BaseModel):
    data: Optional[Dict[str, Any]] = None


class TriggerActivationResponse(BaseModel):
    trigger_id: str
    activated: bool
    timestamp: str
    message: str


class MeridianMetrics(BaseModel):
    meridian_id: str
    connected_nodes: int
    packets_sent: int
    packets_received: int
    queue_size: int
    blockages: int


class DataTierRequest(BaseModel):
    data_id: str
    target_tier: str = Field(..., description="hot, warm, cold, or frozen")


class SystemStats(BaseModel):
    cells_total: int
    cells_running: int
    agents_total: int
    agents_healthy: int
    triggers_24h: int
    storage_tiers: Dict[str, int]


# ============================================================================
# Global State
# ============================================================================

db: Optional[PostgreSQLDatabase] = None
p4_agent: Optional[P4DataAgent] = None


# ============================================================================
# FastAPI App
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global db, p4_agent

    # Startup
    logger.info("Starting Living Knowledge System API...")

    # Connect to database
    db = await create_postgresql_database(
        host=os.getenv("LIVING_DB_HOST", "localhost"),
        port=int(os.getenv("LIVING_DB_PORT", "5432")),
        database=os.getenv("LIVING_DB_NAME", "living_system"),
        user=os.getenv("LIVING_DB_USER", "living"),
        password=os.getenv("LIVING_DB_PASSWORD", "living"),
    )

    # Start P4 Data Agent
    p4_agent = P4DataAgent(db)
    await p4_agent.start()

    logger.info("API server ready")

    yield

    # Shutdown
    logger.info("Shutting down API server...")
    if p4_agent:
        await p4_agent.stop()
    if db:
        await db.disconnect()
    logger.info("API server shutdown complete")


app = FastAPI(
    title="Living Knowledge System API",
    description="API for the organic, self-growing knowledge management system",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Health & Status Endpoints
# ============================================================================

@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint."""
    return {
        "name": "Living Knowledge System",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Get comprehensive system health."""
    if not db or not p4_agent:
        raise HTTPException(status_code=503, detail="System not fully initialized")

    try:
        health = await p4_agent.get_system_health()

        return HealthResponse(
            status="healthy",
            timestamp=datetime.now().isoformat(),
            components={
                "database": "connected",
                "p4_data_agent": "running" if p4_agent.flow_monitor.monitoring else "stopped",
                "alerts_count": len(p4_agent.flow_monitor.alerts),
                **health
            }
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats", response_model=SystemStats)
async def get_system_stats():
    """Get system-wide statistics."""
    if not db:
        raise HTTPException(status_code=503, detail="Database not connected")

    try:
        health = await db.get_system_health()

        return SystemStats(
            cells_total=health["cells"]["total"],
            cells_running=health["cells"]["running"],
            agents_total=health["agents"]["total"],
            agents_healthy=health["agents"]["healthy"],
            triggers_24h=health["triggers_24h"]["total"],
            storage_tiers={}  # Would be populated from actual storage metrics
        )
    except Exception as e:
        logger.error(f"Stats query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Cell (Skill) Endpoints
# ============================================================================

@app.get("/cells", response_model=List[CellInfo])
async def list_cells(
    state: Optional[str] = None,
    limit: int = 100
):
    """List all skill cells."""
    if not db:
        raise HTTPException(status_code=503, detail="Database not connected")

    try:
        states = await db.list_cell_states(state_filter=state, limit=limit)

        return [
            CellInfo(
                skill_id=s.skill_id,
                name=s.metadata.get("name", s.skill_id),
                state=s.state,
                run_count=s.run_count,
                success_rate=s.success_count / max(s.run_count, 1),
                last_run=s.last_run.isoformat() if s.last_run else None,
                next_run=s.next_run.isoformat() if s.next_run else None,
            )
            for s in states
        ]
    except Exception as e:
        logger.error(f"List cells failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/cells/{skill_id}", response_model=Dict[str, Any])
async def get_cell(skill_id: str):
    """Get detailed information about a specific cell."""
    if not db:
        raise HTTPException(status_code=503, detail="Database not connected")

    state = await db.get_cell_state(skill_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"Cell {skill_id} not found")

    stats = await db.get_cell_statistics(skill_id)

    return {
        "state": state.__dict__,
        "statistics": stats,
    }


@app.post("/cells/{skill_id}/invoke")
async def invoke_cell(skill_id: str, context: Optional[Dict] = None):
    """Manually invoke a skill cell."""
    skill = LivingSkill.get_instance(skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail=f"Skill {skill_id} not found")

    try:
        result = await skill.invoke(context or {})
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"Invoke cell failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Agent (Tissue) Endpoints
# ============================================================================

@app.get("/agents", response_model=List[AgentInfo])
async def list_agents(
    status: Optional[str] = None,
    limit: int = 100
):
    """List all agent tissues."""
    if not db:
        raise HTTPException(status_code=503, detail="Database not connected")

    try:
        states = await db.list_agent_states(status_filter=status, limit=limit)

        return [
            AgentInfo(
                agent_id=s.agent_id,
                name=s.name,
                status=s.status,
                energy_level=s.energy_level,
                stress_level=s.stress_level,
                skill_count=len(s.skill_states),
                tasks_completed=s.tasks_completed,
            )
            for s in states
        ]
    except Exception as e:
        logger.error(f"List agents failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agents/{agent_id}")
async def get_agent(agent_id: str):
    """Get detailed information about a specific agent."""
    if not db:
        raise HTTPException(status_code=503, detail="Database not connected")

    state = await db.get_agent_state(agent_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

    return state.__dict__


@app.post("/agents/{agent_id}/execute")
async def execute_agent(agent_id: str, context: Optional[Dict] = None):
    """Manually execute an agent."""
    agent = AgentTissue.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

    try:
        result = await agent.execute(context or {})
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"Execute agent failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agents/{agent_id}/stimulate")
async def stimulate_agent(agent_id: str, stimulus: str, data: Optional[Dict] = None):
    """Stimulate an agent with an external stimulus."""
    agent = AgentTissue.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

    await agent.stimulate(stimulus, data)
    return {"success": True, "message": f"Agent {agent_id} stimulated with {stimulus}"}


# ============================================================================
# Acupoint (Trigger) Endpoints
# ============================================================================

@app.get("/triggers")
async def list_triggers(
    trigger_type: Optional[str] = None,
    tag: Optional[str] = None
):
    """List all registered triggers."""
    triggers = TriggerRegistry.list_all()

    if trigger_type:
        ttype = TriggerType(trigger_type)
        triggers = [t for t in triggers if t.trigger_type == ttype]

    if tag:
        triggers = TriggerRegistry.list_by_tag(tag)

    return [t.to_dict() for t in triggers]


@app.post("/triggers/{trigger_id}/activate", response_model=TriggerActivationResponse)
async def activate_trigger(
    trigger_id: str,
    request: TriggerActivationRequest
):
    """Manually activate a trigger."""
    trigger = TriggerRegistry.get(trigger_id)
    if not trigger:
        raise HTTPException(status_code=404, detail=f"Trigger {trigger_id} not found")

    try:
        activated = await trigger.activate(request.data)
        return TriggerActivationResponse(
            trigger_id=trigger_id,
            activated=activated,
            timestamp=datetime.now().isoformat(),
            message="Trigger activated successfully" if activated else "Trigger activation failed or blocked"
        )
    except Exception as e:
        logger.error(f"Trigger activation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/triggers/{trigger_id}/history")
async def get_trigger_history(
    trigger_id: str,
    limit: int = 100
):
    """Get activation history for a trigger."""
    if not db:
        raise HTTPException(status_code=503, detail="Database not connected")

    history = await db.get_trigger_history(trigger_id, limit=limit)
    return [
        {
            "timestamp": h.timestamp.isoformat(),
            "success": h.success,
            "error": h.error,
            "processing_time_ms": h.processing_time_ms,
        }
        for h in history
    ]


# ============================================================================
# Meridian Endpoints
# ============================================================================

@app.get("/meridians")
async def list_meridians():
    """List all meridians and their status."""
    meridians = []
    for meridian_id, meridian in MeridianSystem._meridians.items():
        meridians.append({
            "meridian_id": meridian_id,
            "name": meridian.name,
            "flow_type": meridian.flow_type.value,
            "connected_nodes": len(meridian.nodes),
            "metrics": meridian.get_metrics(),
        })
    return meridians


@app.get("/meridians/{meridian_id}/metrics")
async def get_meridian_metrics(
    meridian_id: str,
    hours: int = 24
):
    """Get metrics for a meridian over time."""
    if not db:
        raise HTTPException(status_code=503, detail="Database not connected")

    end_time = datetime.now()
    start_time = end_time - timedelta(hours=hours)

    metrics = await db.get_meridian_metrics(meridian_id, start_time, end_time)

    return [
        {
            "timestamp": m.timestamp.isoformat(),
            "packets_sent": m.packets_sent,
            "packets_received": m.packets_received,
            "queue_size": m.queue_size,
            "latency_ms": m.latency_ms,
            "error_rate": m.error_rate,
        }
        for m in metrics
    ]


# ============================================================================
# Data Lifecycle Endpoints
# ============================================================================

@app.get("/data/lineage/{data_id}")
async def get_data_lineage(data_id: str):
    """Get lineage information for a data item."""
    if not db:
        raise HTTPException(status_code=503, detail="Database not connected")

    lineage = await db.get_data_lineage(data_id)
    if not lineage:
        raise HTTPException(status_code=404, detail=f"Data {data_id} not found")

    return {
        "data_id": lineage.data_id,
        "source": lineage.source,
        "source_type": lineage.source_type,
        "created_at": lineage.created_at.isoformat(),
        "current_tier": lineage.current_tier.value,
        "quality_score": lineage.quality_score,
        "dependencies": lineage.dependencies,
        "consumers": lineage.consumers,
    }


@app.post("/data/tier")
async def update_data_tier(request: DataTierRequest):
    """Update the storage tier of a data item."""
    if not db:
        raise HTTPException(status_code=503, detail="Database not connected")

    try:
        tier = DataTier(request.target_tier)
        await db.update_data_tier(request.data_id, tier)
        return {
            "success": True,
            "data_id": request.data_id,
            "new_tier": tier.value
        }
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid tier: {request.target_tier}")


@app.get("/data/alerts")
async def get_data_alerts(limit: int = 10):
    """Get recent data flow alerts."""
    if not p4_agent:
        raise HTTPException(status_code=503, detail="P4 Data Agent not running")

    return p4_agent.flow_monitor.get_recent_alerts(limit)


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Run the API server."""
    import uvicorn

    host = os.getenv("LIVING_HOST", "0.0.0.0")
    port = int(os.getenv("LIVING_PORT", "8888"))

    uvicorn.run(
        "open_notebook.skills.living.api_server:app",
        host=host,
        port=port,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    main()
