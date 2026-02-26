"""Research Assistant - Deep research mode for comprehensive investigation.

This skill provides advanced research capabilities beyond simple Q&A:
1. Multi-round iterative research with sub-query generation
2. Information gathering and cross-source validation
3. Research gap identification
4. Comprehensive report generation with citations
5. Automatic research notes creation

Key Features:
- Iterative depth research (configurable rounds)
- Source quality assessment and fact cross-validation
- Research gap detection
- Structured report generation (executive summary, findings, conclusion)
- Automatic note creation with full research trail
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from loguru import logger

from open_notebook.domain.notebook import Notebook, Note, Source, vector_search
from open_notebook.skills.base import Skill, SkillConfig, SkillContext, SkillResult, SkillStatus
from open_notebook.skills.registry import register_skill


class ResearchDepth(Enum):
    """Research depth levels."""
    QUICK = "quick"  # 1 round, basic synthesis
    STANDARD = "standard"  # 2 rounds, cross-validation
    DEEP = "deep"  # 3+ rounds, comprehensive analysis


class SourceReliability(Enum):
    """Source reliability rating."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


@dataclass
class ResearchFinding:
    """A single research finding with metadata."""
    claim: str
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.8
    sources: List[str] = field(default_factory=list)
    verified: bool = False
    contradictions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "claim": self.claim,
            "evidence": self.evidence,
            "confidence": self.confidence,
            "sources": self.sources,
            "verified": self.verified,
            "contradictions": self.contradictions,
        }


@dataclass
class ResearchRound:
    """A single round of research."""
    round_number: int
    query: str
    sub_queries: List[str] = field(default_factory=list)
    findings: List[ResearchFinding] = field(default_factory=list)
    sources_used: List[str] = field(default_factory=list)
    gaps_identified: List[str] = field(default_factory=list)
    completed_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "round_number": self.round_number,
            "query": self.query,
            "sub_queries": self.sub_queries,
            "findings": [f.to_dict() for f in self.findings],
            "sources_used": self.sources_used,
            "gaps_identified": self.gaps_identified,
            "completed_at": self.completed_at.isoformat(),
        }


@dataclass
class ResearchReport:
    """Complete research report."""
    topic: str
    depth: ResearchDepth
    rounds: List[ResearchRound] = field(default_factory=list)
    executive_summary: str = ""
    key_findings: List[ResearchFinding] = field(default_factory=list)
    contradictions: List[Dict[str, Any]] = field(default_factory=list)
    gaps: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    sources_analyzed: List[Dict[str, Any]] = field(default_factory=list)
    total_sources: int = 0
    confidence_score: float = 0.0
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "topic": self.topic,
            "depth": self.depth.value,
            "rounds": [r.to_dict() for r in self.rounds],
            "executive_summary": self.executive_summary,
            "key_findings": [f.to_dict() for f in self.key_findings],
            "contradictions": self.contradictions,
            "gaps": self.gaps,
            "recommendations": self.recommendations,
            "sources_analyzed": self.sources_analyzed,
            "total_sources": self.total_sources,
            "confidence_score": self.confidence_score,
            "created_at": self.created_at.isoformat(),
        }


