"""Citation Enhancer - Precise text citation system for AI responses.

This skill enhances AI-generated answers with precise paragraph-level citations,
enabling users to:
- See exactly which text segments support each claim
- Click citations to jump to source location
- View highlighted source text in context

Features:
- Paragraph-level citation granularity
- Citation validation and deduplication
- Source text extraction and highlighting
- Support for multiple citation formats
"""

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger

from open_notebook.domain.notebook import Source, Note, SourceInsight
from open_notebook.skills.base import Skill, SkillConfig, SkillContext, SkillResult, SkillStatus
from open_notebook.skills.registry import register_skill


@dataclass
class Citation:
    """A single citation reference."""
    citation_id: str  # Unique ID like "cite_1", "cite_2"
    source_id: str  # Full source ID like "source:abc123"
    source_type: str  # "source", "note", "insight"
    source_title: Optional[str] = None
    text_snippet: str = ""  # The cited text (truncated)
    paragraph_index: Optional[int] = None  # Position in document
    start_char: Optional[int] = None  # Character position start
    end_char: Optional[int] = None  # Character position end
    confidence: float = 1.0  # Match confidence


@dataclass
class CitationBlock:
    """A block of text with its associated citation."""
    text: str
    citation: Optional[Citation] = None


@dataclass
class EnhancedResponse:
    """AI response with enhanced citation information."""
    original_text: str
    annotated_text: str  # Text with citation markers
    citations: List[Citation] = field(default_factory=list)
    citation_map: Dict[str, Citation] = field(default_factory=dict)


