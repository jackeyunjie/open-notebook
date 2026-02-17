"""Unified Open Notebook + Living Knowledge System API.

Merges the main API (port 5055) and LKS API (port 8888) into a single
FastAPI application running on a unified port.

Architecture:
- Main API routes: /api/* (existing)
- LKS API routes: /api/living/* (new prefix)
- Health checks: /health, /api/living/health
- Documentation: /docs (combined)
"""

# Load environment variables
from dotenv import load_dotenv

load_dotenv()

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
from starlette.exceptions import HTTPException as StarletteHTTPException

# Import main API routers
from api.auth import PasswordAuthMiddleware
from api.routers import (
    auth,
    chat,
    commands as commands_router,
    config,
    context,
    credentials,
    embedding,
    embedding_rebuild,
    episode_profiles,
    insights,
    models,
    notebooks,
    notes,
    p0_scheduler,
    p3_evolution,
    personal_ip,
    platform_accounts,
    podcasts,
    publish,
    search,
    settings,
    skills,
    source_chat,
    sources,
    speaker_profiles,
    transformations,
    workflow_builder,
    workflow_templates,
    workflows,
)
import api.routers.skills as skills_module

# Import LKS API
from open_notebook.skills.living.api_endpoints import router as living_router
from open_notebook.skills.living.database.postgresql import PostgreSQLDatabase

# Import sync system
from open_notebook.database import initialize_sync_system, shutdown_sync_system
from open_notebook.database.async_migrate import AsyncMigrationManager
from open_notebook.utils.encryption import get_secret_from_env


