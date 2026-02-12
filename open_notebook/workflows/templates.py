"""Pre-built workflow templates for OPC (One-Person Company) scenarios.

These templates provide ready-to-use workflows for common content creation,
monitoring, and organization tasks.
"""

from typing import Any, Dict, List

from open_notebook.domain.workflow import WorkflowStepDefinition


class WorkflowTemplate:
    """Template for creating a workflow."""

    def __init__(
        self,
        template_id: str,
        name: str,
        description: str,
        category: str,
        steps: List[Dict[str, Any]],
        input_schema: Dict[str, Any],
        output_mapping: Dict[str, str],
    ):
        self.template_id = template_id
        self.name = name
        self.description = description
        self.category = category
        self.steps = steps
        self.input_schema = input_schema
        self.output_mapping = output_mapping

    def to_workflow_data(self, **overrides) -> Dict[str, Any]:
        """Generate workflow creation data with optional overrides."""
        return {
            "name": overrides.get("name", self.name),
            "description": overrides.get("description", self.description),
            "steps": [
                WorkflowStepDefinition(**step).model_dump()
                for step in self.steps
            ],
            "input_schema": self.input_schema,
            "output_mapping": self.output_mapping,
            "target_notebook_id": overrides.get("target_notebook_id"),
            "schedule": overrides.get("schedule"),
            "enabled": overrides.get("enabled", False),
        }


# =============================================================================
# OPC Workflow Templates
# =============================================================================

