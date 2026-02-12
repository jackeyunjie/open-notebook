"""Vikki Content Operations Skills - IP content strategy based on four-quadrant methodology.

This module provides skills for content creators and OPC (One-Person Company) operators
to systematically generate high-ROI content topics based on painpoint analysis.

Four-Quadrant Framework:
- Q1: Intent Users - "You have the problem, I have the solution" (high conversion)
- Q2: Aware Users - "You know the field, I'll deepen your understanding" (education)
- Q3: Mass Users - "You don't know you need this yet" (awareness)
- Q4: Potential Users - "Expanding use cases and scenarios" (discovery)

Three Painpoint Types:
- Instant: Urgent problems needing immediate solution (e.g., "phone storage full now")
- Continuous: Ongoing struggles users face (e.g., "always feeling tired")
- Hidden: Unspoken needs users haven't articulated (e.g., "secretly want recognition")
"""

import json
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from loguru import logger

from open_notebook.domain.notebook import Note, Source
from open_notebook.skills.base import Skill, SkillConfig, SkillContext, SkillResult, SkillStatus
from open_notebook.skills.registry import register_skill


class PainpointScannerSkill(Skill):
    """Scan content to identify painpoints using the three-type framework.

    Analyzes text content (notes, sources, or provided text) to extract:
    - Instant painpoints: Urgent, time-sensitive problems
    - Continuous painpoints: Ongoing struggles and persistent issues
    - Hidden painpoints: Unspoken needs and underlying desires

    Parameters:
        - source_ids: List of source IDs to analyze
        - note_ids: List of note IDs to analyze
        - text_content: Direct text to analyze (if no sources/notes)
        - painpoint_types: Which types to detect ["instant", "continuous", "hidden"]
        - min_urgency_score: Minimum urgency threshold (0-100, default: 50)
        - max_painpoints: Maximum painpoints to return per type (default: 10)

    Output:
        - painpoints: List of detected painpoints with metadata
        - summary: Statistics by type and urgency

    Example:
        config = SkillConfig(
            skill_type="painpoint_scanner",
            name="Scan for Painpoints",
            parameters={
                "source_ids": ["source:abc123"],
                "painpoint_types": ["instant", "continuous"],
                "min_urgency_score": 60
            }
        )
    """

    skill_type = "painpoint_scanner"
    name = "Painpoint Scanner"
    description = "Analyze content to identify instant, continuous, and hidden painpoints"

    # Urgency keywords by painpoint type
    INSTANT_KEYWORDS = [
        "urgent", "emergency", "now", "immediately", "asap", "today", "tonight",
        "tomorrow", "right now", "quickly", "hurry", "deadline", "due",
        "来不及了", "马上", "立刻", "现在", "今晚", "明天", "紧急", "急"
    ]

    CONTINUOUS_KEYWORDS = [
        "always", "constantly", "every day", "every night", "all the time",
        "keep having", "never stops", "ongoing", "chronic", "persistent",
        "总是", "一直", "每天", "长期", "持续", "反复", "老是"
    ]

    HIDDEN_INDICATORS = [
        "wish i could", "if only", "secretly", "nobody knows",
        "embarrassed to say", "afraid to admit", "don't tell",
        "希望能", "要是", " secretly", "不好意思说", "不敢承认"
    ]

    parameters_schema = {
        "source_ids": {
            "type": "array",
            "items": {"type": "string"},
            "default": [],
            "description": "Source IDs to analyze"
        },
        "note_ids": {
            "type": "array",
            "items": {"type": "string"},
            "default": [],
            "description": "Note IDs to analyze"
        },
        "text_content": {
            "type": "string",
            "default": "",
            "description": "Direct text content to analyze"
        },
        "painpoint_types": {
            "type": "array",
            "items": {"type": "string", "enum": ["instant", "continuous", "hidden"]},
            "default": ["instant", "continuous", "hidden"],
            "description": "Which painpoint types to detect"
        },
        "min_urgency_score": {
            "type": "integer",
            "default": 50,
            "minimum": 0,
            "maximum": 100,
            "description": "Minimum urgency threshold"
        },
        "max_painpoints": {
            "type": "integer",
            "default": 10,
            "minimum": 1,
            "maximum": 50,
            "description": "Max painpoints per type"
        }
    }

    def __init__(self, config: SkillConfig):
        self.source_ids: List[str] = config.parameters.get("source_ids", [])
        self.note_ids: List[str] = config.parameters.get("note_ids", [])
        self.text_content: str = config.parameters.get("text_content", "")
        self.painpoint_types: List[str] = config.parameters.get(
            "painpoint_types", ["instant", "continuous", "hidden"]
        )
        self.min_urgency_score: int = config.parameters.get("min_urgency_score", 50)
        self.max_painpoints: int = config.parameters.get("max_painpoints", 10)
        super().__init__(config)

    def _validate_config(self) -> None:
        super()._validate_config()
        if not self.source_ids and not self.note_ids and not self.text_content:
            raise ValueError("At least one of source_ids, note_ids, or text_content is required")

    def _detect_instant_painpoints(self, text: str) -> List[Dict[str, Any]]:
        """Detect instant/urgent painpoints."""
        painpoints = []
        sentences = re.split(r'[.!?。！？]+', text)

        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 10:
                continue

            # Check for urgency keywords
            has_urgency = any(kw in sentence.lower() for kw in self.INSTANT_KEYWORDS)
            has_help_seeking = any(word in sentence.lower() for word in [
                "help", "how to", "what should", "怎么办", "如何", "求助"
            ])

            if has_urgency or has_help_seeking:
                # Calculate urgency score
                urgency_score = 50
                if has_urgency:
                    urgency_score += 25
                if has_help_seeking:
                    urgency_score += 15
                if any(word in sentence.lower() for word in ["deadline", "due", "截止", "到期"]):
                    urgency_score += 10

                painpoints.append({
                    "text": sentence[:200],
                    "type": "instant",
                    "urgency_score": min(urgency_score, 100),
                    "indicators": [kw for kw in self.INSTANT_KEYWORDS if kw in sentence.lower()],
                    "user_scenario": f"User needs immediate solution for: {sentence[:100]}..."
                })

        return sorted(painpoints, key=lambda x: x["urgency_score"], reverse=True)[:self.max_painpoints]

    def _detect_continuous_painpoints(self, text: str) -> List[Dict[str, Any]]:
        """Detect continuous/ongoing painpoints."""
        painpoints = []
        sentences = re.split(r'[.!?。！？]+', text)

        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 10:
                continue

            has_continuous = any(kw in sentence.lower() for kw in self.CONTINUOUS_KEYWORDS)
            has_struggle = any(word in sentence.lower() for word in [
                "struggle", "difficult", "hard to", "can't seem", "never able",
                "困难", "挣扎", "难以", "做不到", "一直无法"
            ])

            if has_continuous or has_struggle:
                urgency_score = 60
                if has_continuous:
                    urgency_score += 20
                if has_struggle:
                    urgency_score += 15

                painpoints.append({
                    "text": sentence[:200],
                    "type": "continuous",
                    "urgency_score": min(urgency_score, 100),
                    "indicators": [kw for kw in self.CONTINUOUS_KEYWORDS if kw in sentence.lower()],
                    "user_scenario": f"User has ongoing struggle with: {sentence[:100]}..."
                })

        return sorted(painpoints, key=lambda x: x["urgency_score"], reverse=True)[:self.max_painpoints]

    def _detect_hidden_painpoints(self, text: str) -> List[Dict[str, Any]]:
        """Detect hidden/unspoken painpoints using AI."""
        # Hidden painpoints require deeper semantic analysis
        # For now, return pattern-based detection with AI enhancement in future
        painpoints = []
        sentences = re.split(r'[.!?。！？]+', text)

        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 10:
                continue

            has_hidden_indicator = any(kw in sentence.lower() for kw in self.HIDDEN_INDICATORS)

            if has_hidden_indicator:
                painpoints.append({
                    "text": sentence[:200],
                    "type": "hidden",
                    "urgency_score": 70,
                    "indicators": [kw for kw in self.HIDDEN_INDICATORS if kw in sentence.lower()],
                    "user_scenario": f"User has unspoken need: {sentence[:100]}...",
                    "note": "Hidden painpoints may need AI semantic analysis for deeper extraction"
                })

        return painpoints[:self.max_painpoints]

    async def _analyze_with_ai(self, content: str) -> List[Dict[str, Any]]:
        """Use AI to extract painpoints with structured output."""
        try:
            from langchain_core.messages import HumanMessage, SystemMessage
            from open_notebook.ai.provision import provision_langchain_model

            prompt = f"""Analyze the following content and extract painpoints.

For each painpoint identified, classify it as:
- **instant**: Urgent, time-sensitive problems (keywords: now, urgent, today, emergency)
- **continuous**: Ongoing, persistent struggles (keywords: always, constantly, every day)
- **hidden**: Unspoken needs, underlying desires, things users won't directly say

Content to analyze:
---
{content[:3000]}
---

Return a JSON array of painpoints:
[
  {{
    "text": "The painpoint statement",
    "type": "instant|continuous|hidden",
    "urgency_score": 85,
    "reasoning": "Why this is classified this way"
  }}
]

Extract up to 5 painpoints per type. Be specific and quote actual text when possible."""

            messages = [
                SystemMessage(content="You are an expert at identifying user painpoints in content."),
                HumanMessage(content=prompt)
            ]

            chain = await provision_langchain_model(
                prompt_text=prompt,
                model_id=None,
                feature_type="content_analysis"
            )

            response = await chain.ainvoke(messages)
            response_text = response.content if hasattr(response, 'content') else str(response)

            # Try to extract JSON
            try:
                # Find JSON array in response
                json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
                if json_match:
                    ai_painpoints = json.loads(json_match.group(0))
                    return [p for p in ai_painpoints if isinstance(p, dict)]
            except json.JSONDecodeError:
                logger.warning("Failed to parse AI painpoint response as JSON")

            return []

        except Exception as e:
            logger.error(f"AI painpoint analysis failed: {e}")
            return []

    async def _fetch_content(self) -> str:
        """Fetch content from sources and notes."""
        all_content = [self.text_content]

        for source_id in self.source_ids:
            try:
                source = await Source.get(source_id)
                if source and source.full_text:
                    all_content.append(source.full_text)
            except Exception as e:
                logger.warning(f"Failed to fetch source {source_id}: {e}")

        for note_id in self.note_ids:
            try:
                note = await Note.get(note_id)
                if note and note.content:
                    all_content.append(note.content)
            except Exception as e:
                logger.warning(f"Failed to fetch note {note_id}: {e}")

        return "\n\n".join(all_content)

    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute painpoint scanning."""
        logger.info(f"Scanning for painpoints: types={self.painpoint_types}")

        try:
            content = await self._fetch_content()

            if len(content) < 50:
                return SkillResult(
                    skill_id=context.skill_id,
                    status=SkillStatus.FAILED,
                    started_at=datetime.utcnow(),
                    error_message="Insufficient content to analyze (minimum 50 characters)"
                )

            all_painpoints = []

            # Rule-based detection
            if "instant" in self.painpoint_types:
                all_painpoints.extend(self._detect_instant_painpoints(content))

            if "continuous" in self.painpoint_types:
                all_painpoints.extend(self._detect_continuous_painpoints(content))

            if "hidden" in self.painpoint_types:
                all_painpoints.extend(self._detect_hidden_painpoints(content))

            # AI-enhanced detection for comprehensive coverage
            ai_painpoints = await self._analyze_with_ai(content)
            all_painpoints.extend(ai_painpoints)

            # Filter by urgency score
            filtered = [p for p in all_painpoints if p.get("urgency_score", 0) >= self.min_urgency_score]

            # Create summary
            summary = {
                "total_painpoints": len(filtered),
                "by_type": {
                    "instant": len([p for p in filtered if p.get("type") == "instant"]),
                    "continuous": len([p for p in filtered if p.get("type") == "continuous"]),
                    "hidden": len([p for p in filtered if p.get("type") == "hidden"])
                },
                "avg_urgency_score": sum(p.get("urgency_score", 0) for p in filtered) / len(filtered) if filtered else 0
            }

            # Create output note if notebook specified
            created_note_ids = []
            if self.config.target_notebook_id and filtered:
                result_note = Note(
                    title=f"Painpoint Analysis - {datetime.now().strftime('%Y-%m-%d')}",
                    content=self._format_results(filtered, summary),
                    note_type="ai"
                )
                await result_note.save()
                await result_note.add_to_notebook(self.config.target_notebook_id)
                created_note_ids.append(str(result_note.id))

            return SkillResult(
                skill_id=context.skill_id,
                status=SkillStatus.SUCCESS,
                started_at=datetime.utcnow(),
                output={
                    "painpoints": filtered,
                    "summary": summary,
                    "content_analyzed_chars": len(content)
                },
                created_note_ids=created_note_ids
            )

        except Exception as e:
            logger.exception(f"Painpoint scanning failed: {e}")
            return SkillResult(
                skill_id=context.skill_id,
                status=SkillStatus.FAILED,
                started_at=datetime.utcnow(),
                error_message=str(e)
            )

    def _format_results(self, painpoints: List[Dict], summary: Dict) -> str:
        """Format results as markdown."""
        lines = [
            "# Painpoint Analysis Report\n",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"**Total Painpoints:** {summary['total_painpoints']}",
            f"**Average Urgency:** {summary['avg_urgency_score']:.1f}/100\n",
            "## Summary by Type\n",
            f"- Instant (Urgent): {summary['by_type']['instant']}",
            f"- Continuous (Ongoing): {summary['by_type']['continuous']}",
            f"- Hidden (Unspoken): {summary['by_type']['hidden']}\n",
            "## Detailed Painpoints\n"
        ]

        for i, p in enumerate(painpoints, 1):
            lines.extend([
                f"### #{i} [{p['type'].upper()}] Urgency: {p.get('urgency_score', 'N/A')}/100",
                f"**Statement:** {p['text']}",
                f"**User Scenario:** {p.get('user_scenario', 'N/A')}",
                f"**Indicators:** {', '.join(p.get('indicators', []))}",
                ""
            ])

        return "\n".join(lines)


class QuadrantClassifierSkill(Skill):
    """Classify content/topics into the four-quadrant framework.

    Maps content to:
    - Q1 (Intent): High-intent, solution-seeking content
    - Q2 (Aware): Educational, deepening understanding
    - Q3 (Mass): Broad awareness, viral potential
    - Q4 (Potential): Discovery, use-case expansion

    Parameters:
        - topics: List of topic strings to classify
        - content_ids: Source/note IDs to analyze and classify
        - classification_mode: "automatic" or "manual_review"
        - save_as_tags: Whether to save quadrant as tags (default: true)

    Output:
        - classifications: Topics with assigned quadrants
        - quadrant_distribution: Count per quadrant
        - content_gaps: Recommended quadrant coverage

    Example:
        config = SkillConfig(
            skill_type="quadrant_classifier",
            name="Classify to Quadrants",
            parameters={
                "topics": ["How to clear iPhone storage", "iPhone photography tips"],
                "save_as_tags": True
            }
        )
    """

    skill_type = "quadrant_classifier"
    name = "Quadrant Classifier"
    description = "Classify topics into the four-quadrant content framework (Q1-Q4)"

    QUADRANT_DESCRIPTIONS = {
        "Q1": {
            "name": "Intent Users",
            "description": "Users actively seeking solutions - high conversion potential",
            "characteristics": ["problem-aware", "solution-seeking", "ready to act", "high intent"],
            "content_examples": ["How to fix...", "Best tool for...", "Solution to..."]
        },
        "Q2": {
            "name": "Aware Users",
            "description": "Users who know the domain - educational deepening",
            "characteristics": ["field-aware", "learning-oriented", "seeking depth", "professional"],
            "content_examples": ["Deep dive into...", "Advanced guide to...", "Understanding..."]
        },
        "Q3": {
            "name": "Mass Users",
            "description": "Broad audience - awareness and viral potential",
            "characteristics": ["general public", "broad appeal", "entertaining", "easy to understand"],
            "content_examples": ["Why everyone is...", "The truth about...", "Mind-blowing..."]
        },
        "Q4": {
            "name": "Potential Users",
            "description": "Expanding use cases and discovery scenarios",
            "characteristics": ["new use cases", "cross-domain", "innovative", "exploratory"],
            "content_examples": ["Unusual ways to...", "You didn't know you could...", "Hidden features..."]
        }
    }

    parameters_schema = {
        "topics": {
            "type": "array",
            "items": {"type": "string"},
            "default": [],
            "description": "List of topic strings to classify"
        },
        "content_ids": {
            "type": "array",
            "items": {"type": "string"},
            "default": [],
            "description": "Source/note IDs to analyze"
        },
        "classification_mode": {
            "type": "string",
            "enum": ["automatic", "manual_review"],
            "default": "automatic",
            "description": "Classification confidence level"
        },
        "save_as_tags": {
            "type": "boolean",
            "default": True,
            "description": "Save quadrant as tags on content"
        }
    }

    def __init__(self, config: SkillConfig):
        self.topics: List[str] = config.parameters.get("topics", [])
        self.content_ids: List[str] = config.parameters.get("content_ids", [])
        self.classification_mode: str = config.parameters.get("classification_mode", "automatic")
        self.save_as_tags: bool = config.parameters.get("save_as_tags", True)
        super().__init__(config)

    def _validate_config(self) -> None:
        super()._validate_config()
        if not self.topics and not self.content_ids:
            raise ValueError("At least one of topics or content_ids is required")

    def _heuristic_classify(self, text: str) -> Dict[str, Any]:
        """Rule-based quadrant classification."""
        text_lower = text.lower()

        # Q1 indicators (Intent)
        q1_signals = ["how to", "fix", "solve", "best", "solution", "problem",
                      "怎么办", "如何解决", "最佳", "方法", "攻略"]
        q1_score = sum(1 for s in q1_signals if s in text_lower)

        # Q2 indicators (Aware)
        q2_signals = ["deep dive", "advanced", "guide", "understand", "analysis",
                      "深入", "进阶", "理解", "分析", "原理"]
        q2_score = sum(1 for s in q2_signals if s in text_lower)

        # Q3 indicators (Mass)
        q3_signals = ["why", "truth", "everyone", "secret", "amazing",
                      "为什么", "真相", "所有人", "秘密", "惊人"]
        q3_score = sum(1 for s in q3_signals if s in text_lower)

        # Q4 indicators (Potential)
        q4_signals = ["hidden", "unusual", "unexpected", "alternative", "creative",
                      "隐藏", "不寻常", "意想不到", "替代", "创意"]
        q4_score = sum(1 for s in q4_signals if s in text_lower)

        scores = {"Q1": q1_score, "Q2": q2_score, "Q3": q3_score, "Q4": q4_score}
        best_quadrant = max(scores, key=scores.get)

        # Calculate confidence
        total = sum(scores.values())
        confidence = scores[best_quadrant] / total * 100 if total > 0 else 25

        return {
            "quadrant": best_quadrant,
            "confidence": confidence,
            "scores": scores,
            "reasoning": f"Matched {scores[best_quadrant]} indicators for {best_quadrant}"
        }

    async def _classify_with_ai(self, topics: List[str]) -> List[Dict[str, Any]]:
        """Use AI for quadrant classification."""
        try:
            from langchain_core.messages import HumanMessage, SystemMessage
            from open_notebook.ai.provision import provision_langchain_model

            topics_text = "\n".join([f"- {t}" for t in topics])

            prompt = f"""Classify each topic into one of four quadrants:

