"""Multi-Model Router - Intelligent model selection based on task characteristics.

This skill provides smart model routing for Open Notebook, automatically selecting
the optimal AI model based on:
- Content language (Chinese → Qwen3.5)
- Task complexity (reasoning → Claude)
- Context length (long text → specialized models)
- Cost/latency requirements (fast → Groq)

Integrates with the existing ModelManager and provision_langchain_model.
"""

import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger

from open_notebook.skills.base import Skill, SkillConfig, SkillContext, SkillResult, SkillStatus
from open_notebook.skills.registry import register_skill


class TaskType(str, Enum):
    """Types of AI tasks with different model requirements."""
    GENERAL = "general"
    CHINESE_CONTENT = "chinese_content"
    CODE_GENERATION = "code_generation"
    COMPLEX_REASONING = "complex_reasoning"
    CREATIVE_WRITING = "creative_writing"
    SUMMARIZATION = "summarization"
    ANALYSIS = "analysis"
    FAST_RESPONSE = "fast_response"


class ModelCapability(str, Enum):
    """Model capabilities for selection criteria."""
    CHINESE = "chinese"  # Strong Chinese language support
    CODE = "code"  # Code generation and understanding
    REASONING = "reasoning"  # Complex reasoning tasks
    CREATIVE = "creative"  # Creative writing
    LONG_CONTEXT = "long_context"  # Large context windows
    FAST = "fast"  # Low latency
    CHEAP = "cheap"  # Cost effective


@dataclass
class ModelRoute:
    """Result of model routing decision."""
    model_type: str  # The model type to use (e.g., "chat", "transformation")
    model_id: Optional[str]  # Specific model ID if determined
    reason: str  # Why this route was chosen
    confidence: float  # Confidence score (0-1)
    estimated_tokens: int  # Estimated token count
    capabilities_needed: List[ModelCapability]


