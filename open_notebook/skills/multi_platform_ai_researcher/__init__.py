"""Multi-Platform AI Tools Researcher Skill.

Automatically collects information about "AI tools for solopreneurs" from
multiple Chinese social media platforms and generates daily research reports.

This is the main skill module that can be used as a Claude Skill.
"""

from .multi_platform_ai_researcher import (
    MultiPlatformAIResearcher,
    research_ai_tools
)

__all__ = ["MultiPlatformAIResearcher", "research_ai_tools"]
