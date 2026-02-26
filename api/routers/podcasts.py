from datetime import datetime
from pathlib import Path
from typing import List, Optional
from urllib.parse import unquote, urlparse

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from loguru import logger
from pydantic import BaseModel

from api.podcast_service import (
    PodcastGenerationRequest,
    PodcastGenerationResponse,
    PodcastService,
)
from open_notebook.skills.auto_podcast_planner import (
    AutoPodcastPlanner,
    plan_podcast,
    suggest_podcast_formats,
)

router = APIRouter()


class PodcastEpisodeResponse(BaseModel):
    id: str
    name: str
    episode_profile: dict
    speaker_profile: dict
    briefing: str
    audio_file: Optional[str] = None
    audio_url: Optional[str] = None
    transcript: Optional[dict] = None
    outline: Optional[dict] = None
    created: Optional[str] = None
    job_status: Optional[str] = None


def _resolve_audio_path(audio_file: str) -> Path:
    if audio_file.startswith("file://"):
        parsed = urlparse(audio_file)
        return Path(unquote(parsed.path))
    return Path(audio_file)


@router.post("/podcasts/generate", response_model=PodcastGenerationResponse)
async def generate_podcast(request: PodcastGenerationRequest):
    """
    Generate a podcast episode using Episode Profiles.
    Returns immediately with job ID for status tracking.
    """
    try:
        job_id = await PodcastService.submit_generation_job(
            episode_profile_name=request.episode_profile,
            speaker_profile_name=request.speaker_profile,
            episode_name=request.episode_name,
            notebook_id=request.notebook_id,
            content=request.content,
            briefing_suffix=request.briefing_suffix,
        )

        return PodcastGenerationResponse(
            job_id=job_id,
            status="submitted",
            message=f"Podcast generation started for episode '{request.episode_name}'",
            episode_profile=request.episode_profile,
            episode_name=request.episode_name,
        )

    except Exception as e:
        logger.error(f"Error generating podcast: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Failed to generate podcast"
        )


@router.get("/podcasts/jobs/{job_id}")
async def get_podcast_job_status(job_id: str):
    """Get the status of a podcast generation job"""
    try:
        status_data = await PodcastService.get_job_status(job_id)
        return status_data

    except Exception as e:
        logger.error(f"Error fetching podcast job status: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Failed to fetch job status"
        )


@router.get("/podcasts/episodes", response_model=List[PodcastEpisodeResponse])
async def list_podcast_episodes():
    """List all podcast episodes"""
    try:
        episodes = await PodcastService.list_episodes()

        response_episodes = []
        for episode in episodes:
            # Skip incomplete episodes without command or audio
            if not episode.command and not episode.audio_file:
                continue

            # Get job status if available
            job_status = None
            if episode.command:
                try:
                    job_status = await episode.get_job_status()
                except Exception:
                    job_status = "unknown"
            else:
                # No command but has audio file = completed import
                job_status = "completed"

            audio_url = None
            if episode.audio_file:
                audio_path = _resolve_audio_path(episode.audio_file)
                if audio_path.exists():
                    audio_url = f"/api/podcasts/episodes/{episode.id}/audio"

            response_episodes.append(
                PodcastEpisodeResponse(
                    id=str(episode.id),
                    name=episode.name,
                    episode_profile=episode.episode_profile,
                    speaker_profile=episode.speaker_profile,
                    briefing=episode.briefing,
                    audio_file=episode.audio_file,
                    audio_url=audio_url,
                    transcript=episode.transcript,
                    outline=episode.outline,
                    created=str(episode.created) if episode.created else None,
                    job_status=job_status,
                )
            )

        return response_episodes

    except Exception as e:
        logger.error(f"Error listing podcast episodes: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Failed to list podcast episodes"
        )


