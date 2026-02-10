"""Skill system for Open Notebook automation.

This module provides a lightweight skill framework based on LangChain,
enabling automated content processing and intelligent note organization.
"""

from open_notebook.skills.base import Skill, SkillConfig, SkillContext, SkillResult
from open_notebook.skills.registry import SkillRegistry, register_skill

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
    # Skill implementations
    "RssCrawlerSkill",
    "BrowserUseSkill",
    "BrowserCrawlerSkill",
    "NoteSummarizerSkill",
    "NoteTaggerSkill",
]
