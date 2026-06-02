#!/usr/bin/env python3
"""
Dry-Run Mode for agenthero-ai workflow.
Test workflows without making changes. Preview and validate before execution.

Phase 2 - Advanced Features
"""

import json
import sys
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from pathlib import Path
import threading
from copy import deepcopy


class DryRunContext:
    """
    Context for dry-run execution.
    Tracks simulated changes without applying them.
    """
    
    def __init__(self):
        """Initialize dry-run context."""
        self.enabled = False
        self.lock = threading.Lock()
        
        # Simulated changes
        self.file_writes: List[Dict[str, Any]] = []
        self.file_reads: List[Dict[str, Any]] = []
        self.state_changes: List[Dict[str, Any]] = []
        self.events_emitted: List[Dict[str, Any]] = []
        
        # Validation results
        self.validation_errors: List[str] = []
        self.validation_warnings: List[str] = []
        
        # Execution plan
        self.execution_plan: List[Dict[str, Any]] = []
    
    def record_file_write(self, file_path: str, content: Any, operation: str = "write"):
        """
        Record a file write operation.
        
        Args:
            file_path: Path to file
            content: Content to write
            operation: Operation type (write, append, delete)
        """
        with self.lock:
            self.file_writes.append({
                "timestamp": datetime.now().isoformat(),
                "file_path": file_path,
                "operation": operation,
                "content_preview": str(content)[:200] if content else None,
                "content_size": len(str(content)) if content else 0
            })
    
    def record_file_read(self, file_path: str, exists: bool):
        """
        Record a file read operation.
        
        Args:
            file_path: Path to file
            exists: Whether file exists
        """
        with self.lock:
            self.file_reads.append({
                "timestamp": datetime.now().isoformat(),
                "file_path": file_path,
                "exists": exists
            })
    
    def record_state_change(self, entity: str, entity_id: str, 
                           old_state: Any, new_state: Any):
        """
        Record a state change.
        
        Args:
            entity: Entity type (topic, step, phase)
            entity_id: Entity identifier
            old_state: Previous state
            new_state: New state
        """
        with self.lock:
            self.state_changes.append({
                "timestamp": datetime.now().isoformat(),
                "entity": entity,
                "entity_id": entity_id,
                "old_state": old_state,
                "new_state": new_state
            })
    
    def record_event(self, event_type: str, event_data: Dict[str, Any]):
        """
        Record an event emission.
        
        Args:
            event_type: Type of event
            event_data: Event data
        """
        with self.lock:
            self.events_emitted.append({
                "timestamp": datetime.now().isoformat(),
                "event_type": event_type,
                "event_data": event_data
            })
    
    def add_validation_error(self, error: str):
        """Add a validation error."""
        with self.lock:
            self.validation_errors.append(error)
    
    def add_validation_warning(self, warning: str):
        """Add a validation warning."""
        with self.lock:
            self.validation_warnings.append(warning)
    
    def add_execution_step(self, step_id: str, step_name: str, 
                          dependencies: List[str], estimated_duration: float = 0):
        """
        Add a step to the execution plan.
        
        Args:
            step_id: Step identifier
            step_name: Step name
            dependencies: List of dependency step IDs
            estimated_duration: Estimated duration in seconds
        """
        with self.lock:
            self.execution_plan.append({
                "step_id": step_id,
                "step_name": step_name,
                "dependencies": dependencies,
                "estimated_duration": estimated_duration
            })
    
    def get_summary(self) -> Dict[str, Any]:
        """Get dry-run summary."""
        with self.lock:
            return {
                "enabled": self.enabled,
                "file_writes": len(self.file_writes),
                "file_reads": len(self.file_reads),
                "state_changes": len(self.state_changes),
                "events_emitted": len(self.events_emitted),
                "validation_errors": len(self.validation_errors),
                "validation_warnings": len(self.validation_warnings),
                "execution_steps": len(self.execution_plan),
                "is_valid": len(self.validation_errors) == 0
            }
    
    def get_detailed_report(self) -> Dict[str, Any]:
        """Get detailed dry-run report."""
        with self.lock:
            return {
                "summary": self.get_summary(),
                "file_writes": self.file_writes,
                "file_reads": self.file_reads,
                "state_changes": self.state_changes,
                "events_emitted": self.events_emitted,
                "validation_errors": self.validation_errors,
                "validation_warnings": self.validation_warnings,
                "execution_plan": self.execution_plan
            }
    
    def reset(self):
        """Reset dry-run context."""
        with self.lock:
            self.file_writes.clear()
            self.file_reads.clear()
            self.state_changes.clear()
            self.events_emitted.clear()
            self.validation_errors.clear()
            self.validation_warnings.clear()
            self.execution_plan.clear()
    
    def enable(self):
        """Enable dry-run mode."""
        self.enabled = True
    
    def disable(self):
        """Disable dry-run mode."""
        self.enabled = False