class MultiModelRouter(Skill):
    """Intelligently route tasks to optimal AI models.

    Analyzes task characteristics (content, language, complexity) and selects
    the best model from available providers (OpenAI, Anthropic, Qwen, Groq, etc.)

    Parameters:
        - content: The text content/prompt to analyze
        - task_type: Type of task (optional, auto-detected if not provided)
        - preferred_provider: Preferred provider if multiple options (optional)
        - require_fast: Prioritize speed over quality (default: false)
        - require_cheap: Prioritize cost over quality (default: false)
        - context_length: Known context length (optional, auto-calculated if not provided)

    Example:
        config = SkillConfig(
            skill_type="model_router",
            name="Model Router",
            parameters={
                "content": "分析这篇中文文章的主要观点...",
                "task_type": "analysis",
                "require_fast": False
            }
        )
    """

    skill_type = "model_router"
    name = "Multi-Model Router"
    description = "Intelligently route AI tasks to optimal models based on content characteristics"

    parameters_schema = {
        "content": {
            "type": "string",
            "description": "The content/prompt to analyze for routing"
        },
        "task_type": {
            "type": "string",
            "enum": ["general", "chinese_content", "code_generation", "complex_reasoning",
                     "creative_writing", "summarization", "analysis", "fast_response"],
            "description": "Task type (auto-detected if not provided)"
        },
        "preferred_provider": {
            "type": "string",
            "description": "Preferred model provider (optional)"
        },
        "require_fast": {
            "type": "boolean",
            "default": False,
            "description": "Prioritize speed over quality"
        },
        "require_cheap": {
            "type": "boolean",
            "default": False,
            "description": "Prioritize cost over quality"
        },
        "context_length": {
            "type": "integer",
            "description": "Known context length in tokens (auto-calculated if not provided)"
        }
    }

    # Provider capability mapping
    PROVIDER_CAPABILITIES = {
        "qwen": [ModelCapability.CHINESE, ModelCapability.CHEAP, ModelCapability.LONG_CONTEXT],
        "alibaba": [ModelCapability.CHINESE, ModelCapability.CHEAP, ModelCapability.LONG_CONTEXT],
        "anthropic": [ModelCapability.REASONING, ModelCapability.CODE, ModelCapability.CREATIVE, ModelCapability.LONG_CONTEXT],
        "openai": [ModelCapability.REASONING, ModelCapability.CODE, ModelCapability.CREATIVE],
        "groq": [ModelCapability.FAST, ModelCapability.CHEAP],
        "ollama": [ModelCapability.CHEAP],  # Local = free but slower
    }

    # Model type recommendations by task
    TASK_MODEL_TYPES = {
        TaskType.CHINESE_CONTENT: ("transformation", [ModelCapability.CHINESE, ModelCapability.CHEAP]),
        TaskType.CODE_GENERATION: ("tools", [ModelCapability.CODE, ModelCapability.REASONING]),
        TaskType.COMPLEX_REASONING: ("chat", [ModelCapability.REASONING]),
        TaskType.CREATIVE_WRITING: ("chat", [ModelCapability.CREATIVE]),
        TaskType.SUMMARIZATION: ("transformation", [ModelCapability.CHEAP]),
        TaskType.ANALYSIS: ("chat", [ModelCapability.REASONING]),
        TaskType.FAST_RESPONSE: ("chat", [ModelCapability.FAST]),
        TaskType.GENERAL: ("chat", []),
    }

    def __init__(self, config: SkillConfig):
        self.content: str = config.parameters.get("content", "")
        self.task_type: Optional[str] = config.parameters.get("task_type")
        self.preferred_provider: Optional[str] = config.parameters.get("preferred_provider")
        self.require_fast: bool = config.parameters.get("require_fast", False)
        self.require_cheap: bool = config.parameters.get("require_cheap", False)
        self.context_length: Optional[int] = config.parameters.get("context_length")
        super().__init__(config)

    def _validate_config(self) -> None:
        """Validate router configuration."""
        super()._validate_config()

        if not self.content:
            raise ValueError("content is required for routing")

    def _is_chinese_content(self, text: str) -> Tuple[bool, float]:
        """Detect if content is primarily Chinese.

        Returns:
            (is_chinese, confidence) tuple
        """
        if not text:
            return False, 0.0

        # Count Chinese characters
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        total_chars = len(text.strip())

        if total_chars == 0:
            return False, 0.0

        ratio = chinese_chars / total_chars

        # If > 30% Chinese characters, consider it Chinese content
        is_chinese = ratio > 0.30
        confidence = min(ratio * 2, 1.0)  # Scale confidence

        return is_chinese, confidence

    def _is_code_content(self, text: str) -> Tuple[bool, float]:
        """Detect if content involves code generation.

        Returns:
            (is_code, confidence) tuple
        """
        code_patterns = [
            r'```[\w]*\n',  # Code blocks
            r'(def |class |function |const |let |var |import |from |#include)',
            r'(<script>|<style>|<html>|<div>)',  # HTML/CSS
            r'(SELECT|INSERT|UPDATE|DELETE|CREATE TABLE)',  # SQL
            r'(if |for |while |return |print|console\.log)',
        ]

        text_lower = text.lower()
        code_keywords = [
            'code', 'function', 'programming', 'python', 'javascript',
            'algorithm', 'implementation', 'class', 'method', 'api',
            'debug', 'error handling', 'syntax'
        ]

        matches = 0
        for pattern in code_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                matches += 1

        keyword_matches = sum(1 for kw in code_keywords if kw in text_lower)

        confidence = min((matches + keyword_matches * 0.5) / 5, 1.0)
        is_code = confidence > 0.3

        return is_code, confidence

    def _is_complex_reasoning(self, text: str) -> Tuple[bool, float]:
        """Detect if content requires complex reasoning.

        Returns:
            (is_complex, confidence) tuple
        """
        reasoning_keywords = [
            'analyze', 'evaluate', 'compare', 'contrast', 'synthesize',
            'explain why', 'reasoning', 'logical', 'critique', 'assess',
            'implications', 'consequences', 'trade-offs', 'optimization',
            'prove', 'deduce', 'infer', 'conclusion', 'therefore'
        ]

        text_lower = text.lower()
        keyword_count = sum(1 for kw in reasoning_keywords if kw in text_lower)

        # Also check for question complexity
        question_count = text.count('?')

        confidence = min((keyword_count + question_count * 0.3) / 5, 1.0)
        is_complex = confidence > 0.25

        return is_complex, confidence

    def _detect_task_type(self) -> Tuple[TaskType, Dict[str, float]]:
        """Automatically detect task type from content.

        Returns:
            (task_type, confidences) tuple
        """
        confidences = {}

        # Check each characteristic
        is_chinese, chinese_conf = self._is_chinese_content(self.content)
        is_code, code_conf = self._is_code_content(self.content)
        is_complex, complex_conf = self._is_complex_reasoning(self.content)

        confidences['chinese'] = chinese_conf
        confidences['code'] = code_conf
        confidences['reasoning'] = complex_conf

        # Determine task type based on characteristics
        if is_chinese and chinese_conf > 0.7:
            return TaskType.CHINESE_CONTENT, confidences
        elif is_code and code_conf > 0.6:
            return TaskType.CODE_GENERATION, confidences
        elif is_complex and complex_conf > 0.6:
            return TaskType.COMPLEX_REASONING, confidences
        elif self.require_fast:
            return TaskType.FAST_RESPONSE, confidences
        else:
            return TaskType.GENERAL, confidences

    def _estimate_tokens(self) -> int:
        """Estimate token count for content."""
        if self.context_length:
            return self.context_length

        # Rough estimation: ~4 chars per token for English, ~1.5 for Chinese
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', self.content))
        other_chars = len(self.content) - chinese_chars

        tokens = int(chinese_chars / 1.5 + other_chars / 4)
        return tokens

    def _select_model_type(self, task_type: TaskType) -> Tuple[str, List[ModelCapability]]:
        """Select model type and required capabilities.

        Args:
            task_type: Detected task type

        Returns:
            (model_type, capabilities) tuple
        """
        return self.TASK_MODEL_TYPES.get(task_type, ("chat", []))

    async def _find_best_model(
        self,
        model_type: str,
        capabilities: List[ModelCapability],
        tokens: int
    ) -> Tuple[Optional[str], str]:
        """Find the best model ID based on requirements.

        Args:
            model_type: Type of model needed
            capabilities: Required capabilities
            tokens: Estimated token count

        Returns:
            (model_id, reason) tuple
        """
        from open_notebook.ai.models import Model, model_manager

        reasons = []

        # Check for large context first
        if tokens > 50000:  # ~50k tokens threshold
            try:
                defaults = await model_manager.get_defaults()
                if defaults.large_context_model:
                    reasons.append(f"Large context ({tokens} tokens)")
                    return defaults.large_context_model, "; ".join(reasons)
            except Exception:
                pass

        # Get all available models
        try:
            all_models = await Model.get_models_by_type("language")
        except Exception as e:
            logger.error(f"Failed to fetch models: {e}")
            return None, "Failed to fetch available models"

        if not all_models:
            return None, "No language models available"

        # Score each model
        model_scores = []

        for model in all_models:
            score = 0
            model_caps = self.PROVIDER_CAPABILITIES.get(model.provider.lower(), [])

            # Capability matching
            for cap in capabilities:
                if cap in model_caps:
                    score += 2

            # Preference matching
            if self.preferred_provider and model.provider.lower() == self.preferred_provider.lower():
                score += 3

            # Speed priority
            if self.require_fast and ModelCapability.FAST in model_caps:
                score += 2

            # Cost priority
            if self.require_cheap and ModelCapability.CHEAP in model_caps:
                score += 2

            model_scores.append((model, score))

        # Sort by score
        model_scores.sort(key=lambda x: x[1], reverse=True)

        if model_scores:
            best_model, best_score = model_scores[0]
            reasons.append(f"Best match (score: {best_score})")
            reasons.append(f"Provider: {best_model.provider}")
            return str(best_model.id), "; ".join(reasons)

        # Fall back to default
        try:
            default_model = await model_manager.get_default_model(model_type)
            if default_model:
                reasons.append("Fallback to default")
                return None, "; ".join(reasons)  # Return None to use default flow
        except Exception:
            pass

        return None, "No suitable model found"

    async def execute(self, context: SkillContext) -> SkillResult:
        """Execute model routing."""
        logger.info("Routing task to optimal model")

        start_time = datetime.utcnow()

        try:
            # Step 1: Detect or use provided task type
            if self.task_type:
                task_type = TaskType(self.task_type)
                detection_confidences = {}
            else:
                task_type, detection_confidences = self._detect_task_type()

            logger.info(f"Detected task type: {task_type.value}")

            # Step 2: Estimate tokens
            estimated_tokens = self._estimate_tokens()
            logger.debug(f"Estimated tokens: {estimated_tokens}")

            # Step 3: Select model type and capabilities
            model_type, capabilities = self._select_model_type(task_type)

            # Add long_context capability if needed
            if estimated_tokens > 50000:
                capabilities.append(ModelCapability.LONG_CONTEXT)

            # Step 4: Find best model
            model_id, reason = await self._find_best_model(
                model_type,
                capabilities,
                estimated_tokens
            )

            # Build result
            route = ModelRoute(
                model_type=model_type,
                model_id=model_id,
                reason=reason,
                confidence=detection_confidences.get(task_type.value.replace('_', ''), 0.8),
                estimated_tokens=estimated_tokens,
                capabilities_needed=capabilities
            )

            logger.info(f"Routed to {model_type}" + (f" ({model_id})" if model_id else " (default)"))

            return SkillResult(
                skill_id=context.skill_id,
                status=SkillStatus.SUCCESS,
                started_at=start_time,
                completed_at=datetime.utcnow(),
                output={
                    "task_type": task_type.value,
                    "model_type": route.model_type,
                    "model_id": route.model_id,
                    "reason": route.reason,
                    "confidence": route.confidence,
                    "estimated_tokens": route.estimated_tokens,
                    "capabilities_needed": [c.value for c in route.capabilities_needed],
                    "detection_confidences": detection_confidences,
                    "routing_decision": {
                        "provider_recommendation": self._get_provider_recommendation(task_type),
                        "use_large_context": estimated_tokens > 50000,
                    }
                }
            )

        except Exception as e:
            logger.error(f"Model routing failed: {e}")
            return SkillResult(
                skill_id=context.skill_id,
                status=SkillStatus.FAILED,
                started_at=start_time,
                completed_at=datetime.utcnow(),
                error_message=str(e),
                output={
                    "error": str(e),
                    "fallback": {
                        "model_type": "chat",
                        "model_id": None,
                        "reason": "Routing failed, use system default"
                    }
                }
            )

    def _get_provider_recommendation(self, task_type: TaskType) -> str:
        """Get human-readable provider recommendation."""
        recommendations = {
            TaskType.CHINESE_CONTENT: "Qwen/Alibaba (best Chinese, cost-effective)",
            TaskType.CODE_GENERATION: "Anthropic Claude or OpenAI (strong coding)",
            TaskType.COMPLEX_REASONING: "Anthropic Claude (best reasoning)",
            TaskType.CREATIVE_WRITING: "Anthropic Claude or OpenAI",
            TaskType.SUMMARIZATION: "Qwen/Alibaba or Groq (fast, cheap)",
            TaskType.ANALYSIS: "Anthropic Claude (best analysis)",
            TaskType.FAST_RESPONSE: "Groq (lowest latency)",
            TaskType.GENERAL: "System default or OpenAI",
        }
        return recommendations.get(task_type, "System default")


