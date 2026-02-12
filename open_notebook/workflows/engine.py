"""WorkflowEngine implementation for orchestrating skills.

The WorkflowEngine is responsible for:
1. Parsing workflow definitions
2. Managing step dependencies and execution order
3. Executing skills with proper context
4. Handling retries and error conditions
5. Persisting execution state
"""

import asyncio
import json
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from loguru import logger

from open_notebook.domain.workflow import (
    StepStatus,
    WorkflowDefinition,
    WorkflowExecution,
    WorkflowStatus,
    WorkflowStepDefinition,
    WorkflowStepExecution,
)
from open_notebook.skills import SkillConfig, SkillContext, SkillRegistry, SkillResult, SkillStatus


class WorkflowContext:
    """Runtime context for workflow execution.

    Maintains the state of the workflow execution including:
    - Input data
    - Step outputs
    - Execution variables
    """

    def __init__(self, input_data: Dict[str, Any]):
        self.input = input_data
        self.steps: Dict[str, WorkflowStepExecution] = {}
        self.variables: Dict[str, Any] = {}

    def set_step_result(self, step_id: str, execution: WorkflowStepExecution) -> None:
        """Store step execution result."""
        self.steps[step_id] = execution

    def get_step_output(self, step_id: str) -> Optional[Dict[str, Any]]:
        """Get output from a completed step."""
        if step_id in self.steps:
            return self.steps[step_id].output
        return None

    def resolve_template(self, template: Any) -> Any:
        """Resolve template strings with workflow context.

        Supports syntax:
        - {{input.field}} - Access input data
        - {{steps.step_id.output.field}} - Access step output
        - {{vars.name}} - Access workflow variables

        Args:
            template: Template string or nested data structure

        Returns:
            Resolved value with templates replaced
        """
        if isinstance(template, str):
            return self._resolve_string_template(template)
        elif isinstance(template, dict):
            return {k: self.resolve_template(v) for k, v in template.items()}
        elif isinstance(template, list):
            return [self.resolve_template(item) for item in template]
        return template

    def _resolve_string_template(self, template: str) -> Any:
        """Resolve a single template string."""
        # Pattern for {{...}}
        pattern = r"\{\{\s*(.+?)\s*\}\}"

        def replacer(match):
            path = match.group(1).strip()
            return str(self._get_value_by_path(path))

        # If the entire string is a template, return the actual value (not stringified)
        full_match = re.fullmatch(pattern, template)
        if full_match:
            return self._get_value_by_path(full_match.group(1).strip())

        # Otherwise, replace all templates within the string
        return re.sub(pattern, replacer, template)

    def _get_value_by_path(self, path: str) -> Any:
        """Get value from context using dot notation path."""
        parts = path.split(".")
        if not parts:
            return None

        root = parts[0]
        remainder = parts[1:]

        if root == "input":
            current = self.input
        elif root == "steps":
            if len(remainder) < 1:
                return None
            step_id = remainder[0]
            current = self.get_step_output(step_id)
            remainder = remainder[1:]
        elif root == "vars":
            if len(remainder) < 1:
                return None
            return self.variables.get(remainder[0])
        else:
            return None

        # Navigate nested structure
        for key in remainder:
            if current is None:
                return None
            if isinstance(current, dict):
                current = current.get(key)
            else:
                return None

        return current


