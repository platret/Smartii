#!/usr/bin/env python3
"""
Workflow manager for agenthero-ai agent.
Implements Phase 1: Core workflow enforcement with schema validation, file locking, 
criteria evaluation, and error recovery.
"""

import json
import sys
import os
import re
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Any, Tuple, Optional

# Platform-specific file locking
try:
    import fcntl  # Linux/Mac
    HAS_FCNTL = True
except ImportError:
    HAS_FCNTL = False
    try:
        import msvcrt  # Windows
        HAS_MSVCRT = True
    except ImportError:
        HAS_MSVCRT = False

# JSON Schema validation
try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False
    print("WARNING: jsonschema not installed. Schema validation disabled.", file=sys.stderr)
    print("Install with: pip install jsonschema", file=sys.stderr)

# Phase 2/3 Integration - Advanced Features
try:
    from event_bus import (
        emit_workflow_started,
        emit_workflow_completed,
        emit_workflow_initialized,
        emit_phase_started,
        emit_phase_completed,
        emit_step_started,
        emit_step_completed,
        emit_step_failed
    )
    HAS_EVENT_BUS = True
except ImportError:
    HAS_EVENT_BUS = False
    print("WARNING: event_bus module not found. Event emissions disabled.", file=sys.stderr)

try:
    from cache import (
        get_cache,
        get_cached_settings,
        cache_settings,
        get_cached_topic_state,
        cache_topic_state
    )
    HAS_CACHE = True
except ImportError:
    HAS_CACHE = False
    print("WARNING: cache module not found. Caching disabled.", file=sys.stderr)

try:
    from hooks import get_hooks_manager
    HAS_HOOKS = True
except ImportError:
    HAS_HOOKS = False
    print("WARNING: hooks module not found. Hooks disabled.", file=sys.stderr)

try:
    from performance import get_performance_monitor
    HAS_PERFORMANCE = True
except ImportError:
    HAS_PERFORMANCE = False
    print("WARNING: performance module not found. Performance monitoring disabled.", file=sys.stderr)

import time  # For performance timing


class FileLock:
    """Cross-platform file locking context manager."""

    def __init__(self, file_handle):
        self.file_handle = file_handle
        self.locked = False
        self.platform = None

    def __enter__(self):
        """Acquire lock."""
        try:
            if HAS_FCNTL:
                fcntl.flock(self.file_handle.fileno(), fcntl.LOCK_EX)
                self.locked = True
                self.platform = 'fcntl'
            elif HAS_MSVCRT:
                # Windows locking - lock 1 byte at position 0
                self.file_handle.seek(0)
                msvcrt.locking(self.file_handle.fileno(), msvcrt.LK_NBLCK, 1)
                self.locked = True
                self.platform = 'msvcrt'
            else:
                print("WARNING: File locking not available on this platform", file=sys.stderr)
        except (IOError, OSError) as e:
            # If locking fails, continue without lock (better than crashing)
            print(f"WARNING: Could not acquire file lock: {e}", file=sys.stderr)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Release lock."""
        if self.locked:
            try:
                if self.platform == 'fcntl':
                    fcntl.flock(self.file_handle.fileno(), fcntl.LOCK_UN)
                elif self.platform == 'msvcrt':
                    # Windows unlock - unlock 1 byte at position 0
                    self.file_handle.seek(0)
                    msvcrt.locking(self.file_handle.fileno(), msvcrt.LK_UNLCK, 1)
            except (IOError, OSError) as e:
                print(f"WARNING: Could not release file lock: {e}", file=sys.stderr)
        return False


class CriteriaEvaluator:
    """Safe expression evaluator for completion criteria."""
    
    @staticmethod
    def evaluate(criterion: str, context: Dict[str, Any]) -> bool:
        """
        Safely evaluate a completion criterion.
        
        Supported patterns:
        - "variable_name" - Check existence (truthy)
        - "variable_name == value" - Equality
        - "variable_name != value" - Inequality
        - "variable_name > value" - Greater than
        - "variable_name >= value" - Greater than or equal
        - "variable_name < value" - Less than
        - "variable_name <= value" - Less than or equal
        - "variable_name in [list]" - Membership
        
        Args:
            criterion: Criterion string to evaluate
            context: Dictionary of variables available for evaluation
            
        Returns:
            True if criterion is met, False otherwise
        """
        criterion = criterion.strip()
        
        # Pattern: variable_name > value
        comparison_match = re.match(r'^(\w+)\s*(==|!=|>=|<=|>|<)\s*(.+)$', criterion)
        if comparison_match:
            var_name, operator, value_str = comparison_match.groups()
            
            if var_name not in context:
                return False
            
            var_value = context[var_name]
            
            # Try to parse value as int, float, or keep as string
            try:
                if '.' in value_str:
                    value = float(value_str)
                else:
                    value = int(value_str)
            except ValueError:
                value = value_str.strip('"\'')
            
            # Perform comparison
            if operator == '==':
                return var_value == value
            elif operator == '!=':
                return var_value != value
            elif operator == '>':
                return var_value > value
            elif operator == '>=':
                return var_value >= value
            elif operator == '<':
                return var_value < value
            elif operator == '<=':
                return var_value <= value
        
        # Pattern: variable_name (existence check)
        if re.match(r'^\w+$', criterion):
            return criterion in context and bool(context[criterion])
        
        # Pattern: not variable_name
        not_match = re.match(r'^not\s+(\w+)$', criterion)
        if not_match:
            var_name = not_match.group(1)
            return var_name not in context or not bool(context[var_name])
        
        # If no pattern matches, return False
        return False


def load_settings(settings_path: str = ".claude/agents/agenthero-ai/settings.json") -> Dict[str, Any]:
    """
    Load workflow settings with schema validation and caching (Phase 2).

    Args:
        settings_path: Path to settings.json file

    Returns:
        Validated settings dictionary

    Raises:
        FileNotFoundError: If settings file doesn't exist
        jsonschema.ValidationError: If settings don't match schema
    """
    settings_file = Path(settings_path)

    if not settings_file.exists():
        raise FileNotFoundError(f"Settings file not found: {settings_path}")

    # Phase 2: Try cache first
    if HAS_CACHE:
        cached = get_cached_settings(settings_file)
        if cached:
            return cached

    with open(settings_file, 'r', encoding='utf-8') as f:
        settings = json.load(f)

    # Validate against schema if jsonschema is available
    if HAS_JSONSCHEMA:
        schema_path = settings_file.parent / "settings.schema.json"
        if schema_path.exists():
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema = json.load(f)

            try:
                jsonschema.validate(settings, schema)
            except jsonschema.ValidationError as e:
                print(f"ERROR: Settings validation failed: {e.message}", file=sys.stderr)
                print(f"Path: {' -> '.join(str(p) for p in e.path)}", file=sys.stderr)
                raise

    # Phase 2: Cache the settings
    if HAS_CACHE:
        cache_settings(settings, settings_file)

    return settings


def load_topic_state(topic_slug: str, settings: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Load topic state file with file locking and caching (Phase 2).

    Args:
        topic_slug: Topic slug identifier
        settings: Optional settings dict (will load if not provided)

    Returns:
        Topic state dictionary
    """
    if settings is None:
        settings = load_settings()

    topics_dir = settings["paths"]["topics_directory"]
    topic_file = Path(topics_dir) / topic_slug / "topic.json"

    if not topic_file.exists():
        raise FileNotFoundError(f"Topic state file not found: {topic_file}")

    # Phase 2: Try cache first
    if HAS_CACHE:
        cached = get_cached_topic_state(topic_slug, topic_file)
        if cached:
            return cached

    # Open in r+ mode for locking compatibility (Windows requires write access for locking)
    with open(topic_file, 'r+', encoding='utf-8') as f:
        with FileLock(f):
            f.seek(0)
            topic = json.load(f)

    # Phase 2: Cache the topic state
    if HAS_CACHE:
        cache_topic_state(topic_slug, topic, topic_file)

    return topic


