#!/usr/bin/env python3
"""
End-to-End Test for Workflow Manager with Real Topic Files
Tests the complete workflow with actual file system operations.
"""

import json
import sys
import os
import shutil
from pathlib import Path
from datetime import datetime, timezone

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from workflow_manager import (
    load_settings,
    initialize_topic_workflow,
    mark_step_started,
    mark_step_complete,
    mark_step_failed,
    get_next_step,
    validate_dependencies,
    load_topic_state
)


def create_test_spec_file(test_dir: Path) -> Path:
    """Create a test specification file."""
    spec_dir = test_dir / "spec"
    spec_dir.mkdir(parents=True, exist_ok=True)
    
    spec_file = spec_dir / "test-spec.md"
    spec_content = """# Test Project Specification

## Project Overview
This is a test project for E2E workflow testing.

## Requirements
1. Parse specification file
2. Extract requirements
3. Validate structure

## Deliverables
1. Parsed spec data
2. Requirements list
3. Validation report

## Acceptance Criteria
1. All requirements extracted
2. Spec format validated
3. No errors in parsing
"""
    
    spec_file.write_text(spec_content, encoding='utf-8')
    return spec_file


def create_test_topic_state(test_dir: Path, topic_slug: str) -> Path:
    """Create a test topic state file."""
    topics_dir = test_dir / ".claude" / "agents" / "state" / "agenthero-ai" / "topics" / topic_slug
    topics_dir.mkdir(parents=True, exist_ok=True)
    
    topic_file = topics_dir / "topic.json"
    topic_data = {
        "topic": {
            "id": topic_slug,
            "title": "Test Topic",
            "description": "E2E test topic",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "active"
        }
    }
    
    with open(topic_file, 'w', encoding='utf-8') as f:
        json.dump(topic_data, f, indent=2)
    
    return topic_file