@router.get("/podcasts/episodes/{episode_id}", response_model=PodcastEpisodeResponse)
async def get_podcast_episode(episode_id: str):
    """Get a specific podcast episode"""
    try:
        episode = await PodcastService.get_episode(episode_id)

        # Get job status if available
        job_status = None
        if episode.command:
            try:
                job_status = await episode.get_job_status()
            except Exception:
                job_status = "unknown"
        else:
            # No command but has audio file = completed import
            job_status = "completed" if episode.audio_file else "unknown"

        audio_url = None
        if episode.audio_file:
            audio_path = _resolve_audio_path(episode.audio_file)
            if audio_path.exists():
                audio_url = f"/api/podcasts/episodes/{episode.id}/audio"

        return PodcastEpisodeResponse(
            id=str(episode.id),
            name=episode.name,
            episode_profile=episode.episode_profile,
            speaker_profile=episode.speaker_profile,
            briefing=episode.briefing,
            audio_file=episode.audio_file,
            audio_url=audio_url,
            transcript=episode.transcript,
            outline=episode.outline,
            created=str(episode.created) if episode.created else None,
            job_status=job_status,
        )

    except Exception as e:
        logger.error(f"Error fetching podcast episode: {str(e)}")
        raise HTTPException(status_code=404, detail="Episode not found")


