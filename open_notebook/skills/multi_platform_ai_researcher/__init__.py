"""Multi-Platform AI Tools Researcher Skill.

Automatically collects information about "AI tools for solopreneurs" from
multiple Chinese social media platforms and generates daily research reports.

This is the main skill module that can be used as a Claude Skill.
"""

from .multi_platform_ai_researcher import (
    MultiPlatformAIResearcher,
    research_ai_tools
)
from .platform_content_optimizer import (
    PlatformContentOptimizer,
    optimize_for_platform,
    create_multi_platform_content,
    get_platform_guide
)
from .content_creation_workflow import (
    ContentCreationWorkflow,
    TopicSelector,
    MaterialCollector,
    CopywritingGenerator,
    DistributionManager,
    create_content_project,
    generate_platform_content,
    get_platform_comparison
)

__all__ = [
    # Core researcher
    "MultiPlatformAIResearcher",
    "research_ai_tools",
    # Platform optimizer
    "PlatformContentOptimizer",
    "optimize_for_platform",
    "create_multi_platform_content",
    "get_platform_guide",
    # Content workflow
    "ContentCreationWorkflow",
    "TopicSelector",
    "MaterialCollector",
    "CopywritingGenerator",
    "DistributionManager",
    "create_content_project",
    "generate_platform_content",
    "get_platform_comparison"
]