class DryRunValidator:
    """
    Validates workflow before execution.
    Checks for common issues and provides recommendations.
    """
    
    def __init__(self, context: DryRunContext):
        """
        Initialize validator.
        
        Args:
            context: Dry-run context
        """
        self.context = context
    
    def validate_workflow(self, workflow_data: Dict[str, Any]) -> bool:
        """
        Validate workflow configuration.
        
        Args:
            workflow_data: Workflow data to validate
            
        Returns:
            True if valid, False otherwise
        """
        is_valid = True
        
        # Check required fields
        if "phases" not in workflow_data:
            self.context.add_validation_error("Missing 'phases' in workflow")
            is_valid = False
        
        # Validate phases
        if "phases" in workflow_data:
            for phase in workflow_data["phases"]:
                if not self._validate_phase(phase):
                    is_valid = False
        
        return is_valid
    
    def _validate_phase(self, phase: Dict[str, Any]) -> bool:
        """Validate a single phase."""
        is_valid = True
        
        phase_id = phase.get("id", "unknown")
        
        # Check required fields
        if "id" not in phase:
            self.context.add_validation_error(f"Phase missing 'id'")
            is_valid = False
        
        if "steps" not in phase:
            self.context.add_validation_error(f"Phase '{phase_id}' missing 'steps'")
            is_valid = False
        
        # Validate steps
        if "steps" in phase:
            for step in phase["steps"]:
                if not self._validate_step(step, phase_id):
                    is_valid = False
        
        return is_valid
    
    def _validate_step(self, step: Dict[str, Any], phase_id: str) -> bool:
        """Validate a single step."""
        is_valid = True
        
        step_id = step.get("id", "unknown")
        
        # Check required fields
        if "id" not in step:
            self.context.add_validation_error(f"Step in phase '{phase_id}' missing 'id'")
            is_valid = False
        
        # Check completion criteria
        if "completion_criteria" in step:
            criteria = step["completion_criteria"]
            if not isinstance(criteria, (str, dict)):
                self.context.add_validation_error(
                    f"Step '{step_id}' has invalid completion_criteria type"
                )
                is_valid = False
        else:
            self.context.add_validation_warning(
                f"Step '{step_id}' has no completion_criteria"
            )
        
        # Check dependencies
        if "depends_on" in step:
            deps = step["depends_on"]
            if not isinstance(deps, list):
                self.context.add_validation_error(
                    f"Step '{step_id}' has invalid depends_on type (must be list)"
                )
                is_valid = False
        
        return is_valid


# Global singleton instance
_dry_run_context: Optional[DryRunContext] = None


def get_dry_run_context() -> DryRunContext:
    """
    Get global dry-run context (singleton).
    
    Returns:
        DryRunContext instance
    """
    global _dry_run_context
    if _dry_run_context is None:
        _dry_run_context = DryRunContext()
    return _dry_run_context


def is_dry_run() -> bool:
    """Check if dry-run mode is enabled."""
    context = get_dry_run_context()
    return context.enabled


def enable_dry_run():
    """Enable dry-run mode."""
    context = get_dry_run_context()
    context.enable()
    context.reset()


def disable_dry_run():
    """Disable dry-run mode."""
    context = get_dry_run_context()
    context.disable()


if __name__ == "__main__":
    # Test dry-run mode
    print("Testing Dry-Run Mode...")
    print("="*80)
    
    # Enable dry-run
    context = get_dry_run_context()
    context.enable()
    
    print("\n1. Recording Operations")
    context.record_file_write("/path/to/topic.json", {"data": "test"}, "write")
    context.record_file_read("/path/to/spec.md", True)
    context.record_state_change("step", "parse-spec", "pending", "completed")
    context.record_event("step_completed", {"step_id": "parse-spec"})
    
    print(f"  ✓ Recorded 1 file write")
    print(f"  ✓ Recorded 1 file read")
    print(f"  ✓ Recorded 1 state change")
    print(f"  ✓ Recorded 1 event")
    
    # Test validation
    print("\n2. Workflow Validation")
    validator = DryRunValidator(context)
    
    # Valid workflow
    valid_workflow = {
        "phases": [
            {
                "id": "phase-1",
                "steps": [
                    {
                        "id": "step-1",
                        "completion_criteria": "spec_valid"
                    }
                ]
            }
        ]
    }
    
    result = validator.validate_workflow(valid_workflow)
    print(f"  Valid workflow: {result}")
    
    # Invalid workflow
    invalid_workflow = {
        "phases": [
            {
                "steps": [  # Missing 'id'
                    {
                        "completion_criteria": 123  # Invalid type
                    }
                ]
            }
        ]
    }
    
    result = validator.validate_workflow(invalid_workflow)
    print(f"  Invalid workflow: {result}")
    
    # Get summary
    print("\n3. Dry-Run Summary")
    summary = context.get_summary()
    print(json.dumps(summary, indent=2))
    
    # Get detailed report
    print("\n4. Detailed Report")
    report = context.get_detailed_report()
    print(f"  Validation Errors: {report['validation_errors']}")
    print(f"  Validation Warnings: {report['validation_warnings']}")
    print(f"  File Operations: {len(report['file_writes'])} writes, {len(report['file_reads'])} reads")
    
    print("\n" + "="*80)
    print("Dry-Run Test Complete!")