def save_topic_state(topic_slug: str, topic_data: Dict[str, Any], settings: Optional[Dict[str, Any]] = None) -> None:
    """
    Save topic state file with file locking and atomic writes.

    Uses temp file + atomic rename to prevent data loss if crash occurs during write.

    Args:
        topic_slug: Topic slug identifier
        topic_data: Topic state dictionary to save
        settings: Optional settings dict (will load if not provided)
    """
    if settings is None:
        settings = load_settings()

    topics_dir = settings["paths"]["topics_directory"]
    topic_file = Path(topics_dir) / topic_slug / "topic.json"
    temp_file = topic_file.with_suffix('.tmp')

    # Write to temporary file first (no lock needed - it's our temp file)
    with open(temp_file, 'w', encoding='utf-8') as f:
        json.dump(topic_data, f, indent=2, ensure_ascii=False)

    # Now acquire lock on original file, then close it before rename
    # (Windows requires file to be closed before rename)
    with open(topic_file, 'r+', encoding='utf-8') as f:
        with FileLock(f):
            pass  # Just acquire and release lock

    # File is now closed, safe to rename (atomic operation)
    # POSIX: atomic; Windows: atomic if same volume
    temp_file.replace(topic_file)

    # Phase 2: Invalidate cache after write
    if HAS_CACHE:
        cache = get_cache()
        cache.invalidate(str(topic_file))


