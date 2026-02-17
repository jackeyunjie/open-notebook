"""API Router for Personal IP Command Center.

Provides endpoints for managing 10-dimensional profiles,
content calendars, and IP analytics dashboards.
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from open_notebook.domain.personal_ip import (
    PersonalIPProfile,
    ContentCalendarEntry,
    ContentStatus,
    ContentQuadrant,
    PlatformType,
    IPDashboard,
    IPDashboardMetrics,
)

router = APIRouter(prefix="/personal-ip", tags=["Personal IP Command Center"])


# ============================================================================
# Pydantic Models for Requests/Responses
# ============================================================================

class CreateProfileRequest(BaseModel):
    """Request to create a new profile."""
    name: str = Field(..., description="Profile name")
    description: str = Field(default="", description="Profile description")


class UpdateDimensionRequest(BaseModel):
    """Request to update a dimension."""
    data: Dict[str, Any]


class CreateCalendarEntryRequest(BaseModel):
    """Request to create a calendar entry."""
    title: str
    description: str = ""
    content_type: str = "post"
    quadrant: str = "Q3"
    planned_date: Optional[date] = None
    planned_time: Optional[str] = None
    target_platforms: List[str] = Field(default_factory=list)
    profile_id: Optional[str] = None


class UpdateCalendarEntryRequest(BaseModel):
    """Request to update a calendar entry."""
    status: Optional[str] = None
    planned_date: Optional[date] = None
    performance_data: Optional[Dict[str, Any]] = None


class PublishContentRequest(BaseModel):
    """Request to mark content as published."""
    platform: str
    url: str


# ============================================================================
# Profile Endpoints
# ============================================================================

@router.post("/profiles", summary="Create 10-Dimensional Profile")
async def create_profile(request: CreateProfileRequest):
    """Create a new Personal IP Profile with empty 10 dimensions."""
    try:
        profile = PersonalIPProfile(
            name=request.name,
            description=request.description,
        )
        await profile.save()
        return {
            "status": "created",
            "profile_id": str(profile.id),
            "name": profile.name,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profiles", summary="List All Profiles")
async def list_profiles():
    """List all personal IP profiles."""
    try:
        profiles = await PersonalIPProfile.get_all()
        return {
            "profiles": [
                {
                    "id": str(p.id),
                    "name": p.name,
                    "description": p.description,
                    "is_active": p.is_active,
                    "created_at": p.created_at.isoformat(),
                }
                for p in profiles
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profiles/{profile_id}", summary="Get Profile Details")
async def get_profile(profile_id: str):
    """Get full details of a profile including all 10 dimensions."""
    try:
        profile = await PersonalIPProfile.get(profile_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")

        return {
            "profile": {
                "id": str(profile.id),
                "name": profile.name,
                "description": profile.description,
                "is_active": profile.is_active,
                "d1_static_identity": profile.d1_static_identity.dict(),
                "d2_dynamic_behavior": profile.d2_dynamic_behavior.dict(),
                "d3_value_drivers": profile.d3_value_drivers.dict(),
                "d4_relationship_network": profile.d4_relationship_network.dict(),
                "d5_environmental_constraints": profile.d5_environmental_constraints.dict(),
                "d6_dynamic_feedback": profile.d6_dynamic_feedback.dict(),
                "d7_knowledge_assets": profile.d7_knowledge_assets.dict(),
                "d8_tacit_knowledge": profile.d8_tacit_knowledge.dict(),
                "d9_ai_collaboration": profile.d9_ai_collaboration.dict(),
                "d10_cognitive_evolution": profile.d10_cognitive_evolution.dict(),
                "created_at": profile.created_at.isoformat(),
                "updated_at": profile.updated_at.isoformat(),
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profiles/{profile_id}/summary", summary="Get Profile Summary")
async def get_profile_summary(profile_id: str):
    """Get condensed summary of profile (for dashboard)."""
    try:
        profile = await PersonalIPProfile.get(profile_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")

        return profile.get_dimension_summary()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/profiles/{profile_id}/dimensions/{dimension}", summary="Update Dimension")
async def update_dimension(
    profile_id: str,
    dimension: str,
    request: UpdateDimensionRequest
):
    """Update a specific dimension of the profile.

    Dimensions: d1, d2, d3, d4, d5, d6, d7, d8, d9, d10
    """
    try:
        profile = await PersonalIPProfile.get(profile_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")

        await profile.update_dimension(dimension, request.data)
        return {
            "status": "updated",
            "dimension": dimension,
            "profile_id": profile_id,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/profiles/{profile_id}", summary="Delete Profile")
async def delete_profile(profile_id: str):
    """Delete a profile and all associated data."""
    try:
        profile = await PersonalIPProfile.get(profile_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")

        await profile.delete()
        return {"status": "deleted", "profile_id": profile_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Content Calendar Endpoints
# ============================================================================

@router.post("/calendar", summary="Create Calendar Entry")
async def create_calendar_entry(request: CreateCalendarEntryRequest):
    """Create a new content calendar entry."""
    try:
        entry = ContentCalendarEntry(
            title=request.title,
            description=request.description,
            content_type=request.content_type,
            quadrant=ContentQuadrant(request.quadrant),
            planned_date=request.planned_date,
            planned_time=request.planned_time,
            target_platforms=[PlatformType(p) for p in request.target_platforms],
            profile_id=request.profile_id,
        )
        await entry.save()
        return {
            "status": "created",
            "entry_id": str(entry.id),
            "title": entry.title,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/calendar", summary="List Calendar Entries")
async def list_calendar_entries(
    profile_id: Optional[str] = None,
    status: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    quadrant: Optional[str] = None,
):
    """List content calendar entries with filters."""
    try:
        # This would query the database with filters
        # For now, return empty list
        return {"entries": [], "total": 0}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/calendar/upcoming", summary="Get Upcoming Content")
async def get_upcoming_content(
    days: int = Query(default=7, ge=1, le=30),
    profile_id: Optional[str] = None,
):
    """Get upcoming content for the next N days."""
    try:
        entries = await ContentCalendar.get_upcoming_entries(days, profile_id)
        return {
            "entries": [
                {
                    "id": str(e.id),
                    "title": e.title,
                    "planned_date": e.planned_date.isoformat() if e.planned_date else None,
                    "planned_time": e.planned_time,
                    "status": e.status.value,
                    "quadrant": e.quadrant.value,
                    "target_platforms": [p.value for p in e.target_platforms],
                }
                for e in entries
            ],
            "total": len(entries),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/calendar/{entry_id}", summary="Get Calendar Entry")
async def get_calendar_entry(entry_id: str):
    """Get details of a specific calendar entry."""
    try:
        entry = await ContentCalendarEntry.get(entry_id)
        if not entry:
            raise HTTPException(status_code=404, detail="Entry not found")

        return {
            "entry": {
                "id": str(entry.id),
                "title": entry.title,
                "description": entry.description,
                "content_type": entry.content_type,
                "quadrant": entry.quadrant.value,
                "planned_date": entry.planned_date.isoformat() if entry.planned_date else None,
                "planned_time": entry.planned_time,
                "status": entry.status.value,
                "target_platforms": [p.value for p in entry.target_platforms],
                "platform_specific_notes": entry.platform_specific_notes,
                "published_urls": entry.published_urls,
                "performance_data": entry.performance_data,
                "p0_signal_id": entry.p0_signal_id,
                "created_at": entry.created_at.isoformat(),
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/calendar/{entry_id}", summary="Update Calendar Entry")
async def update_calendar_entry(entry_id: str, request: UpdateCalendarEntryRequest):
    """Update a calendar entry."""
    try:
        entry = await ContentCalendarEntry.get(entry_id)
        if not entry:
            raise HTTPException(status_code=404, detail="Entry not found")

        if request.status:
            entry.status = ContentStatus(request.status)
        if request.planned_date:
            entry.planned_date = request.planned_date
        if request.performance_data:
            entry.performance_data = request.performance_data

        entry.updated_at = datetime.utcnow()
        await entry.save()

        return {"status": "updated", "entry_id": entry_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/calendar/{entry_id}/publish", summary="Mark Content as Published")
async def mark_published(entry_id: str, request: PublishContentRequest):
    """Mark a calendar entry as published on a platform."""
    try:
        entry = await ContentCalendarEntry.get(entry_id)
        if not entry:
            raise HTTPException(status_code=404, detail="Entry not found")

        await entry.mark_as_published(PlatformType(request.platform), request.url)
        return {"status": "published", "entry_id": entry_id, "platform": request.platform}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/calendar/{entry_id}", summary="Delete Calendar Entry")
async def delete_calendar_entry(entry_id: str):
    """Delete a calendar entry."""
    try:
        entry = await ContentCalendarEntry.get(entry_id)
        if not entry:
            raise HTTPException(status_code=404, detail="Entry not found")

        await entry.delete()
        return {"status": "deleted", "entry_id": entry_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Dashboard Endpoints
# ============================================================================

@router.get("/dashboard/{profile_id}/metrics", summary="Get Dashboard Metrics")
async def get_dashboard_metrics(profile_id: str):
    """Get comprehensive dashboard metrics for a profile."""
    try:
        metrics = await IPDashboard.get_metrics(profile_id)
        return metrics.dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard/{profile_id}/quadrants", summary="Get Quadrant Distribution")
async def get_quadrant_distribution(profile_id: str):
    """Get content distribution across four quadrants."""
    try:
        distribution = await IPDashboard.get_quadrant_distribution(profile_id)
        return {"distribution": distribution}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard/{profile_id}/pipeline", summary="Get Content Pipeline")
async def get_content_pipeline(profile_id: str):
    """Get content pipeline status (idea → published)."""
    try:
        pipeline = await IPDashboard.get_content_pipeline(profile_id)
        return {"pipeline": pipeline}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard/{profile_id}/dimension-health", summary="Get 10-Dimension Health")
async def get_dimension_health(profile_id: str):
    """Get completeness score for each of the 10 dimensions."""
    try:
        profile = await PersonalIPProfile.get(profile_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")

        # Calculate completeness for each dimension
        health = {
            "d1_static_identity": _calculate_d1_completeness(profile.d1_static_identity),
            "d2_dynamic_behavior": _calculate_d2_completeness(profile.d2_dynamic_behavior),
            "d3_value_drivers": _calculate_d3_completeness(profile.d3_value_drivers),
            "d4_relationship_network": _calculate_d4_completeness(profile.d4_relationship_network),
            "d5_environmental_constraints": _calculate_d5_completeness(profile.d5_environmental_constraints),
            "d6_dynamic_feedback": _calculate_d6_completeness(profile.d6_dynamic_feedback),
            "d7_knowledge_assets": _calculate_d7_completeness(profile.d7_knowledge_assets),
            "d8_tacit_knowledge": _calculate_d8_completeness(profile.d8_tacit_knowledge),
            "d9_ai_collaboration": _calculate_d9_completeness(profile.d9_ai_collaboration),
            "d10_cognitive_evolution": _calculate_d10_completeness(profile.d10_cognitive_evolution),
        }

        overall = sum(health.values()) / len(health) if health else 0

        return {
            "dimension_health": health,
            "overall_completeness": round(overall, 2),
            "status": "complete" if overall > 0.8 else "in_progress" if overall > 0.4 else "needs_work",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Helper Functions
# ============================================================================

def _calculate_d1_completeness(d1) -> float:
    """Calculate completeness of D1: Static Identity."""
    score = 0
    if d1.core_values: score += 0.2
    if d1.positioning_statement: score += 0.2
    if d1.brand_voice: score += 0.2
    if d1.origin_story: score += 0.2
    if d1.mission_statement: score += 0.2
    return round(score, 2)


def _calculate_d2_completeness(d2) -> float:
    """Calculate completeness of D2: Dynamic Behavior."""
    score = 0
    if d2.content_frequency: score += 0.25
    if d2.best_posting_times: score += 0.25
    if d2.content_formats: score += 0.25
    if d2.interaction_patterns: score += 0.25
    return round(score, 2)


def _calculate_d3_completeness(d3) -> float:
    """Calculate completeness of D3: Value Drivers."""
    score = 0
    if d3.expertise_areas: score += 0.2
    if d3.key_themes: score += 0.2
    if d3.content_pillars: score += 0.2
    if d3.unique_perspectives: score += 0.2
    if d3.value_proposition: score += 0.2
    return round(score, 2)


def _calculate_d4_completeness(d4) -> float:
    """Calculate completeness of D4: Relationship Network."""
    score = 0
    if d4.audience_segments: score += 0.25
    if d4.key_relationships: score += 0.25
    if d4.community_ties: score += 0.25
    if d4.follower_growth_milestones: score += 0.25
    return round(score, 2)


def _calculate_d5_completeness(d5) -> float:
    """Calculate completeness of D5: Environmental Constraints."""
    score = 0
    if d5.platform_policies: score += 0.2
    if d5.market_trends: score += 0.2
    if d5.competitive_landscape: score += 0.2
    if d5.opportunity_windows: score += 0.2
    if d5.regulatory_constraints: score += 0.2
    return round(score, 2)


def _calculate_d6_completeness(d6) -> float:
    """Calculate completeness of D6: Dynamic Feedback."""
    score = 0
    if d6.performance_metrics: score += 0.25
    if d6.content_analytics: score += 0.25
    if d6.engagement_patterns: score += 0.25
    if d6.feedback_summary: score += 0.25
    return round(score, 2)


def _calculate_d7_completeness(d7) -> float:
    """Calculate completeness of D7: Knowledge Assets."""
    score = 0
    if d7.published_content_count > 0: score += 0.2
    if d7.top_performing_content: score += 0.2
    if d7.content_series: score += 0.2
    if d7.reusable_templates: score += 0.2
    if d7.evergreen_content: score += 0.2
    return round(score, 2)


def _calculate_d8_completeness(d8) -> float:
    """Calculate completeness of D8: Tacit Knowledge."""
    score = 0
    if d8.intuitions: score += 0.2
    if d8.pattern_recognitions: score += 0.2
    if d8.lessons_learned: score += 0.2
    if d8.insider_observations: score += 0.2
    if d8.tacit_insights: score += 0.2
    return round(score, 2)


def _calculate_d9_completeness(d9) -> float:
    """Calculate completeness of D9: AI Collaboration."""
    score = 0
    if d9.preferred_agents: score += 0.25
    if d9.automation_rules: score += 0.25
    if d9.review_preferences: score += 0.25
    if d9.custom_prompts: score += 0.25
    return round(score, 2)


def _calculate_d10_completeness(d10) -> float:
    """Calculate completeness of D10: Cognitive Evolution."""
    score = 0
    if d10.evolution_logs: score += 0.34
    if d10.pivot_points: score += 0.33
    if d10.capability_milestones: score += 0.33
    return round(score, 2)