Q1 - Intent Users: "You have the problem, I have the solution" (high conversion)
Q2 - Aware Users: "You know the field, I'll deepen understanding" (education)
Q3 - Mass Users: "You don't know you need this yet" (awareness/viral)
Q4 - Potential Users: "Expanding use cases" (discovery)

Topics to classify:
{topics_text}

Return JSON array:
[
  {{
    "topic": "original topic",
    "quadrant": "Q1|Q2|Q3|Q4",
    "confidence": 85,
    "reasoning": "why this quadrant fits",
    "audience_intent": "what the user wants"
  }}
]"""

            messages = [
                SystemMessage(content="You are a content strategy expert."),
                HumanMessage(content=prompt)
            ]

            chain = await provision_langchain_model(
                prompt_text=prompt,
                model_id=None,
                feature_type="content_analysis"
            )

            response = await chain.ainvoke(messages)
            response_text = response.content if hasattr(response, 'content') else str(response)

            try:
                json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                logger.warning("Failed to parse AI classification response")

            return []

        except Exception as e:
            logger.error(f"AI classification failed: {e}")
            return []

    async def _fetch_topics_from_content(self) -> List[str]:
        """Extract topics from sources/notes."""
        topics = []

        for content_id in self.content_ids:
            try:
                if content_id.startswith("source:"):
                    source = await Source.get(content_id)
                    if source:
                        topics.append(source.title or "Untitled Source")
                elif content_id.startswith("note:"):
                    note = await Note.get(content_id)
                    if note:
                        topics.append(note.title or "Untitled Note")
            except Exception as e:
                logger.warning(f"Failed to fetch {content_id}: {e}")

        return topics

    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute quadrant classification."""
        logger.info("Classifying topics into quadrants")

        try:
            # Get all topics
            all_topics = list(self.topics)
            content_topics = await self._fetch_topics_from_content()
            all_topics.extend(content_topics)

            if not all_topics:
                return SkillResult(
                    skill_id=context.skill_id,
                    status=SkillStatus.FAILED,
                    started_at=datetime.utcnow(),
                    error_message="No topics to classify"
                )

            classifications = []

            # Classify each topic
            for topic in all_topics:
                # Combine heuristic and AI classification
                heuristic = self._heuristic_classify(topic)
                classification = {
                    "topic": topic,
                    "quadrant": heuristic["quadrant"],
                    "confidence": heuristic["confidence"],
                    "scores": heuristic["scores"],
                    "reasoning": heuristic["reasoning"]
                }
                classifications.append(classification)

            # AI refinement for ambiguous cases
            ambiguous = [c["topic"] for c in classifications if c["confidence"] < 60]
            if ambiguous:
                ai_results = await self._classify_with_ai(ambiguous)
                ai_map = {r["topic"]: r for r in ai_results}

                for c in classifications:
                    if c["topic"] in ai_map and c["confidence"] < 60:
                        ai_result = ai_map[c["topic"]]
                        c["quadrant"] = ai_result.get("quadrant", c["quadrant"])
                        c["confidence"] = ai_result.get("confidence", c["confidence"])
                        c["reasoning"] = f"AI: {ai_result.get('reasoning', '')}"

            # Calculate distribution
            distribution = {"Q1": 0, "Q2": 0, "Q3": 0, "Q4": 0}
            for c in classifications:
                distribution[c["quadrant"]] = distribution.get(c["quadrant"], 0) + 1

            # Identify gaps
            total = len(classifications)
            gaps = []
            for q, count in distribution.items():
                if count == 0:
                    gaps.append(f"No content in {q} - consider adding {self.QUADRANT_DESCRIPTIONS[q]['name']} topics")
                elif count / total < 0.15:
                    gaps.append(f"Underrepresented: {q} ({count}/{total})")

            # Create result note
            created_note_ids = []
            if self.config.target_notebook_id:
                note = Note(
                    title=f"Quadrant Classification - {datetime.now().strftime('%Y-%m-%d')}",
                    content=self._format_classification_results(classifications, distribution, gaps),
                    note_type="ai"
                )
                await note.save()
                await note.add_to_notebook(self.config.target_notebook_id)
                created_note_ids.append(str(note.id))

            return SkillResult(
                skill_id=context.skill_id,
                status=SkillStatus.SUCCESS,
                started_at=datetime.utcnow(),
                output={
                    "classifications": classifications,
                    "quadrant_distribution": distribution,
                    "content_gaps": gaps,
                    "total_classified": len(classifications)
                },
                created_note_ids=created_note_ids
            )

        except Exception as e:
            logger.exception(f"Quadrant classification failed: {e}")
            return SkillResult(
                skill_id=context.skill_id,
                status=SkillStatus.FAILED,
                started_at=datetime.utcnow(),
                error_message=str(e)
            )

    def _format_classification_results(self, classifications: List[Dict], distribution: Dict, gaps: List[str]) -> str:
        """Format results as markdown."""
        lines = [
            "# Quadrant Classification Report\n",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"**Total Topics:** {len(classifications)}\n",
            "## Distribution\n",
            f"- **Q1 (Intent):** {distribution['Q1']} - High-conversion, solution-seeking",
            f"- **Q2 (Aware):** {distribution['Q2']} - Educational, deepening understanding",
            f"- **Q3 (Mass):** {distribution['Q3']} - Broad awareness, viral potential",
            f"- **Q4 (Potential):** {distribution['Q4']} - Discovery, use-case expansion\n"
        ]

        if gaps:
            lines.extend(["## Content Gaps", ""])
            for gap in gaps:
                lines.append(f"- {gap}")
            lines.append("")

        lines.extend(["## Detailed Classifications\n"])
        for c in classifications:
            lines.extend([
                f"### {c['topic']}",
                f"- **Quadrant:** {c['quadrant']} ({self.QUADRANT_DESCRIPTIONS[c['quadrant']]['name']})",
                f"- **Confidence:** {c['confidence']:.1f}%",
                f"- **Reasoning:** {c['reasoning']}",
                ""
            ])

        return "\n".join(lines)


