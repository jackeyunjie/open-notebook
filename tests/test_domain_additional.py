"""
Additional unit tests for uncovered domain models.

This test suite covers:
- Credential (encryption, config generation)
- SkillInstance and SkillExecution
- WorkflowDefinition, WorkflowExecution, and related classes
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import SecretStr

from open_notebook.domain.credential import Credential
from open_notebook.domain.skill import SkillExecution, SkillInstance
from open_notebook.domain.workflow import (
    StepStatus,
    WorkflowDefinition,
    WorkflowExecution,
    WorkflowStatus,
    WorkflowStepDefinition,
    WorkflowStepExecution,
)


# ============================================================================
# TEST SUITE 1: Credential Domain
# ============================================================================


class TestCredentialDomain:
    """Test suite for Credential model."""

    def test_credential_creation(self):
        """Test basic credential creation."""
        cred = Credential(
            name="Test OpenAI",
            provider="openai",
            modalities=["language", "embedding"],
            api_key=SecretStr("sk-test123"),
        )
        assert cred.name == "Test OpenAI"
        assert cred.provider == "openai"
        assert cred.modalities == ["language", "embedding"]
        assert cred.api_key.get_secret_value() == "sk-test123"

    def test_credential_optional_fields(self):
        """Test credential with optional fields."""
        cred = Credential(
            name="Test Azure",
            provider="azure",
            modalities=["language"],
            api_key=SecretStr("key123"),
            base_url="https://api.example.com",
            endpoint="https://endpoint.example.com",
            api_version="2024-01-01",
            endpoint_llm="https://llm.example.com",
            project="my-project",
            location="eastus",
        )
        assert cred.base_url == "https://api.example.com"
        assert cred.endpoint == "https://endpoint.example.com"
        assert cred.api_version == "2024-01-01"
        assert cred.project == "my-project"

    def test_credential_to_esperanto_config(self):
        """Test config generation for Esperanto AIFactory."""
        cred = Credential(
            name="Test",
            provider="openai",
            modalities=["language"],
            api_key=SecretStr("sk-secret"),
            base_url="https://api.openai.com",
            api_version="v1",
        )
        config = cred.to_esperanto_config()
        assert config["api_key"] == "sk-secret"
        assert config["base_url"] == "https://api.openai.com"
        assert config["api_version"] == "v1"

    def test_credential_to_esperanto_config_partial(self):
        """Test config generation with only some fields set."""
        cred = Credential(
            name="Test",
            provider="openai",
            modalities=["language"],
            api_key=SecretStr("sk-secret"),
        )
        config = cred.to_esperanto_config()
        assert config["api_key"] == "sk-secret"
        assert "base_url" not in config
        assert "endpoint" not in config

    def test_credential_to_esperanto_config_no_api_key(self):
        """Test config generation without API key."""
        cred = Credential(
            name="Test",
            provider="ollama",
            modalities=["language"],
            base_url="http://localhost:11434",
        )
        config = cred.to_esperanto_config()
        assert "api_key" not in config
        assert config["base_url"] == "http://localhost:11434"

    def test_credential_nullable_fields(self):
        """Test that nullable fields are properly declared."""
        nullable_fields = Credential.nullable_fields
        expected_nullable = {
            "api_key",
            "base_url",
            "endpoint",
            "api_version",
            "endpoint_llm",
            "endpoint_embedding",
            "endpoint_stt",
            "endpoint_tts",
            "project",
            "location",
            "credentials_path",
        }
        assert expected_nullable.issubset(nullable_fields)


# ============================================================================
# TEST SUITE 2: Skill Domain
# ============================================================================


class TestSkillInstance:
    """Test suite for SkillInstance model."""

    def test_skill_instance_creation(self):
        """Test basic skill instance creation."""
        skill = SkillInstance(
            name="My RSS Feed",
            skill_type="rss_crawler",
            description="Crawls RSS feeds daily",
        )
        assert skill.name == "My RSS Feed"
        assert skill.skill_type == "rss_crawler"
        assert skill.description == "Crawls RSS feeds daily"
        assert skill.enabled is True
        assert skill.parameters == {}
        assert skill.schedule is None

    def test_skill_instance_defaults(self):
        """Test skill instance default values."""
        skill = SkillInstance(
            name="Test",
            skill_type="note_summarizer",
        )
        assert skill.enabled is True
        assert skill.parameters == {}
        assert skill.schedule is None
        assert skill.target_notebook_id is None

    def test_skill_instance_with_schedule(self):
        """Test skill instance with cron schedule."""
        skill = SkillInstance(
            name="Daily Summary",
            skill_type="note_summarizer",
            schedule="0 9 * * *",  # Daily at 9am
            target_notebook_id="notebook:123",
            parameters={"max_length": 500},
        )
        assert skill.schedule == "0 9 * * *"
        assert skill.target_notebook_id == "notebook:123"
        assert skill.parameters["max_length"] == 500

    def test_skill_instance_disabled(self):
        """Test disabled skill instance."""
        skill = SkillInstance(
            name="Disabled Skill",
            skill_type="rss_crawler",
            enabled=False,
        )
        assert skill.enabled is False

    def test_skill_instance_table_name(self):
        """Test skill instance table name."""
        assert SkillInstance.table_name == "skill_instance"


class TestSkillExecution:
    """Test suite for SkillExecution model."""

    def test_skill_execution_creation(self):
        """Test basic skill execution creation."""
        execution = SkillExecution(
            skill_instance_id="skill_instance:123",
            trigger_type="manual",
            triggered_by="user:456",
        )
        assert execution.skill_instance_id == "skill_instance:123"
        assert execution.status == "pending"
        assert execution.trigger_type == "manual"
        assert execution.triggered_by == "user:456"

    def test_skill_execution_defaults(self):
        """Test skill execution default values."""
        execution = SkillExecution(
            skill_instance_id="skill:123",
        )
        assert execution.status == "pending"
        assert execution.trigger_type == "manual"
        assert execution.output is None
        assert execution.error_message is None
        assert execution.created_source_ids == []
        assert execution.created_note_ids == []

    def test_skill_execution_mark_completed_success(self):
        """Test marking execution as successful."""
        execution = SkillExecution(
            skill_instance_id="skill:123",
            started_at="2024-01-01 10:00:00",
        )
        execution.mark_completed(
            status="success",
            output={"summary": "Test output"},
        )
        assert execution.status == "success"
        assert execution.output == {"summary": "Test output"}
        assert execution.completed_at is not None

    def test_skill_execution_mark_completed_failed(self):
        """Test marking execution as failed."""
        execution = SkillExecution(
            skill_instance_id="skill:123",
            started_at="2024-01-01 10:00:00",
        )
        execution.mark_completed(
            status="failed",
            error="Something went wrong",
        )
        assert execution.status == "failed"
        assert execution.error_message == "Something went wrong"
        assert execution.completed_at is not None

    def test_skill_execution_duration_seconds(self):
        """Test duration calculation."""
        execution = SkillExecution(
            skill_instance_id="skill:123",
            started_at="2024-01-01 10:00:00",
            completed_at="2024-01-01 10:00:30",
        )
        assert execution.duration_seconds == 30.0

    def test_skill_execution_duration_seconds_not_completed(self):
        """Test duration when not completed."""
        execution = SkillExecution(
            skill_instance_id="skill:123",
            started_at="2024-01-01 10:00:00",
        )
        assert execution.duration_seconds is None

    def test_skill_execution_duration_seconds_no_start(self):
        """Test duration when no start time."""
        execution = SkillExecution(
            skill_instance_id="skill:123",
            completed_at="2024-01-01 10:00:30",
        )
        assert execution.duration_seconds is None

    def test_skill_execution_table_name(self):
        """Test skill execution table name."""
        assert SkillExecution.table_name == "skill_execution"


# ============================================================================
# TEST SUITE 3: Workflow Domain
# ============================================================================


class TestWorkflowStepDefinition:
    """Test suite for WorkflowStepDefinition."""

    def test_step_definition_creation(self):
        """Test basic step definition creation."""
        step = WorkflowStepDefinition(
            step_id="step1",
            skill_type="rss_crawler",
            name="Fetch RSS",
            description="Fetches RSS feed",
        )
        assert step.step_id == "step1"
        assert step.skill_type == "rss_crawler"
        assert step.name == "Fetch RSS"
        assert step.depends_on == []
        assert step.parameters == {}
        assert step.retry_on_fail == 0

    def test_step_definition_with_dependencies(self):
        """Test step with dependencies."""
        step = WorkflowStepDefinition(
            step_id="step2",
            skill_type="note_summarizer",
            name="Summarize",
            depends_on=["step1", "step3"],
            parameters={"input": "{{steps.step1.output}}"},
            condition="steps.step1.status == 'success'",
            retry_on_fail=3,
            retry_delay_seconds=10,
            continue_on_fail=True,
        )
        assert step.depends_on == ["step1", "step3"]
        assert step.parameters["input"] == "{{steps.step1.output}}"
        assert step.condition == "steps.step1.status == 'success'"
        assert step.retry_on_fail == 3
        assert step.retry_delay_seconds == 10
        assert step.continue_on_fail is True


class TestWorkflowDefinition:
    """Test suite for WorkflowDefinition model."""

    def test_workflow_definition_creation(self):
        """Test basic workflow definition creation."""
        workflow = WorkflowDefinition(
            name="Content Pipeline",
            description="Fetches and processes content",
        )
        assert workflow.name == "Content Pipeline"
        assert workflow.description == "Fetches and processes content"
        assert workflow.enabled is True
        assert workflow.steps == []
        assert workflow.schedule is None

    def test_workflow_definition_with_steps(self):
        """Test workflow with steps."""
        steps = [
            WorkflowStepDefinition(step_id="step1", skill_type="rss_crawler"),
            WorkflowStepDefinition(
                step_id="step2",
                skill_type="note_summarizer",
                depends_on=["step1"],
            ),
        ]
        workflow = WorkflowDefinition(
            name="RSS Pipeline",
            steps=steps,
            input_schema={"url": {"type": "string"}},
            output_mapping={"result": "step2.output"},
        )
        assert len(workflow.steps) == 2
        assert workflow.input_schema == {"url": {"type": "string"}}
        assert workflow.output_mapping == {"result": "step2.output"}

    def test_workflow_get_step(self):
        """Test getting a step by ID."""
        workflow = WorkflowDefinition(
            name="Test",
            steps=[
                WorkflowStepDefinition(step_id="step1", skill_type="rss_crawler"),
                WorkflowStepDefinition(step_id="step2", skill_type="summarizer"),
            ],
        )
        step = workflow.get_step("step2")
        assert step is not None
        assert step.step_id == "step2"
        assert step.skill_type == "summarizer"

    def test_workflow_get_step_not_found(self):
        """Test getting a non-existent step."""
        workflow = WorkflowDefinition(
            name="Test",
            steps=[WorkflowStepDefinition(step_id="step1", skill_type="rss_crawler")],
        )
        step = workflow.get_step("nonexistent")
        assert step is None

    def test_workflow_get_root_steps(self):
        """Test getting root steps (no dependencies)."""
        workflow = WorkflowDefinition(
            name="Test",
            steps=[
                WorkflowStepDefinition(step_id="step1", skill_type="rss_crawler"),
                WorkflowStepDefinition(
                    step_id="step2",
                    skill_type="summarizer",
                    depends_on=["step1"],
                ),
                WorkflowStepDefinition(step_id="step3", skill_type="translator"),
            ],
        )
        roots = workflow.get_root_steps()
        assert len(roots) == 2
        assert {s.step_id for s in roots} == {"step1", "step3"}

    def test_workflow_get_dependent_steps(self):
        """Test getting steps that depend on a given step."""
        workflow = WorkflowDefinition(
            name="Test",
            steps=[
                WorkflowStepDefinition(step_id="step1", skill_type="rss_crawler"),
                WorkflowStepDefinition(
                    step_id="step2",
                    skill_type="summarizer",
                    depends_on=["step1"],
                ),
                WorkflowStepDefinition(
                    step_id="step3",
                    skill_type="translator",
                    depends_on=["step1"],
                ),
            ],
        )
        dependents = workflow.get_dependent_steps("step1")
        assert len(dependents) == 2
        assert {s.step_id for s in dependents} == {"step2", "step3"}

    def test_workflow_definition_table_name(self):
        """Test workflow definition table name."""
        assert WorkflowDefinition.table_name == "workflow_definition"


class TestWorkflowStepExecution:
    """Test suite for WorkflowStepExecution."""

    def test_step_execution_creation(self):
        """Test basic step execution creation."""
        exec_step = WorkflowStepExecution(
            step_id="step1",
            skill_type="rss_crawler",
        )
        assert exec_step.step_id == "step1"
        assert exec_step.skill_type == "rss_crawler"
        assert exec_step.status == StepStatus.PENDING
        assert exec_step.attempt == 1

    def test_step_execution_duration(self):
        """Test step execution duration calculation."""
        exec_step = WorkflowStepExecution(
            step_id="step1",
            skill_type="rss_crawler",
            started_at="2024-01-01T10:00:00",
            completed_at="2024-01-01T10:00:45",
        )
        assert exec_step.duration_seconds == 45.0

    def test_step_execution_duration_with_datetime_objects(self):
        """Test duration with datetime objects."""
        exec_step = WorkflowStepExecution(
            step_id="step1",
            skill_type="rss_crawler",
            started_at=datetime(2024, 1, 1, 10, 0, 0),
            completed_at=datetime(2024, 1, 1, 10, 1, 30),
        )
        assert exec_step.duration_seconds == 90.0

    def test_step_execution_duration_not_completed(self):
        """Test duration when not completed."""
        exec_step = WorkflowStepExecution(
            step_id="step1",
            skill_type="rss_crawler",
            started_at="2024-01-01T10:00:00",
        )
        assert exec_step.duration_seconds is None


class TestWorkflowExecution:
    """Test suite for WorkflowExecution model."""

    def test_workflow_execution_creation(self):
        """Test basic workflow execution creation."""
        execution = WorkflowExecution(
            workflow_definition_id="workflow_def:123",
            trigger_type="schedule",
            triggered_by="system",
        )
        assert execution.workflow_definition_id == "workflow_def:123"
        assert execution.status == WorkflowStatus.PENDING
        assert execution.trigger_type == "schedule"
        assert execution.step_executions == []

    def test_workflow_execution_get_step(self):
        """Test getting step execution."""
        execution = WorkflowExecution(
            workflow_definition_id="workflow:123",
            step_executions=[
                WorkflowStepExecution(step_id="step1", skill_type="rss_crawler"),
                WorkflowStepExecution(step_id="step2", skill_type="summarizer"),
            ],
        )
        step = execution.get_step_execution("step2")
        assert step is not None
        assert step.step_id == "step2"

    def test_workflow_execution_get_step_not_found(self):
        """Test getting non-existent step execution."""
        execution = WorkflowExecution(
            workflow_definition_id="workflow:123",
            step_executions=[
                WorkflowStepExecution(step_id="step1", skill_type="rss_crawler"),
            ],
        )
        step = execution.get_step_execution("nonexistent")
        assert step is None

    def test_workflow_execution_update_step(self):
        """Test updating step execution."""
        execution = WorkflowExecution(
            workflow_definition_id="workflow:123",
            step_executions=[
                WorkflowStepExecution(step_id="step1", skill_type="rss_crawler"),
            ],
        )
        new_step = WorkflowStepExecution(
            step_id="step1",
            skill_type="rss_crawler",
            status=StepStatus.SUCCESS,
            output={"items": [1, 2, 3]},
        )
        execution.update_step_execution(new_step)

        updated = execution.get_step_execution("step1")
        assert updated.status == StepStatus.SUCCESS
        assert updated.output == {"items": [1, 2, 3]}

    def test_workflow_execution_add_step(self):
        """Test adding new step execution."""
        execution = WorkflowExecution(
            workflow_definition_id="workflow:123",
            step_executions=[],
        )
        new_step = WorkflowStepExecution(
            step_id="step1",
            skill_type="rss_crawler",
            status=StepStatus.SUCCESS,
        )
        execution.update_step_execution(new_step)

        assert len(execution.step_executions) == 1
        assert execution.step_executions[0].step_id == "step1"

    def test_workflow_execution_mark_completed(self):
        """Test marking workflow execution as completed."""
        execution = WorkflowExecution(
            workflow_definition_id="workflow:123",
            started_at="2024-01-01 10:00:00",
        )
        execution.mark_completed(
            status=WorkflowStatus.SUCCESS,
            output={"result": "All done"},
        )
        assert execution.status == WorkflowStatus.SUCCESS
        assert execution.output == {"result": "All done"}
        assert execution.completed_at is not None

    def test_workflow_execution_duration(self):
        """Test workflow execution duration."""
        execution = WorkflowExecution(
            workflow_definition_id="workflow:123",
            started_at="2024-01-01T10:00:00",
            completed_at="2024-01-01T10:05:30",
        )
        assert execution.duration_seconds == 330.0  # 5.5 minutes

    def test_workflow_execution_success_rate(self):
        """Test success rate calculation."""
        execution = WorkflowExecution(
            workflow_definition_id="workflow:123",
            step_executions=[
                WorkflowStepExecution(
                    step_id="step1",
                    skill_type="rss_crawler",
                    status=StepStatus.SUCCESS,
                ),
                WorkflowStepExecution(
                    step_id="step2",
                    skill_type="summarizer",
                    status=StepStatus.SUCCESS,
                ),
                WorkflowStepExecution(
                    step_id="step3",
                    skill_type="translator",
                    status=StepStatus.FAILED,
                ),
            ],
        )
        assert execution.success_rate == 2 / 3

    def test_workflow_execution_success_rate_empty(self):
        """Test success rate with no steps."""
        execution = WorkflowExecution(
            workflow_definition_id="workflow:123",
            step_executions=[],
        )
        assert execution.success_rate == 0.0

    def test_workflow_execution_table_name(self):
        """Test workflow execution table name."""
        assert WorkflowExecution.table_name == "workflow_execution"


# ============================================================================
# TEST SUITE 4: Workflow Status Enums
# ============================================================================


class TestWorkflowEnums:
    """Test suite for workflow status enums."""

    def test_workflow_status_values(self):
        """Test workflow status enum values."""
        assert WorkflowStatus.PENDING == "pending"
        assert WorkflowStatus.RUNNING == "running"
        assert WorkflowStatus.SUCCESS == "success"
        assert WorkflowStatus.FAILED == "failed"
        assert WorkflowStatus.CANCELLED == "cancelled"
        assert WorkflowStatus.PARTIAL == "partial"

    def test_step_status_values(self):
        """Test step status enum values."""
        assert StepStatus.PENDING == "pending"
        assert StepStatus.RUNNING == "running"
        assert StepStatus.SUCCESS == "success"
        assert StepStatus.FAILED == "failed"
        assert StepStatus.SKIPPED == "skipped"
        assert StepStatus.RETRYING == "retrying"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