@asynccontextmanager
async def unified_lifespan(app: FastAPI):
    """
    Unified lifespan event handler for the combined FastAPI application.
    Handles initialization of both main system and LKS.
    """
    import os

    # ==================== STARTUP ====================
    logger.info("Starting Unified API initialization...")

    # 1. Security checks
    if not get_secret_from_env("OPEN_NOTEBOOK_ENCRYPTION_KEY"):
        logger.warning(
            "OPEN_NOTEBOOK_ENCRYPTION_KEY not set. "
            "API key encryption will fail until this is configured."
        )

    # 2. Run SurrealDB migrations
    try:
        migration_manager = AsyncMigrationManager()
        current_version = await migration_manager.get_current_version()
        logger.info(f"SurrealDB current version: {current_version}")

        if await migration_manager.needs_migration():
            logger.warning("SurrealDB migrations pending. Running...")
            await migration_manager.run_migration_up()
            new_version = await migration_manager.get_current_version()
            logger.success(f"SurrealDB migrations completed. Version: {new_version}")
    except Exception as e:
        logger.error(f"CRITICAL: SurrealDB migration failed: {e}")
        raise RuntimeError(f"Failed to run SurrealDB migrations: {e}") from e

    # 3. Initialize PostgreSQL (LKS)
    db_postgres: PostgreSQLDatabase = None
    try:
        db_postgres = PostgreSQLDatabase(
            host=os.getenv("LIVING_DB_HOST", "localhost"),
            port=int(os.getenv("LIVING_DB_PORT", "5433")),
            database=os.getenv("LIVING_DB_NAME", "living_system"),
            user=os.getenv("LIVING_DB_USER", "living"),
            password=os.getenv("LIVING_DB_PASSWORD", "living"),
        )
        await db_postgres.connect()
        logger.success("PostgreSQL (LKS) connected")
        
        # Store in app state for access in routes
        app.state.living_db = db_postgres
    except Exception as e:
        logger.error(f"Failed to connect to PostgreSQL: {e}")
        logger.warning("LKS features will be unavailable")
        app.state.living_db = None

    # 4. Initialize sync system (cross-domain synchronization)
    try:
        sync_system = await initialize_sync_system()
        app.state.sync_system = sync_system
        logger.success("Cross-domain sync system initialized")
    except Exception as e:
        logger.error(f"Failed to initialize sync system: {e}")
        logger.warning("Cross-domain sync will be unavailable")
        app.state.sync_system = None

    # 5. Initialize AI providers
    try:
        from open_notebook.ai.key_provider import init_all_providers_from_env
        init_results = await init_all_providers_from_env()
        initialized = [p for p, success in init_results.items() if success]
        if initialized:
            logger.success(f"AI providers initialized: {', '.join(initialized)}")
    except Exception as e:
        logger.warning(f"Provider initialization failed: {e}")

    # 6. Initialize Skill Scheduler
    try:
        from open_notebook.skills.scheduler import skill_scheduler
        from open_notebook.skills.runner import SkillRunner
        from open_notebook.workflows.service import WorkflowService
        runner = SkillRunner()
        workflow_service = WorkflowService()
        await skill_scheduler.start(runner, workflow_service)
        scheduled_count = await skill_scheduler.load_schedules_from_database()
        logger.success(f"Skill scheduler started ({scheduled_count} schedules)")
    except Exception as e:
        logger.error(f"Failed to start skill scheduler: {e}")

    # 7. Initialize P0 Daily Sync Scheduler
    try:
        from open_notebook.skills import p0_sync_scheduler, setup_default_p0_schedule
        p0_auto_start = os.getenv("P0_DAILY_SYNC_AUTO_START", "false").lower() == "true"
        if p0_auto_start:
            p0_sync_time = os.getenv("P0_DAILY_SYNC_TIME", "06:00")
            p0_notebook_id = os.getenv("P0_DAILY_SYNC_NOTEBOOK_ID", "")
            runner = SkillRunner()
            await setup_default_p0_schedule(runner, p0_sync_time, p0_notebook_id)
            logger.success(f"P0 Daily Sync auto-started ({p0_sync_time})")
    except Exception as e:
        logger.error(f"Failed to initialize P0 Daily Sync: {e}")

    logger.success("Unified API initialization completed")

    # Yield control to application
    yield

    # ==================== SHUTDOWN ====================
    logger.info("Shutting down Unified API...")

    # Shutdown sync system
    try:
        await shutdown_sync_system()
        logger.info("Sync system shut down")
    except Exception as e:
        logger.error(f"Error shutting down sync system: {e}")

    # Disconnect PostgreSQL
    if db_postgres:
        try:
            await db_postgres.disconnect()
            logger.info("PostgreSQL disconnected")
        except Exception as e:
            logger.error(f"Error disconnecting PostgreSQL: {e}")

    # Shutdown skill scheduler
    try:
        from open_notebook.skills.scheduler import skill_scheduler
        await skill_scheduler.shutdown()
        logger.info("Skill scheduler shut down")
    except Exception as e:
        logger.error(f"Error shutting down skill scheduler: {e}")

    # Shutdown P0 scheduler
    try:
        from open_notebook.skills import p0_sync_scheduler
        await p0_sync_scheduler.stop()
        logger.info("P0 scheduler stopped")
    except Exception as e:
        logger.error(f"Error stopping P0 scheduler: {e}")

    logger.info("Unified API shutdown complete")


