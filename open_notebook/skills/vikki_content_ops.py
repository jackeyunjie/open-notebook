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


class CycleDiagnosticianSkill(Skill):
    """Diagnose account lifecycle stage for content strategy optimization.

    Analyzes account metrics to determine current phase:
    - launch (起号期): Building initial audience, 0-1000 followers
    - breakout (破圈期): Rapid growth, viral content working
    - stable (稳定期): Consistent engagement, slower growth
    - monetize (转化期): Focus on conversion and sales

    Each phase requires different content strategy and quadrant focus.

    Parameters:
        - follower_count: Current follower/subscriber count
        - previous_follower_count: Follower count 30 days ago (for trend)
        - engagement_rate: Current engagement rate (0-100)
        - content_history: List of recent content with performance metrics
        - account_age_days: How long the account has been active
        - platform: Target platform (twitter, linkedin, xiaohongshu, etc.)

    Output:
        - current_cycle: Detected lifecycle stage
        - cycle_confidence: Confidence score (0-100)
        - metrics_analysis: Breakdown of key indicators
        - strategy_recommendations: Phase-specific content strategy
        - target_quadrant_ratios: Recommended Q1-Q4 content distribution

    Example:
        config = SkillConfig(
            skill_type="cycle_diagnostician",
            name="Diagnose Account Cycle",
            parameters={
                "follower_count": 5000,
                "previous_follower_count": 3000,
                "engagement_rate": 4.5,
                "platform": "xiaohongshu"
            }
        )
    """

    skill_type = "cycle_diagnostician"
    name = "Cycle Diagnostician"
    description = "Diagnose account lifecycle stage and recommend content strategy"

    # Cycle definitions with thresholds
    CYCLE_DEFINITIONS = {
        "launch": {
            "name": "起号期 (Launch)",
            "description": "Building initial audience and establishing presence",
            "follower_max": 1000,
            "growth_rate_min": 0,
            "characteristics": ["Low follower count", "Testing content", "Finding voice"],
            "content_focus": "Establish expertise, test different formats",
            "quadrant_ratios": {"Q1": 20, "Q2": 30, "Q3": 40, "Q4": 10},  # Heavy on Q3 for awareness
            "priority": " virality and reach"
        },
        "breakout": {
            "name": "破圈期 (Breakout)",
            "description": "Rapid growth phase with working viral content",
            "follower_max": 50000,
            "growth_rate_min": 20,  # 20%+ monthly growth
            "characteristics": ["Rapid follower growth", "Viral content", "Expanding reach"],
            "content_focus": "Double down on winning formats, scale success",
            "quadrant_ratios": {"Q1": 25, "Q2": 35, "Q3": 30, "Q4": 10},  # Balanced with education
            "priority": "growth and engagement"
        },
        "stable": {
            "name": "稳定期 (Stable)",
            "description": "Mature account with consistent but slower growth",
            "follower_max": 500000,
            "growth_rate_min": 5,
            "growth_rate_max": 20,
            "characteristics": ["Steady engagement", "Loyal audience", "Slower growth"],
            "content_focus": "Deepen expertise, community building",
            "quadrant_ratios": {"Q1": 30, "Q2": 40, "Q3": 20, "Q4": 10},  # Heavy on Q2 for depth
            "priority": "authority and trust"
        },
        "monetize": {
            "name": "转化期 (Monetize)",
            "description": "Conversion-focused phase for revenue generation",
            "follower_min": 5000,
            "growth_rate_max": 15,
            "characteristics": ["Product/service ready", "High trust", "Sales focus"],
            "content_focus": "Pain point solutions, case studies, offers",
            "quadrant_ratios": {"Q1": 50, "Q2": 30, "Q3": 15, "Q5": 5},  # Heavy on Q1 for conversion
            "priority": "conversion and revenue"
        }
    }

    parameters_schema = {
        "follower_count": {
            "type": "integer",
            "minimum": 0,
            "description": "Current follower/subscriber count"
        },
        "previous_follower_count": {
            "type": "integer",
            "default": 0,
            "description": "Follower count 30 days ago (for growth calculation)"
        },
        "engagement_rate": {
            "type": "number",
            "minimum": 0,
            "maximum": 100,
            "description": "Current engagement rate percentage"
        },
        "previous_engagement_rate": {
            "type": "number",
            "default": 0,
            "description": "Engagement rate 30 days ago"
        },
        "content_history": {
            "type": "array",
            "items": {"type": "object"},
            "default": [],
            "description": "Recent content with metrics (views, likes, shares)"
        },
        "account_age_days": {
            "type": "integer",
            "default": 0,
            "description": "Account age in days"
        },
        "platform": {
            "type": "string",
            "default": "general",
            "enum": ["twitter", "linkedin", "xiaohongshu", "instagram", "tiktok", "general"],
            "description": "Target platform for platform-specific recommendations"
        },
        "monetization_ready": {
            "type": "boolean",
            "default": False,
            "description": "Whether product/service is ready for monetization"
        }
    }

    def __init__(self, config: SkillConfig):
        self.follower_count: int = config.parameters.get("follower_count", 0)
        self.previous_follower_count: int = config.parameters.get("previous_follower_count", 0)
        self.engagement_rate: float = config.parameters.get("engagement_rate", 0)
        self.previous_engagement_rate: float = config.parameters.get("previous_engagement_rate", 0)
        self.content_history: List[Dict] = config.parameters.get("content_history", [])
        self.account_age_days: int = config.parameters.get("account_age_days", 0)
        self.platform: str = config.parameters.get("platform", "general")
        self.monetization_ready: bool = config.parameters.get("monetization_ready", False)
        super().__init__(config)

    def _validate_config(self) -> None:
        super()._validate_config()
        if self.follower_count < 0:
            raise ValueError("follower_count must be non-negative")

    def _calculate_growth_rate(self) -> float:
        """Calculate monthly follower growth rate."""
        if self.previous_follower_count <= 0:
            return 0
        return ((self.follower_count - self.previous_follower_count) / self.previous_follower_count) * 100

    def _calculate_engagement_trend(self) -> str:
        """Determine if engagement is improving or declining."""
        if self.previous_engagement_rate <= 0:
            return "stable"
        diff = self.engagement_rate - self.previous_engagement_rate
        if diff > 0.5:
            return "improving"
        elif diff < -0.5:
            return "declining"
        return "stable"

    def _analyze_content_performance(self) -> Dict[str, Any]:
        """Analyze recent content for viral hits and patterns."""
        if not self.content_history:
            return {"viral_count": 0, "avg_performance": 0, "top_performer": None}

        # Sort by engagement/views
        sorted_content = sorted(
            self.content_history,
            key=lambda x: x.get("engagement", 0),
            reverse=True
        )

        # Count viral content (top 10% performance)
        threshold = len(sorted_content) // 10 or 1
        viral_count = sum(1 for c in sorted_content[:threshold] if c.get("is_viral", False))

        # Calculate average
        avg_engagement = sum(c.get("engagement", 0) for c in self.content_history) / len(self.content_history)

        return {
            "viral_count": viral_count,
            "avg_performance": avg_engagement,
            "top_performer": sorted_content[0] if sorted_content else None,
            "content_count": len(self.content_history)
        }

    def _determine_cycle(self, growth_rate: float, engagement_trend: str, content_analysis: Dict) -> tuple:
        """Determine lifecycle stage based on metrics."""
        scores = {}

        for cycle_id, definition in self.CYCLE_DEFINITIONS.items():
            score = 0
            reasons = []

            # Check follower count
            follower_max = definition.get("follower_max", float('inf'))
            follower_min = definition.get("follower_min", 0)

            if follower_min <= self.follower_count <= follower_max:
                score += 30
                reasons.append(f"Follower count ({self.follower_count}) in range")

            # Check growth rate
            growth_min = definition.get("growth_rate_min", 0)
            growth_max = definition.get("growth_rate_max", float('inf'))

            if growth_min <= growth_rate <= growth_max:
                score += 40
                reasons.append(f"Growth rate ({growth_rate:.1f}%) matches")

            # Special handling for monetize phase
            if cycle_id == "monetize":
                if self.monetization_ready and self.follower_count >= 5000:
                    score += 30
                    reasons.append("Monetization ready with sufficient followers")
                elif self.monetization_ready:
                    score += 10

            # Content performance indicators
            if cycle_id == "breakout" and content_analysis["viral_count"] >= 2:
                score += 20
                reasons.append(f"Has {content_analysis['viral_count']} viral posts")
            elif cycle_id == "launch" and content_analysis["viral_count"] == 0:
                score += 15
                reasons.append("No viral posts yet (typical for launch)")

            # Engagement trend
            if cycle_id in ["breakout", "monetize"] and engagement_trend == "improving":
                score += 10

            scores[cycle_id] = {"score": score, "reasons": reasons}

        # Find highest scoring cycle
        best_cycle = max(scores.keys(), key=lambda k: scores[k]["score"])
        best_score = scores[best_cycle]["score"]

        return best_cycle, best_score, scores

    def _generate_recommendations(self, cycle_id: str, growth_rate: float) -> List[Dict[str, str]]:
        """Generate phase-specific recommendations."""
        definition = self.CYCLE_DEFINITIONS[cycle_id]
        recommendations = []

        # Phase-specific advice
        if cycle_id == "launch":
            recommendations.extend([
                {"area": "Content", "advice": "Post 3-5x daily to test different formats and topics"},
                {"area": "Quadrant", "advice": "Focus on Q3 (Mass) content for broad awareness - 40% of posts"},
                {"area": "Engagement", "advice": "Actively comment on larger accounts in your niche"},
                {"area": "Metrics", "advice": f"Current growth ({growth_rate:.1f}%) is {'good' if growth_rate > 10 else 'needs improvement'}"}
            ])
        elif cycle_id == "breakout":
            recommendations.extend([
                {"area": "Content", "advice": "Double down on your 2-3 best performing content formats"},
                {"area": "Quadrant", "advice": "Increase Q2 (Educational) to 35% - build authority while growing"},
                {"area": "Posting", "advice": "Maintain or increase frequency - momentum is key"},
                {"area": "Engagement", "advice": "Respond to every comment to boost algorithmic distribution"}
            ])
        elif cycle_id == "stable":
            recommendations.extend([
                {"area": "Content", "advice": "Focus on depth over breadth - comprehensive guides"},
                {"area": "Quadrant", "advice": "Heavy Q2 (40%) + Q1 (30%) for authority and early conversion"},
                {"area": "Community", "advice": "Build deeper relationships with existing followers"},
                {"area": "Innovation", "advice": "Test 1 new format monthly to prevent stagnation"}
            ])
        elif cycle_id == "monetize":
            recommendations.extend([
                {"area": "Content", "advice": "50% Q1 (Intent) content - direct pain point solutions"},
                {"area": "Offers", "advice": "Create clear CTAs and lead magnets in every post"},
                {"area": "Trust", "advice": "Share case studies and testimonials regularly"},
                {"area": "Funnel", "advice": "Build email list - platform algorithms can change"}
            ])

        # Platform-specific additions
        if self.platform == "xiaohongshu":
            recommendations.append({"area": "Platform", "advice": "Xiaohongshu: High-quality cover images are critical"})
        elif self.platform == "twitter":
            recommendations.append({"area": "Platform", "advice": "Twitter: Thread format performs best for educational content"})

        return recommendations

    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute cycle diagnosis."""
        logger.info(f"Diagnosing account cycle: followers={self.follower_count}, platform={self.platform}")

        try:
            # Calculate metrics
            growth_rate = self._calculate_growth_rate()
            engagement_trend = self._calculate_engagement_trend()
            content_analysis = self._analyze_content_performance()

            # Determine cycle
            cycle_id, confidence, all_scores = self._determine_cycle(growth_rate, engagement_trend, content_analysis)
            definition = self.CYCLE_DEFINITIONS[cycle_id]

            # Generate recommendations
            recommendations = self._generate_recommendations(cycle_id, growth_rate)

            # Build result
            result = {
                "current_cycle": cycle_id,
                "cycle_name": definition["name"],
                "cycle_description": definition["description"],
                "confidence_score": min(confidence, 100),
                "metrics": {
                    "follower_count": self.follower_count,
                    "monthly_growth_rate": round(growth_rate, 2),
                    "engagement_rate": self.engagement_rate,
                    "engagement_trend": engagement_trend,
                    "account_age_days": self.account_age_days,
                    "content_analysis": content_analysis
                },
                "scoring_breakdown": all_scores,
                "target_quadrant_ratios": definition["quadrant_ratios"],
                "content_focus": definition["content_focus"],
                "current_priority": definition["priority"],
                "recommendations": recommendations,
                "next_cycle_transition": self._estimate_next_transition(cycle_id, growth_rate)
            }

            # Create result note
            created_note_ids = []
            if self.config.target_notebook_id:
                note = Note(
                    title=f"Account Cycle Diagnosis - {definition['name']}",
                    content=self._format_diagnosis(result),
                    note_type="ai"
                )
                await note.save()
                await note.add_to_notebook(self.config.target_notebook_id)
                created_note_ids.append(str(note.id))

            return SkillResult(
                skill_id=context.skill_id,
                status=SkillStatus.SUCCESS,
                started_at=datetime.utcnow(),
                output=result,
                created_note_ids=created_note_ids
            )

        except Exception as e:
            logger.exception(f"Cycle diagnosis failed: {e}")
            return SkillResult(
                skill_id=context.skill_id,
                status=SkillStatus.FAILED,
                started_at=datetime.utcnow(),
                error_message=str(e)
            )

    def _estimate_next_transition(self, current_cycle: str, growth_rate: float) -> Dict[str, Any]:
        """Estimate when account might transition to next cycle."""
        transitions = {
            "launch": {"next": "breakout", "threshold": "1000 followers or 20% monthly growth"},
            "breakout": {"next": "stable", "threshold": "Growth rate drops below 20% for 2 months"},
            "stable": {"next": "monetize", "threshold": "Monetization readiness + 5000+ followers"},
            "monetize": {"next": "scale", "threshold": "Consistent revenue, team building"}
        }

        transition = transitions.get(current_cycle, {"next": "unknown", "threshold": "N/A"})

        # Add estimated time
        if current_cycle == "launch":
            if growth_rate > 30:
                transition["estimated_time"] = "1-2 months"
            elif growth_rate > 10:
                transition["estimated_time"] = "3-6 months"
            else:
                transition["estimated_time"] = "6+ months (growth needs acceleration)"
        elif current_cycle == "breakout":
            transition["estimated_time"] = "When growth naturally slows"

        return transition

    def _format_diagnosis(self, result: Dict) -> str:
        """Format diagnosis as markdown."""
        lines = [
            f"# Account Cycle Diagnosis: {result['cycle_name']}",
            "",
            f"**Confidence:** {result['confidence_score']}%",
            f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "",
            f"## Stage Description",
            result['cycle_description'],
            "",
            "## Current Metrics",
            f"- **Followers:** {result['metrics']['follower_count']:,}",
            f"- **Monthly Growth:** {result['metrics']['monthly_growth_rate']}%",
            f"- **Engagement Rate:** {result['metrics']['engagement_rate']}%",
            f"- **Engagement Trend:** {result['metrics']['engagement_trend']}",
            "",
            "## Recommended Content Strategy",
            f"**Focus:** {result['content_focus']}",
            f"**Priority:** {result['current_priority']}",
            "",
            "### Target Quadrant Distribution",
            f"- Q1 (Intent): {result['target_quadrant_ratios']['Q1']}%",
            f"- Q2 (Aware): {result['target_quadrant_ratios']['Q2']}%",
            f"- Q3 (Mass): {result['target_quadrant_ratios']['Q3']}%",
            f"- Q4 (Potential): {result['target_quadrant_ratios']['Q4']}%",
            "",
            "## Recommendations",
        ]

        for rec in result['recommendations']:
            lines.append(f"### {rec['area']}")
            lines.append(rec['advice'])
            lines.append("")

        lines.extend([
            "## Next Phase",
            f"**Transition to:** {result['next_cycle_transition']['next']}",
            f"**When:** {result['next_cycle_transition']['threshold']}",
        ])

        if 'estimated_time' in result['next_cycle_transition']:
            lines.append(f"**Estimated Time:** {result['next_cycle_transition']['estimated_time']}")

        return "\n".join(lines)


class TopicEvaluatorSkill(Skill):
    """Evaluate content topics across multiple dimensions for quality scoring.

    Analyzes topics using AI + heuristic scoring across:
    - Traffic potential: Likelihood of high reach
    - Conversion potential: Ability to drive actions
    - Feasibility: Ease of content creation
    - Differentiation: Uniqueness vs competition
    - Platform fit: Alignment with platform algorithm

    Parameters:
        - topics: List of topic strings or topic objects to evaluate
        - evaluation_dimensions: Which dimensions to score (default: all)
        - platform: Target platform for platform-fit scoring
        - competitor_content: Optional sample of competitor content for differentiation
        - min_overall_score: Minimum score to pass (default: 60)

    Output:
        - evaluated_topics: Topics with dimension scores and overall score
        - top_topics: Highest scoring topics
        - improvement_suggestions: How to improve low-scoring topics

    Example:
        config = SkillConfig(
            skill_type="topic_evaluator",
            name="Evaluate Topics",
            parameters={
                "topics": ["How to fix iPhone storage", "iPhone tips"],
                "platform": "xiaohongshu",
                "min_overall_score": 65
            }
        )
    """

    skill_type = "topic_evaluator"
    name = "Topic Evaluator"
    description = "Evaluate content topics across traffic, conversion, feasibility, and differentiation"

    # Scoring criteria by dimension
    SCORING_CRITERIA = {
        "traffic_potential": {
            "weight": 0.25,
            "factors": ["search_volume", "trending_status", "evergreen_value", "shareability"]
        },
        "conversion_potential": {
            "weight": 0.25,
            "factors": ["pain_point_intensity", "solution_clarity", "cta_naturalness", "audience_intent"]
        },
        "feasibility": {
            "weight": 0.20,
            "factors": ["creation_time", "resource_requirements", "expertise_needed", "research_needed"]
        },
        "differentiation": {
            "weight": 0.15,
            "factors": ["unique_angle", "novelty", "perspective_uniqueness", "competition_gap"]
        },
        "platform_fit": {
            "weight": 0.15,
            "factors": ["algorithm_alignment", "format_suitability", "audience_match", "timing_relevance"]
        }
    }

    parameters_schema = {
        "topics": {
            "type": "array",
            "items": {"type": ["string", "object"]},
            "description": "List of topics to evaluate"
        },
        "evaluation_dimensions": {
            "type": "array",
            "items": {"type": "string", "enum": ["traffic_potential", "conversion_potential", "feasibility", "differentiation", "platform_fit"]},
            "default": ["traffic_potential", "conversion_potential", "feasibility", "differentiation", "platform_fit"],
            "description": "Dimensions to evaluate"
        },
        "platform": {
            "type": "string",
            "default": "general",
            "enum": ["twitter", "linkedin", "xiaohongshu", "instagram", "tiktok", "general"],
            "description": "Target platform for platform-fit scoring"
        },
        "competitor_content": {
            "type": "array",
            "items": {"type": "string"},
            "default": [],
            "description": "Sample competitor content titles for differentiation analysis"
        },
        "min_overall_score": {
            "type": "integer",
            "default": 60,
            "minimum": 0,
            "maximum": 100,
            "description": "Minimum overall score for a topic to pass"
        },
        "industry": {
            "type": "string",
            "default": "general",
            "description": "Industry context for evaluation"
        }
    }

    def __init__(self, config: SkillConfig):
        self.topics: List = config.parameters.get("topics", [])
        self.evaluation_dimensions: List[str] = config.parameters.get(
            "evaluation_dimensions",
            list(self.SCORING_CRITERIA.keys())
        )
        self.platform: str = config.parameters.get("platform", "general")
        self.competitor_content: List[str] = config.parameters.get("competitor_content", [])
        self.min_overall_score: int = config.parameters.get("min_overall_score", 60)
        self.industry: str = config.parameters.get("industry", "general")
        super().__init__(config)

    def _validate_config(self) -> None:
        super()._validate_config()
        if not self.topics:
            raise ValueError("At least one topic is required for evaluation")

    def _heuristic_score(self, topic: str, dimension: str) -> tuple:
        """Calculate heuristic score for a dimension."""
        topic_lower = topic.lower()
        score = 50  # Base score
        indicators = []

        if dimension == "traffic_potential":
            # Check for traffic indicators
            viral_words = ["secret", "truth", "hack", "ultimate", "complete", "为什么", "真相", "终极"]
            search_words = ["how to", "guide", "tutorial", "怎么办", "如何", "攻略"]

            if any(w in topic_lower for w in viral_words):
                score += 20
                indicators.append("viral keywords")
            if any(w in topic_lower for w in search_words):
                score += 15
                indicators.append("search intent")
            if "?" in topic or "？" in topic:
                score += 10
                indicators.append("question format")

        elif dimension == "conversion_potential":
            # Check for conversion indicators
            pain_words = ["problem", "fix", "solve", "struggle", "issue", "问题", "解决", "困扰"]
            solution_words = ["solution", "method", "system", "framework", "方法", "方案", "体系"]

            if any(w in topic_lower for w in pain_words):
                score += 20
                indicators.append("pain point focus")
            if any(w in topic_lower for w in solution_words):
                score += 15
                indicators.append("solution promise")
            if "number" in topic_lower or any(c.isdigit() for c in topic):
                score += 10
                indicators.append("specific numbers")

        elif dimension == "feasibility":
            # Assess creation difficulty
            complex_indicators = ["comprehensive", "deep dive", "complete guide", "全面", "深入", "完整"]
            simple_indicators = ["tips", "quick", "simple", "fast", "技巧", "快速", "简单"]

            if any(w in topic_lower for w in complex_indicators):
                score -= 15
                indicators.append("complex content")
            if any(w in topic_lower for w in simple_indicators):
                score += 20
                indicators.append("easy to create")

        elif dimension == "differentiation":
            # Check uniqueness vs competitors
            if self.competitor_content:
                similar_count = sum(1 for c in self.competitor_content if self._similarity(topic, c) > 0.7)
                if similar_count == 0:
                    score += 30
                    indicators.append("unique angle")
                elif similar_count > 2:
                    score -= 20
                    indicators.append("high competition")
                else:
                    score += 10
                    indicators.append("moderate competition")

        elif dimension == "platform_fit":
            # Platform-specific scoring
            if self.platform == "xiaohongshu":
                if any(w in topic_lower for w in ["review", "test", "unboxing", "测评", "开箱", "种草"]):
                    score += 20
                    indicators.append("XHS-friendly format")
            elif self.platform == "twitter":
                if "thread" in topic_lower or len(topic) < 100:
                    score += 15
                    indicators.append("Twitter-native format")

        return min(max(score, 0), 100), indicators

    def _similarity(self, text1: str, text2: str) -> float:
        """Simple text similarity check."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        if not words1 or not words2:
            return 0
        intersection = words1 & words2
        return len(intersection) / max(len(words1), len(words2))

    async def _evaluate_with_ai(self, topics: List[str]) -> List[Dict]:
        """Use AI for comprehensive topic evaluation."""
        try:
            from langchain_core.messages import HumanMessage, SystemMessage
            from open_notebook.ai.provision import provision_langchain_model

            topics_text = "\n".join([f"{i+1}. {t}" for i, t in enumerate(topics)])

            prompt = f"""Evaluate these content topics across 5 dimensions (score 0-100 each):

Topics to evaluate:
{topics_text}

Target Platform: {self.platform}
Industry: {self.industry}

For each topic, evaluate:
1. **traffic_potential**: Likelihood of high reach and shares
2. **conversion_potential**: Ability to drive actions and sales
3. **feasibility**: Ease and speed of content creation
4. **differentiation**: Uniqueness vs existing content
5. **platform_fit**: Alignment with {self.platform} algorithm and users

Return JSON array:
[
  {{
    "topic": "original topic",
    "scores": {{
      "traffic_potential": 75,
      "conversion_potential": 80,
      "feasibility": 90,
      "differentiation": 60,
      "platform_fit": 85
    }},
    "overall_score": 78,
    "strengths": ["what works well"],
    "weaknesses": ["what could improve"],
    "improvement_suggestions": "specific advice to improve score"
  }}
]

Be critical but fair. Most topics should score 50-80."""

            messages = [
                SystemMessage(content="You are a content strategy expert who evaluates content ideas objectively."),
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
                logger.warning("Failed to parse AI evaluation response")

            return []

        except Exception as e:
            logger.error(f"AI evaluation failed: {e}")
            return []

    def _calculate_overall(self, scores: Dict[str, int]) -> int:
        """Calculate weighted overall score."""
        total_weight = 0
        weighted_sum = 0

        for dimension, config in self.SCORING_CRITERIA.items():
            if dimension in scores:
                weight = config["weight"]
                weighted_sum += scores[dimension] * weight
                total_weight += weight

        return round(weighted_sum / total_weight) if total_weight > 0 else 50

    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute topic evaluation."""
        logger.info(f"Evaluating {len(self.topics)} topics for {self.platform}")

        try:
            evaluated = []

            # Heuristic scoring for all topics
            for topic in self.topics:
                topic_text = topic if isinstance(topic, str) else topic.get("title", str(topic))

                scores = {}
                all_indicators = []

                for dimension in self.evaluation_dimensions:
                    score, indicators = self._heuristic_score(topic_text, dimension)
                    scores[dimension] = score
                    all_indicators.extend(indicators)

                overall = self._calculate_overall(scores)

                evaluated.append({
                    "topic": topic_text,
                    "original_topic": topic,
                    "scores": scores,
                    "overall_score": overall,
                    "indicators": list(set(all_indicators)),
                    "passed": overall >= self.min_overall_score,
                    "evaluation_method": "heuristic"
                })

            # AI enhancement for top candidates
            passed_topics = [e["topic"] for e in evaluated if e["passed"]]
            if passed_topics:
                ai_results = await self._evaluate_with_ai(passed_topics[:5])

                # Merge AI scores
                for ai_result in ai_results:
                    for e in evaluated:
                        if e["topic"] == ai_result.get("topic"):
                            e["scores"] = ai_result.get("scores", e["scores"])
                            e["overall_score"] = ai_result.get("overall_score", e["overall_score"])
                            e["strengths"] = ai_result.get("strengths", [])
                            e["weaknesses"] = ai_result.get("weaknesses", [])
                            e["improvement_suggestions"] = ai_result.get("improvement_suggestions", "")
                            e["evaluation_method"] = "ai_enhanced"

            # Sort by overall score
            evaluated.sort(key=lambda x: x["overall_score"], reverse=True)

            # Categorize
            top_topics = [e for e in evaluated if e["overall_score"] >= 75]
            good_topics = [e for e in evaluated if 60 <= e["overall_score"] < 75]
            needs_work = [e for e in evaluated if e["overall_score"] < 60]

            # Create result
            result = {
                "evaluated_topics": evaluated,
                "summary": {
                    "total": len(evaluated),
                    "top_quality": len(top_topics),
                    "good": len(good_topics),
                    "needs_improvement": len(needs_work),
                    "pass_rate": len([e for e in evaluated if e["passed"]]) / len(evaluated) * 100 if evaluated else 0
                },
                "top_topics": top_topics[:5],
                "recommendations": self._generate_evaluation_recommendations(evaluated)
            }

            # Create result note
            created_note_ids = []
            if self.config.target_notebook_id:
                note = Note(
                    title=f"Topic Evaluation Report - {datetime.now().strftime('%Y-%m-%d')}",
                    content=self._format_evaluation(result),
                    note_type="ai"
                )
                await note.save()
                await note.add_to_notebook(self.config.target_notebook_id)
                created_note_ids.append(str(note.id))

            return SkillResult(
                skill_id=context.skill_id,
                status=SkillStatus.SUCCESS,
                started_at=datetime.utcnow(),
                output=result,
                created_note_ids=created_note_ids
            )

        except Exception as e:
            logger.exception(f"Topic evaluation failed: {e}")
            return SkillResult(
                skill_id=context.skill_id,
                status=SkillStatus.FAILED,
                started_at=datetime.utcnow(),
                error_message=str(e)
            )

    def _generate_evaluation_recommendations(self, evaluated: List[Dict]) -> List[str]:
        """Generate recommendations based on evaluation results."""
        recommendations = []

        avg_scores = {}
        for dim in self.evaluation_dimensions:
            scores = [e["scores"].get(dim, 0) for e in evaluated]
            avg_scores[dim] = sum(scores) / len(scores) if scores else 0

        # Identify weak areas
        for dim, avg in avg_scores.items():
            if avg < 50:
                recommendations.append(f"{dim}: Critical weakness. Review topic selection criteria.")
            elif avg < 65:
                recommendations.append(f"{dim}: Below average. Consider adjusting angle or format.")

        if not recommendations:
            recommendations.append("All dimensions scoring well. Focus on execution consistency.")

        return recommendations

    def _format_evaluation(self, result: Dict) -> str:
        """Format evaluation as markdown."""
        summary = result["summary"]

        lines = [
            "# Topic Evaluation Report",
            "",
            f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"**Platform:** {self.platform}",
            f"**Total Topics:** {summary['total']}",
            f"**Pass Rate:** {summary['pass_rate']:.1f}%",
            "",
            "## Summary",
            f"- Top Quality (75+): {summary['top_quality']}",
            f"- Good (60-74): {summary['good']}",
            f"- Needs Work (<60): {summary['needs_improvement']}",
            "",
            "## Top Topics",
        ]

        for i, topic in enumerate(result["top_topics"], 1):
            lines.extend([
                f"### #{i} {topic['topic'][:60]}",
                f"**Overall Score:** {topic['overall_score']}/100",
                "",
                "**Dimension Scores:**",
            ])
            for dim, score in topic["scores"].items():
                lines.append(f"- {dim}: {score}")
            lines.append("")

            if "strengths" in topic:
                lines.append(f"**Strengths:** {', '.join(topic['strengths'])}")
            if "weaknesses" in topic:
                lines.append(f"**Weaknesses:** {', '.join(topic['weaknesses'])}")
            if "improvement_suggestions" in topic:
                lines.append(f"**Suggestions:** {topic['improvement_suggestions']}")
            lines.append("")

        lines.extend([
            "## Recommendations",
            ""
        ])
        for rec in result["recommendations"]:
            lines.append(f"- {rec}")

        return "\n".join(lines)


class RatioMonitorSkill(Skill):
    """Monitor content quadrant distribution and suggest ratio adjustments.

    Ensures content mix aligns with account cycle goals. Alerts when
    quadrant distribution deviates from target ratios.

    Parameters:
        - current_plan: List of planned content with quadrant assignments
        - target_ratios: Desired Q1-Q4 distribution (default based on cycle)
        - account_cycle: Current lifecycle stage for auto-adjusted targets
        - tolerance_percent: Allowed deviation before alert (default: 10)
        - lookahead_days: Number of days to analyze (default: 30)

    Output:
        - current_ratios: Actual distribution in plan
        - deviation_analysis: Comparison with targets
        - alerts: Warnings for significant deviations
        - adjustment_suggestions: Specific content to add/remove

    Example:
        config = SkillConfig(
            skill_type="ratio_monitor",
            name="Monitor Quadrant Ratios",
            parameters={
                "current_plan": [{"title": "...", "quadrant": "Q1"}, ...],
                "account_cycle": "stable"
            }
        )
    """

    skill_type = "ratio_monitor"
    name = "Ratio Monitor"
    description = "Monitor content quadrant distribution and suggest balance adjustments"

    # Default ratios by cycle (same as CycleDiagnostician)
    CYCLE_RATIOS = {
        "launch": {"Q1": 20, "Q2": 30, "Q3": 40, "Q4": 10},
        "breakout": {"Q1": 25, "Q2": 35, "Q3": 30, "Q4": 10},
        "stable": {"Q1": 30, "Q2": 40, "Q3": 20, "Q4": 10},
        "monetize": {"Q1": 50, "Q2": 30, "Q3": 15, "Q4": 5}
    }

    parameters_schema = {
        "current_plan": {
            "type": "array",
            "items": {"type": "object"},
            "description": "List of content items with quadrant assignments"
        },
        "target_ratios": {
            "type": "object",
            "default": {},
            "description": "Custom Q1-Q4 target percentages (overrides cycle defaults)"
        },
        "account_cycle": {
            "type": "string",
            "enum": ["launch", "breakout", "stable", "monetize"],
            "description": "Account cycle for auto-adjusted targets"
        },
        "tolerance_percent": {
            "type": "integer",
            "default": 10,
            "minimum": 0,
            "maximum": 50,
            "description": "Allowed deviation percentage before alert"
        },
        "lookahead_days": {
            "type": "integer",
            "default": 30,
            "description": "Analysis period in days"
        },
        "recently_published": {
            "type": "array",
            "items": {"type": "object"},
            "default": [],
            "description": "Recently published content for historical analysis"
        }
    }

    def __init__(self, config: SkillConfig):
        self.current_plan: List[Dict] = config.parameters.get("current_plan", [])
        self.target_ratios: Dict[str, int] = config.parameters.get("target_ratios", {})
        self.account_cycle: str = config.parameters.get("account_cycle", "stable")
        self.tolerance_percent: int = config.parameters.get("tolerance_percent", 10)
        self.lookahead_days: int = config.parameters.get("lookahead_days", 30)
        self.recently_published: List[Dict] = config.parameters.get("recently_published", [])
        super().__init__(config)

    def _validate_config(self) -> None:
        super()._validate_config()
        # Use cycle defaults if no custom targets
        if not self.target_ratios and self.account_cycle:
            self.target_ratios = self.CYCLE_RATIOS.get(self.account_cycle, self.CYCLE_RATIOS["stable"])

    def _calculate_ratios(self, content_list: List[Dict]) -> Dict[str, float]:
        """Calculate quadrant distribution."""
        if not content_list:
            return {"Q1": 0, "Q2": 0, "Q3": 0, "Q4": 0}

        total = len(content_list)
        counts = {"Q1": 0, "Q2": 0, "Q3": 0, "Q4": 0}

        for item in content_list:
            quadrant = item.get("quadrant", "Q1")
            if quadrant in counts:
                counts[quadrant] += 1

        return {q: (count / total * 100) for q, count in counts.items()}

    def _analyze_deviation(self, current: Dict[str, float], target: Dict[str, int]) -> List[Dict]:
        """Analyze deviations from target ratios."""
        deviations = []

        for quadrant in ["Q1", "Q2", "Q3", "Q4"]:
            current_pct = current.get(quadrant, 0)
            target_pct = target.get(quadrant, 25)
            diff = current_pct - target_pct

            if abs(diff) > self.tolerance_percent:
                status = "over" if diff > 0 else "under"
                severity = "critical" if abs(diff) > 20 else "warning"

                deviations.append({
                    "quadrant": quadrant,
                    "current": round(current_pct, 1),
                    "target": target_pct,
                    "difference": round(diff, 1),
                    "status": status,
                    "severity": severity
                })

        return deviations

    def _generate_alerts(self, deviations: List[Dict]) -> List[Dict]:
        """Generate actionable alerts."""
        alerts = []

        for dev in deviations:
            if dev["severity"] == "critical":
                alerts.append({
                    "level": "critical",
                    "message": f"{dev['quadrant']} is {dev['status']}represented by {abs(dev['difference']):.1f}%",
                    "action": f"{'Reduce' if dev['status'] == 'over' else 'Add'} {dev['quadrant']} content immediately"
                })
            else:
                alerts.append({
                    "level": "warning",
                    "message": f"{dev['quadrant']} slightly {dev['status']} by {abs(dev['difference']):.1f}%",
                    "action": f"Consider {'reducing' if dev['status'] == 'over' else 'adding'} {dev['quadrant']} in next batch"
                })

        return alerts

    def _suggest_adjustments(self, deviations: List[Dict], current_plan: List[Dict]) -> List[Dict]:
        """Suggest specific content adjustments."""
        suggestions = []

        for dev in deviations:
            quadrant = dev["quadrant"]
            diff = dev["difference"]

            if dev["status"] == "under":
                # Suggest adding content
                needed_count = max(1, int(abs(diff) / 100 * len(current_plan)))
                suggestions.append({
                    "type": "add",
                    "quadrant": quadrant,
                    "count": needed_count,
                    "suggestion": f"Add {needed_count} {quadrant} topic(s) to balance ratio",
                    "example_topics": self._example_topics_for_quadrant(quadrant)
                })
            else:
                # Suggest reducing or postponing
                excess_count = max(1, int(abs(diff) / 100 * len(current_plan)))
                # Find excess content
                excess_content = [c for c in current_plan if c.get("quadrant") == quadrant][:excess_count]

                suggestions.append({
                    "type": "reduce",
                    "quadrant": quadrant,
                    "count": excess_count,
                    "suggestion": f"Postpone or replace {excess_count} {quadrant} content item(s)",
                    "candidates": [c.get("title", "Untitled") for c in excess_content]
                })

        return suggestions

    def _example_topics_for_quadrant(self, quadrant: str) -> List[str]:
        """Generate example topic ideas for a quadrant."""
        examples = {
            "Q1": [
                "How to solve [pain point] in 5 minutes",
                "The fastest way to [desired outcome]",
                "Stop [common mistake] - do this instead"
            ],
            "Q2": [
                "Deep dive: How [system] really works",
                "Advanced guide to [topic]",
                "What experts know about [field] that beginners don't"
            ],
            "Q3": [
                "Why everyone is talking about [trend]",
                "The uncomfortable truth about [topic]",
                "I tried [thing] for 30 days - shocking results"
            ],
            "Q4": [
                "10 unexpected uses for [product/tool]",
                "Hidden features of [common thing]",
                "You can use [thing] for [unexpected purpose]"
            ]
        }
        return examples.get(quadrant, [])

    def _analyze_trends(self) -> Dict[str, Any]:
        """Analyze historical trend if recent data provided."""
        if not self.recently_published:
            return {"has_trend_data": False}

        historical_ratios = self._calculate_ratios(self.recently_published)

        return {
            "has_trend_data": True,
            "historical_ratios": historical_ratios,
            "published_count": len(self.recently_published)
        }

    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute ratio monitoring."""
        logger.info(f"Monitoring ratios for {len(self.current_plan)} content items")

        try:
            if not self.current_plan:
                return SkillResult(
                    skill_id=context.skill_id,
                    status=SkillStatus.FAILED,
                    started_at=datetime.utcnow(),
                    error_message="No content plan provided for analysis"
                )

            # Calculate current distribution
            current_ratios = self._calculate_ratios(self.current_plan)

            # Analyze deviations
            deviations = self._analyze_deviation(current_ratios, self.target_ratios)

            # Generate alerts
            alerts = self._generate_alerts(deviations)

            # Suggest adjustments
            adjustments = self._suggest_adjustments(deviations, self.current_plan)

            # Analyze trends
            trends = self._analyze_trends()

            # Build result
            result = {
                "account_cycle": self.account_cycle,
                "target_ratios": self.target_ratios,
                "current_ratios": current_ratios,
                "content_count": len(self.current_plan),
                "deviations": deviations,
                "alerts": alerts,
                "adjustment_suggestions": adjustments,
                "is_balanced": len(deviations) == 0,
                "trends": trends,
                "health_score": max(0, 100 - sum(d["severity"] == "critical" for d in deviations) * 25)
            }

            # Create result note
            created_note_ids = []
            if self.config.target_notebook_id:
                note = Note(
                    title=f"Content Ratio Analysis - {datetime.now().strftime('%Y-%m-%d')}",
                    content=self._format_monitoring(result),
                    note_type="ai"
                )
                await note.save()
                await note.add_to_notebook(self.config.target_notebook_id)
                created_note_ids.append(str(note.id))

            return SkillResult(
                skill_id=context.skill_id,
                status=SkillStatus.SUCCESS,
                started_at=datetime.utcnow(),
                output=result,
                created_note_ids=created_note_ids
            )

        except Exception as e:
            logger.exception(f"Ratio monitoring failed: {e}")
            return SkillResult(
                skill_id=context.skill_id,
                status=SkillStatus.FAILED,
                started_at=datetime.utcnow(),
                error_message=str(e)
            )

    def _format_monitoring(self, result: Dict) -> str:
        """Format monitoring report as markdown."""
        lines = [
            "# Content Quadrant Ratio Analysis",
            "",
            f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"**Account Cycle:** {result['account_cycle']}",
            f"**Health Score:** {result['health_score']}/100",
            f"**Status:** {'✅ Balanced' if result['is_balanced'] else '⚠️ Needs Adjustment'}",
            "",
            "## Ratio Comparison",
            "",
            "| Quadrant | Target | Current | Diff | Status |",
            "|----------|--------|---------|------|--------|",
        ]

        for q in ["Q1", "Q2", "Q3", "Q4"]:
            target = result['target_ratios'].get(q, 25)
            current = result['current_ratios'].get(q, 0)
            diff = current - target

            # Find status
            status = "✅"
            for d in result['deviations']:
                if d['quadrant'] == q:
                    status = "🔴" if d['severity'] == 'critical' else "🟡"
                    break

            lines.append(f"| {q} | {target}% | {current:.1f}% | {diff:+.1f}% | {status} |")

        lines.extend([
            "",
            "## Alerts",
            ""
        ])

        if result['alerts']:
            for alert in result['alerts']:
                lines.append(f"### {alert['level'].upper()}")
                lines.append(f"**{alert['message']}**")
                lines.append(f"Action: {alert['action']}")
                lines.append("")
        else:
            lines.append("No alerts - content mix is well-balanced!")
            lines.append("")

        if result['adjustment_suggestions']:
            lines.extend([
                "## Suggested Adjustments",
                ""
            ])
            for sugg in result['adjustment_suggestions']:
                lines.append(f"### {sugg['type'].upper()}: {sugg['quadrant']}")
                lines.append(f"{sugg['suggestion']}")

                if 'example_topics' in sugg and sugg['example_topics']:
                    lines.append("")
                    lines.append("**Example topics to add:**")
                    for ex in sugg['example_topics']:
                        lines.append(f"- {ex}")

                lines.append("")

        return "\n".join(lines)


# Register all Vikki skills
register_skill(PainpointScannerSkill)
register_skill(QuadrantClassifierSkill)
register_skill(TopicGeneratorSkill)
register_skill(ContentAdaptorSkill)
register_skill(CycleDiagnosticianSkill)
register_skill(TopicEvaluatorSkill)
register_skill(RatioMonitorSkill)