@router.get("/podcasts/episodes/{episode_id}/audio")
async def stream_podcast_episode_audio(episode_id: str):
    """Stream the audio file associated with a podcast episode"""
    try:
        episode = await PodcastService.get_episode(episode_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching podcast episode for audio: {str(e)}")
        raise HTTPException(status_code=404, detail="Episode not found")

    if not episode.audio_file:
        raise HTTPException(status_code=404, detail="Episode has no audio file")

    audio_path = _resolve_audio_path(episode.audio_file)
    if not audio_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found on disk")

    return FileResponse(
        audio_path,
        media_type="audio/mpeg",
        filename=audio_path.name,
    )


@router.delete("/podcasts/episodes/{episode_id}")
async def delete_podcast_episode(episode_id: str):
    """Delete a podcast episode and its associated audio file"""
    try:
        # Get the episode first to check if it exists and get the audio file path
        episode = await PodcastService.get_episode(episode_id)

        # Delete the physical audio file if it exists
        if episode.audio_file:
            audio_path = _resolve_audio_path(episode.audio_file)
            if audio_path.exists():
                try:
                    audio_path.unlink()
                    logger.info(f"Deleted audio file: {audio_path}")
                except Exception as e:
                    logger.warning(f"Failed to delete audio file {audio_path}: {e}")

        # Delete the episode from the database
        await episode.delete()

        logger.info(f"Deleted podcast episode: {episode_id}")
        return {"message": "Episode deleted successfully", "episode_id": episode_id}

    except Exception as e:
        logger.error(f"Error deleting podcast episode: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Failed to delete episode"
        )


# Auto Podcast Planner endpoints
class PodcastPlanRequest(BaseModel):
    notebook_id: str
    source_ids: Optional[List[str]] = None
    preferred_duration: int = 15
    preferred_format: Optional[str] = None
    audience: str = "general"


class PodcastPlanResponse(BaseModel):
    success: bool
    plan: Optional[dict] = None
    episode_profile: Optional[dict] = None
    speaker_profile: Optional[dict] = None
    recommendations: Optional[dict] = None
    error_message: Optional[str] = None


class SuggestFormatsRequest(BaseModel):
    notebook_id: str


class SuggestFormatsResponse(BaseModel):
    success: bool
    suggestions: List[dict] = []
    error_message: Optional[str] = None


@router.post("/podcasts/plan", response_model=PodcastPlanResponse)
async def create_podcast_plan(request: PodcastPlanRequest):
    """
    Generate an AI-powered podcast plan based on notebook content.
    Analyzes content and recommends format, speakers, and structure.
    """
    try:
        from open_notebook.skills.base import SkillConfig, SkillContext

        config = SkillConfig(
            skill_type="auto_podcast_planner",
            name="Auto Podcast Planner",
            parameters={
                "notebook_id": request.notebook_id,
                "source_ids": request.source_ids,
                "preferred_duration": request.preferred_duration,
                "preferred_format": request.preferred_format,
                "audience": request.audience,
            }
        )

        planner = AutoPodcastPlanner(config)
        ctx = SkillContext(
            skill_id=f"podcast_plan_api_{datetime.utcnow().timestamp()}",
            trigger_type="api"
        )

        result = await planner.run(ctx)

        if result.success:
            return PodcastPlanResponse(
                success=True,
                plan=result.output.get("podcast_plan"),
                episode_profile=result.output.get("episode_profile"),
                speaker_profile=result.output.get("speaker_profile"),
                recommendations=result.output.get("recommendations"),
            )
        else:
            return PodcastPlanResponse(
                success=False,
                error_message=result.error_message
            )

    except Exception as e:
        logger.error(f"Error creating podcast plan: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to create podcast plan: {str(e)}"
        )


@router.post("/podcasts/suggest-formats", response_model=SuggestFormatsResponse)
async def suggest_podcast_formats_endpoint(request: SuggestFormatsRequest):
    """
    Suggest suitable podcast formats for notebook content.
    Returns ranked format recommendations with scores.
    """
    try:
        suggestions = await suggest_podcast_formats(request.notebook_id)

        return SuggestFormatsResponse(
            success=True,
            suggestions=suggestions
        )

    except Exception as e:
        logger.error(f"Error suggesting podcast formats: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to suggest formats: {str(e)}"
        )


@router.post("/podcasts/plan-and-generate")
async def plan_and_generate_podcast(request: PodcastPlanRequest):
    """
    Plan a podcast and immediately generate it using the planned profiles.
    Creates temporary episode and speaker profiles based on AI recommendations.
    """
    try:
        from open_notebook.skills.base import SkillConfig, SkillContext
        from open_notebook.podcasts.models import EpisodeProfile, SpeakerProfile
        from datetime import datetime

        # Step 1: Create plan
        config = SkillConfig(
            skill_type="auto_podcast_planner",
            name="Auto Podcast Planner",
            parameters={
                "notebook_id": request.notebook_id,
                "source_ids": request.source_ids,
                "preferred_duration": request.preferred_duration,
                "preferred_format": request.preferred_format,
                "audience": request.audience,
            }
        )

        planner = AutoPodcastPlanner(config)
        ctx = SkillContext(
            skill_id=f"podcast_plan_generate_{datetime.utcnow().timestamp()}",
            trigger_type="api"
        )

        result = await planner.run(ctx)

        if not result.success:
            return {
                "success": False,
                "stage": "planning",
                "error_message": result.error_message
            }

        # Step 2: Save profiles
        plan = result.output["podcast_plan"]
        episode_profile_data = result.output["episode_profile"]
        speaker_profile_data = result.output["speaker_profile"]

        # Create and save episode profile
        episode_profile = EpisodeProfile(**episode_profile_data)
        await episode_profile.save()

        # Create and save speaker profile
        speaker_profile = SpeakerProfile(**speaker_profile_data)
        await speaker_profile.save()

        # Step 3: Submit generation job
        job_id = await PodcastService.submit_generation_job(
            episode_profile_name=episode_profile.name,
            speaker_profile_name=speaker_profile.name,
            episode_name=plan["title"],
            notebook_id=request.notebook_id,
            briefing_suffix=f"Original hook: {plan['hook']}"
        )

        return {
            "success": True,
            "stage": "generation_submitted",
            "job_id": job_id,
            "episode_profile_name": episode_profile.name,
            "speaker_profile_name": speaker_profile.name,
            "plan": plan,
            "message": f"Podcast generation started with {plan['num_speakers']} speakers in {plan['format_type']} format"
        }

    except Exception as e:
        logger.error(f"Error in plan and generate: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to plan and generate podcast: {str(e)}"
        )