def test_real_topic_workflow():
    """Test with real topic file, not mocks."""
    
    print("=" * 80)
    print("E2E Test: Real Topic Workflow")
    print("=" * 80)
    
    # Setup test directory
    test_dir = Path(__file__).parent.parent.parent.parent / "test-e2e-temp"
    topic_slug = "test-e2e-topic"
    
    try:
        # Clean up any previous test
        if test_dir.exists():
            shutil.rmtree(test_dir)
        
        print("\n1. Creating test environment...")
        
        # Create test spec file
        spec_file = create_test_spec_file(test_dir)
        print(f"   OK Created spec file: {spec_file}")
        
        # Create test topic state
        topic_file = create_test_topic_state(test_dir, topic_slug)
        print(f"   OK Created topic file: {topic_file}")
        
        # Copy settings file to test directory
        # Get repository root (scripts -> agenthero-ai -> skills -> .claude -> root)
        repo_root = Path(__file__).parent.parent.parent.parent.parent
        settings_src = repo_root / ".claude" / "agents" / "agenthero-ai" / "settings.json"
        settings_dest = test_dir / ".claude" / "agents" / "agenthero-ai" / "settings.json"
        settings_dest.parent.mkdir(parents=True, exist_ok=True)

        if settings_src.exists():
            shutil.copy(settings_src, settings_dest)
            print(f"   OK Copied settings file from {settings_src}")
        else:
            print(f"   WARNING: Settings file not found at {settings_src}")
            print(f"   Skipping settings copy")
        
        # Update settings paths to point to test directory
        if settings_dest.exists():
            with open(settings_dest, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            
            settings["paths"]["state_directory"] = str(test_dir / ".claude/agents/state/agenthero-ai/")
            settings["paths"]["topics_directory"] = str(test_dir / ".claude/agents/state/agenthero-ai/topics/")
            settings["paths"]["project_tasks_directory"] = str(test_dir / "Project-tasks/")
            
            with open(settings_dest, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2)
            
            print(f"   OK Updated settings paths")
        
        print("\n2. Initializing workflow...")
        
        # Initialize workflow
        os.chdir(test_dir)
        initialize_topic_workflow(topic_slug, settings=settings if settings_dest.exists() else None)
        print(f"   OK Workflow initialized")
        
        # Verify state file created correctly
        topic = load_topic_state(topic_slug, settings=settings if settings_dest.exists() else None)
        assert "workflow" in topic["topic"], "Workflow not found in topic state"
        assert len(topic["topic"]["workflow"]["phases"]) > 0, "No phases in workflow"
        print(f"   OK Workflow structure verified ({len(topic['topic']['workflow']['phases'])} phases)")
        
        print("\n3. Executing Phase 1 steps...")
        
        # Get first step
        first_step = get_next_step(topic_slug, settings=settings if settings_dest.exists() else None)
        print(f"   OK Next step: {first_step}")
        
        # Mark step as started
        mark_step_started(topic_slug, first_step, settings=settings if settings_dest.exists() else None)
        print(f"   OK Step {first_step} started")
        
        # Verify step status
        topic = load_topic_state(topic_slug, settings=settings if settings_dest.exists() else None)
        step_status = None
        for phase in topic["topic"]["workflow"]["phases"]:
            for step in phase["steps"]:
                if step["id"] == first_step:
                    step_status = step["status"]
                    break
        
        assert step_status == "in_progress", f"Step status should be 'in_progress', got '{step_status}'"
        print(f"   OK Step status verified: {step_status}")
        
        # Mark step as complete
        result = {"spec_valid": True, "spec_file": str(spec_file)}
        mark_step_complete(topic_slug, first_step, result, settings=settings if settings_dest.exists() else None)
        print(f"   OK Step {first_step} completed")
        
        # Verify completion
        topic = load_topic_state(topic_slug, settings=settings if settings_dest.exists() else None)
        step_status = None
        for phase in topic["topic"]["workflow"]["phases"]:
            for step in phase["steps"]:
                if step["id"] == first_step:
                    step_status = step["status"]
                    break
        
        assert step_status == "completed", f"Step status should be 'completed', got '{step_status}'"
        print(f"   OK Step completion verified")
        
        print("\n4. Verifying audit log...")
        
        # Check audit log
        audit_log = topic["topic"]["workflow"]["audit_log"]
        assert len(audit_log) >= 2, f"Expected at least 2 audit entries, got {len(audit_log)}"
        print(f"   OK Audit log has {len(audit_log)} entries")
        
        # Verify audit log entries
        started_entry = next((e for e in audit_log if e["action"] == "started"), None)
        completed_entry = next((e for e in audit_log if e["action"] == "completed"), None)
        
        assert started_entry is not None, "No 'started' entry in audit log"
        assert completed_entry is not None, "No 'completed' entry in audit log"
        print(f"   OK Audit log entries verified (started, completed)")
        
        print("\n5. Testing step failure...")
        
        # Get next step
        next_step = get_next_step(topic_slug, settings=settings if settings_dest.exists() else None)
        if next_step:
            mark_step_started(topic_slug, next_step, settings=settings if settings_dest.exists() else None)
            mark_step_failed(topic_slug, next_step, "Test failure", settings=settings if settings_dest.exists() else None)
            print(f"   OK Step {next_step} marked as failed")
            
            # Verify failure
            topic = load_topic_state(topic_slug, settings=settings if settings_dest.exists() else None)
            step_status = None
            for phase in topic["topic"]["workflow"]["phases"]:
                for step in phase["steps"]:
                    if step["id"] == next_step:
                        step_status = step["status"]
                        break
            
            assert step_status == "failed", f"Step status should be 'failed', got '{step_status}'"
            print(f"   OK Step failure verified")
        
        print("\n" + "=" * 80)
        print("OK All E2E tests passed!")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print(f"\nFAIL Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Cleanup
        os.chdir(Path(__file__).parent)
        if test_dir.exists():
            try:
                shutil.rmtree(test_dir)
                print(f"\nOK Cleaned up test directory: {test_dir}")
            except Exception as e:
                print(f"\nWARNING: Could not clean up test directory: {e}")


if __name__ == "__main__":
    success = test_real_topic_workflow()
    sys.exit(0 if success else 1)