def get_mandatory_agents(settings: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract mandatory agents from settings.

    Args:
        settings: Settings dictionary

    Returns:
        List of mandatory agent configurations

    Example:
        [
            {
                "name": "agenthero-docs-expert",
                "feature": "documentation_generation",
                "trigger": "after_all_primary_tasks",
                "depends_on": [],
                "deliverables": ["README.md"],
                "handover_context": {...}
            },
            {
                "name": "agenthero-qa-validate",
                "feature": "qa_validation",
                "trigger": "after_documentation",
                "depends_on": ["documentation_generation"],
                "deliverables": [],
                "handover_context": {...}
            }
        ]
    """
    mandatory = []
    features = settings.get("features", {})

    # Check documentation_generation feature
    doc_gen = features.get("documentation_generation", {})
    if doc_gen.get("enabled", False) and doc_gen.get("enforce", False):
        mandatory.append({
            "name": doc_gen.get("agent", "agenthero-docs-expert"),
            "feature": "documentation_generation",
            "trigger": doc_gen.get("trigger", "after_all_primary_tasks"),
            "depends_on": [],
            "deliverables": doc_gen.get("deliverables", ["README.md"]),
            "location": doc_gen.get("location", "Project-tasks/{topic-slug}/deliverables/"),
            "handover_context": doc_gen.get("handover_context", {})
        })

    # Check qa_validation feature
    qa_val = features.get("qa_validation", {})
    if qa_val.get("enabled", False) and qa_val.get("enforce", False):
        mandatory.append({
            "name": qa_val.get("validator_agent", "agenthero-qa-validate"),
            "feature": "qa_validation",
            "trigger": qa_val.get("trigger", "after_documentation"),
            "depends_on": qa_val.get("depends_on", ["documentation_generation"]),
            "deliverables": [],
            "handover_context": qa_val.get("handover_context", {})
        })

    return mandatory


def validate_agent_name(agent_name: str, settings: Optional[Dict[str, Any]] = None) -> Tuple[bool, str]:
    """
    Validate agent name follows AgentHero AI naming conventions.

    All agents created by AgentHero AI MUST use the 'aghero-' prefix.
    Standalone agents (documentation-expert, deliverables-qa-validator) are exempt.

    Args:
        agent_name: Agent name to validate
        settings: Optional settings dict (checks enforce_naming_conventions flag)

    Returns:
        Tuple of (is_valid, message)

    Examples:
        >>> validate_agent_name("aghero-testing-agent")
        (True, "✅ Valid agent name")

        >>> validate_agent_name("testing-agent")
        (False, "❌ Agent name must start with 'aghero-' prefix...")

        >>> validate_agent_name("agenthero-docs-expert")
        (True, "✅ Valid standalone agent: agenthero-docs-expert")
    """
    # Load settings if not provided
    if settings is None:
        try:
            settings = load_settings()
        except Exception:
            settings = {}

    # Check if naming convention enforcement is enabled
    agent_library = settings.get("features", {}).get("agent_library", {})
    enforce = agent_library.get("enforce_naming_conventions", True)

    if not enforce:
        return True, "✅ Naming convention enforcement disabled"

    # List of standalone agents that don't require aghero- prefix
    # NOTE: Core infrastructure agents now use agenthero- prefix
    STANDALONE_AGENTS = [
        "agenthero-docs-expert",      # Core infrastructure: Documentation generation
        "agenthero-qa-validate",      # Core infrastructure: QA validation
        "single-page-website-builder",
        "market-research-analyst",
        "feature-comparison-analyst"
    ]

    # Check if it's a standalone agent
    if agent_name in STANDALONE_AGENTS:
        return True, f"✅ Valid standalone agent: {agent_name}"

    # Check if it starts with aghero- prefix
    if agent_name.startswith("aghero-"):
        # Validate format: aghero-{descriptive-name}
        if len(agent_name) <= 7:  # Just "aghero-" with nothing after
            return False, "❌ Agent name must have descriptive name after 'aghero-' prefix. Example: aghero-testing-agent"

        # Check for valid characters (lowercase, hyphens only)
        if not re.match(r'^aghero-[a-z0-9]+(-[a-z0-9]+)*$', agent_name):
            return False, "❌ Agent name must use lowercase letters, numbers, and hyphens only. Example: aghero-api-builder"

        return True, f"✅ Valid AgentHero AI agent: {agent_name}"

    # Invalid: doesn't start with aghero- and not a standalone agent
    return False, f"""❌ Agent name must start with 'aghero-' prefix.

AgentHero AI Naming Convention:
- All created agents MUST use 'aghero-' prefix
- Examples: aghero-testing-agent, aghero-api-builder, aghero-ui-designer

Your agent name: {agent_name}
Suggested name: aghero-{agent_name}

Core infrastructure agents (agenthero- prefix):
- agenthero-docs-expert (documentation generation)
- agenthero-qa-validate (QA validation)

Other standalone agents:
- single-page-website-builder
"""


def build_handover_context(
    topic_slug: str,
    context_spec: Dict[str, Any],
    settings: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Build handover context for mandatory agents based on specification.

    Args:
        topic_slug: Topic identifier
        context_spec: Context specification from settings (handover_context field)
        settings: Optional settings dict

    Returns:
        Dictionary of context data to pass to agent

    Example:
        {
            "topic_slug": "subshero-website",
            "all_deliverables_list": [
                {"name": "subshero-landing-v1.html", "path": "...", "status": "complete"},
                {"name": "subshero-landing-v2.html", "path": "...", "status": "complete"}
            ],
            "task_summaries": [
                {"task_id": "task-001", "agent": "single-page-website-builder", "status": "complete"}
            ],
            "acceptance_criteria_complete": [...],
            "spec_file_path": "Project-tasks/subshero-website/spec/subshero-website-spec.md"
        }
    """
    if settings is None:
        settings = load_settings()

    topic = load_topic_state(topic_slug, settings)
    context = {"topic_slug": topic_slug}

    include_list = context_spec.get("include", [])

    for item in include_list:
        if item == "all_deliverables_list":
            # Extract all deliverables from completed tasks
            deliverables = []
            for task in topic.get("topic", {}).get("tasks", []):
                if task.get("status") == "completed" and "deliverables" in task:
                    deliverables.extend(task["deliverables"])
            context["all_deliverables_list"] = deliverables

        elif item == "task_summaries":
            # Extract task summaries
            summaries = []
            for task in topic.get("topic", {}).get("tasks", []):
                summaries.append({
                    "task_id": task.get("id"),
                    "agent": task.get("agent"),
                    "status": task.get("status"),
                    "result": task.get("result", {})
                })
            context["task_summaries"] = summaries

        elif item == "acceptance_criteria_complete":
            # Extract all acceptance criteria from workflow
            criteria = []
            workflow = topic.get("topic", {}).get("workflow", {})
            for phase in workflow.get("phases", []):
                for step in phase.get("steps", []):
                    if "completion_criteria" in step:
                        criteria.extend(step["completion_criteria"])
            context["acceptance_criteria_complete"] = criteria

        elif item == "technical_constraints":
            # Extract technical constraints from spec (if available)
            spec_data = topic.get("topic", {}).get("spec_data", {})
            context["technical_constraints"] = spec_data.get("technical_constraints", [])

        elif item == "spec_file_path":
            # Get spec file path
            context["spec_file_path"] = topic.get("topic", {}).get("spec_file", "")

        elif item == "topicplan_path":
            # Get topicplan.md path
            topics_dir = Path(settings["paths"]["topics_directory"])
            topicplan_path = topics_dir / topic_slug / "topicplan.md"
            context["topicplan_path"] = str(topicplan_path)

        elif item == "all_deliverables_paths":
            # Get all deliverable file paths
            paths = []
            for task in topic.get("topic", {}).get("tasks", []):
                if "deliverables" in task:
                    for deliverable in task["deliverables"]:
                        if "path" in deliverable:
                            paths.append(deliverable["path"])
            context["all_deliverables_paths"] = paths

    return context


def find_step(settings: Dict[str, Any], step_id: str) -> Optional[Dict[str, Any]]:
    """
    Find step definition in settings.
    
    Args:
        settings: Settings dictionary
        step_id: Step identifier
        
    Returns:
        Step definition dict or None if not found
    """
    for phase in settings["workflow"]["phases"]:
        for step in phase["steps"]:
            if step["id"] == step_id:
                return step
    return None


def find_phase(settings: Dict[str, Any], phase_id: str) -> Optional[Dict[str, Any]]:
    """
    Find phase definition in settings.
    
    Args:
        settings: Settings dictionary
        phase_id: Phase identifier
        
    Returns:
        Phase definition dict or None if not found
    """
    for phase in settings["workflow"]["phases"]:
        if phase["id"] == phase_id:
            return phase
    return None


def is_step_complete(topic: Dict[str, Any], step_id: str) -> bool:
    """
    Check if step is complete in topic state.
    
    Args:
        topic: Topic state dictionary
        step_id: Step identifier
        
    Returns:
        True if step is completed, False otherwise
    """
    workflow = topic.get("topic", {}).get("workflow", {})
    for phase in workflow.get("phases", []):
        for step in phase.get("steps", []):
            if step["id"] == step_id:
                return step["status"] == "completed"
    return False


def is_phase_complete(topic: Dict[str, Any], phase_id: str) -> bool:
    """
    Check if phase is complete in topic state.

    Args:
        topic: Topic state dictionary
        phase_id: Phase identifier

    Returns:
        True if phase is completed, False otherwise
    """
    workflow = topic.get("topic", {}).get("workflow", {})
    for phase in workflow.get("phases", []):
        if phase["id"] == phase_id:
            return phase["status"] == "completed"
    return False


def validate_dependencies(topic_slug: str, step_id: str, settings: Optional[Dict[str, Any]] = None) -> Tuple[bool, str]:
    """
    Verify all dependencies are complete.

    Args:
        topic_slug: Topic slug identifier
        step_id: Step identifier to validate
        settings: Optional settings dict

    Returns:
        Tuple of (is_valid, message)
    """
    if settings is None:
        settings = load_settings()

    step = find_step(settings, step_id)
    if not step:
        return False, f"Step {step_id} not found in settings"

    topic = load_topic_state(topic_slug, settings)

    # Check step dependencies
    for dep_id in step.get("depends_on", []):
        if not is_step_complete(topic, dep_id):
            return False, f"Dependency {dep_id} not complete"

    # Check phase dependencies
    current_phase_id = None
    for phase in settings["workflow"]["phases"]:
        for s in phase["steps"]:
            if s["id"] == step_id:
                current_phase_id = phase["id"]
                break
        if current_phase_id:
            break

    if current_phase_id:
        current_phase = find_phase(settings, current_phase_id)
        for phase_dep_id in current_phase.get("depends_on", []):
            if not is_phase_complete(topic, phase_dep_id):
                return False, f"Phase dependency {phase_dep_id} not complete"

    return True, "All dependencies satisfied"


def evaluate_completion_criteria(step_id: str, result: Dict[str, Any], settings: Optional[Dict[str, Any]] = None) -> Tuple[bool, List[str]]:
    """
    Evaluate completion criteria for a step.

    Args:
        step_id: Step identifier
        result: Result context dictionary
        settings: Optional settings dict

    Returns:
        Tuple of (all_met, failed_criteria)
    """
    if settings is None:
        settings = load_settings()

    step = find_step(settings, step_id)
    if not step:
        return False, [f"Step {step_id} not found"]

    criteria = step.get("completion_criteria", [])
    if not criteria:
        return True, []  # No criteria = always pass

    evaluator = CriteriaEvaluator()
    failed = []

    for criterion in criteria:
        if not evaluator.evaluate(criterion, result):
            failed.append(criterion)

    return len(failed) == 0, failed


def get_workflow_status(topic_slug: str, settings: Optional[Dict[str, Any]] = None) -> None:
    """
    Get and display current workflow status for topic.

    Args:
        topic_slug: Topic slug identifier
        settings: Optional settings dict
    """
    if settings is None:
        settings = load_settings()

    topic = load_topic_state(topic_slug, settings)
    workflow = topic.get("topic", {}).get("workflow", {})

    print(f"\n{'='*80}")
    print(f"Workflow Status: {topic_slug}")
    print(f"{'='*80}\n")

    current_phase = workflow.get("current_phase")
    current_step = workflow.get("current_step")

    for phase in workflow.get("phases", []):
        phase_id = phase["id"]
        phase_status = phase["status"]

        # Status icon
        if phase_status == "completed":
            icon = "[DONE]"
        elif phase_status == "in_progress":
            icon = "[>>]"
        else:
            icon = "[ ]"

        # Calculate progress
        steps = phase.get("steps", [])
        completed_steps = sum(1 for s in steps if s["status"] == "completed")
        total_steps = len(steps)
        progress = (completed_steps / total_steps * 100) if total_steps > 0 else 0

        print(f"{icon} {phase['id']} - {phase_status.upper()} ({progress:.0f}% - {completed_steps}/{total_steps} steps)")

        # Show steps
        for step in steps:
            step_id = step["id"]
            step_status = step["status"]

            if step_status == "completed":
                step_icon = "  [OK]"
            elif step_status == "in_progress":
                step_icon = "  [>>]"
            else:
                step_icon = "  [ ]"

            # Highlight current step
            if step_id == current_step:
                print(f"{step_icon} {step_id} ({step_status}) <-- CURRENT")
            else:
                print(f"{step_icon} {step_id} ({step_status})")

    print(f"\n{'='*80}")
    print(f"Current Phase: {current_phase}")
    print(f"Current Step: {current_step}")
    print(f"{'='*80}\n")


def get_next_step(topic_slug: str, settings: Optional[Dict[str, Any]] = None) -> Optional[str]:
    """
    Find next pending step.

    Args:
        topic_slug: Topic slug identifier
        settings: Optional settings dict

    Returns:
        Next step ID or None if all complete
    """
    if settings is None:
        settings = load_settings()

    topic = load_topic_state(topic_slug, settings)
    workflow = topic.get("topic", {}).get("workflow", {})

    for phase in workflow.get("phases", []):
        if phase["status"] != "completed":
            for step in phase.get("steps", []):
                if step["status"] == "pending":
                    return step["id"]

    return None


def log_to_audit_trail(topic_slug: str, level: str, phase_id: str, step_id: str,
                       action: str, details: Dict[str, Any], duration_seconds: Optional[int] = None,
                       settings: Optional[Dict[str, Any]] = None) -> None:
    """
    Log to JSON audit trail with file locking.

    Args:
        topic_slug: Topic slug identifier
        level: Log level (info, warning, error)
        phase_id: Phase identifier
        step_id: Step identifier
        action: Action performed (started, completed, failed, etc.)
        details: Additional details dictionary
        duration_seconds: Optional duration in seconds
        settings: Optional settings dict
    """
    if settings is None:
        settings = load_settings()

    topic = load_topic_state(topic_slug, settings)

    workflow = topic.get("topic", {}).get("workflow", {})
    audit_log = workflow.get("audit_log", [])

    audit_log.append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": level,
        "phase_id": phase_id,
        "step_id": step_id,
        "action": action,
        "details": details,
        "duration_seconds": duration_seconds
    })

    workflow["audit_log"] = audit_log
    topic["topic"]["workflow"] = workflow

    save_topic_state(topic_slug, topic, settings)


