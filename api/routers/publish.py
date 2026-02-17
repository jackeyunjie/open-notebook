"""API Router for Auto-Publish System.

Provides endpoints for publishing content to social media platforms.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from open_notebook.domain.publish_job import (
    ContentAdapter,
    PublishJob,
    PublishQueue,
    PublishStatus,
    publish_queue,
)
from open_notebook.domain.platform_connector import PlatformAccount, ConnectorRegistry

router = APIRouter(prefix="/publish", tags=["Auto Publish"])


# ============================================================================
# Pydantic Models
# ============================================================================

class CreatePublishJobRequest(BaseModel):
    """Request to create a publish job."""
    title: str
    content_text: str
    content_format: str = "text"  # text, image, video, carousel
    target_platforms: List[str]
    media_urls: List[str] = Field(default_factory=list)
    media_captions: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    quadrant: Optional[str] = None
    source_note_id: Optional[str] = None
    calendar_entry_id: Optional[str] = None


class SchedulePublishRequest(BaseModel):
    """Request to schedule a publish job."""
    scheduled_at: datetime


class PublishResponse(BaseModel):
    """Response with publish job details."""
    job_id: str
    status: str
    message: str


class PlatformVariantResponse(BaseModel):
    """Response with platform-specific content variants."""
    platform: str
    title: str
    text: str
    hashtags: List[str]
    media_count: int


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/jobs", response_model=PublishResponse, summary="Create Publish Job")
async def create_publish_job(request: CreatePublishJobRequest):
    """Create a new content publish job."""
    try:
        job = PublishJob(
            title=request.title,
            content_text=request.content_text,
            content_format=request.content_format,
            target_platforms=request.target_platforms,
            media_urls=request.media_urls,
            media_captions=request.media_captions,
            tags=request.tags,
            quadrant=request.quadrant,
            source_note_id=request.source_note_id,
            calendar_entry_id=request.calendar_entry_id,
            status=PublishStatus.PENDING.value,
        )
        await job.save()

        return PublishResponse(
            job_id=str(job.id),
            status="created",
            message=f"Publish job created for {len(request.target_platforms)} platforms"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/jobs/{job_id}/publish-now", summary="Publish Immediately")
async def publish_now(job_id: str, background_tasks: BackgroundTasks):
    """Immediately publish a job to all target platforms."""
    try:
        job = await PublishJob.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Publish job not found")

        if job.status not in [PublishStatus.PENDING.value, PublishStatus.SCHEDULED.value]:
            raise HTTPException(status_code=400, detail=f"Job cannot be published (status: {job.status})")

        # Process immediately in background
        background_tasks.add_task(_process_publish_job, job_id)

        return {
            "status": "publishing",
            "job_id": job_id,
            "message": "Publishing started"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/jobs/{job_id}/schedule", summary="Schedule Publishing")
async def schedule_publish(job_id: str, request: SchedulePublishRequest):
    """Schedule a job for future publishing."""
    try:
        job = await PublishJob.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Publish job not found")

        if request.scheduled_at < datetime.utcnow():
            raise HTTPException(status_code=400, detail="Scheduled time must be in the future")

        await publish_queue.schedule_job(job, request.scheduled_at)

        return {
            "status": "scheduled",
            "job_id": job_id,
            "scheduled_at": request.scheduled_at.isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/jobs/{job_id}/cancel", summary="Cancel Publish Job")
async def cancel_publish(job_id: str):
    """Cancel a scheduled or pending publish job."""
    try:
        success = await publish_queue.cancel_job(job_id)
        if not success:
            raise HTTPException(status_code=400, detail="Job cannot be cancelled")

        return {
            "status": "cancelled",
            "job_id": job_id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs", summary="List Publish Jobs")
async def list_publish_jobs(
    status: Optional[str] = None,
    platform: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """List publish jobs with filters."""
    try:
        # Query jobs from database
        jobs = await PublishJob.get_all()

        if status:
            jobs = [j for j in jobs if j.status == status]

        if platform:
            jobs = [j for j in jobs if platform in j.target_platforms]

        # Sort by created_at desc
        jobs.sort(key=lambda x: x.created_at, reverse=True)

        total = len(jobs)
        jobs = jobs[offset:offset + limit]

        return {
            "jobs": [
                {
                    "id": str(j.id),
                    "title": j.title,
                    "content_format": j.content_format,
                    "target_platforms": j.target_platforms,
                    "status": j.status,
                    "scheduled_at": j.scheduled_at.isoformat() if j.scheduled_at else None,
                    "published_at": j.published_at.isoformat() if j.published_at else None,
                    "platform_urls": j.platform_urls,
                    "retry_count": j.retry_count,
                    "created_at": j.created_at.isoformat(),
                }
                for j in jobs
            ],
            "total": total,
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/{job_id}", summary="Get Publish Job Details")
async def get_publish_job(job_id: str):
    """Get detailed information about a publish job."""
    try:
        job = await PublishJob.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Publish job not found")

        # Generate platform variants
        variants = ContentAdapter.generate_platform_variants(job)

        return {
            "job": {
                "id": str(job.id),
                "title": job.title,
                "content_text": job.content_text,
                "content_format": job.content_format,
                "target_platforms": job.target_platforms,
                "media_urls": job.media_urls,
                "tags": job.tags,
                "quadrant": job.quadrant,
                "status": job.status,
                "scheduled_at": job.scheduled_at.isoformat() if job.scheduled_at else None,
                "published_at": job.published_at.isoformat() if job.published_at else None,
                "publish_results": job.publish_results,
                "platform_urls": job.platform_urls,
                "retry_count": job.retry_count,
                "last_error": job.last_error,
                "created_at": job.created_at.isoformat(),
                "updated_at": job.updated_at.isoformat(),
            },
            "platform_variants": variants
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/jobs/{job_id}/preview", summary="Preview Platform Variants")
async def preview_platform_variants(job_id: str):
    """Preview how content will look on each platform."""
    try:
        job = await PublishJob.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Publish job not found")

        variants = ContentAdapter.generate_platform_variants(job)

        return {
            "variants": [
                {
                    "platform": platform,
                    "title": content.get("title", ""),
                    "text_preview": content.get("text", "")[:200] + "..." if len(content.get("text", "")) > 200 else content.get("text", ""),
                    "hashtags": content.get("hashtags", []),
                    "media_count": len(content.get("media", [])),
                }
                for platform, content in variants.items()
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/publish-all", summary="One-Click Multi-Platform Publish")
async def publish_to_all_platforms(request: CreatePublishJobRequest):
    """Create and immediately publish to all specified platforms."""
    try:
        # Create job
        job = PublishJob(
            title=request.title,
            content_text=request.content_text,
            content_format=request.content_format,
            target_platforms=request.target_platforms,
            media_urls=request.media_urls,
            media_captions=request.media_captions,
            tags=request.tags,
            quadrant=request.quadrant,
            source_note_id=request.source_note_id,
            status=PublishStatus.PENDING.value,
        )
        await job.save()

        # Process immediately
        await _process_publish_job(str(job.id))

        # Refresh job data
        job = await PublishJob.get(str(job.id))

        return {
            "status": "completed",
            "job_id": str(job.id),
            "results": job.publish_results if job else {},
            "platform_urls": job.platform_urls if job else {},
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/queue/status", summary="Get Publish Queue Status")
async def get_queue_status():
    """Get current status of the publish queue."""
    try:
        # Count jobs by status
        jobs = await PublishJob.get_all()

        status_counts = {}
        for status in PublishStatus:
            status_counts[status.value] = len([j for j in jobs if j.status == status.value])

        return {
            "status_counts": status_counts,
            "total_jobs": len(jobs),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Background Tasks
# ============================================================================

async def _process_publish_job(job_id: str):
    """Process a single publish job."""
    try:
        job = await PublishJob.get(job_id)
        if not job:
            return

        await job.mark_publishing()

        platforms_pending = job.get_platforms_pending()

        for platform_str in platforms_pending:
            try:
                # Get platform account
                accounts = await PlatformAccount.get_all()
                account = next(
                    (a for a in accounts if a.platform == platform_str and a.is_authenticated),
                    None
                )

                if not account:
                    await job.mark_failed(f"No authenticated account for {platform_str}", platform_str)
                    continue

                # Get publisher
                from open_notebook.domain.publish_job import PublisherRegistry
                publisher = PublisherRegistry.get_publisher(account)

                if not publisher:
                    await job.mark_failed(f"No publisher available for {platform_str}", platform_str)
                    continue

                # Validate
                valid, error = await publisher.validate_content(job)
                if not valid:
                    await job.mark_failed(error, platform_str)
                    continue

                # Publish
                result = await publisher.publish(job)

                await job.mark_published(
                    platform=platform_str,
                    url=result.get("url", ""),
                    platform_data=result
                )

            except Exception as e:
                await job.mark_failed(str(e), platform_str)

    except Exception as e:
        logger.exception(f"Error processing publish job {job_id}: {e}")
