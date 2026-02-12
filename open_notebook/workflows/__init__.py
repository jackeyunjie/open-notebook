"""Workflow orchestration system for Open Notebook.

This module provides workflow capabilities that orchestrate multiple skills
into pipelines with dependencies, conditions, and retry logic.

Components:
- WorkflowEngine: Core orchestration engine
- WorkflowService: High-level service for workflow operations
- WorkflowTemplate: Pre-built workflow templates
- TemplateRegistry: Registry for browsing templates
"""

from open_notebook.workflows.conversational import (
    ConversationalWorkflowBuilder,
    WorkflowSuggestionEngine,
)
from open_notebook.workflows.engine import WorkflowEngine
from open_notebook.workflows.service import WorkflowService
from open_notebook.workflows.templates import TemplateRegistry, WorkflowTemplate

__all__ = [
    "WorkflowEngine",
    "WorkflowService",
    "TemplateRegistry",
    "WorkflowTemplate",
    "ConversationalWorkflowBuilder",
    "WorkflowSuggestionEngine",
]
