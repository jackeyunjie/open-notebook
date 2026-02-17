"""API Router for P3 Evolution Layer.

Provides endpoints to control and monitor the P3 evolution system,
including triggering evolution cycles and viewing evolution reports.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from open_notebook.skills import (
    p3_evolution_scheduler,
    evolution_orchestrator,
    initialize_p3_evolution,
    run_evolution_cycle,
    EvolutionScheduleType,
    EvolutionType,
)

router = APIRouter(prefix="/p3-evolution", tags=["P3 Evolution Layer"])


# ============================================================================
# Pydantic Models
# ============================================================================

class EvolutionConfigRequest(BaseModel):
    """Request to update evolution configuration."""
    schedule_type: str = Field(default="daily", description="daily, weekly, feedback, or manual")
    run_time: str = Field(default="02:00", description="Time to run (HH:MM)")
    feedback_threshold: int = Field(default=50, description="Feedback count threshold")
    enable_auto_deploy: bool = Field(default=False, description="Auto-deploy evolved strategies")
    min_fitness_for_deploy: float = Field(default=0.7, ge=0.0, le=1.0)
    max_generations_per_run: int = Field(default=5, ge=1, le=20)


class EvolutionTriggerResponse(BaseModel):
    """Response from triggering evolution."""
    execution_id: str
    status: str
    message: str


class EvolutionStatusResponse(BaseModel):
    """Response with evolution system status."""
    running: bool
    schedule_type: str
    config: Dict[str, Any]
    total_executions: int
    recent_executions: List[Dict[str, Any]]
    evolution_summary: Optional[Dict[str, Any]]


class EvolutionReportResponse(BaseModel):
    """Response with evolution report."""
    report_id: str
    generated_at: str
    generation: int
    strategies_evaluated: int
    strategies_selected: int
    fitness_improvement: float
    key_mutations: List[str]
    deployment_recommendations: List[Dict[str, Any]]
    meta_learnings: List[str]


class StrategyPopulationResponse(BaseModel):
    """Response with strategy population info."""
    agent_type: str
    quadrant: str
    generation: int
    population_size: int
    best_strategy: Optional[Dict[str, Any]]
    average_fitness: float


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/initialize", summary="Initialize P3 Evolution System")
async def initialize_p3():
    """Initialize the P3 evolution layer and create strategy populations."""
    try:
        orchestrator = initialize_p3_evolution()
        return {
            "status": "initialized",
            "populations": len(orchestrator.populations),
            "message": "P3 Evolution Layer initialized successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/start", summary="Start P3 Evolution Scheduler")
async def start_scheduler(config: Optional[EvolutionConfigRequest] = None):
    """Start the automated P3 evolution scheduler."""
    try:
        if config:
            p3_evolution_scheduler.update_config(**config.dict())

        await p3_evolution_scheduler.start()
        return {
            "status": "started",
            "schedule_type": p3_evolution_scheduler.config.schedule_type.value,
            "message": "P3 Evolution Scheduler started"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop", summary="Stop P3 Evolution Scheduler")
async def stop_scheduler():
    """Stop the P3 evolution scheduler."""
    try:
        await p3_evolution_scheduler.stop()
        return {
            "status": "stopped",
            "message": "P3 Evolution Scheduler stopped"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trigger", response_model=EvolutionTriggerResponse, summary="Trigger Manual Evolution")
async def trigger_evolution(background_tasks: BackgroundTasks):
    """Manually trigger an evolution cycle."""
    try:
        execution_id = p3_evolution_scheduler.trigger_manual_evolution()
        return EvolutionTriggerResponse(
            execution_id=execution_id,
            status="triggered",
            message="Evolution cycle started in background"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status", response_model=EvolutionStatusResponse, summary="Get P3 Status")
async def get_status():
    """Get current status of the P3 evolution system."""
    try:
        status = p3_evolution_scheduler.get_status()
        return EvolutionStatusResponse(**status)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/config", summary="Update P3 Configuration")
async def update_config(config: EvolutionConfigRequest):
    """Update P3 evolution scheduler configuration."""
    try:
        p3_evolution_scheduler.update_config(**config.dict())
        return {
            "status": "updated",
            "config": p3_evolution_scheduler.config.to_dict()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/populations", summary="List Strategy Populations")
async def list_populations():
    """List all strategy populations and their status."""
    try:
        populations = []
        for key, pop in evolution_orchestrator.populations.items():
            best = pop.get_best_strategy()
            avg_fitness = sum(s.fitness_score for s in pop.strategies) / len(pop.strategies) if pop.strategies else 0

            populations.append({
                "key": key,
                "agent_type": pop.agent_type,
                "quadrant": pop.quadrant,
                "generation": pop.generation,
                "population_size": len(pop.strategies),
                "best_fitness": best.fitness_score if best else 0,
                "average_fitness": avg_fitness
            })

        return {"populations": populations}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/populations/{population_key}", response_model=StrategyPopulationResponse, summary="Get Population Details")
async def get_population(population_key: str):
    """Get detailed information about a specific strategy population."""
    try:
        if population_key not in evolution_orchestrator.populations:
            raise HTTPException(status_code=404, detail=f"Population {population_key} not found")

        pop = evolution_orchestrator.populations[population_key]
        best = pop.get_best_strategy()
        avg_fitness = sum(s.fitness_score for s in pop.strategies) / len(pop.strategies) if pop.strategies else 0

        return StrategyPopulationResponse(
            agent_type=pop.agent_type,
            quadrant=pop.quadrant,
            generation=pop.generation,
            population_size=len(pop.strategies),
            best_strategy=best.to_dict() if best else None,
            average_fitness=avg_fitness
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/populations/{population_key}/evolve", summary="Evolve Specific Population")
async def evolve_population(population_key: str, generations: int = 1):
    """Manually trigger evolution for a specific population."""
    try:
        if population_key not in evolution_orchestrator.populations:
            raise HTTPException(status_code=404, detail=f"Population {population_key} not found")

        pop = evolution_orchestrator.populations[population_key]

        for _ in range(generations):
            pop.evaluate_fitness(evolution_orchestrator.feedback_orchestrator)
            pop.evolve_generation()

        best = pop.get_best_strategy()
        return {
            "status": "evolved",
            "population": population_key,
            "new_generation": pop.generation,
            "best_fitness": best.fitness_score if best else 0
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reports/latest", response_model=Optional[EvolutionReportResponse], summary="Get Latest Report")
async def get_latest_report():
    """Get the most recent evolution report."""
    try:
        from open_notebook.skills.p0_orchestrator import SharedMemory
        sm = SharedMemory()

        # Find latest report
        reports = []
        # This is a simplified search - in production would use proper indexing
        # For now, return mock/latest from history

        if evolution_orchestrator.execution_history:
            latest = evolution_orchestrator.execution_history[-1]
            if latest.report:
                return EvolutionReportResponse(**latest.report)

        return None
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/meta-learnings", summary="Get Meta-Learnings")
async def get_meta_learnings():
    """Get accumulated meta-learnings from the evolution system."""
    try:
        learnings = evolution_orchestrator.meta_engine.get_meta_learnings()
        return {
            "meta_learnings": learnings,
            "meta_parameters": evolution_orchestrator.meta_engine.meta_parameters
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/deploy", summary="Deploy Evolved Strategies")
async def deploy_strategies(min_fitness: float = 0.7):
    """Deploy evolved strategies that meet fitness threshold."""
    try:
        from open_notebook.skills.p3_evolution import EvolutionReport

        # Create a report with current recommendations
        recommendations = []
        for key, pop in evolution_orchestrator.populations.items():
            best = pop.get_best_strategy()
            if best and best.fitness_score >= min_fitness:
                recommendations.append({
                    "agent": key,
                    "strategy_id": best.strategy_id,
                    "fitness": best.fitness_score,
                    "parameters": {g.parameter: g.value for g in best.genes},
                    "confidence": "high" if best.fitness_score > 0.8 else "medium"
                })

        # Create temporary report for deployment
        report = EvolutionReport(
            report_id=f"manual_deploy_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            generated_at=datetime.utcnow(),
            evolution_type=EvolutionType.STRATEGY_EVOLUTION,
            generation=evolution_orchestrator.evolution_generation,
            strategies_evaluated=len(evolution_orchestrator.populations),
            strategies_selected=len(recommendations),
            fitness_improvement=0.0,
            key_mutations=[],
            deployment_recommendations=recommendations,
            meta_learnings=[]
        )

        deployed = evolution_orchestrator.deploy_evolved_strategies(report)

        return {
            "status": "deployed",
            "strategies_deployed": deployed,
            "recommendations": recommendations
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/memory", summary="Get Long-Term Memory")
async def get_long_term_memory():
    """Get consolidated long-term memory from P3."""
    try:
        memories = evolution_orchestrator.long_term_memory.memory_chunks[-10:]
        knowledge = evolution_orchestrator.long_term_memory.compress_knowledge()

        return {
            "memory_chunks": len(evolution_orchestrator.long_term_memory.memory_chunks),
            "recent_memories": memories,
            "compressed_knowledge": knowledge
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/memory/consolidate", summary="Consolidate Memories")
async def consolidate_memories(days: int = 7):
    """Manually trigger memory consolidation."""
    try:
        evolution_orchestrator.long_term_memory.consolidate_memories(days=days)
        return {
            "status": "consolidated",
            "period_days": days,
            "memory_chunks": len(evolution_orchestrator.long_term_memory.memory_chunks)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
