"""Skill system for Open Notebook automation.

This module provides a lightweight skill framework based on LangChain,
enabling automated content processing and intelligent note organization.
"""

from open_notebook.skills.base import Skill, SkillConfig, SkillContext, SkillResult
from open_notebook.skills.registry import SkillRegistry, register_skill
from open_notebook.skills.runner import SkillRunner, get_skill_runner

# Import all skills to ensure registration
from open_notebook.skills.content_crawler import RssCrawlerSkill
from open_notebook.skills.browser_base import BrowserUseSkill, BrowserCrawlerSkill
from open_notebook.skills.note_organizer import NoteSummarizerSkill, NoteTaggerSkill

__all__ = [
    "Skill",
    "SkillConfig",
    "SkillContext",
    "SkillResult",
    "SkillRegistry",
    "register_skill",
    "SkillRunner",
    "get_skill_runner",
    # Skill implementations
    "RssCrawlerSkill",
    "BrowserUseSkill",
    "BrowserCrawlerSkill",
    "NoteSummarizerSkill",
    "NoteTaggerSkill",
]
