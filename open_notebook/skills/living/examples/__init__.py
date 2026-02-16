"""Examples for the Living Knowledge System.

This package contains example implementations showing how to use
the living knowledge system architecture.
"""

from open_notebook.skills.living.examples.p0_perception_organ import (
    create_pain_scanner_skill,
    create_emotion_watcher_skill,
    create_trend_hunter_skill,
    create_scene_discover_skill,
    create_p0_perception_agent,
    create_p0_meridians,
    initialize_p0_organ,
)

__all__ = [
    "create_pain_scanner_skill",
    "create_emotion_watcher_skill",
    "create_trend_hunter_skill",
    "create_scene_discover_skill",
    "create_p0_perception_agent",
    "create_p0_meridians",
    "initialize_p0_organ",
]