# Integration function for provision_langchain_model
async def route_and_provision_model(
    content: str,
    model_id: Optional[str] = None,
    default_type: str = "chat",
    **kwargs
):
    """Route to best model and provision it.

    This is a drop-in replacement for provision_langchain_model
    with intelligent routing.

    Args:
        content: The content/prompt
        model_id: Specific model ID (optional, overrides routing)
        default_type: Default model type if routing fails
        **kwargs: Additional model parameters

    Returns:
        LangChain model instance
    """
    from open_notebook.ai.provision import provision_langchain_model

    # If explicit model_id provided, use it directly
    if model_id:
        return await provision_langchain_model(content, model_id, default_type, **kwargs)

    # Otherwise, route intelligently
    config = SkillConfig(
        skill_type="model_router",
        name="Auto Model Router",
        parameters={"content": content}
    )

    router = MultiModelRouter(config)

    from open_notebook.skills.base import SkillContext
    ctx = SkillContext(
        skill_id=f"route_{datetime.utcnow().timestamp()}",
        trigger_type="auto"
    )

    result = await router.run(ctx)

    if result.success:
        routed_model_id = result.output.get("model_id")
        if routed_model_id:
            logger.info(f"Using routed model: {routed_model_id}")
            return await provision_langchain_model(
                content, routed_model_id, default_type, **kwargs
            )

    # Fall back to original behavior
    return await provision_langchain_model(content, None, default_type, **kwargs)


# Convenience function for quick routing decisions
async def get_model_recommendation(
    content: str,
    require_fast: bool = False,
    require_cheap: bool = False
) -> Dict[str, Any]:
    """Get model recommendation without provisioning.

    Args:
        content: The content to analyze
        require_fast: Prioritize speed
        require_cheap: Prioritize cost

    Returns:
        Recommendation dict with model info
    """
    config = SkillConfig(
        skill_type="model_router",
        name="Model Recommendation",
        parameters={
            "content": content,
            "require_fast": require_fast,
            "require_cheap": require_cheap
        }
    )

    router = MultiModelRouter(config)

    from open_notebook.skills.base import SkillContext
    ctx = SkillContext(
        skill_id=f"rec_{datetime.utcnow().timestamp()}",
        trigger_type="manual"
    )

    result = await router.run(ctx)

    if result.success:
        return {
            "success": True,
            "recommendation": result.output
        }
    else:
        return {
            "success": False,
            "error": result.error_message,
            "fallback": result.output.get("fallback")
        }


# Register the skill
register_skill(MultiModelRouter)