class ResearchAssistant(Skill):
    """Deep research assistant for comprehensive investigation.

    This skill performs multi-round iterative research:
    1. Analyzes research question and generates sub-queries
    2. Searches across notebook sources using vector search
    3. Extracts and validates findings
    4. Identifies gaps and performs additional rounds
    5. Generates comprehensive report with citations

    Parameters:
        - notebook_id: Notebook containing source materials
        - research_question: Main research question or topic
        - depth: Research depth (quick, standard, deep)
        - max_rounds: Maximum research rounds (default: 3)
        - min_confidence: Minimum confidence threshold for findings (default: 0.7)
        - source_ids: Limit to specific sources (optional)
        - auto_save_note: Save research as note (default: true)

    Example:
        config = SkillConfig(
            skill_type="research_assistant",
            name="Research Assistant",
            parameters={
                "notebook_id": "notebook:abc123",
                "research_question": "What are the latest developments in quantum computing?",
                "depth": "deep",
                "max_rounds": 3
            }
        )
    """

    skill_type = "research_assistant"
    name = "Research Assistant"
    description = "Deep research mode with iterative investigation and comprehensive report generation"

    parameters_schema = {
        "notebook_id": {
            "type": "string",
            "description": "Notebook ID containing source materials"
        },
        "research_question": {
            "type": "string",
            "description": "Main research question or topic"
        },
        "depth": {
            "type": "string",
            "enum": ["quick", "standard", "deep"],
            "default": "standard",
            "description": "Research depth level"
        },
        "max_rounds": {
            "type": "integer",
            "default": 3,
            "minimum": 1,
            "maximum": 5,
            "description": "Maximum research rounds"
        },
        "min_confidence": {
            "type": "number",
            "default": 0.7,
            "minimum": 0.0,
            "maximum": 1.0,
            "description": "Minimum confidence threshold for findings"
        },
        "source_ids": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Specific source IDs to use (optional)"
        },
        "auto_save_note": {
            "type": "boolean",
            "default": True,
            "description": "Automatically save research as note"
        }
    }

    def __init__(self, config: SkillConfig):
        self.notebook_id: str = config.parameters.get("notebook_id", "")
        self.research_question: str = config.parameters.get("research_question", "")
        self.depth: ResearchDepth = ResearchDepth(config.parameters.get("depth", "standard"))
        self.max_rounds: int = config.parameters.get("max_rounds", 3)
        self.min_confidence: float = config.parameters.get("min_confidence", 0.7)
        self.source_ids: Optional[List[str]] = config.parameters.get("source_ids")
        self.auto_save_note: bool = config.parameters.get("auto_save_note", True)
        super().__init__(config)

    def _validate_config(self) -> None:
        """Validate configuration."""
        super()._validate_config()
        if not self.notebook_id:
            raise ValueError("notebook_id is required")
        if not self.research_question:
            raise ValueError("research_question is required")
        if self.max_rounds < 1 or self.max_rounds > 5:
            raise ValueError("max_rounds must be between 1 and 5")

    def _get_rounds_for_depth(self) -> int:
        """Get number of rounds based on depth setting."""
        depth_rounds = {
            ResearchDepth.QUICK: 1,
            ResearchDepth.STANDARD: 2,
            ResearchDepth.DEEP: min(3, self.max_rounds),
        }
        return min(depth_rounds.get(self.depth, 2), self.max_rounds)

    async def _generate_sub_queries(
        self,
        query: str,
        previous_rounds: List[ResearchRound],
        gaps: List[str]
    ) -> List[str]:
        """Generate sub-queries for research round.

        Args:
            query: Main research question
            previous_rounds: Previous research rounds
            gaps: Identified knowledge gaps

        Returns:
            List of sub-queries
        """
        try:
            from open_notebook.ai.provision import provision_langchain_model

            context = ""
            if previous_rounds:
                context = "\n\nPrevious findings:\n"
                for r in previous_rounds[-2:]:  # Last 2 rounds
                    context += f"\nRound {r.round_number}:\n"
                    for f in r.findings[:3]:  # Top 3 findings
                        context += f"- {f.claim}\n"

            if gaps:
                context += f"\n\nKnowledge gaps to address:\n"
                for gap in gaps:
                    context += f"- {gap}\n"

            prompt = f"""Generate sub-queries for deep research.

Main Research Question: {query}
{context}

Generate 3-5 specific sub-queries that will help investigate this topic thoroughly.
Each sub-query should:
- Focus on a specific aspect of the main question
- Be answerable from source documents
- Build on previous findings if available
- Address identified knowledge gaps

Return as JSON:
{{
  "sub_queries": [
    "specific question 1",
    "specific question 2",
    ...
  ]
}}

Return ONLY the JSON."""

            model = await provision_langchain_model(
                prompt_text=prompt,
                model_id=None,
                default_type="transformation"
            )

            response = await model.ainvoke(prompt)
            response_text = response.content if hasattr(response, 'content') else str(response)

            # Clean and parse
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()

            data = json.loads(response_text)
            return data.get("sub_queries", [query])

        except Exception as e:
            logger.error(f"Sub-query generation failed: {e}")
            return [query]  # Fallback to main query

    async def _search_and_extract(
        self,
        sub_queries: List[str],
        sources: List[Source]
    ) -> Tuple[List[ResearchFinding], List[str]]:
        """Search sources and extract findings.

        Args:
            sub_queries: Sub-queries to search
            sources: Available sources

        Returns:
            Tuple of (findings, source_ids_used)
        """
        findings = []
        sources_used = set()

        for sub_query in sub_queries:
            try:
                # Vector search for relevant content
                results = await vector_search(sub_query, limit=5, include_embeddings=False)

                if not results:
                    continue

                # Track sources
                for result in results:
                    source_id = result.get("id", "")
                    if source_id:
                        sources_used.add(str(source_id))

                # Extract findings using AI
                finding = await self._extract_finding(sub_query, results)
                if finding and finding.confidence >= self.min_confidence:
                    findings.append(finding)

            except Exception as e:
                logger.warning(f"Search failed for '{sub_query}': {e}")
                continue

        return findings, list(sources_used)

    async def _extract_finding(
        self,
        query: str,
        search_results: List[Dict[str, Any]]
    ) -> Optional[ResearchFinding]:
        """Extract a structured finding from search results.

        Args:
            query: The query being answered
            search_results: Vector search results

        Returns:
            ResearchFinding or None
        """
        try:
            from open_notebook.ai.provision import provision_langchain_model

            # Prepare context from search results
            context = "\n\n".join([
                f"Source: {r.get('title', 'Unknown')}\n{r.get('text', r.get('full_text', ''))[:1500]}"
                for r in search_results[:3]
            ])

            source_ids = [str(r.get("id", "")) for r in search_results[:3] if r.get("id")]

            prompt = f"""Extract a research finding from the following information.

Query: {query}

Source Material:
{context}

Extract a finding in this JSON format:
{{
  "claim": "The main claim or finding (1-2 sentences)",
  "confidence": 0.85,
  "evidence": [
    {{
      "quote": "Relevant quote from source",
      "source": "source title"
    }}
  ],
  "key_points": ["point1", "point2"]
}}

Guidelines:
- Claim should be specific and verifiable
- Confidence 0.0-1.0 based on source quality and clarity
- Include direct quotes as evidence
- Note any uncertainties or limitations

Return ONLY the JSON."""

            model = await provision_langchain_model(
                prompt_text=prompt,
                model_id=None,
                default_type="transformation"
            )

            response = await model.ainvoke(prompt)
            response_text = response.content if hasattr(response, 'content') else str(response)

            # Clean and parse
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()

            data = json.loads(response_text)

            return ResearchFinding(
                claim=data.get("claim", ""),
                evidence=data.get("evidence", []),
                confidence=data.get("confidence", 0.7),
                sources=source_ids,
            )

        except Exception as e:
            logger.error(f"Finding extraction failed: {e}")
            return None

    async def _identify_gaps(
        self,
        findings: List[ResearchFinding],
        query: str
    ) -> List[str]:
        """Identify knowledge gaps from findings.

        Args:
            findings: Current findings
            query: Research question

        Returns:
            List of identified gaps
        """
        if len(findings) < 2:
            return []

        try:
            from open_notebook.ai.provision import provision_langchain_model

            findings_text = "\n".join([
                f"- {f.claim} (confidence: {f.confidence})"
                for f in findings
            ])

            prompt = f"""Identify knowledge gaps based on these research findings.

Research Question: {query}

Current Findings:
{findings_text}

What important questions remain unanswered? What aspects need further investigation?

Return as JSON:
{{
  "gaps": [
    "specific knowledge gap 1",
    "specific knowledge gap 2"
  ]
}}

Return ONLY the JSON."""

            model = await provision_langchain_model(
                prompt_text=prompt,
                model_id=None,
                default_type="transformation"
            )

            response = await model.ainvoke(prompt)
            response_text = response.content if hasattr(response, 'content') else str(response)

            # Clean and parse
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()

            data = json.loads(response_text)
            return data.get("gaps", [])

        except Exception as e:
            logger.warning(f"Gap identification failed: {e}")
            return []

    async def _cross_validate_findings(
        self,
        findings: List[ResearchFinding]
    ) -> List[ResearchFinding]:
        """Cross-validate findings across sources.

        Args:
            findings: Findings to validate

        Returns:
            Validated findings with updated confidence
        """
        if len(findings) < 2:
            return findings

        validated = []

        for finding in findings:
            # Check for supporting evidence from multiple sources
            if len(finding.sources) >= 2:
                finding.verified = True
                finding.confidence = min(finding.confidence * 1.1, 1.0)
            else:
                # Check for similar claims in other findings
                for other in findings:
                    if other != finding and self._claims_similar(finding.claim, other.claim):
                        finding.verified = True
                        finding.confidence = min(finding.confidence * 1.05, 1.0)
                        break

            validated.append(finding)

        return validated

    def _claims_similar(self, claim1: str, claim2: str) -> bool:
        """Check if two claims are similar (simple heuristic).

        Args:
            claim1: First claim
            claim2: Second claim

        Returns:
            True if claims appear similar
        """
        # Simple word overlap check
        words1 = set(claim1.lower().split())
        words2 = set(claim2.lower().split())

        if not words1 or not words2:
            return False

        overlap = len(words1 & words2)
        similarity = overlap / max(len(words1), len(words2))

        return similarity > 0.5

    async def _generate_report(
        self,
        rounds: List[ResearchRound],
        query: str
    ) -> ResearchReport:
        """Generate comprehensive research report.

        Args:
            rounds: All research rounds
            query: Original research question

        Returns:
            Complete research report
        """
        # Collect all findings
        all_findings = []
        all_sources = set()
        all_gaps = []

        for round_data in rounds:
            all_findings.extend(round_data.findings)
            all_sources.update(round_data.sources_used)
            all_gaps.extend(round_data.gaps_identified)

        # Cross-validate
        validated_findings = await self._cross_validate_findings(all_findings)

        # Sort by confidence
        validated_findings.sort(key=lambda f: f.confidence, reverse=True)

        # Get top findings
        key_findings = validated_findings[:10]

        # Calculate overall confidence
        if key_findings:
            confidence_score = sum(f.confidence for f in key_findings) / len(key_findings)
        else:
            confidence_score = 0.0

        # Generate executive summary
        try:
            from open_notebook.ai.provision import provision_langchain_model

            findings_text = "\n".join([
                f"- {f.claim} (verified: {f.verified})"
                for f in key_findings[:5]
            ])

            prompt = f"""Write an executive summary for this research.

Research Question: {query}

Key Findings:
{findings_text}

Write a 2-3 paragraph executive summary that:
1. Introduces the research topic
2. Highlights the most important findings
3. Provides overall assessment

Be concise but informative."""

            model = await provision_langchain_model(
                prompt_text=prompt,
                model_id=None,
                default_type="transformation"
            )

            response = await model.ainvoke(prompt)
            executive_summary = response.content if hasattr(response, 'content') else str(response)

            # Generate recommendations
            rec_prompt = f"""Based on this research, provide recommendations.

Research Question: {query}
Key Findings: {len(key_findings)} findings
Knowledge Gaps: {len(all_gaps)} gaps identified

Provide 2-3 recommendations for:
1. Next steps for further research
2. How to apply these findings
3. Areas needing additional investigation

Return as bullet points."""

            rec_response = await model.ainvoke(rec_prompt)
            rec_text = rec_response.content if hasattr(rec_response, 'content') else str(rec_response)
            recommendations = [r.strip("- ").strip() for r in rec_text.split("\n") if r.strip().startswith("-")]

        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            executive_summary = f"Research on: {query}"
            recommendations = []

        # Build sources analyzed list
        sources_analyzed = []
        for source_id in all_sources:
            try:
                source = await Source.get(source_id)
                if source:
                    sources_analyzed.append({
                        "id": str(source_id),
                        "title": source.title or "Untitled",
                        "source_type": getattr(source, "source_type", "unknown"),
                    })
            except Exception:
                continue

        return ResearchReport(
            topic=query,
            depth=self.depth,
            rounds=rounds,
            executive_summary=executive_summary,
            key_findings=key_findings,
            gaps=list(set(all_gaps)),
            recommendations=recommendations,
            sources_analyzed=sources_analyzed,
            total_sources=len(sources_analyzed),
            confidence_score=confidence_score,
        )

    async def _save_research_note(
        self,
        notebook_id: str,
        report: ResearchReport
    ) -> Optional[str]:
        """Save research report as note.

        Args:
            notebook_id: Notebook to save to
            report: Research report

        Returns:
            Note ID or None
        """
        try:
            # Format report as markdown
            content = f"""# Research Report: {report.topic}

## Executive Summary

{report.executive_summary}

## Research Parameters
- **Depth**: {report.depth.value.title()}
- **Rounds**: {len(report.rounds)}
- **Sources Analyzed**: {report.total_sources}
- **Confidence Score**: {report.confidence_score:.0%}

## Key Findings

"""
            for i, finding in enumerate(report.key_findings[:10], 1):
                verified_mark = "✓" if finding.verified else "~"
                content += f"""### {i}. [{verified_mark}] {finding.claim}

- **Confidence**: {finding.confidence:.0%}
- **Sources**: {len(finding.sources)}

"""
                if finding.evidence:
                    content += "**Evidence:**\n"
                    for ev in finding.evidence[:2]:
                        content += f"- \"{ev.get('quote', '')[:150]}...\"\n"
                    content += "\n"

            if report.gaps:
                content += "## Knowledge Gaps\n\n"
                for gap in report.gaps:
                    content += f"- {gap}\n"
                content += "\n"

            if report.recommendations:
                content += "## Recommendations\n\n"
                for rec in report.recommendations:
                    content += f"- {rec}\n"
                content += "\n"

            content += f"""## Sources

"""
            for src in report.sources_analyzed[:20]:
                content += f"- {src.get('title', 'Untitled')}\n"

            content += f"""
---
*Research completed on {report.created_at.strftime('%Y-%m-%d %H:%M')}*
"""

            # Create note
            note = Note(
                title=f"Research: {report.topic[:50]}",
                content=content,
                note_type="ai",
            )
            await note.save()
            await note.add_to_notebook(notebook_id)

            logger.info(f"Research note saved: {note.id}")
            return str(note.id) if note.id else None

        except Exception as e:
            logger.error(f"Failed to save research note: {e}")
            return None

    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute deep research."""
        logger.info(f"Starting research on: {self.research_question}")

        start_time = datetime.utcnow()

        try:
            # 1. Get notebook and sources
            notebook = await Notebook.get(self.notebook_id)
            if not notebook:
                raise ValueError(f"Notebook {self.notebook_id} not found")

            if self.source_ids:
                sources = []
                for sid in self.source_ids:
                    source = await Source.get(sid)
                    if source:
                        sources.append(source)
            else:
                sources = await notebook.get_sources()

            if not sources:
                return SkillResult(
                    skill_id=context.skill_id,
                    status=SkillStatus.FAILED,
                    started_at=start_time,
                    error_message="No sources found in notebook"
                )

            logger.info(f"Researching with {len(sources)} sources")

            # 2. Determine number of rounds
            num_rounds = self._get_rounds_for_depth()
            logger.info(f"Research depth: {self.depth.value}, rounds: {num_rounds}")

            # 3. Execute research rounds
            rounds = []
            gaps = []

            for round_num in range(1, num_rounds + 1):
                logger.info(f"Starting research round {round_num}")

                # Generate sub-queries
                sub_queries = await self._generate_sub_queries(
                    self.research_question,
                    rounds,
                    gaps
                )

                # Search and extract findings
                findings, sources_used = await self._search_and_extract(
                    sub_queries,
                    sources
                )

                # Identify gaps for next round
                if round_num < num_rounds:
                    gaps = await self._identify_gaps(findings, self.research_question)

                # Create round record
                round_data = ResearchRound(
                    round_number=round_num,
                    query=self.research_question,
                    sub_queries=sub_queries,
                    findings=findings,
                    sources_used=sources_used,
                    gaps_identified=gaps,
                )
                rounds.append(round_data)

                logger.info(f"Round {round_num} complete: {len(findings)} findings")

                # Early exit if no gaps and we have findings
                if not gaps and findings and round_num >= 2:
                    logger.info("No gaps identified, concluding research early")
                    break

            # 4. Generate comprehensive report
            report = await self._generate_report(rounds, self.research_question)
            logger.info(f"Research report generated: {len(report.key_findings)} key findings")

            # 5. Save as note if enabled
            note_id = None
            if self.auto_save_note:
                note_id = await self._save_research_note(self.notebook_id, report)

            return SkillResult(
                skill_id=context.skill_id,
                status=SkillStatus.SUCCESS,
                started_at=start_time,
                completed_at=datetime.utcnow(),
                output={
                    "research_report": report.to_dict(),
                    "note_id": note_id,
                    "stats": {
                        "rounds_completed": len(rounds),
                        "total_findings": sum(len(r.findings) for r in rounds),
                        "sources_used": report.total_sources,
                        "confidence_score": report.confidence_score,
                    },
                    "query_info": {
                        "original_question": self.research_question,
                        "depth": self.depth.value,
                    }
                }
            )

        except Exception as e:
            logger.error(f"Research failed: {e}")
            return SkillResult(
                skill_id=context.skill_id,
                status=SkillStatus.FAILED,
                started_at=start_time,
                completed_at=datetime.utcnow(),
                error_message=str(e)
            )


# Convenience functions
async def conduct_research(
    notebook_id: str,
    research_question: str,
    depth: str = "standard",
    max_rounds: int = 3
) -> Optional[ResearchReport]:
    """Conduct deep research on a topic.

    Args:
        notebook_id: Notebook ID
        research_question: Research question
        depth: Research depth (quick, standard, deep)
        max_rounds: Maximum rounds

    Returns:
        ResearchReport or None
    """
    config = SkillConfig(
        skill_type="research_assistant",
        name="Research Assistant",
        parameters={
            "notebook_id": notebook_id,
            "research_question": research_question,
            "depth": depth,
            "max_rounds": max_rounds,
            "auto_save_note": True,
        }
    )

    assistant = ResearchAssistant(config)

    from open_notebook.skills.base import SkillContext
    ctx = SkillContext(
        skill_id=f"research_{datetime.utcnow().timestamp()}",
        trigger_type="manual"
    )

    result = await assistant.run(ctx)

    if result.success and result.output.get("research_report"):
        report_data = result.output["research_report"]
        # Reconstruct ResearchReport from dict
        return ResearchReport(
            topic=report_data["topic"],
            depth=ResearchDepth(report_data["depth"]),
            executive_summary=report_data.get("executive_summary", ""),
            confidence_score=report_data.get("confidence_score", 0.0),
            total_sources=report_data.get("total_sources", 0),
        )

    return None


# Register the skill
register_skill(ResearchAssistant)