def create_step_backup(topic_slug: str, step_id: str, settings: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Create backup of step state before execution (for rollback).

    Args:
        topic_slug: Topic slug identifier
        step_id: Step identifier
        settings: Optional settings dict

    Returns:
        Backup state dictionary
    """
    if settings is None:
        settings = load_settings()

    topic = load_topic_state(topic_slug, settings)
    workflow = topic.get("topic", {}).get("workflow", {})

    # Find step in workflow
    for phase in workflow.get("phases", []):
        for step in phase.get("steps", []):
            if step["id"] == step_id:
                return {
                    "step_id": step_id,
                    "phase_id": phase["id"],
                    "previous_state": step.copy(),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }

    return {}


def rollback_step(topic_slug: str, step_id: str, backup_state: Dict[str, Any],
                  settings: Optional[Dict[str, Any]] = None) -> None:
    """
    Rollback step to previous state on failure.

    Args:
        topic_slug: Topic slug identifier
        step_id: Step identifier
        backup_state: Backup state from create_step_backup()
        settings: Optional settings dict
    """
    if settings is None:
        settings = load_settings()

    if not backup_state:
        print(f"WARNING: No backup state for step {step_id}, cannot rollback", file=sys.stderr)
        return

    topic = load_topic_state(topic_slug, settings)
    workflow = topic.get("topic", {}).get("workflow", {})

    # Find and restore step
    for phase in workflow.get("phases", []):
        if phase["id"] == backup_state["phase_id"]:
            for i, step in enumerate(phase.get("steps", [])):
                if step["id"] == step_id:
                    phase["steps"][i] = backup_state["previous_state"]
                    break
            break

    topic["topic"]["workflow"] = workflow
    save_topic_state(topic_slug, topic, settings)

    # Log rollback
    log_to_audit_trail(
        topic_slug, "warning", backup_state["phase_id"], step_id,
        "rolled_back", {"reason": "step_failure", "backup_timestamp": backup_state["timestamp"]},
        settings=settings
    )


def is_step_idempotent(step_id: str, settings: Optional[Dict[str, Any]] = None) -> bool:
    """
    Check if step can be safely re-executed.

    Args:
        step_id: Step identifier
        settings: Optional settings dict

    Returns:
        True if step is idempotent (safe to re-run)
    """
    if settings is None:
        settings = load_settings()

    step = find_step(settings, step_id)
    if not step:
        return False

    # Check if step has idempotent flag
    if "idempotent" in step:
        return step["idempotent"]

    # Default: read-only operations are idempotent
    idempotent_patterns = [
        "parse", "extract", "analyze", "scan", "validate",
        "generate-summary", "generate-list", "generate-report"
    ]

    for pattern in idempotent_patterns:
        if pattern in step_id:
            return True

    # Write operations are not idempotent by default
    return False


def mark_step_started(topic_slug: str, step_id: str, settings: Optional[Dict[str, Any]] = None) -> None:
    """
    Mark step as started in topic state and emit events (Phase 2).

    Args:
        topic_slug: Topic slug identifier
        step_id: Step identifier
        settings: Optional settings dict
    """
    if settings is None:
        settings = load_settings()

    topic = load_topic_state(topic_slug, settings)
    workflow = topic.get("topic", {}).get("workflow", {})

    # Find and update step
    step_found = False
    phase_id = None

    for phase in workflow.get("phases", []):
        for step in phase.get("steps", []):
            if step["id"] == step_id:
                step["status"] = "in_progress"
                step["started_at"] = datetime.now(timezone.utc).isoformat()
                step_found = True
                phase_id = phase["id"]
                break
        if step_found:
            break

    if not step_found:
        raise ValueError(f"Step {step_id} not found in topic workflow")

    topic["topic"]["workflow"] = workflow
    save_topic_state(topic_slug, topic, settings)

    # Log step start
    log_to_audit_trail(
        topic_slug, "info", phase_id, step_id,
        "started", {}, settings=settings
    )

    # Phase 2: Emit event
    if HAS_EVENT_BUS:
        emit_step_started(topic_slug, phase_id, step_id)


def mark_step_failed(topic_slug: str, step_id: str, error: str, settings: Optional[Dict[str, Any]] = None) -> None:
    """
    Mark step as failed in topic state and emit events (Phase 2).

    Args:
        topic_slug: Topic slug identifier
        step_id: Step identifier
        error: Error message
        settings: Optional settings dict
    """
    if settings is None:
        settings = load_settings()

    topic = load_topic_state(topic_slug, settings)
    workflow = topic.get("topic", {}).get("workflow", {})

    # Find and update step
    step_found = False
    phase_id = None

    for phase in workflow.get("phases", []):
        for step in phase.get("steps", []):
            if step["id"] == step_id:
                step["status"] = "failed"
                step["completed_at"] = datetime.now(timezone.utc).isoformat()
                step["result"] = {"error": error}
                step_found = True
                phase_id = phase["id"]
                break
        if step_found:
            break

    if not step_found:
        raise ValueError(f"Step {step_id} not found in topic workflow")

    topic["topic"]["workflow"] = workflow
    save_topic_state(topic_slug, topic, settings)

    # Log failure
    log_to_audit_trail(
        topic_slug, "error", phase_id, step_id,
        "failed", {"error": error}, settings=settings
    )

    # Phase 2: Emit event
    if HAS_EVENT_BUS:
        emit_step_failed(topic_slug, phase_id, step_id, error)


def mark_step_complete(topic_slug: str, step_id: str, result: Dict[str, Any],
                       settings: Optional[Dict[str, Any]] = None) -> None:
    """
    Mark step as complete in topic state with validation, events, and performance tracking (Phase 2).

    Args:
        topic_slug: Topic slug identifier
        step_id: Step identifier
        result: Result dictionary from step execution
        settings: Optional settings dict

    Raises:
        ValueError: If completion criteria not met
    """
    # Phase 2: Start performance timing
    start_time = time.time()

    if settings is None:
        settings = load_settings()

    # Validate completion criteria
    all_met, failed = evaluate_completion_criteria(step_id, result, settings)
    if not all_met:
        raise ValueError(f"Completion criteria not met for {step_id}: {', '.join(failed)}")

    topic = load_topic_state(topic_slug, settings)
    workflow = topic.get("topic", {}).get("workflow", {})

    # Find and update step
    step_found = False
    phase_id = None

    for phase in workflow.get("phases", []):
        for step in phase.get("steps", []):
            if step["id"] == step_id:
                step["status"] = "completed"
                step["completed_at"] = datetime.now(timezone.utc).isoformat()
                step["result"] = result
                step_found = True
                phase_id = phase["id"]
                break
        if step_found:
            break

    if not step_found:
        raise ValueError(f"Step {step_id} not found in topic workflow")

    # Update current step to next pending
    next_step = get_next_step(topic_slug, settings)
    workflow["current_step"] = next_step

    # Check if phase is complete
    phase_complete = False
    phase = find_phase(settings, phase_id)
    if phase:
        all_steps_complete = all(
            s["status"] == "completed"
            for p in workflow.get("phases", [])
            if p["id"] == phase_id
            for s in p.get("steps", [])
        )

        if all_steps_complete:
            phase_complete = True
            for p in workflow.get("phases", []):
                if p["id"] == phase_id:
                    p["status"] = "completed"
                    p["completed_at"] = datetime.now(timezone.utc).isoformat()
                    break

            # Move to next phase
            next_phase_order = phase["order"] + 1
            for p in settings["workflow"]["phases"]:
                if p["order"] == next_phase_order:
                    workflow["current_phase"] = p["id"]
                    break

    topic["topic"]["workflow"] = workflow
    save_topic_state(topic_slug, topic, settings)

    # Log completion
    log_to_audit_trail(
        topic_slug, "info", phase_id, step_id,
        "completed", result, settings=settings
    )

    # Phase 2: Record performance metrics
    if HAS_PERFORMANCE:
        execution_time = time.time() - start_time
        perf_monitor = get_performance_monitor()
        perf_monitor.record_operation("mark_step_complete", execution_time)

    # Phase 2: Emit events
    if HAS_EVENT_BUS:
        emit_step_completed(topic_slug, phase_id, step_id, result)

        # Emit phase completed event if phase is done
        if phase_complete:
            emit_phase_completed(topic_slug, phase_id)


def get_audit_log(topic_slug: str, limit: Optional[int] = None,
                  settings: Optional[Dict[str, Any]] = None) -> None:
    """
    View audit log history.

    Args:
        topic_slug: Topic slug identifier
        limit: Optional limit to recent entries
        settings: Optional settings dict
    """
    if settings is None:
        settings = load_settings()

    topic = load_topic_state(topic_slug, settings)
    audit_log = topic.get("topic", {}).get("workflow", {}).get("audit_log", [])

    # Optionally limit to recent entries
    if limit:
        audit_log = audit_log[-limit:]

    print(f"\n{'='*80}")
    print(f"Audit Log: {topic_slug}")
    if limit:
        print(f"(Last {limit} entries)")
    print(f"{'='*80}\n")

    # Print formatted audit log
    for entry in audit_log:
        timestamp = entry.get("timestamp", "")
        level = entry.get("level", "info").upper()
        step_id = entry.get("step_id", "")
        action = entry.get("action", "").upper()
        details = entry.get("details", {})
        duration = entry.get("duration_seconds")

        details_str = " | ".join(f"{k}={v}" for k, v in details.items())
        duration_str = f" ({duration}s)" if duration else ""

        print(f"{timestamp} | {level:7} | {step_id:30} | {action:12}{duration_str}" +
              (f" | {details_str}" if details_str else ""))

    print(f"\n{'='*80}\n")


def initialize_topic_workflow(topic_slug: str, settings: Optional[Dict[str, Any]] = None) -> None:
    """
    Initialize workflow structure in topic.json with events and hooks (Phase 2).

    Args:
        topic_slug: Topic slug identifier
        settings: Optional settings dict
    """
    if settings is None:
        settings = load_settings()

    topic = load_topic_state(topic_slug, settings)

    # Initialize workflow structure
    workflow = {
        "current_phase": settings["workflow"]["phases"][0]["id"],
        "current_step": settings["workflow"]["phases"][0]["steps"][0]["id"],
        "phases": [],
        "audit_log": []
    }

    # Initialize phases and steps
    total_steps = 0
    for phase_def in settings["workflow"]["phases"]:
        phase = {
            "id": phase_def["id"],
            "status": "pending" if phase_def["order"] > 1 else "in_progress",
            "started_at": datetime.now(timezone.utc).isoformat() if phase_def["order"] == 1 else None,
            "completed_at": None,
            "steps": []
        }

        for step_def in phase_def["steps"]:
            step = {
                "id": step_def["id"],
                "status": "pending",
                "started_at": None,
                "completed_at": None,
                "result": None
            }
            phase["steps"].append(step)
            total_steps += 1

        workflow["phases"].append(phase)

    # Update topic
    if "topic" not in topic:
        topic["topic"] = {}

    topic["topic"]["workflow"] = workflow
    save_topic_state(topic_slug, topic, settings)

    print(f"OK Workflow initialized for topic: {topic_slug}")

    # Phase 2: Emit events
    if HAS_EVENT_BUS:
        emit_workflow_initialized(topic_slug)
        emit_workflow_started(topic_slug, total_steps)
        # Emit first phase started
        first_phase_id = settings["workflow"]["phases"][0]["id"]
        emit_phase_started(topic_slug, first_phase_id)

    # Phase 2: Initialize hooks if enabled
    if HAS_HOOKS and settings.get("advanced", {}).get("hooks", {}).get("enabled", False):
        # Hooks are initialized automatically by get_hooks_manager()
        _ = get_hooks_manager()


def main():
    """CLI interface for workflow manager."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Workflow Manager - Workflow orchestration and step management",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python workflow_manager.py get_workflow_status my-topic
  python workflow_manager.py start_step my-topic parse-spec
  python workflow_manager.py complete_step my-topic parse-spec '{"spec_valid": true}'
  python workflow_manager.py fail_step my-topic parse-spec "File not found"
  python workflow_manager.py get_audit_log my-topic --limit 20
  python workflow_manager.py get_mandatory_agents
  python workflow_manager.py build_handover_context my-topic documentation_generation
  python workflow_manager.py validate_agent_name aghero-testing-agent
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # get_workflow_status
    p = subparsers.add_parser('get_workflow_status', help='Get workflow status for topic')
    p.add_argument('topic_slug', help='Topic slug')

    # get_next_step
    p = subparsers.add_parser('get_next_step', help='Get next step to execute')
    p.add_argument('topic_slug', help='Topic slug')

    # validate_dependencies
    p = subparsers.add_parser('validate_dependencies', help='Validate step dependencies')
    p.add_argument('topic_slug', help='Topic slug')
    p.add_argument('step_id', help='Step ID')

    # start_step
    p = subparsers.add_parser('start_step', help='Mark step as started')
    p.add_argument('topic_slug', help='Topic slug')
    p.add_argument('step_id', help='Step ID')

    # complete_step
    p = subparsers.add_parser('complete_step', help='Mark step as complete')
    p.add_argument('topic_slug', help='Topic slug')
    p.add_argument('step_id', help='Step ID')
    p.add_argument('result_json', help='Result as JSON string')

    # fail_step
    p = subparsers.add_parser('fail_step', help='Mark step as failed')
    p.add_argument('topic_slug', help='Topic slug')
    p.add_argument('step_id', help='Step ID')
    p.add_argument('error_message', help='Error message')

    # get_audit_log
    p = subparsers.add_parser('get_audit_log', help='Get audit log entries')
    p.add_argument('topic_slug', help='Topic slug')
    p.add_argument('--limit', type=int, default=None, help='Maximum number of entries')

    # initialize_workflow
    p = subparsers.add_parser('initialize_workflow', help='Initialize workflow for topic')
    p.add_argument('topic_slug', help='Topic slug')

    # validate_settings
    p = subparsers.add_parser('validate_settings', help='Validate settings file')
    p.add_argument('--settings-path', default='.claude/agents/agenthero-ai/settings.json',
                   help='Path to settings.json (default: .claude/agents/agenthero-ai/settings.json)')

    # get_mandatory_agents
    subparsers.add_parser('get_mandatory_agents', help='Get mandatory agents from settings')

    # build_handover_context
    p = subparsers.add_parser('build_handover_context', help='Build handover context for mandatory agent')
    p.add_argument('topic_slug', help='Topic slug')
    p.add_argument('feature', help='Feature name (e.g., documentation_generation, qa_validation)')

    # validate_agent_name
    p = subparsers.add_parser('validate_agent_name', help='Validate agent name follows aghero- convention')
    p.add_argument('agent_name', help='Agent name to validate')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        if args.command == "get_workflow_status":
            get_workflow_status(args.topic_slug)

        elif args.command == "get_next_step":
            next_step = get_next_step(args.topic_slug)
            if next_step:
                print(f"Next step: {next_step}")
            else:
                print("All steps completed!")

        elif args.command == "validate_dependencies":
            valid, message = validate_dependencies(args.topic_slug, args.step_id)
            print(message)
            sys.exit(0 if valid else 1)

        elif args.command == "start_step":
            mark_step_started(args.topic_slug, args.step_id)
            print(f"OK Step {args.step_id} marked as started")

        elif args.command == "complete_step":
            result = json.loads(args.result_json)
            mark_step_complete(args.topic_slug, args.step_id, result)
            print(f"OK Step {args.step_id} marked complete")

        elif args.command == "fail_step":
            mark_step_failed(args.topic_slug, args.step_id, args.error_message)
            print(f"FAIL Step {args.step_id} marked as failed")

        elif args.command == "get_audit_log":
            get_audit_log(args.topic_slug, args.limit)

        elif args.command == "initialize_workflow":
            initialize_topic_workflow(args.topic_slug)

        elif args.command == "validate_settings":
            try:
                settings = load_settings(args.settings_path)
                print(f"OK Settings file is valid: {args.settings_path}")
                print(f"  Version: {settings['version']}")
                print(f"  Schema Version: {settings['schema_version']}")
                print(f"  Phases: {len(settings['workflow']['phases'])}")
                total_steps = sum(len(p['steps']) for p in settings['workflow']['phases'])
                print(f"  Total Steps: {total_steps}")
            except Exception as e:
                print(f"FAIL Settings validation failed: {e}", file=sys.stderr)
                sys.exit(1)

        elif args.command == "get_mandatory_agents":
            settings = load_settings()
            mandatory = get_mandatory_agents(settings)
            print(json.dumps(mandatory, indent=2))

        elif args.command == "build_handover_context":
            settings = load_settings()

            if args.feature not in settings.get("features", {}):
                print(f"ERROR: Unknown feature: {args.feature}", file=sys.stderr)
                print(f"  Available features: {list(settings.get('features', {}).keys())}", file=sys.stderr)
                sys.exit(1)

            context_spec = settings["features"][args.feature].get("handover_context", {})
            if not context_spec:
                print(f"ERROR: Feature '{args.feature}' has no handover_context configuration", file=sys.stderr)
                sys.exit(1)

            context = build_handover_context(args.topic_slug, context_spec, settings)
            print(json.dumps(context, indent=2))

        elif args.command == "validate_agent_name":
            settings = load_settings()
            is_valid, message = validate_agent_name(args.agent_name, settings)
            print(message)
            sys.exit(0 if is_valid else 1)

    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