class CitationEnhancer(Skill):
    """Enhance AI responses with precise paragraph-level citations.

    This skill processes AI-generated text to:
    1. Extract and validate citation references
    2. Locate exact text positions in source documents
    3. Generate citation snippets for display
    4. Format annotated responses with clickable citations

    Parameters:
        - response_text: The AI-generated text to process
        - source_ids: List of source IDs that were referenced
        - citation_format: Format style ("bracket", "superscript", "footnote")
        - snippet_length: Length of citation snippets (default: 150 chars)
        - validate_citations: Whether to validate citations against sources (default: True)

    Example:
        config = SkillConfig(
            skill_type="citation_enhancer",
            name="Citation Enhancer",
            parameters={
                "response_text": "AI is transforming education [cite:source:abc123:para_3].",
                "source_ids": ["source:abc123"],
                "citation_format": "bracket",
                "snippet_length": 150
            }
        )
    """

    skill_type = "citation_enhancer"
    name = "Citation Enhancer"
    description = "Enhance AI responses with precise paragraph-level citations"

    parameters_schema = {
        "response_text": {
            "type": "string",
            "description": "The AI-generated text to process"
        },
        "source_ids": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of source IDs that were referenced"
        },
        "citation_format": {
            "type": "string",
            "enum": ["bracket", "superscript", "footnote", "inline"],
            "default": "bracket",
            "description": "Citation display format"
        },
        "snippet_length": {
            "type": "integer",
            "default": 150,
            "minimum": 50,
            "maximum": 500,
            "description": "Length of citation snippets in characters"
        },
        "validate_citations": {
            "type": "boolean",
            "default": True,
            "description": "Validate citations against source content"
        }
    }

    def __init__(self, config: SkillConfig):
        self.response_text: str = config.parameters.get("response_text", "")
        self.source_ids: List[str] = config.parameters.get("source_ids", [])
        self.citation_format: str = config.parameters.get("citation_format", "bracket")
        self.snippet_length: int = config.parameters.get("snippet_length", 150)
        self.validate_citations: bool = config.parameters.get("validate_citations", True)
        super().__init__(config)

    def _validate_config(self) -> None:
        """Validate enhancer configuration."""
        super()._validate_config()

        if not self.response_text:
            raise ValueError("response_text is required")

    def _extract_citations(self, text: str) -> List[Tuple[str, str]]:
        """Extract citation references from text.

        Supports formats:
        - [source:id] - Document-level citation
        - [cite:source:id:para_N] - Paragraph-level citation
        - [note:id] - Note citation
        - [insight:id] - Insight citation

        Returns:
            List of (full_match, citation_ref) tuples
        """
        # Pattern matches [type:id] or [cite:type:id:location]
        pattern = r'\[((?:cite:)?(?:source|note|insight):[a-zA-Z0-9_]+(?::[a-zA-Z0-9_]+)*)\]'
        matches = re.findall(pattern, text)

        citations = []
        for match in matches:
            full_match = f"[{match}]"
            citations.append((full_match, match))

        return citations

    def _parse_citation_ref(self, ref: str) -> Optional[Dict[str, Any]]:
        """Parse a citation reference string.

        Args:
            ref: Citation reference like "cite:source:abc123:para_3"

        Returns:
            Parsed citation info dict or None if invalid
        """
        parts = ref.split(":")

        # Handle "cite:" prefix
        if parts[0] == "cite":
            parts = parts[1:]

        if len(parts) < 2:
            return None

        source_type = parts[0]
        source_id = f"{parts[0]}:{parts[1]}"

        # Parse location info if present
        location = None
        if len(parts) >= 3:
            location = ":".join(parts[2:])

        return {
            "source_type": source_type,
            "source_id": source_id,
            "location": location,
            "original_ref": ref
        }

    async def _fetch_source_content(self, source_id: str) -> Optional[str]:
        """Fetch content from a source."""
        try:
            # Determine source type and fetch accordingly
            if source_id.startswith("source:"):
                source = await Source.get(source_id)
                return source.full_text if source else None
            elif source_id.startswith("note:"):
                note = await Note.get(source_id)
                return note.content if note else None
            elif source_id.startswith("insight:"):
                insight = await SourceInsight.get(source_id)
                return insight.content if insight else None
            return None
        except Exception as e:
            logger.error(f"Failed to fetch content for {source_id}: {e}")
            return None

    def _find_text_position(self, content: str, text_snippet: str) -> Optional[Tuple[int, int]]:
        """Find the position of a text snippet in content.

        Uses fuzzy matching for robustness.

        Returns:
            (start_char, end_char) tuple or None if not found
        """
        if not content or not text_snippet:
            return None

        # Clean snippets for matching
        clean_snippet = text_snippet.strip().lower()
        clean_content = content.lower()

        # Try exact match first
        idx = clean_content.find(clean_snippet)
        if idx >= 0:
            return (idx, idx + len(text_snippet))

        # Try with shorter snippet (first 50 chars)
        if len(clean_snippet) > 50:
            short_snippet = clean_snippet[:50]
            idx = clean_content.find(short_snippet)
            if idx >= 0:
                return (idx, min(idx + len(text_snippet), len(content)))

        return None

    def _extract_paragraph_index(self, location: Optional[str]) -> Optional[int]:
        """Extract paragraph index from location string.

        Args:
            location: Location string like "para_3" or "p5"

        Returns:
            Paragraph index or None
        """
        if not location:
            return None

        # Match patterns like "para_3", "p5", "paragraph_10"
        patterns = [
            r'para(?:graph)?[_-]?(\d+)',
            r'p[_-]?(\d+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, location, re.IGNORECASE)
            if match:
                return int(match.group(1))

        return None

    async def _validate_and_enhance_citation(
        self,
        citation_ref: str,
        index: int
    ) -> Optional[Citation]:
        """Validate a citation and create a Citation object.

        Args:
            citation_ref: The citation reference string
            index: Citation index for ID generation

        Returns:
            Citation object or None if invalid
        """
        parsed = self._parse_citation_ref(citation_ref)
        if not parsed:
            return None

        source_id = parsed["source_id"]
        source_type = parsed["source_type"]
        location = parsed["location"]

        # Fetch source content
        content = await self._fetch_source_content(source_id)
        if not content and self.validate_citations:
            logger.warning(f"Could not fetch content for citation: {citation_ref}")
            # Still create citation, but mark as unvalidated

        # Extract paragraph index
        para_idx = self._extract_paragraph_index(location)

        # Get source title
        source_title = None
        try:
            if source_id.startswith("source:"):
                source = await Source.get(source_id)
                source_title = source.title if source else None
            elif source_id.startswith("note:"):
                note = await Note.get(source_id)
                source_title = note.title if note else None
        except Exception:
            pass

        # Extract text snippet if paragraph index available
        text_snippet = ""
        start_char = None
        end_char = None

        if content and para_idx is not None:
            paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
            if 0 <= para_idx < len(paragraphs):
                text_snippet = paragraphs[para_idx][:self.snippet_length]
                # Find position
                pos = self._find_text_position(content, paragraphs[para_idx])
                if pos:
                    start_char, end_char = pos

        # Create citation
        citation = Citation(
            citation_id=f"cite_{index}",
            source_id=source_id,
            source_type=source_type,
            source_title=source_title,
            text_snippet=text_snippet,
            paragraph_index=para_idx,
            start_char=start_char,
            end_char=end_char,
            confidence=1.0 if content else 0.5
        )

        return citation

    def _format_annotated_text(
        self,
        text: str,
        citations: List[Citation],
        citation_map: Dict[str, Citation]
    ) -> str:
        """Format text with citation annotations.

        Replaces original citations with enhanced format.

        Args:
            text: Original text
            citations: List of Citation objects
            citation_map: Map from original ref to Citation

        Returns:
            Annotated text
        """
        annotated = text

        for orig_ref, citation in citation_map.items():
            # Replace based on format
            if self.citation_format == "superscript":
                replacement = f"<sup>[{citation.citation_id}]</sup>"
            elif self.citation_format == "footnote":
                replacement = f"[{citation.citation_id}]"
            elif self.citation_format == "inline":
                replacement = f"[{citation.source_title or citation.source_id}]"
            else:  # bracket (default)
                replacement = f"[{citation.citation_id}]"

            # Escape special regex chars in orig_ref
            escaped_ref = re.escape(f"[{orig_ref}]")
            annotated = re.sub(escaped_ref, replacement, annotated)

        return annotated

    def _generate_citation_list(self, citations: List[Citation]) -> str:
        """Generate a formatted list of citations.

        Args:
            citations: List of Citation objects

        Returns:
            Formatted citation list (markdown)
        """
        lines = ["\n\n---\n\n## Sources", ""]

        for cite in citations:
            title = cite.source_title or cite.source_id
            snippet = cite.text_snippet or ""

            line = f"**[{cite.citation_id}]** {title}"
            if snippet:
                # Truncate snippet if too long
                display_snippet = snippet[:self.snippet_length]
                if len(snippet) > self.snippet_length:
                    display_snippet += "..."
                line += f"\n> {display_snippet}"

            lines.append(line)
            lines.append("")

        return "\n".join(lines)

    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute citation enhancement."""
        logger.info("Enhancing citations for response")

        start_time = datetime.utcnow()

        try:
            # Step 1: Extract citations from text
            raw_citations = self._extract_citations(self.response_text)

            if not raw_citations:
                logger.info("No citations found in text")
                return SkillResult(
                    skill_id=context.skill_id,
                    status=SkillStatus.SUCCESS,
                    started_at=start_time,
                    output={
                        "annotated_text": self.response_text,
                        "citations": [],
                        "citation_count": 0,
                        "enhanced": False
                    }
                )

            logger.info(f"Found {len(raw_citations)} citations to enhance")

            # Step 2: Validate and enhance each citation
            citations = []
            citation_map = {}

            for idx, (full_match, citation_ref) in enumerate(raw_citations, 1):
                citation = await self._validate_and_enhance_citation(citation_ref, idx)
                if citation:
                    citations.append(citation)
                    citation_map[citation_ref] = citation

            # Step 3: Format annotated text
            annotated_text = self._format_annotated_text(
                self.response_text,
                citations,
                citation_map
            )

            # Step 4: Add citation list if footnote format
            if self.citation_format == "footnote":
                annotated_text += self._generate_citation_list(citations)

            # Prepare output
            citations_data = [
                {
                    "citation_id": c.citation_id,
                    "source_id": c.source_id,
                    "source_type": c.source_type,
                    "source_title": c.source_title,
                    "text_snippet": c.text_snippet,
                    "paragraph_index": c.paragraph_index,
                    "start_char": c.start_char,
                    "end_char": c.end_char,
                    "confidence": c.confidence
                }
                for c in citations
            ]

            logger.info(f"Enhanced {len(citations)} citations")

            return SkillResult(
                skill_id=context.skill_id,
                status=SkillStatus.SUCCESS,
                started_at=start_time,
                completed_at=datetime.utcnow(),
                output={
                    "original_text": self.response_text,
                    "annotated_text": annotated_text,
                    "citations": citations_data,
                    "citation_count": len(citations),
                    "citation_format": self.citation_format,
                    "enhanced": True
                }
            )

        except Exception as e:
            logger.error(f"Citation enhancement failed: {e}")
            return SkillResult(
                skill_id=context.skill_id,
                status=SkillStatus.FAILED,
                started_at=start_time,
                completed_at=datetime.utcnow(),
                error_message=str(e),
                output={
                    "original_text": self.response_text,
                    "annotated_text": self.response_text,
                    "citations": [],
                    "citation_count": 0,
                    "enhanced": False,
                    "error": str(e)
                }
            )


# Convenience function for direct usage
async def enhance_response_citations(
    response_text: str,
    source_ids: List[str],
    citation_format: str = "bracket",
    snippet_length: int = 150
) -> EnhancedResponse:
    """Convenience function to enhance citations in a response.

    Args:
        response_text: AI-generated text with citations
        source_ids: List of referenced source IDs
        citation_format: Format style
        snippet_length: Snippet length

    Returns:
        EnhancedResponse with annotations
    """
    config = SkillConfig(
        skill_type="citation_enhancer",
        name="Citation Enhancer",
        parameters={
            "response_text": response_text,
            "source_ids": source_ids,
            "citation_format": citation_format,
            "snippet_length": snippet_length
        }
    )

    enhancer = CitationEnhancer(config)

    from open_notebook.skills.base import SkillContext
    ctx = SkillContext(
        skill_id=f"enhance_{datetime.utcnow().timestamp()}",
        trigger_type="manual"
    )

    result = await enhancer.run(ctx)

    if result.success and result.output.get("enhanced"):
        return EnhancedResponse(
            original_text=result.output["original_text"],
            annotated_text=result.output["annotated_text"],
            citations=[Citation(**c) for c in result.output["citations"]],
            citation_map={c["citation_id"]: Citation(**c) for c in result.output["citations"]}
        )

    # Return original if enhancement failed
    return EnhancedResponse(
        original_text=response_text,
        annotated_text=response_text,
        citations=[],
        citation_map={}
    )


# Register the skill
register_skill(CitationEnhancer)