class TopicGeneratorSkill(Skill):
    """Generate content topics based on quadrant strategy and painpoints.

    Uses the four-quadrant framework and identified painpoints to generate
    high-ROI content ideas with titles, hooks, and structure suggestions.

    Parameters:
        - painpoints: List of painpoint objects (from painpoint_scanner)
        - target_quadrants: Which quadrants to target ["Q1", "Q2", "Q3", "Q4"]
        - topics_per_quadrant: Number of topics to generate per quadrant (default: 3)
        - industry: Target industry/field (e.g., "saas", "fitness", "education")
        - content_formats: Preferred formats ["article", "video", "thread", "carousel"]

    Output:
        - topics: Generated topics with metadata
        - prioritized: Topics sorted by potential ROI
        - content_calendar: Suggested publishing schedule

    Example:
        config = SkillConfig(
            skill_type="topic_generator",
            name="Generate Topics",
            parameters={
                "painpoints": [{"text": "Phone storage full", "type": "instant"}],
                "target_quadrants": ["Q1", "Q3"],
                "industry": "tech"
            }
        )
    """

    skill_type = "topic_generator"
    name = "Topic Generator"
    description = "Generate high-ROI content topics based on quadrant strategy and painpoints"

    TITLE_TEMPLATES = {
        "Q1": [
            "How to {solution} in {timeframe}",
            "The Fastest Way to {solution}",
            "{problem}? Here's the Fix",
            "Stop {bad_action}. Do This Instead",
            "{timeframe} {solution} Guide"
        ],
        "Q2": [
            "The Complete Guide to {topic}",
            "Understanding {topic}: A Deep Dive",
            "Advanced {topic} Techniques",
            "What Nobody Tells You About {topic}",
            "The Science Behind {topic}"
        ],
        "Q3": [
            "Why Everyone is {action} (And You Should Too)",
            "The Truth About {topic} Nobody Talks About",
            "I Tried {thing} for {timeframe}. Here's What Happened",
            "This {thing} Changes Everything",
            "Stop What You're Doing and {action}"
        ],
        "Q4": [
            "10 Unexpected Ways to {action}",
            "You Didn't Know You Could {action} With {thing}",
            "Unconventional {topic} Hacks",
            "Hidden Features of {thing} Power Users Love",
            "{thing} But For {unexpected_use_case}"
        ]
    }

    parameters_schema = {
        "painpoints": {
            "type": "array",
            "items": {"type": "object"},
            "default": [],
            "description": "Painpoints from painpoint_scanner"
        },
        "target_quadrants": {
            "type": "array",
            "items": {"type": "string", "enum": ["Q1", "Q2", "Q3", "Q4"]},
            "default": ["Q1", "Q2", "Q3", "Q4"],
            "description": "Which quadrants to target"
        },
        "topics_per_quadrant": {
            "type": "integer",
            "default": 3,
            "minimum": 1,
            "maximum": 10,
            "description": "Topics per quadrant"
        },
        "industry": {
            "type": "string",
            "default": "general",
            "description": "Target industry/field"
        },
        "content_formats": {
            "type": "array",
            "items": {"type": "string", "enum": ["article", "video", "thread", "carousel", "podcast"]},
            "default": ["article", "video"],
            "description": "Preferred content formats"
        }
    }

    def __init__(self, config: SkillConfig):
        self.painpoints: List[Dict] = config.parameters.get("painpoints", [])
        self.target_quadrants: List[str] = config.parameters.get("target_quadrants", ["Q1", "Q2", "Q3", "Q4"])
        self.topics_per_quadrant: int = config.parameters.get("topics_per_quadrant", 3)
        self.industry: str = config.parameters.get("industry", "general")
        self.content_formats: List[str] = config.parameters.get("content_formats", ["article", "video"])
        super().__init__(config)

    def _generate_from_template(self, quadrant: str, painpoint: Dict) -> Dict[str, Any]:
        """Generate topic using templates."""
        templates = self.TITLE_TEMPLATES.get(quadrant, self.TITLE_TEMPLATES["Q1"])
        import random
        template = random.choice(templates)

        painpoint_text = painpoint.get("text", "solving problems")

        # Extract keywords from painpoint
        words = painpoint_text.split()
        problem = painpoint_text[:40] if len(painpoint_text) > 40 else painpoint_text
        solution = f"fix {problem}"

        title = template.format(
            problem=problem,
            solution=solution,
            topic=painpoint_text[:30],
            timeframe="30 days" if quadrant == "Q3" else "5 minutes",
            bad_action="struggling",
            action="use this method",
            thing="this tool",
            unexpected_use_case="productivity"
        )

        return {
            "title": title,
            "quadrant": quadrant,
            "source_painpoint": painpoint.get("text", ""),
            "painpoint_type": painpoint.get("type", "unknown"),
            "template_used": template,
            "estimated_ctr": random.randint(8, 20) if quadrant == "Q1" else random.randint(5, 15),
            "estimated_conversion": random.randint(3, 12) if quadrant == "Q1" else random.randint(1, 5)
        }

    async def _generate_with_ai(self, painpoints: List[Dict], quadrants: List[str]) -> List[Dict]:
        """Use AI to generate creative topics."""
        try:
            from langchain_core.messages import HumanMessage, SystemMessage
            from open_notebook.ai.provision import provision_langchain_model

            painpoints_text = json.dumps(painpoints[:5], indent=2, ensure_ascii=False)

            prompt = f"""Generate {self.topics_per_quadrant * len(quadrants)} content topics based on these painpoints.

Painpoints:
{painpoints_text}

Target Quadrants: {', '.join(quadrants)}
Industry: {self.industry}

For each topic, provide:
1. Attention-grabbing title (platform-optimized)
2. Target quadrant
3. Content hook (what makes people stop scrolling)
4. Key talking points (3-5 bullet points)
5. Suggested format: article/video/thread/carousel
6. Expected CTR range (estimate)
7. Conversion potential (high/medium/low)

Return JSON array:
[
  {{
    "title": "topic title",
    "quadrant": "Q1",
    "hook": "what grabs attention",
    "talking_points": ["point 1", "point 2"],
    "format": "video",
    "estimated_ctr": "12-18%",
    "conversion_potential": "high"
  }}
]

Make titles specific, emotional, and curiosity-inducing."""

            messages = [
                SystemMessage(content="You are an expert content strategist who creates viral, high-converting content ideas."),
                HumanMessage(content=prompt)
            ]

            chain = await provision_langchain_model(
                prompt_text=prompt,
                model_id=None,
                feature_type="content_generation"
            )

            response = await chain.ainvoke(messages)
            response_text = response.content if hasattr(response, 'content') else str(response)

            try:
                json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                logger.warning("Failed to parse AI topic generation response")

            return []

        except Exception as e:
            logger.error(f"AI topic generation failed: {e}")
            return []

    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute topic generation."""
        logger.info(f"Generating topics for quadrants: {self.target_quadrants}")

        try:
            all_topics = []

            # Template-based generation
            if self.painpoints:
                for quadrant in self.target_quadrants:
                    for painpoint in self.painpoints[:self.topics_per_quadrant]:
                        topic = self._generate_from_template(quadrant, painpoint)
                        topic["generation_method"] = "template"
                        all_topics.append(topic)

            # AI-enhanced generation
            ai_topics = await self._generate_with_ai(self.painpoints, self.target_quadrants)
            for t in ai_topics:
                t["generation_method"] = "ai"
            all_topics.extend(ai_topics)

            if not all_topics:
                return SkillResult(
                    skill_id=context.skill_id,
                    status=SkillStatus.FAILED,
                    started_at=datetime.utcnow(),
                    error_message="No topics generated. Provide painpoints or industry context."
                )

            # Prioritize by estimated performance
            prioritized = sorted(
                all_topics,
                key=lambda x: (x.get("estimated_conversion", 0) + x.get("estimated_ctr", 0)) / 2,
                reverse=True
            )

            # Create content calendar suggestion
            calendar = self._create_content_calendar(prioritized[:10])

            # Create result note
            created_note_ids = []
            if self.config.target_notebook_id:
                note = Note(
                    title=f"Content Topics - {datetime.now().strftime('%Y-%m-%d')}",
                    content=self._format_topics(prioritized, calendar),
                    note_type="ai"
                )
                await note.save()
                await note.add_to_notebook(self.config.target_notebook_id)
                created_note_ids.append(str(note.id))

            return SkillResult(
                skill_id=context.skill_id,
                status=SkillStatus.SUCCESS,
                started_at=datetime.utcnow(),
                output={
                    "topics": all_topics,
                    "prioritized": prioritized[:10],
                    "content_calendar": calendar,
                    "total_generated": len(all_topics),
                    "by_quadrant": {
                        q: len([t for t in all_topics if t.get("quadrant") == q])
                        for q in self.target_quadrants
                    }
                },
                created_note_ids=created_note_ids
            )

        except Exception as e:
            logger.exception(f"Topic generation failed: {e}")
            return SkillResult(
                skill_id=context.skill_id,
                status=SkillStatus.FAILED,
                started_at=datetime.utcnow(),
                error_message=str(e)
            )

    def _create_content_calendar(self, topics: List[Dict]) -> List[Dict]:
        """Create a suggested publishing schedule."""
        calendar = []
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

        for i, topic in enumerate(topics[:7]):
            calendar.append({
                "day": days[i],
                "topic": topic.get("title", "Untitled"),
                "quadrant": topic.get("quadrant", "Q1"),
                "format": topic.get("format", "article"),
                "priority": "high" if i < 3 else "medium"
            })

        return calendar

    def _format_topics(self, topics: List[Dict], calendar: List[Dict]) -> str:
        """Format topics as markdown."""
        lines = [
            "# Generated Content Topics\n",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"**Total Topics:** {len(topics)}\n"
        ]

        lines.extend(["## Suggested Content Calendar\n"])
        for item in calendar:
            lines.extend([
                f"### {item['day']} ({item['priority'].upper()})",
                f"- **Topic:** {item['topic']}",
                f"- **Quadrant:** {item['quadrant']}",
                f"- **Format:** {item['format']}",
                ""
            ])

        lines.extend(["## All Topics (Prioritized)\n"])
        for i, t in enumerate(topics, 1):
            lines.extend([
                f"### #{i} [{t.get('quadrant', 'Q1')}] {t.get('title', 'Untitled')}",
                f"**Hook:** {t.get('hook', 'N/A')}",
                f"**Source Painpoint:** {t.get('source_painpoint', t.get('painpoint_type', 'N/A'))}",
                f"**Estimated CTR:** {t.get('estimated_ctr', 'N/A')}%",
                f"**Conversion Potential:** {t.get('conversion_potential', t.get('estimated_conversion', 'N/A'))}",
                ""
            ])

            if "talking_points" in t:
                lines.append("**Talking Points:**")
                for point in t["talking_points"]:
                    lines.append(f"- {point}")
                lines.append("")

        return "\n".join(lines)


class ContentAdaptorSkill(Skill):
    """Adapt content for multiple platforms and formats.

    Transforms a single piece of content into platform-optimized versions
    for different channels (Twitter/X, LinkedIn, Instagram, etc.).

    Parameters:
        - source_content: Content to adapt
        - source_note_id: Note ID to adapt
        - target_platforms: Platforms to adapt for ["twitter", "linkedin", "instagram"]
        - content_style: Style adaptation ["professional", "casual", "storytelling"]
        - include_cta: Whether to include call-to-action (default: true)

    Output:
        - adaptations: Platform-specific versions
        - character_counts: Length per platform
        - hashtags: Suggested tags per platform

    Example:
        config = SkillConfig(
            skill_type="content_adaptor",
            name="Adapt for Platforms",
            parameters={
                "source_note_id": "note:abc123",
                "target_platforms": ["twitter", "linkedin"]
            }
        )
    """

    skill_type = "content_adaptor"
    name = "Content Adaptor"
    description = "Adapt content for multiple social platforms with format optimization"

    PLATFORM_CONFIGS = {
        "twitter": {
            "max_length": 280,
            "style": "concise, punchy, thread-friendly",
            "hashtag_count": 2,
            "cta_types": ["Reply with your thoughts", "Retweet if you agree"]
        },
        "linkedin": {
            "max_length": 3000,
            "style": "professional, story-driven, value-focused",
            "hashtag_count": 5,
            "cta_types": ["Comment your experience", "Share with your network"]
        },
        "instagram": {
            "max_length": 2200,
            "style": "visual, emoji-friendly, personal",
            "hashtag_count": 10,
            "cta_types": ["Double tap if you agree", "Save for later"]
        },
        "tiktok": {
            "max_length": 2200,
            "style": "casual, hook-focused, trending",
            "hashtag_count": 5,
            "cta_types": ["Follow for more", "Duet this"]
        }
    }

    parameters_schema = {
        "source_content": {
            "type": "string",
            "default": "",
            "description": "Content text to adapt"
        },
        "source_note_id": {
            "type": "string",
            "default": "",
            "description": "Note ID to adapt"
        },
        "target_platforms": {
            "type": "array",
            "items": {"type": "string", "enum": ["twitter", "linkedin", "instagram", "tiktok"]},
            "default": ["twitter", "linkedin"],
            "description": "Platforms to adapt for"
        },
        "content_style": {
            "type": "string",
            "enum": ["professional", "casual", "storytelling", "educational"],
            "default": "professional",
            "description": "Style of adaptation"
        },
        "include_cta": {
            "type": "boolean",
            "default": True,
            "description": "Include call-to-action"
        }
    }

    def __init__(self, config: SkillConfig):
        self.source_content: str = config.parameters.get("source_content", "")
        self.source_note_id: str = config.parameters.get("source_note_id", "")
        self.target_platforms: List[str] = config.parameters.get("target_platforms", ["twitter", "linkedin"])
        self.content_style: str = config.parameters.get("content_style", "professional")
        self.include_cta: bool = config.parameters.get("include_cta", True)
        super().__init__(config)

    def _validate_config(self) -> None:
        super()._validate_config()
        if not self.source_content and not self.source_note_id:
            raise ValueError("Either source_content or source_note_id is required")

    async def _fetch_source_content(self) -> str:
        """Fetch content from note if specified."""
        if self.source_note_id:
            try:
                note = await Note.get(self.source_note_id)
                if note and note.content:
                    return note.content
            except Exception as e:
                logger.warning(f"Failed to fetch note {self.source_note_id}: {e}")
        return self.source_content

    async def _adapt_with_ai(self, content: str, platform: str) -> Dict[str, Any]:
        """Use AI to adapt content for platform."""
        try:
            from langchain_core.messages import HumanMessage, SystemMessage
            from open_notebook.ai.provision import provision_langchain_model

            config = self.PLATFORM_CONFIGS.get(platform, self.PLATFORM_CONFIGS["twitter"])

            prompt = f"""Adapt the following content for {platform.upper()}.

