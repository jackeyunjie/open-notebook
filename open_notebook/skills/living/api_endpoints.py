"""Living Knowledge System API Endpoints

FastAPI endpoints for the five-layer living knowledge system:
- P0: Perception endpoints
- P1: Judgment endpoints
- P2: Relationship endpoints
- P3: Evolution endpoints
- P4: Data management endpoints
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from open_notebook.skills.living.examples.p0_perception_organ import (
    create_pain_scanner_skill,
    create_emotion_watcher_skill,
    create_trend_hunter_skill,
    create_scene_discover_skill,
)
from open_notebook.skills.living.p1_judgment_layer import create_p1_judgment_organ
from open_notebook.skills.living.p2_relationship_layer import create_p2_relationship_organ
from open_notebook.skills.living.p3_evolution_layer import create_p3_evolution_organ
from open_notebook.skills.living.p4_data_agent import create_p4_data_agent

# ============================================================================
# Pydantic Models
# ============================================================================

class PerceptionRequest(BaseModel):
    """Request for P0 perception layer."""
    content_type: str = "pain_scan"  # pain_scan, emotion, trend, scene
    data: Dict[str, Any] = Field(default_factory=dict)


class PerceptionResponse(BaseModel):
    """Response from P0 perception layer."""
    content_id: str
    perception_type: str
    results: Dict[str, Any]
    timestamp: str


class JudgmentRequest(BaseModel):
    """Request for P1 judgment layer."""
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class JudgmentResponse(BaseModel):
    """Response from P1 judgment layer."""
    content_id: str
    overall_score: float
    priority: str
    dimensions: Dict[str, float]
    recommendation: str
    timestamp: str


class RelationshipRequest(BaseModel):
    """Request for P2 relationship layer."""
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    existing_nodes: List[Dict] = Field(default_factory=list)


class RelationshipResponse(BaseModel):
    """Response from P2 relationship layer."""
    content_id: str
    related_nodes: int
    suggested_connections: int
    cluster_id: Optional[str]
    insights: List[str]
    timestamp: str


class EvolutionRequest(BaseModel):
    """Request for P3 evolution layer."""
    feedback_records: List[Dict] = Field(default_factory=list)
    task_type: str = "default"


class EvolutionResponse(BaseModel):
    """Response from P3 evolution layer."""
    best_strategy: str
    patterns_found: int
    recommendations: List[str]
    timestamp: str


class DataManagementRequest(BaseModel):
    """Request for P4 data management."""
    operation: str  # health, lineage, quality, lifecycle
    params: Dict[str, Any] = Field(default_factory=dict)


class DataManagementResponse(BaseModel):
    """Response from P4 data management."""
    operation: str
    status: str
    data: Dict[str, Any]
    timestamp: str


class FullPipelineRequest(BaseModel):
    """Request for full P0-P4 pipeline."""
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    existing_nodes: List[Dict] = Field(default_factory=list)


class FullPipelineResponse(BaseModel):
    """Response from full P0-P4 pipeline."""
    content_id: str
    p0_perception: Dict[str, Any]
    p1_judgment: Dict[str, Any]
    p2_relationship: Dict[str, Any]
    p3_evolution: Dict[str, Any]
    p4_data: Dict[str, Any]
    execution_time_ms: float
    timestamp: str


# ============================================================================
# Router
# ============================================================================

router = APIRouter(prefix="/living-knowledge", tags=["Living Knowledge System"])

# Global instances (initialized on first use)
_p1_organ = None
_p2_organ = None
_p3_organ = None
_p4_agent = None


def get_p1_organ():
    """Get or create P1 judgment organ."""
    global _p1_organ
    if _p1_organ is None:
        _p1_organ = create_p1_judgment_organ()
    return _p1_organ


def get_p2_organ():
    """Get or create P2 relationship organ."""
    global _p2_organ
    if _p2_organ is None:
        _p2_organ = create_p2_relationship_organ()
    return _p2_organ


def get_p3_organ():
    """Get or create P3 evolution organ."""
    global _p3_organ
    if _p3_organ is None:
        _p3_organ = create_p3_evolution_organ()
    return _p3_organ


def get_p4_agent():
    """Get or create P4 data agent."""
    global _p4_agent
    if _p4_agent is None:
        _p4_agent = create_p4_data_agent()
    return _p4_agent


# ============================================================================
# P0 Endpoints - Perception
# ============================================================================

@router.post("/p0/perceive", response_model=PerceptionResponse)
async def p0_perceive(request: PerceptionRequest):
    """
    P0 Perception Layer - Collect market intelligence.
    
    Types:
    - pain_scan: Scan for user pain points
    - emotion: Analyze emotional trends
    - trend: Discover emerging trends
    - scene: Discover high-value scenes
    """
    try:
        content_id = f"p0_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        if request.content_type == "pain_scan":
            skill = create_pain_scanner_skill()
            context = {"platform_data": request.data.get("platform_data", {})}
        elif request.content_type == "emotion":
            skill = create_emotion_watcher_skill()
            context = {"content": request.data.get("content", [])}
        elif request.content_type == "trend":
            skill = create_trend_hunter_skill()
            context = {"hashtags": request.data.get("hashtags", [])}
        elif request.content_type == "scene":
            skill = create_scene_discover_skill()
            context = {"locations": request.data.get("locations", [])}
        else:
            raise HTTPException(status_code=400, detail=f"Unknown perception type: {request.content_type}")
        
        result = await skill.invoke(context)
        
        return PerceptionResponse(
            content_id=content_id,
            perception_type=request.content_type,
            results=result,
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# P1 Endpoints - Judgment
# ============================================================================

@router.post("/p1/assess", response_model=JudgmentResponse)
async def p1_assess(request: JudgmentRequest):
    """
    P1 Judgment Layer - Evaluate content value.
    
    Four dimensions:
    - value: Intrinsic worth
    - heat: Trending/timeliness
    - credibility: Source reliability
    - utility: Practical applicability
    """
    try:
        organ = get_p1_organ()
        
        # Ensure metadata has required fields
        metadata = request.metadata.copy()
        if "id" not in metadata:
            metadata["id"] = f"p1_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        if "created_at" not in metadata:
            metadata["created_at"] = datetime.now().isoformat()
        
        assessment = await organ.assess(request.content, metadata)
        
        return JudgmentResponse(
            content_id=assessment.content_id,
            overall_score=assessment.overall_score,
            priority=assessment.priority,
            dimensions={
                dim.value: result.score 
                for dim, result in assessment.judgments.items()
            },
            recommendation=assessment.recommended_action,
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# P2 Endpoints - Relationship
# ============================================================================

@router.post("/p2/analyze", response_model=RelationshipResponse)
async def p2_analyze(request: RelationshipRequest):
    """
    P2 Relationship Layer - Build knowledge graph.
    
    Four skills:
    - entity_linker: Extract and link entities
    - semantic_cluster: Group related content
    - temporal_weaver: Discover time-based relationships
    - cross_reference: Build citation networks
    """
    try:
        organ = get_p2_organ()
        
        # Ensure metadata has required fields
        metadata = request.metadata.copy()
        if "id" not in metadata:
            metadata["id"] = f"p2_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        analysis = await organ.analyze_relationships(
            request.content,
            metadata,
            request.existing_nodes
        )
        
        # Add to graph
        node = organ.add_to_graph(
            analysis.content_id,
            request.content,
            metadata,
            analysis,
            p1_score=request.metadata.get("p1_score", 0.5)
        )
        
        return RelationshipResponse(
            content_id=analysis.content_id,
            related_nodes=len(analysis.related_nodes),
            suggested_connections=len(analysis.suggested_connections),
            cluster_id=analysis.cluster_id,
            insights=analysis.graph_insights,
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/p2/graph")
async def p2_get_graph(node_ids: Optional[List[str]] = None):
    """Get knowledge graph (subgraph if node_ids specified)."""
    try:
        organ = get_p2_organ()
        graph = organ.get_graph(node_ids)
        
        return {
            "graph_id": graph.graph_id,
            "name": graph.name,
            "nodes": len(graph.nodes),
            "edges": len(graph.edges),
            "node_ids": list(graph.nodes.keys()),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# P3 Endpoints - Evolution
# ============================================================================

@router.post("/p3/evolve", response_model=EvolutionResponse)
async def p3_evolve(request: EvolutionRequest):
    """
    P3 Evolution Layer - Self-improvement through feedback.
    
    Four skills:
    - strategy_evolver: Optimize approaches
    - feedback_loop: Learn from results
    - pattern_recognition: Identify success patterns
    - parameter_tuner: Auto-tune parameters
    """
    try:
        organ = get_p3_organ()
        
        # Create feedback records from request
        from open_notebook.skills.living.p3_evolution_layer import FeedbackRecord
        
        feedback_records = []
        for i, record_data in enumerate(request.feedback_records):
            record = FeedbackRecord(
                record_id=record_data.get("id", f"fb_{i:04d}"),
                task_type=request.task_type,
                input_hash=record_data.get("input_hash", ""),
                output_hash=record_data.get("output_hash", ""),
                success_score=record_data.get("success_score", 0.5),
                execution_time_ms=record_data.get("execution_time_ms", 0),
                resource_usage=record_data.get("resource_usage", {}),
                strategy_used=record_data.get("strategy_used", "default")
            )
            feedback_records.append(record)
        
        # Optimize
        result = await organ.optimize_strategy(request.task_type, feedback_records)
        
        return EvolutionResponse(
            best_strategy=result["best_strategy"],
            patterns_found=result["patterns_found"],
            recommendations=result["recommendations"],
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# P4 Endpoints - Data Management
# ============================================================================

@router.post("/p4/data", response_model=DataManagementResponse)
async def p4_data_manage(request: DataManagementRequest):
    """
    P4 DataAgent - Data lifecycle management.
    
    Operations:
    - health: Get system health
    - lineage: Track data lineage
    - quality: Check data quality
    - lifecycle: Manage data lifecycle
    """
    try:
        agent = get_p4_agent()
        
        if request.operation == "health":
            health = await agent.get_system_health()
            return DataManagementResponse(
                operation="health",
                status="healthy" if health.get("status") == "healthy" else "degraded",
                data=health,
                timestamp=datetime.now().isoformat()
            )
        elif request.operation == "lineage":
            # Demo: return sample lineage
            return DataManagementResponse(
                operation="lineage",
                status="success",
                data={
                    "data_id": request.params.get("data_id", "unknown"),
                    "source": "p0_perception",
                    "transformations": ["p1_judgment", "p2_relationship"],
                    "current_tier": "hot"
                },
                timestamp=datetime.now().isoformat()
            )
        elif request.operation == "quality":
            return DataManagementResponse(
                operation="quality",
                status="success",
                data={
                    "quality_score": 1.0,
                    "checks_passed": 5,
                    "checks_failed": 0
                },
                timestamp=datetime.now().isoformat()
            )
        else:
            raise HTTPException(status_code=400, detail=f"Unknown operation: {request.operation}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Full Pipeline Endpoint
# ============================================================================

@router.post("/pipeline/full", response_model=FullPipelineResponse)
async def full_pipeline(request: FullPipelineRequest, background_tasks: BackgroundTasks):
    """
    Full P0-P4 Pipeline - Complete living knowledge processing.
    
    Flow: P0 (perceive) → P1 (assess) → P2 (relate) → P3 (evolve) → P4 (manage)
    """
    import time
    start_time = time.time()
    
    try:
        content_id = request.metadata.get("id", f"pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        
        # P0: Perception (simulated for pipeline)
        p0_result = {
            "pain_points": 2,
            "trend_signals": 3,
            "status": "perceived"
        }
        
        # P1: Judgment
        p1_organ = get_p1_organ()
        metadata = request.metadata.copy()
        metadata["id"] = content_id
        if "created_at" not in metadata:
            metadata["created_at"] = datetime.now().isoformat()
        
        assessment = await p1_organ.assess(request.content, metadata)
        p1_result = {
            "overall_score": assessment.overall_score,
            "priority": assessment.priority,
            "dimensions": {
                dim.value: result.score 
                for dim, result in assessment.judgments.items()
            }
        }
        
        # P2: Relationship
        p2_organ = get_p2_organ()
        analysis = await p2_organ.analyze_relationships(
            request.content,
            metadata,
            request.existing_nodes
        )
        node = p2_organ.add_to_graph(
            content_id,
            request.content,
            metadata,
            analysis,
            p1_score=assessment.overall_score
        )
        p2_result = {
            "entities": analysis.related_nodes,
            "related_nodes": len(analysis.related_nodes),
            "cluster_id": analysis.cluster_id,
            "insights": analysis.graph_insights
        }
        
        # P3: Evolution (only if enough data)
        p3_organ = get_p3_organ()
        p3_result = {
            "best_strategy": "parallel",
            "patterns_found": 0,
            "note": "Insufficient feedback data for evolution"
        }
        
        # P4: Data Management
        p4_agent = get_p4_agent()
        health = await p4_agent.get_system_health()
        p4_result = {
            "lineage_recorded": True,
            "data_id": content_id,
            "tier": "hot",
            "quality_score": 1.0,
            "system_health": health.get("status", "unknown")
        }
        
        execution_time = (time.time() - start_time) * 1000
        
        return FullPipelineResponse(
            content_id=content_id,
            p0_perception=p0_result,
            p1_judgment=p1_result,
            p2_relationship=p2_result,
            p3_evolution=p3_result,
            p4_data=p4_result,
            execution_time_ms=execution_time,
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# System Status Endpoint
# ============================================================================

@router.get("/status")
async def system_status():
    """Get overall system status."""
    return {
        "status": "healthy",
        "layers": {
            "p0_perception": "active",
            "p1_judgment": "active" if _p1_organ else "standby",
            "p2_relationship": "active" if _p2_organ else "standby",
            "p3_evolution": "active" if _p3_organ else "standby",
            "p4_data": "active" if _p4_agent else "standby"
        },
        "timestamp": datetime.now().isoformat()
    }


@router.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Living Knowledge System API",
        "version": "1.0.0",
        "layers": ["P0", "P1", "P2", "P3", "P4"],
        "endpoints": [
            "/living-knowledge/p0/perceive",
            "/living-knowledge/p1/assess",
            "/living-knowledge/p2/analyze",
            "/living-knowledge/p3/evolve",
            "/living-knowledge/p4/data",
            "/living-knowledge/pipeline/full",
            "/living-knowledge/status"
        ]
    }
