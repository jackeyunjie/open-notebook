"""API Router for P0 Daily Sync Scheduler management.

Provides endpoints for:
- Starting/stopping the scheduler
- Checking scheduler status
- Viewing execution history
- Manual sync triggers
- Health monitoring
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from open_notebook.skills import (
    P0SyncScheduler,
    P0ScheduleConfig,
    SyncStatus,
    p0_sync_scheduler,
    setup_default_p0_schedule,
)
from open_notebook.skills.runner import get_skill_runner

router = APIRouter(prefix="/p0-scheduler", tags=["P0 Scheduler"])


# =============================================================================
# Pydantic Models
# =============================================================================

class ScheduleConfigRequest(BaseModel):
    """Request model for configuring P0 sync schedule."""
    sync_time: str = Field(default="06:00", description="Daily sync time in HH:MM format")
    timezone: str = Field(default="UTC", description="Timezone for scheduling")
    max_retries: int = Field(default=3, ge=0, le=10, description="Max retry attempts")
    retry_delay_minutes: int = Field(default=30, ge=5, le=120)
    timeout_minutes: int = Field(default=30, ge=10, le=120)
    target_notebook_id: str = Field(default="", description="Notebook for sync reports")
    agents_to_run: List[str] = Field(
        default=["Q1P0", "Q2P0", "Q3P0", "Q4P0"],
        description="Which P0 agents to run"
    )


class CronScheduleRequest(BaseModel):
    """Request model for cron-based scheduling."""
    cron_expression: str = Field(
        default="0 6 * * *",
        description="Cron expression (min hour day month day_of_week)"
    )
    timezone: str = Field(default="UTC")
    target_notebook_id: str = Field(default="")


class SchedulerStatusResponse(BaseModel):
    """Response model for scheduler status."""
    running: bool
    health_status: str  # healthy, warning, critical, stopped, unknown
    schedule_config: Optional[Dict[str, Any]]
    next_run_time: Optional[str]
    last_execution: Optional[Dict[str, Any]]
    current_execution: Optional[Dict[str, Any]]
    execution_history_count: int
    last_successful_sync: Optional[str]


class ExecutionHistoryResponse(BaseModel):
    """Response model for execution history."""
    executions: List[Dict[str, Any]]
    total_count: int


class HealthMetricsResponse(BaseModel):
    """Response model for health metrics."""
    total_executions: int
    successful: int
    failed: int
    success_rate_percent: float
    average_duration_seconds: float
    average_signals_generated: float
    last_24h_executions: int


class TriggerSyncResponse(BaseModel):
    """Response model for manual sync trigger."""
    success: bool
    execution_id: Optional[str]
    message: str
    result: Optional[Dict[str, Any]]


# =============================================================================
# API Endpoints
# =============================================================================

@router.post("/start", response_model=Dict[str, Any])
async def start_scheduler(config: ScheduleConfigRequest):
    """Start the P0 Daily Sync scheduler with simple time configuration.

    Example:
        POST /p0-scheduler/start
        {
            "sync_time": "06:00",
            "timezone": "Asia/Shanghai",
            "max_retries": 3,
            "target_notebook_id": "notebook:abc123"
        }
    """
    try:
        runner = get_skill_runner()

        schedule_config = P0ScheduleConfig.from_simple_time(
            time_str=config.sync_time,
            timezone=config.timezone,
            max_retries=config.max_retries,
            retry_delay_minutes=config.retry_delay_minutes,
            timeout_minutes=config.timeout_minutes,
            target_notebook_id=config.target_notebook_id,
            agents_to_run=config.agents_to_run
        )

        success = await p0_sync_scheduler.start_with_config(runner, schedule_config)

        if success:
            return {
                "success": True,
                "message": f"P0 Daily Sync scheduler started",
                "schedule": {
                    "sync_time": config.sync_time,
                    "timezone": config.timezone,
                    "agents": config.agents_to_run
                }
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to start scheduler")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting scheduler: {str(e)}")


@router.post("/start/cron", response_model=Dict[str, Any])
async def start_scheduler_cron(config: CronScheduleRequest):
    """Start the P0 Daily Sync scheduler with cron expression.

    Example:
        POST /p0-scheduler/start/cron
        {
            "cron_expression": "0 */6 * * *",
            "timezone": "UTC"
        }
    """
    try:
        runner = get_skill_runner()

        schedule_config = P0ScheduleConfig(
            cron_expression=config.cron_expression,
            timezone=config.timezone,
            target_notebook_id=config.target_notebook_id
        )

        success = await p0_sync_scheduler.start_with_config(runner, schedule_config)

        if success:
            return {
                "success": True,
                "message": "P0 Daily Sync scheduler started with cron",
                "cron_expression": config.cron_expression,
                "timezone": config.timezone
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to start scheduler")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting scheduler: {str(e)}")


@router.post("/stop", response_model=Dict[str, Any])
async def stop_scheduler():
    """Stop the P0 Daily Sync scheduler."""
    try:
        await p0_sync_scheduler.stop()
        return {
            "success": True,
            "message": "P0 Daily Sync scheduler stopped"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error stopping scheduler: {str(e)}")


@router.get("/status", response_model=SchedulerStatusResponse)
async def get_scheduler_status():
    """Get current scheduler status and next run time."""
    try:
        status = p0_sync_scheduler.get_status()
        return SchedulerStatusResponse(**status)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting status: {str(e)}")


@router.post("/trigger", response_model=TriggerSyncResponse)
async def trigger_sync_now():
    """Manually trigger a P0 Daily Sync immediately."""
    try:
        result = await p0_sync_scheduler.trigger_sync_now()

        if result:
            return TriggerSyncResponse(
                success=True,
                execution_id=result.get("session_id"),
                message="P0 Daily Sync triggered successfully",
                result=result
            )
        else:
            return TriggerSyncResponse(
                success=False,
                execution_id=None,
                message="Failed to trigger sync",
                result=None
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error triggering sync: {str(e)}")


@router.get("/history", response_model=ExecutionHistoryResponse)
async def get_execution_history(
    limit: int = 10,
    status: Optional[str] = None
):
    """Get execution history with optional filtering.

    Args:
        limit: Maximum number of records to return (default 10)
        status: Filter by status (pending, running, success, failed, retrying)
    """
    try:
        status_filter = None
        if status:
            try:
                status_filter = SyncStatus(status)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")

        history = p0_sync_scheduler.get_execution_history(
            limit=limit,
            status_filter=status_filter
        )

        return ExecutionHistoryResponse(
            executions=history,
            total_count=len(history)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting history: {str(e)}")


@router.get("/health", response_model=HealthMetricsResponse)
async def get_health_metrics():
    """Get health metrics for monitoring sync performance."""
    try:
        metrics = p0_sync_scheduler.get_health_metrics()
        return HealthMetricsResponse(**metrics)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting metrics: {str(e)}")


@router.patch("/schedule", response_model=Dict[str, Any])
async def update_schedule(sync_time: str):
    """Update the daily sync schedule to a new time.

    Args:
        sync_time: New time in HH:MM format (e.g., "08:00")
    """
    try:
        success = await p0_sync_scheduler.update_schedule(sync_time)

        if success:
            return {
                "success": True,
                "message": f"Schedule updated to {sync_time}"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to update schedule")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating schedule: {str(e)}")


@router.get("/signals/active", response_model=List[Dict[str, Any]])
async def get_active_signals(hours: int = 24):
    """Get active signals from SharedMemory.

    Args:
        hours: How many hours back to look (default 24)
    """
    try:
        from open_notebook.skills.p0_orchestrator import SharedMemory

        memory = SharedMemory()
        signals = memory.get_recent_signals(hours=hours)
        return signals

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting signals: {str(e)}")