TEMPLATES: List[WorkflowTemplate] = [
    # -------------------------------------------------------------------------
    # Content Monitoring & Curation
    # -------------------------------------------------------------------------
    WorkflowTemplate(
        template_id="rss_to_notes",
        name="RSS to Notes Pipeline",
        description="Monitor RSS feeds, extract articles, and generate summary notes automatically.",
        category="content_monitoring",
        steps=[
            {
                "step_id": "fetch_rss",
                "skill_type": "rss_crawler",
                "name": "Fetch RSS Feeds",
                "description": "Crawl RSS feeds for new articles",
                "parameters": {
                    "feed_urls": "{{input.feed_urls}}",
                    "max_entries": "{{input.max_entries|default(10)}}",
                    "deduplicate": True,
                },
                "depends_on": [],
            },
            {
                "step_id": "summarize_articles",
                "skill_type": "note_summarizer",
                "name": "Summarize Articles",
                "description": "Generate summaries for fetched articles",
                "parameters": {
                    "source_ids": "{{steps.fetch_rss.output.created_source_ids}}",
                    "summary_length": "{{input.summary_length|default('medium')}}",
                    "summary_style": "{{input.summary_style|default('bullet_points')}}",
                },
                "depends_on": ["fetch_rss"],
                "continue_on_fail": True,
            },
        ],
        input_schema={
            "feed_urls": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of RSS feed URLs to monitor",
            },
            "max_entries": {
                "type": "integer",
                "default": 10,
                "description": "Maximum entries to fetch per feed",
            },
            "summary_length": {
                "type": "string",
                "enum": ["short", "medium", "long"],
                "default": "medium",
            },
            "summary_style": {
                "type": "string",
                "enum": ["concise", "detailed", "bullet_points", "executive"],
                "default": "bullet_points",
            },
        },
        output_mapping={
            "sources_created": "{{steps.fetch_rss.output.created_source_ids}}",
            "notes_created": "{{steps.summarize_articles.output.created_note_ids}}",
        },
    ),

    # -------------------------------------------------------------------------
    # Content Repurposing
    # -------------------------------------------------------------------------
    WorkflowTemplate(
        template_id="content_repurpose",
        name="Content Repurposing Pipeline",
        description="Transform a long-form article into multiple formats: Twitter thread, LinkedIn post, and newsletter.",
        category="content_creation",
        steps=[
            {
                "step_id": "transform_twitter",
                "skill_type": "content_transform",
                "name": "Create Twitter Thread",
                "description": "Transform content into Twitter thread",
                "parameters": {
                    "source_ids": "{{input.source_ids}}",
                    "transformation_type": "social_post",
                    "options": {
                        "platform": "twitter",
                        "max_length": 280,
                        "thread_count": "{{input.twitter_thread_count|default(5)}}",
                    },
                },
                "depends_on": [],
                "continue_on_fail": True,
            },
            {
                "step_id": "transform_linkedin",
                "skill_type": "content_transform",
                "name": "Create LinkedIn Post",
                "description": "Transform content into LinkedIn post",
                "parameters": {
                    "source_ids": "{{input.source_ids}}",
                    "transformation_type": "social_post",
                    "options": {
                        "platform": "linkedin",
                        "tone": "professional",
                        "include_hashtags": True,
                    },
                },
                "depends_on": [],
                "continue_on_fail": True,
            },
            {
                "step_id": "transform_newsletter",
                "skill_type": "content_transform",
                "name": "Create Newsletter",
                "description": "Transform content into newsletter format",
                "parameters": {
                    "source_ids": "{{input.source_ids}}",
                    "transformation_type": "newsletter",
                    "options": {
                        "length": "{{input.newsletter_length|default('medium')}}",
                        "include_summary": True,
                        "include_cta": True,
                    },
                },
                "depends_on": [],
                "continue_on_fail": True,
            },
        ],
        input_schema={
            "source_ids": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Source IDs to repurpose",
            },
            "twitter_thread_count": {
                "type": "integer",
                "default": 5,
                "description": "Number of tweets in thread",
            },
            "newsletter_length": {
                "type": "string",
                "enum": ["short", "medium", "long"],
                "default": "medium",
            },
        },
        output_mapping={
            "twitter_note_id": "{{steps.transform_twitter.output.created_note_ids[0]}}",
            "linkedin_note_id": "{{steps.transform_linkedin.output.created_note_ids[0]}}",
            "newsletter_note_id": "{{steps.transform_newsletter.output.created_note_ids[0]}}",
        },
    ),

    # -------------------------------------------------------------------------
    # Competitor Monitoring
    # -------------------------------------------------------------------------
    WorkflowTemplate(
        template_id="competitor_monitor",
        name="Competitor Website Monitor",
        description="Monitor competitor websites for changes and extract key information.",
        category="monitoring",
        steps=[
            {
                "step_id": "crawl_website",
                "skill_type": "browser_crawler",
                "name": "Crawl Competitor Website",
                "description": "Extract content from competitor websites",
                "parameters": {
                    "urls": "{{input.urls}}",
                    "extraction_task": "{{input.extraction_task|default('Extract product updates, pricing changes, and news')}}",
                    "max_pages": "{{input.max_pages|default(5)}}",
                },
                "depends_on": [],
            },
            {
                "step_id": "analyze_changes",
                "skill_type": "content_transform",
                "name": "Analyze Changes",
                "description": "Compare with previous crawl and identify changes",
                "parameters": {
                    "source_ids": "{{steps.crawl_website.output.created_source_ids}}",
                    "transformation_type": "comparison",
                    "options": {
                        "compare_with_previous": True,
                        "highlight_changes": True,
                    },
                },
                "depends_on": ["crawl_website"],
                "continue_on_fail": True,
            },
            {
                "step_id": "generate_insights",
                "skill_type": "note_summarizer",
                "name": "Generate Insights",
                "description": "Create actionable insights from competitor changes",
                "parameters": {
                    "source_ids": "{{steps.analyze_changes.output.created_source_ids}}",
                    "summary_style": "executive",
                },
                "depends_on": ["analyze_changes"],
                "continue_on_fail": True,
            },
        ],
        input_schema={
            "urls": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Competitor URLs to monitor",
            },
            "extraction_task": {
                "type": "string",
                "default": "Extract product updates, pricing changes, and news",
                "description": "Specific extraction instructions",
            },
            "max_pages": {
                "type": "integer",
                "default": 5,
                "description": "Maximum pages to crawl per site",
            },
        },
        output_mapping={
            "sources_created": "{{steps.crawl_website.output.created_source_ids}}",
            "insights_note_id": "{{steps.generate_insights.output.created_note_ids[0]}}",
        },
    ),

    # -------------------------------------------------------------------------
    # Content Organization
    # -------------------------------------------------------------------------
    WorkflowTemplate(
        template_id="auto_organize",
        name="Auto-Organize Notebook",
        description="Automatically tag, summarize, and organize all unprocessed sources in a notebook.",
        category="organization",
        steps=[
            {
                "step_id": "tag_sources",
                "skill_type": "note_tagger",
                "name": "Auto-Tag Sources",
                "description": "Generate and apply tags to sources",
                "parameters": {
                    "notebook_id": "{{input.notebook_id}}",
                    "target_type": "source",
                    "max_tags": "{{input.max_tags|default(5)}}",
                    "auto_apply": True,
                },
                "depends_on": [],
                "continue_on_fail": True,
            },
            {
                "step_id": "summarize_sources",
                "skill_type": "note_summarizer",
                "name": "Summarize Sources",
                "description": "Generate summaries for sources without notes",
                "parameters": {
                    "notebook_id": "{{input.notebook_id}}",
                    "filter": "unprocessed",
                    "summary_length": "short",
                },
                "depends_on": ["tag_sources"],
                "continue_on_fail": True,
            },
            {
                "step_id": "create_index",
                "skill_type": "note_organizer",
                "name": "Create Index Note",
                "description": "Create an organized index of all content",
                "parameters": {
                    "notebook_id": "{{input.notebook_id}}",
                    "organization_type": "by_tag",
                    "include_summaries": True,
                },
                "depends_on": ["summarize_sources"],
                "continue_on_fail": True,
            },
        ],
        input_schema={
            "notebook_id": {
                "type": "string",
                "description": "Notebook ID to organize",
            },
            "max_tags": {
                "type": "integer",
                "default": 5,
                "description": "Maximum tags per source",
            },
        },
        output_mapping={
            "organized_sources": "{{steps.tag_sources.output.processed_count}}",
            "index_note_id": "{{steps.create_index.output.created_note_id}}",
        },
    ),

    # -------------------------------------------------------------------------
    # Research Digest
    # -------------------------------------------------------------------------
    WorkflowTemplate(
        template_id="research_digest",
        name="Weekly Research Digest",
        description="Compile all sources from the past week into a digestible summary report.",
        category="content_creation",
        steps=[
            {
                "step_id": "gather_sources",
                "skill_type": "note_organizer",
                "name": "Gather Recent Sources",
                "description": "Collect sources from the past week",
                "parameters": {
                    "notebook_id": "{{input.notebook_id}}",
                    "filter": {
                        "created_after": "{{input.time_period|default('7d')}}",
                    },
                },
                "depends_on": [],
            },
            {
                "step_id": "categorize",
                "skill_type": "content_transform",
                "name": "Categorize Content",
                "description": "Group sources by topic/theme",
                "parameters": {
                    "source_ids": "{{steps.gather_sources.output.source_ids}}",
                    "transformation_type": "categorization",
                    "options": {
                        "categories": "{{input.categories|default([])}}",
                        "auto_detect": True,
                    },
                },
                "depends_on": ["gather_sources"],
                "continue_on_fail": True,
            },
            {
                "step_id": "generate_digest",
                "skill_type": "content_transform",
                "name": "Generate Digest",
                "description": "Create formatted digest document",
                "parameters": {
                    "source_ids": "{{steps.gather_sources.output.source_ids}}",
                    "transformation_type": "digest",
                    "options": {
                        "format": "{{input.format|default('markdown')}}",
                        "include_toc": True,
                        "include_key_insights": True,
                    },
                },
                "depends_on": ["categorize"],
                "continue_on_fail": True,
            },
        ],
        input_schema={
            "notebook_id": {
                "type": "string",
                "description": "Notebook ID to compile",
            },
            "time_period": {
                "type": "string",
                "default": "7d",
                "description": "Time period to include (e.g., '7d', '24h', '30d')",
            },
            "categories": {
                "type": "array",
                "items": {"type": "string"},
                "default": [],
                "description": "Optional predefined categories",
            },
            "format": {
                "type": "string",
                "enum": ["markdown", "html", "plain"],
                "default": "markdown",
            },
        },
        output_mapping={
            "digest_note_id": "{{steps.generate_digest.output.created_note_ids[0]}}",
            "sources_included": "{{steps.gather_sources.output.source_count}}",
        },
    ),

    # -------------------------------------------------------------------------
    # Vikki Content Operations (IP Content Strategy)
    # -------------------------------------------------------------------------
    WorkflowTemplate(
        template_id="vikki_content_pipeline",
        name="Vikki Content Pipeline",
        description="Four-quadrant content strategy: scan painpoints → classify → generate topics → adapt for platforms. Based on Vikki's IP operations methodology.",
        category="content_creation",
        steps=[
            {
                "step_id": "scan_painpoints",
                "skill_type": "painpoint_scanner",
                "name": "Scan for Painpoints",
                "description": "Identify instant, continuous, and hidden painpoints from content",
                "parameters": {
                    "source_ids": "{{input.source_ids|default([])}}",
                    "note_ids": "{{input.note_ids|default([])}}",
                    "text_content": "{{input.text_content|default('')}}",
                    "painpoint_types": "{{input.painpoint_types|default(['instant', 'continuous', 'hidden'])}}",
                    "min_urgency_score": "{{input.min_urgency_score|default(50)}}",
                    "max_painpoints": "{{input.max_painpoints|default(10)}}",
                    "target_notebook_id": "{{input.target_notebook_id}}",
                },
                "depends_on": [],
            },
            {
                "step_id": "classify_quadrant",
                "skill_type": "quadrant_classifier",
                "name": "Classify to Quadrants",
                "description": "Classify painpoints into Q1-Q4 framework",
                "parameters": {
                    "topics": "{{steps.scan_painpoints.output.painpoints|map(attribute='text')|list}}",
                    "classification_mode": "{{input.classification_mode|default('automatic')}}",
                    "save_as_tags": True,
                    "target_notebook_id": "{{input.target_notebook_id}}",
                },
                "depends_on": ["scan_painpoints"],
                "continue_on_fail": True,
            },
            {
                "step_id": "generate_topics",
                "skill_type": "topic_generator",
                "name": "Generate Content Topics",
                "description": "Generate high-ROI content ideas based on painpoints and quadrants",
                "parameters": {
                    "painpoints": "{{steps.scan_painpoints.output.painpoints}}",
                    "target_quadrants": "{{steps.classify_quadrant.output.quadrant_distribution|dictsort(by='value')|reverse|map(attribute='0')|list[:2]}}",
                    "topics_per_quadrant": "{{input.topics_per_quadrant|default(3)}}",
                    "industry": "{{input.industry|default('general')}}",
                    "content_formats": "{{input.content_formats|default(['article', 'video'])}}",
                    "target_notebook_id": "{{input.target_notebook_id}}",
                },
                "depends_on": ["classify_quadrant"],
            },
            {
                "step_id": "adapt_platforms",
                "skill_type": "content_adaptor",
                "name": "Adapt for Platforms",
                "description": "Adapt generated topics for multiple social platforms (Q1/Q2 only)",
                "parameters": {
                    "source_content": "{{steps.generate_topics.output.prioritized[0].title}}\n\n{{steps.generate_topics.output.prioritized[0].hook}}",
                    "target_platforms": "{{input.target_platforms|default(['twitter', 'linkedin'])}}",
                    "content_style": "{{input.content_style|default('professional')}}",
                    "include_cta": True,
                    "target_notebook_id": "{{input.target_notebook_id}}",
                },
                "depends_on": ["generate_topics"],
                "condition": "steps.classify_quadrant.output.classifications[0].quadrant in ['Q1', 'Q2'] if steps.classify_quadrant.output.classifications else False",
                "continue_on_fail": True,
            },
        ],
        input_schema={
            "source_ids": {
                "type": "array",
                "items": {"type": "string"},
                "default": [],
                "description": "Source IDs to analyze for painpoints",
            },
            "note_ids": {
                "type": "array",
                "items": {"type": "string"},
                "default": [],
                "description": "Note IDs to analyze for painpoints",
            },
            "text_content": {
                "type": "string",
                "default": "",
                "description": "Direct text content to analyze",
            },
            "target_notebook_id": {
                "type": "string",
                "description": "Notebook ID to save generated notes",
            },
            "painpoint_types": {
                "type": "array",
                "items": {"type": "string", "enum": ["instant", "continuous", "hidden"]},
                "default": ["instant", "continuous", "hidden"],
                "description": "Types of painpoints to detect",
            },
            "industry": {
                "type": "string",
                "default": "general",
                "description": "Target industry for topic generation (e.g., saas, fitness, education)",
            },
            "topics_per_quadrant": {
                "type": "integer",
                "default": 3,
                "minimum": 1,
                "maximum": 10,
                "description": "Number of topics to generate per quadrant",
            },
            "target_platforms": {
                "type": "array",
                "items": {"type": "string", "enum": ["twitter", "linkedin", "instagram", "tiktok"]},
                "default": ["twitter", "linkedin"],
                "description": "Platforms to adapt content for",
            },
            "content_style": {
                "type": "string",
                "enum": ["professional", "casual", "storytelling", "educational"],
                "default": "professional",
                "description": "Style of content adaptation",
            },
            "classification_mode": {
                "type": "string",
                "enum": ["automatic", "manual_review"],
                "default": "automatic",
                "description": "Classification confidence level",
            },
            "min_urgency_score": {
                "type": "integer",
                "default": 50,
                "minimum": 0,
                "maximum": 100,
                "description": "Minimum urgency threshold for painpoints",
            },
        },
        output_mapping={
            "painpoints": "{{steps.scan_painpoints.output.painpoints}}",
            "quadrant_distribution": "{{steps.classify_quadrant.output.quadrant_distribution}}",
            "generated_topics": "{{steps.generate_topics.output.prioritized}}",
            "content_calendar": "{{steps.generate_topics.output.content_calendar}}",
            "platform_adaptations": "{{steps.adapt_platforms.output.adaptations}}",
            "notes_created": "{{steps.scan_painpoints.output.created_note_ids + steps.classify_quadrant.output.created_note_ids + steps.generate_topics.output.created_note_ids + steps.adapt_platforms.output.created_note_ids}}",
        },
    ),

    # -------------------------------------------------------------------------
    # Podcast Production
    # -------------------------------------------------------------------------
    WorkflowTemplate(
        template_id="podcast_from_sources",
        name="Podcast from Sources",
        description="Generate a podcast episode from selected sources with custom speakers.",
        category="content_creation",
        steps=[
            {
                "step_id": "prepare_content",
                "skill_type": "note_organizer",
                "name": "Prepare Content",
                "description": "Compile and organize source content",
                "parameters": {
                    "source_ids": "{{input.source_ids}}",
                    "extract_key_points": True,
                },
                "depends_on": [],
            },
            {
                "step_id": "generate_podcast",
                "skill_type": "podcast_generator",
                "name": "Generate Podcast",
                "description": "Generate podcast episode from prepared content",
                "parameters": {
                    "source_ids": "{{input.source_ids}}",
                    "episode_profile_id": "{{input.episode_profile_id}}",
                    "speaker_profile_ids": "{{input.speaker_profile_ids}}",
                    "length_minutes": "{{input.length_minutes|default(15)}}",
                },
                "depends_on": ["prepare_content"],
            },
        ],
        input_schema={
            "source_ids": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Source IDs to include in podcast",
            },
            "episode_profile_id": {
                "type": "string",
                "description": "Episode profile ID",
            },
            "speaker_profile_ids": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Speaker profile IDs",
            },
            "length_minutes": {
                "type": "integer",
                "default": 15,
                "description": "Target podcast length in minutes",
            },
        },
        output_mapping={
            "podcast_id": "{{steps.generate_podcast.output.podcast_id}}",
            "audio_url": "{{steps.generate_podcast.output.audio_url}}",
        },
    ),
]


# =============================================================================
# Template Registry
# =============================================================================

class TemplateRegistry:
    """Registry for workflow templates."""

    _templates: Dict[str, WorkflowTemplate] = {}

    @classmethod
    def register(cls, template: WorkflowTemplate) -> None:
        """Register a template."""
        cls._templates[template.template_id] = template

    @classmethod
    def get(cls, template_id: str) -> Optional[WorkflowTemplate]:
        """Get a template by ID."""
        return cls._templates.get(template_id)

    @classmethod
    def list_all(cls) -> List[WorkflowTemplate]:
        """List all registered templates."""
        return list(cls._templates.values())

    @classmethod
    def list_by_category(cls, category: str) -> List[WorkflowTemplate]:
        """List templates by category."""
        return [t for t in cls._templates.values() if t.category == category]

    @classmethod
    def get_categories(cls) -> List[str]:
        """Get all unique categories."""
        return list(set(t.category for t in cls._templates.values()))


# Register all templates
for template in TEMPLATES:
    TemplateRegistry.register(template)