class WorkflowEngine:
    """Engine for executing workflows.

    Manages the execution lifecycle:
    1. Parse workflow definition
    2. Build dependency graph
    3. Execute steps in dependency order
    4. Handle retries and conditions
    5. Persist execution state
    """

    def __init__(self):
        self._running: Set[str] = set()  # Track running workflow executions

    async def execute(
        self,
        workflow: WorkflowDefinition,
        input_data: Optional[Dict[str, Any]] = None,
        trigger_type: str = "manual",
        triggered_by: Optional[str] = None,
    ) -> WorkflowExecution:
        """Execute a workflow.

        Args:
            workflow: The workflow definition to execute
            input_data: Input parameters for the workflow
            trigger_type: How the workflow was triggered
            triggered_by: ID of the user/system that triggered it

        Returns:
            WorkflowExecution with complete execution history
        """
        # Create execution record
        execution = WorkflowExecution(
            workflow_definition_id=workflow.id or "",
            trigger_type=trigger_type,
            triggered_by=triggered_by,
            input_data=input_data or {},
            status=WorkflowStatus.PENDING,
        )
        await execution.save()

        # Check if workflow is enabled
        if not workflow.enabled:
            execution.mark_completed(
                WorkflowStatus.CANCELLED,
                error="Workflow is disabled"
            )
            await execution.save()
            return execution

        # Start execution
        self._running.add(execution.id)
        execution.status = WorkflowStatus.RUNNING
        execution.started_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        await execution.save()

        try:
            # Build and execute dependency graph
            context = WorkflowContext(input_data or {})
            await self._execute_workflow(workflow, execution, context)

        except Exception as e:
            logger.exception(f"Workflow execution failed: {e}")
            execution.mark_completed(
                WorkflowStatus.FAILED,
                error=str(e)
            )
            await execution.save()

        finally:
            self._running.discard(execution.id)

        return execution

    async def _execute_workflow(
        self,
        workflow: WorkflowDefinition,
        execution: WorkflowExecution,
        context: WorkflowContext,
    ) -> None:
        """Execute all steps in the workflow."""
        # Validate workflow before execution
        self._validate_workflow(workflow)

        # Build dependency graph
        dependency_graph = self._build_dependency_graph(workflow.steps)

        # Track completed and failed steps
        completed_steps: Set[str] = set()
        failed_steps: Set[str] = set()
        skipped_steps: Set[str] = set()

        # Execute steps in waves (all steps whose dependencies are satisfied)
        while len(completed_steps) + len(failed_steps) + len(skipped_steps) < len(workflow.steps):
            # Find ready steps (all dependencies satisfied)
            ready_steps = self._get_ready_steps(
                workflow.steps,
                dependency_graph,
                completed_steps,
                failed_steps,
                skipped_steps
            )

            if not ready_steps:
                # Deadlock or circular dependency
                remaining = set(step.step_id for step in workflow.steps) - completed_steps - failed_steps - skipped_steps
                if remaining:
                    logger.error(f"Deadlock detected. Remaining steps: {remaining}")
                    for step_id in remaining:
                        step_exec = WorkflowStepExecution(
                            step_id=step_id,
                            skill_type="unknown",
                            status=StepStatus.FAILED,
                            error_message="Deadlock - dependencies cannot be satisfied"
                        )
                        execution.update_step_execution(step_exec)
                break

            # Execute ready steps in parallel
            step_tasks = []
            for step in ready_steps:
                task = self._execute_step(step, workflow, execution, context)
                step_tasks.append((step.step_id, task))

            # Wait for all ready steps to complete
            for step_id, task in step_tasks:
                try:
                    step_exec = await task
                    context.set_step_result(step_id, step_exec)
                    execution.update_step_execution(step_exec)

                    if step_exec.status == StepStatus.SUCCESS:
                        completed_steps.add(step_id)
                    elif step_exec.status == StepStatus.SKIPPED:
                        skipped_steps.add(step_id)
                    else:
                        failed_steps.add(step_id)

                except Exception as e:
                    logger.exception(f"Step {step_id} failed with exception: {e}")
                    failed_steps.add(step_id)

        # Determine final status
        if failed_steps:
            if completed_steps:
                final_status = WorkflowStatus.PARTIAL
            else:
                final_status = WorkflowStatus.FAILED
        else:
            final_status = WorkflowStatus.SUCCESS

        # Aggregate created resources
        all_source_ids = []
        all_note_ids = []
        for step_exec in execution.step_executions:
            if step_exec.created_source_ids:
                all_source_ids.extend(step_exec.created_source_ids)
            if step_exec.created_note_ids:
                all_note_ids.extend(step_exec.created_note_ids)

        execution.created_source_ids = list(set(all_source_ids))
        execution.created_note_ids = list(set(all_note_ids))

        # Build final output
        output = self._build_output(workflow, context)
        execution.mark_completed(final_status, output=output)
        await execution.save()

    def _build_dependency_graph(
        self,
        steps: List[WorkflowStepDefinition]
    ) -> Dict[str, Set[str]]:
        """Build a graph of step dependencies.

        Returns:
            Dict mapping step_id -> set of dependency step_ids
        """
        graph = {}
        for step in steps:
            graph[step.step_id] = set(step.depends_on)
        return graph

    def _detect_cycle(self, graph: Dict[str, Set[str]]) -> Optional[List[str]]:
        """Detect cycle in dependency graph using DFS.

        Returns:
            List of step IDs forming a cycle, or None if no cycle
        """
        WHITE, GRAY, BLACK = 0, 1, 2
        color = {node: WHITE for node in graph}
        path = []

        def dfs(node):
            color[node] = GRAY
            path.append(node)
            for neighbor in graph.get(node, set()):
                if color[neighbor] == GRAY:
                    cycle_start = path.index(neighbor)
                    return path[cycle_start:] + [neighbor]
                if color[neighbor] == WHITE:
                    result = dfs(neighbor)
                    if result:
                        return result
            path.pop()
            color[node] = BLACK
            return None

        for node in graph:
            if color[node] == WHITE:
                result = dfs(node)
                if result:
                    return result
        return None

    def _validate_workflow(self, workflow: WorkflowDefinition) -> None:
        """Validate workflow definition before execution.

        Raises:
            ValueError: If validation fails (duplicate IDs, undefined deps, cycles)
        """
        # Check step ID uniqueness
        step_ids = [step.step_id for step in workflow.steps]
        if len(step_ids) != len(set(step_ids)):
            from collections import Counter
            counts = Counter(step_ids)
            duplicates = [sid for sid, count in counts.items() if count > 1]
            raise ValueError(f"Duplicate step IDs: {duplicates}")

        # Check dependencies exist
        all_step_ids = set(step_ids)
        for step in workflow.steps:
            for dep_id in step.depends_on:
                if dep_id not in all_step_ids:
                    raise ValueError(
                        f"Step '{step.step_id}' depends on undefined step '{dep_id}'"
                    )

        # Detect circular dependencies
        graph = self._build_dependency_graph(workflow.steps)
        cycle = self._detect_cycle(graph)
        if cycle:
            raise ValueError(f"Circular dependency detected: {' -> '.join(cycle)}")

    def _get_ready_steps(
        self,
        steps: List[WorkflowStepDefinition],
        dependency_graph: Dict[str, Set[str]],
        completed_steps: Set[str],
        failed_steps: Set[str],
        skipped_steps: Set[str],
    ) -> List[WorkflowStepDefinition]:
        """Get steps that are ready to execute.

        A step is ready when:
        - It hasn't been executed yet
        - All its dependencies are completed (success or skipped)
        - No dependencies have failed (unless continue_on_fail)
        """
        ready = []
        executed = completed_steps | failed_steps | skipped_steps

        for step in steps:
            if step.step_id in executed:
                continue

            deps = dependency_graph.get(step.step_id, set())

            # Check if all dependencies are satisfied
            deps_satisfied = True
            for dep_id in deps:
                if dep_id in failed_steps:
                    # Dependency failed - check if we should continue
                    dep_step = next((s for s in steps if s.step_id == dep_id), None)
                    if not dep_step or not dep_step.continue_on_fail:
                        deps_satisfied = False
                        break
                elif dep_id not in completed_steps and dep_id not in skipped_steps:
                    deps_satisfied = False
                    break

            if deps_satisfied:
                ready.append(step)

        return ready

    async def _execute_step(
        self,
        step: WorkflowStepDefinition,
        workflow: WorkflowDefinition,
        execution: WorkflowExecution,
        context: WorkflowContext,
    ) -> WorkflowStepExecution:
        """Execute a single workflow step."""
        step_exec = WorkflowStepExecution(
            step_id=step.step_id,
            skill_type=step.skill_type,
            status=StepStatus.PENDING,
            max_attempts=step.retry_on_fail + 1,
        )

        # Check condition if specified
        if step.condition:
            should_run = self._evaluate_condition(step.condition, context)
            if not should_run:
                step_exec.status = StepStatus.SKIPPED
                step_exec.output = {"skipped": True, "reason": "Condition not met"}
                return step_exec

        # Resolve parameters with template substitution
        resolved_params = context.resolve_template(step.parameters)

        # Execute with retry logic
        for attempt in range(1, step.retry_on_fail + 2):
            step_exec.attempt = attempt
            step_exec.started_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            step_exec.status = StepStatus.RUNNING

            try:
                # Get skill class
                skill_class = SkillRegistry.get_skill_class(step.skill_type)
                if not skill_class:
                    raise ValueError(f"Unknown skill type: {step.skill_type}")

                # Create skill config
                config = SkillConfig(
                    skill_type=step.skill_type,
                    name=step.name or step.skill_type,
                    description=step.description,
                    parameters=resolved_params,
                    target_notebook_id=workflow.target_notebook_id,
                )

                # Create skill instance
                skill = skill_class(config)

                # Build skill context
                skill_context = SkillContext(
                    skill_id=f"{execution.id}:{step.step_id}",
                    trigger_type="workflow",
                    notebook_id=workflow.target_notebook_id,
                    parameters=resolved_params,
                )

                # Execute skill
                logger.info(f"Executing step {step.step_id} (attempt {attempt})")
                result: SkillResult = await skill.run(skill_context)

                # Process result
                if result.success:
                    step_exec.status = StepStatus.SUCCESS
                    step_exec.output = result.output
                    step_exec.completed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    step_exec.created_source_ids = result.created_source_ids
                    step_exec.created_note_ids = result.created_note_ids
                    return step_exec
                else:
                    # Skill failed
                    step_exec.error_message = result.error_message
                    if attempt <= step.retry_on_fail:
                        logger.warning(
                            f"Step {step.step_id} failed (attempt {attempt}), retrying..."
                        )
                        step_exec.status = StepStatus.RETRYING
                        await asyncio.sleep(step.retry_delay_seconds)
                    else:
                        step_exec.status = StepStatus.FAILED
                        step_exec.completed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        return step_exec

            except Exception as e:
                logger.exception(f"Step {step.step_id} execution failed: {e}")
                step_exec.error_message = str(e)
                if attempt <= step.retry_on_fail:
                    step_exec.status = StepStatus.RETRYING
                    await asyncio.sleep(step.retry_delay_seconds)
                else:
                    step_exec.status = StepStatus.FAILED
                    step_exec.completed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    return step_exec

        return step_exec

    def _evaluate_condition(self, condition: str, context: WorkflowContext) -> bool:
        """Evaluate a condition expression with restricted context.

        Args:
            condition: Python expression using context variables
            context: Workflow context with step results

        Returns:
            True if condition passes, False otherwise
        """
        try:
            # Whitelist of allowed builtins for safe evaluation
            allowed_builtins = {
                'len': len,
                'any': any,
                'all': all,
                'isinstance': isinstance,
                'str': str,
                'int': int,
                'bool': bool,
                'float': float,
                'list': list,
                'dict': dict,
                'set': set,
                'tuple': tuple,
                'abs': abs,
                'min': min,
                'max': max,
                'sum': sum,
                'round': round,
            }

            eval_context = {
                "__builtins__": allowed_builtins,
                "input": context.input,
                "steps": {
                    step_id: {
                        "status": exec.status.value,
                        "output": exec.output or {},
                    }
                    for step_id, exec in context.steps.items()
                },
                "vars": context.variables,
            }

            # Evaluate condition with restricted context
            result = eval(condition, eval_context)
            return bool(result)

        except Exception as e:
            logger.error(f"Condition evaluation failed: {e}")
            return False

    def _build_output(
        self,
        workflow: WorkflowDefinition,
        context: WorkflowContext,
    ) -> Dict[str, Any]:
        """Build final workflow output based on output mapping."""
        output = {
            "steps": {
                step_id: {
                    "status": exec.status.value,
                    "output": exec.output,
                }
                for step_id, exec in context.steps.items()
            },
            "sources_created": [],
            "notes_created": [],
        }

        # Apply output mapping if defined
        if workflow.output_mapping:
            for key, template in workflow.output_mapping.items():
                output[key] = context.resolve_template(template)

        return output

    async def cancel(self, execution_id: str) -> bool:
        """Cancel a running workflow execution.

        Args:
            execution_id: ID of the execution to cancel

        Returns:
            True if cancelled, False if not running
        """
        if execution_id not in self._running:
            return False

        # Note: Actual cancellation is complex with async tasks
        # This is a simplified implementation
        self._running.discard(execution_id)

        execution = await WorkflowExecution.get(execution_id)
        if execution and execution.status == WorkflowStatus.RUNNING:
            execution.mark_completed(
                WorkflowStatus.CANCELLED,
                error="Cancelled by user"
            )
            await execution.save()

        return True

    def is_running(self, execution_id: str) -> bool:
        """Check if a workflow execution is currently running."""
        return execution_id in self._running