# Create unified FastAPI app
app = FastAPI(
    title="Open Notebook + Living Knowledge System API",
    description="""
    Unified API for Open Notebook with integrated Living Knowledge System.
    
    ## Main API (Core)
    - Notebooks, Sources, Notes management
    - Chat, Search, Transformations
    - Skills, Workflows, Podcasts
    
    ## Living Knowledge System (LKS)
    - P0: Perception Layer - Market intelligence
    - P1: Judgment Layer - Value assessment
    - P2: Relationship Layer - Knowledge graphs
    - P3: Evolution Layer - Self-improvement
    - P4: Data Layer - Lifecycle management
    
    ## Authentication
    Most endpoints require authentication via the `/api/auth/login` endpoint.
    """,
    version="2.0.0",
    lifespan=unified_lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add password authentication middleware
app.add_middleware(
    PasswordAuthMiddleware,
    excluded_paths=[
        "/",
        "/health",
        "/docs",
        "/openapi.json",
        "/redoc",
        "/api/auth/status",
        "/api/config",
        "/api/living/health",
    ],
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Custom exception handler for CORS
@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Ensure CORS headers are included in error responses."""
    origin = request.headers.get("origin", "*")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers={
            **(exc.headers or {}),
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        },
    )


# ==================== MAIN API ROUTES ====================
# Core Open Notebook functionality

app.include_router(auth.router, prefix="/api", tags=["auth"])
app.include_router(config.router, prefix="/api", tags=["config"])
app.include_router(notebooks.router, prefix="/api", tags=["notebooks"])
app.include_router(search.router, prefix="/api", tags=["search"])
app.include_router(models.router, prefix="/api", tags=["models"])
app.include_router(transformations.router, prefix="/api", tags=["transformations"])
app.include_router(notes.router, prefix="/api", tags=["notes"])
app.include_router(embedding.router, prefix="/api", tags=["embedding"])
app.include_router(embedding_rebuild.router, prefix="/api/embeddings", tags=["embeddings"])
app.include_router(settings.router, prefix="/api", tags=["settings"])
app.include_router(context.router, prefix="/api", tags=["context"])
app.include_router(sources.router, prefix="/api", tags=["sources"])
app.include_router(insights.router, prefix="/api", tags=["insights"])
app.include_router(commands_router.router, prefix="/api", tags=["commands"])
app.include_router(podcasts.router, prefix="/api", tags=["podcasts"])
app.include_router(episode_profiles.router, prefix="/api", tags=["episode-profiles"])
app.include_router(speaker_profiles.router, prefix="/api", tags=["speaker-profiles"])
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(source_chat.router, prefix="/api", tags=["source-chat"])
app.include_router(credentials.router, prefix="/api", tags=["credentials"])
app.include_router(skills_module.router, prefix="/api", tags=["skills"])
app.include_router(workflows.router, prefix="/api", tags=["workflows"])
app.include_router(workflow_templates.router, prefix="/api", tags=["workflow-templates"])
app.include_router(workflow_builder.router, prefix="/api", tags=["workflow-builder"])
app.include_router(p0_scheduler.router, prefix="/api", tags=["p0-scheduler"])
app.include_router(p3_evolution.router, prefix="/api", tags=["p3-evolution"])
app.include_router(personal_ip.router, prefix="/api", tags=["personal-ip"])
app.include_router(platform_accounts.router, prefix="/api", tags=["platform-accounts"])
app.include_router(publish.router, prefix="/api", tags=["publish"])


# ==================== LKS API ROUTES ====================
# Living Knowledge System - prefixed with /api/living

app.include_router(living_router, prefix="/api/living", tags=["living-knowledge"])


# ==================== ROOT & HEALTH ENDPOINTS ====================

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Open Notebook + Living Knowledge System API",
        "version": "2.0.0",
        "description": "Unified API with integrated LKS",
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "living_health": "/api/living/health",
        }
    }


@app.get("/health")
async def health():
    """Combined health check for all systems."""
    from fastapi import Request
    
    # Get app state (set during lifespan)
    living_db = getattr(app.state, 'living_db', None)
    sync_system = getattr(app.state, 'sync_system', None)
    
    # Check PostgreSQL
    postgres_healthy = False
    if living_db and living_db.pool:
        try:
            health = await living_db.get_system_health()
            postgres_healthy = health.get("status") == "healthy"
        except:
            pass
    
    # Check sync system
    sync_healthy = sync_system is not None and sync_system._initialized
    
    return {
        "status": "healthy",
        "components": {
            "api": "healthy",
            "surrealdb": "healthy",  # If we got here, migrations passed
            "postgresql": "healthy" if postgres_healthy else "degraded",
            "sync_system": "healthy" if sync_healthy else "degraded",
        },
        "timestamp": __import__("datetime").datetime.now().isoformat(),
    }


@app.get("/api/living/health")
async def living_health():
    """LKS-specific health check."""
    living_db = getattr(app.state, 'living_db', None)
    
    if not living_db or not living_db.pool:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unavailable",
                "database": "disconnected",
                "message": "Living Knowledge System is not available"
            }
        )
    
    try:
        health = await living_db.get_system_health()
        return {
            "status": health.get("status", "unknown"),
            "database": "connected",
            "cells": health.get("cells", {}),
            "agents": health.get("agents", {}),
            "triggers_24h": health.get("triggers_24h", {}),
            "timestamp": __import__("datetime").datetime.now().isoformat(),
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "error",
                "database": "error",
                "message": str(e)
            }
        )