Original Content:
---
{content[:1500]}
---

Platform Requirements:
- Max length: {config['max_length']} characters
- Style: {config['style']}
- Content style: {self.content_style}
- Include CTA: {self.include_cta}

Provide:
1. Adapted text (optimized for {platform})
2. Suggested hashtags (max {config['hashtag_count']})
3. Hook/first line (what grabs attention)
4. Character count
5. Recommended media type (image, video, carousel)

Return JSON:
{{
  "adapted_text": "platform-optimized content",
  "hashtags": ["tag1", "tag2"],
  "hook": "attention-grabbing first line",
  "character_count": 245,
  "media_suggestion": "image carousel"
}}"""

            messages = [
                SystemMessage(content=f"You are a {platform} content expert."),
                HumanMessage(content=prompt)
            ]

            chain = await provision_langchain_model(
                prompt_text=prompt,
                model_id=None,
                feature_type="content_adaptation"
            )

            response = await chain.ainvoke(messages)
            response_text = response.content if hasattr(response, 'content') else str(response)

            try:
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass

            # Fallback
            return {
                "adapted_text": response_text[:config['max_length']],
                "hashtags": [f"#{self.content_style}"],
                "hook": response_text[:50],
                "character_count": len(response_text),
                "media_suggestion": "image"
            }

        except Exception as e:
            logger.error(f"AI adaptation failed for {platform}: {e}")
            return {
                "adapted_text": content[:self.PLATFORM_CONFIGS.get(platform, {}).get('max_length', 280)],
                "hashtags": [],
                "error": str(e)
            }

    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute content adaptation."""
        logger.info(f"Adapting content for platforms: {self.target_platforms}")

        try:
            content = await self._fetch_source_content()

            if not content or len(content) < 20:
                return SkillResult(
                    skill_id=context.skill_id,
                    status=SkillStatus.FAILED,
                    started_at=datetime.utcnow(),
                    error_message="Insufficient content to adapt (minimum 20 characters)"
                )

            adaptations = []
            for platform in self.target_platforms:
                adaptation = await self._adapt_with_ai(content, platform)
                adaptation["platform"] = platform
                adaptations.append(adaptation)

            # Create result note
            created_note_ids = []
            if self.config.target_notebook_id:
                note = Note(
                    title=f"Platform Adaptations - {datetime.now().strftime('%Y-%m-%d')}",
                    content=self._format_adaptations(adaptations, content),
                    note_type="ai"
                )
                await note.save()
                await note.add_to_notebook(self.config.target_notebook_id)
                created_note_ids.append(str(note.id))

            return SkillResult(
                skill_id=context.skill_id,
                status=SkillStatus.SUCCESS,
                started_at=datetime.utcnow(),
                output={
                    "adaptations": adaptations,
                    "platforms": self.target_platforms,
                    "original_length": len(content),
                    "style": self.content_style
                },
                created_note_ids=created_note_ids
            )

        except Exception as e:
            logger.exception(f"Content adaptation failed: {e}")
            return SkillResult(
                skill_id=context.skill_id,
                status=SkillStatus.FAILED,
                started_at=datetime.utcnow(),
                error_message=str(e)
            )

    def _format_adaptations(self, adaptations: List[Dict], original: str) -> str:
        """Format adaptations as markdown."""
        lines = [
            "# Platform Content Adaptations\n",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"**Style:** {self.content_style}",
            f"**Original Length:** {len(original)} characters\n",
            "## Original Content\n",
            f"> {original[:300]}{'...' if len(original) > 300 else ''}\n"
        ]

        for adaptation in adaptations:
            platform = adaptation.get("platform", "unknown")
            lines.extend([
                f"## {platform.upper()}\n",
                f"**Hook:** {adaptation.get('hook', 'N/A')}",
                f"**Character Count:** {adaptation.get('character_count', len(adaptation.get('adapted_text', '')))}",
                f"**Media Suggestion:** {adaptation.get('media_suggestion', 'image')}",
                "",
                "**Content:**",
                f"```\n{adaptation.get('adapted_text', 'N/A')}\n```",
                "",
                f"**Hashtags:** {', '.join(adaptation.get('hashtags', []))}",
                ""
            ])

        return "\n".join(lines)


# Register all Vikki skills
register_skill(PainpointScannerSkill)
register_skill(QuadrantClassifierSkill)
register_skill(TopicGeneratorSkill)
register_skill(ContentAdaptorSkill)
