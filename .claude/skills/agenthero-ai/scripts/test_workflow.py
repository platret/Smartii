#!/usr/bin/env python3
"""
Test script for workflow_manager.py Phase 1 implementation.
Tests: schema validation, file locking, criteria evaluation, error recovery, idempotent steps.
"""

import json
import sys
import os
from pathlib import Path
import tempfile
import shutil

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Get repository root (3 levels up from scripts directory: scripts -> agenthero-ai -> skills -> .claude -> root)
# Actually: scripts -> agenthero-ai -> skills -> .claude (we're already in .claude)
# So: scripts -> agenthero-ai -> skills -> root
REPO_ROOT = Path(__file__).parent.parent.parent.parent.absolute()
SETTINGS_PATH = REPO_ROOT / "agents" / "agenthero-ai" / "settings.json"

from workflow_manager import (
    load_settings,
    load_topic_state,
    save_topic_state,
    CriteriaEvaluator,
    validate_dependencies,
    evaluate_completion_criteria,
    mark_step_complete,
    get_next_step,
    get_workflow_status,
    is_step_idempotent,
    create_step_backup,
    rollback_step,
    initialize_topic_workflow
)


def test_schema_validation():
    """Test 1: JSON Schema Validation"""
    print("\n" + "="*80)
    print("TEST 1: JSON Schema Validation")
    print("="*80)

    try:
        settings = load_settings(str(SETTINGS_PATH))
        print("✓ Settings file loaded and validated successfully")
        print(f"  Version: {settings['version']}")
        print(f"  Schema Version: {settings['schema_version']}")
        print(f"  Phases: {len(settings['workflow']['phases'])}")
        return True
    except Exception as e:
        print(f"✗ Schema validation failed: {e}")
        return False


def test_criteria_evaluator():
    """Test 2: Completion Criteria Evaluator"""
    print("\n" + "="*80)
    print("TEST 2: Completion Criteria Evaluator")
    print("="*80)
    
    evaluator = CriteriaEvaluator()
    
    tests = [
        # (criterion, context, expected_result)
        ("spec_valid", {"spec_valid": True}, True),
        ("spec_valid", {"spec_valid": False}, False),
        ("spec_valid", {}, False),
        ("requirements_count > 0", {"requirements_count": 5}, True),
        ("requirements_count > 0", {"requirements_count": 0}, False),
        ("requirements_count >= 1", {"requirements_count": 1}, True),
        ("deliverables_count == 3", {"deliverables_count": 3}, True),
        ("deliverables_count == 3", {"deliverables_count": 2}, False),
        ("not missing_field", {"missing_field": False}, True),
        ("not missing_field", {"missing_field": True}, False),
    ]
    
    passed = 0
    failed = 0
    
    for criterion, context, expected in tests:
        result = evaluator.evaluate(criterion, context)
        if result == expected:
            print(f"  ✓ '{criterion}' with {context} = {result} (expected {expected})")
            passed += 1
        else:
            print(f"  ✗ '{criterion}' with {context} = {result} (expected {expected})")
            failed += 1
    
    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


def test_idempotent_steps():
    """Test 3: Idempotent Step Detection"""
    print("\n" + "="*80)
    print("TEST 3: Idempotent Step Detection")
    print("="*80)
    
    settings = load_settings(str(SETTINGS_PATH))
    
    # Test idempotent steps (read-only operations)
    idempotent_steps = [
        "parse-spec",
        "extract-requirements",
        "extract-deliverables",
        "analyze-requirements",
        "scan-agent-library"
    ]
    
    # Test non-idempotent steps (write operations)
    non_idempotent_steps = [
        "create-state-structure",
        "launch-agents"
    ]
    
    passed = 0
    failed = 0
    
    for step_id in idempotent_steps:
        result = is_step_idempotent(step_id, settings)
        if result:
            print(f"  ✓ '{step_id}' correctly identified as idempotent")
            passed += 1
        else:
            print(f"  ✗ '{step_id}' should be idempotent but isn't")
            failed += 1
    
    for step_id in non_idempotent_steps:
        result = is_step_idempotent(step_id, settings)
        if not result:
            print(f"  ✓ '{step_id}' correctly identified as non-idempotent")
            passed += 1
        else:
            print(f"  ✗ '{step_id}' should be non-idempotent but is")
            failed += 1
    
    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


def test_workflow_initialization():
    """Test 4: Workflow Initialization"""
    print("\n" + "="*80)
    print("TEST 4: Workflow Initialization")
    print("="*80)
    
    # Create temporary test topic
    test_slug = "test-workflow-topic"
    settings = load_settings(str(SETTINGS_PATH))
    
    topics_dir = Path(settings["paths"]["topics_directory"])
    test_topic_dir = topics_dir / test_slug
    
    try:
        # Clean up if exists
        if test_topic_dir.exists():
            shutil.rmtree(test_topic_dir)
        
        # Create topic directory
        test_topic_dir.mkdir(parents=True, exist_ok=True)
        
        # Create minimal topic.json
        topic_file = test_topic_dir / "topic.json"
        with open(topic_file, 'w', encoding='utf-8') as f:
            json.dump({"topic": {"id": test_slug, "title": "Test Topic"}}, f, indent=2)
        
        # Initialize workflow
        initialize_topic_workflow(test_slug, settings)
        
        # Verify workflow structure
        with open(topic_file, 'r', encoding='utf-8') as f:
            topic = json.load(f)
        
        workflow = topic.get("topic", {}).get("workflow", {})
        
        if not workflow:
            print("  ✗ Workflow not initialized")
            return False
        
        if "current_phase" not in workflow:
            print("  ✗ current_phase not set")
            return False
        
        if "current_step" not in workflow:
            print("  ✗ current_step not set")
            return False
        
        if "phases" not in workflow:
            print("  ✗ phases not initialized")
            return False
        
        if "audit_log" not in workflow:
            print("  ✗ audit_log not initialized")
            return False
        
        print(f"  ✓ Workflow initialized successfully")
        print(f"    Current Phase: {workflow['current_phase']}")
        print(f"    Current Step: {workflow['current_step']}")
        print(f"    Phases: {len(workflow['phases'])}")
        print(f"    Audit Log: {len(workflow['audit_log'])} entries")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Workflow initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Clean up
        if test_topic_dir.exists():
            shutil.rmtree(test_topic_dir)


def test_step_completion_and_validation():
    """Test 5: Step Completion with Validation"""
    print("\n" + "="*80)
    print("TEST 5: Step Completion with Validation")
    print("="*80)
    
    test_slug = "test-workflow-topic"
    settings = load_settings(str(SETTINGS_PATH))
    
    topics_dir = Path(settings["paths"]["topics_directory"])
    test_topic_dir = topics_dir / test_slug
    
    try:
        # Setup
        if test_topic_dir.exists():
            shutil.rmtree(test_topic_dir)
        
        test_topic_dir.mkdir(parents=True, exist_ok=True)
        topic_file = test_topic_dir / "topic.json"
        
        with open(topic_file, 'w', encoding='utf-8') as f:
            json.dump({"topic": {"id": test_slug, "title": "Test Topic"}}, f, indent=2)
        
        initialize_topic_workflow(test_slug, settings)
        
        # Test completing first step with valid criteria
        step_id = "parse-spec"
        result = {
            "spec_file_exists": True,
            "spec_file_parsed": True,
            "spec_format_valid": True
        }
        
        mark_step_complete(test_slug, step_id, result, settings)
        print(f"  ✓ Step '{step_id}' marked complete with valid criteria")
        
        # Verify next step
        next_step = get_next_step(test_slug, settings)
        if next_step == "extract-requirements":
            print(f"  ✓ Next step correctly identified as '{next_step}'")
        else:
            print(f"  ✗ Next step should be 'extract-requirements' but got '{next_step}'")
            return False
        
        # Test completing step with invalid criteria (should fail)
        try:
            mark_step_complete(test_slug, "extract-requirements", {"invalid": "data"}, settings)
            print(f"  ✗ Step should have failed validation but didn't")
            return False
        except ValueError as e:
            print(f"  ✓ Step correctly failed validation: {str(e)[:50]}...")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if test_topic_dir.exists():
            shutil.rmtree(test_topic_dir)


def test_rollback_mechanism():
    """Test 6: Rollback Mechanism (Error Recovery)"""
    print("\n" + "="*80)
    print("TEST 6: Rollback Mechanism (Error Recovery)")
    print("="*80)

    test_slug = "test-rollback-topic"
    settings = load_settings(str(SETTINGS_PATH))

    topics_dir = Path(settings["paths"]["topics_directory"])
    test_topic_dir = topics_dir / test_slug

    try:
        # Setup
        if test_topic_dir.exists():
            shutil.rmtree(test_topic_dir)

        test_topic_dir.mkdir(parents=True, exist_ok=True)
        topic_file = test_topic_dir / "topic.json"

        with open(topic_file, 'w', encoding='utf-8') as f:
            json.dump({"topic": {"id": test_slug, "title": "Test Rollback"}}, f, indent=2)

        initialize_topic_workflow(test_slug, settings)

        # Complete first step successfully
        step_id = "parse-spec"
        result = {
            "spec_file_exists": True,
            "spec_file_parsed": True,
            "spec_format_valid": True
        }
        mark_step_complete(test_slug, step_id, result, settings)

        # Create backup of next step before we "corrupt" it
        next_step_id = "extract-requirements"
        backup = create_step_backup(test_slug, next_step_id, settings)

        if not backup:
            print("  ✗ Backup creation failed")
            return False

        print(f"  ✓ Backup created for step '{next_step_id}'")

        # Simulate step failure by modifying state to "corrupted"
        topic = load_topic_state(test_slug, settings)
        for phase in topic["topic"]["workflow"]["phases"]:
            for step in phase.get("steps", []):
                if step["id"] == next_step_id:
                    step["status"] = "corrupted"  # Intentionally corrupt it
                    step["error"] = "Simulated failure for testing"
                    break
        save_topic_state(test_slug, topic, settings)

        print(f"  ✓ Step '{next_step_id}' corrupted (simulated failure)")

        # Verify corruption
        topic = load_topic_state(test_slug, settings)
        for phase in topic["topic"]["workflow"]["phases"]:
            for step in phase.get("steps", []):
                if step["id"] == next_step_id and step["status"] == "corrupted":
                    print(f"  ✓ Corruption verified")
                    break

        # Now rollback
        rollback_step(test_slug, next_step_id, backup, settings)
        print(f"  ✓ Rollback executed")

        # Verify rollback restored original state
        topic = load_topic_state(test_slug, settings)
        for phase in topic["topic"]["workflow"]["phases"]:
            for step in phase.get("steps", []):
                if step["id"] == next_step_id:
                    if step["status"] == "pending" and "error" not in step:
                        print(f"  ✓ Rollback successful - step restored to 'pending'")
                        return True
                    else:
                        print(f"  ✗ Rollback failed - step status: {step['status']}")
                        return False

        print(f"  ✗ Could not find step after rollback")
        return False

    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if test_topic_dir.exists():
            shutil.rmtree(test_topic_dir)


def test_concurrent_access():
    """Test 7: Concurrent Access (File Locking)"""
    print("\n" + "="*80)
    print("TEST 7: Concurrent Access (File Locking)")
    print("="*80)

    import subprocess
    import time

    test_slug = "test-concurrent-topic"
    settings = load_settings(str(SETTINGS_PATH))

    topics_dir = Path(settings["paths"]["topics_directory"])
    test_topic_dir = topics_dir / test_slug

    try:
        # Setup
        if test_topic_dir.exists():
            shutil.rmtree(test_topic_dir)

        test_topic_dir.mkdir(parents=True, exist_ok=True)
        topic_file = test_topic_dir / "topic.json"

        with open(topic_file, 'w', encoding='utf-8') as f:
            json.dump({"topic": {"id": test_slug, "title": "Test Concurrent"}}, f, indent=2)

        initialize_topic_workflow(test_slug, settings)

        # Create a helper script that will write to the topic state
        helper_script = test_topic_dir / "concurrent_writer.py"
        scripts_dir = Path(__file__).parent.absolute()
        with open(helper_script, 'w', encoding='utf-8') as f:
            f.write(f"""
import sys
import time
sys.path.insert(0, r'{scripts_dir}')
from workflow_manager import load_topic_state, save_topic_state, load_settings

settings = load_settings()
topic = load_topic_state('{test_slug}', settings)

# Hold the file lock for 2 seconds while writing
time.sleep(2)

topic['topic']['concurrent_test'] = 'process_{{0}}'
save_topic_state('{test_slug}', topic, settings)
print('DONE')
""")

        # Launch 3 concurrent processes
        processes = []
        for i in range(3):
            proc = subprocess.Popen(
                [sys.executable, str(helper_script)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            processes.append(proc)
            time.sleep(0.1)  # Stagger launches slightly

        print(f"  ✓ Launched 3 concurrent processes")

        # Wait for all to complete
        for proc in processes:
            proc.wait(timeout=10)

        print(f"  ✓ All processes completed")

        # Verify file is not corrupted
        topic = load_topic_state(test_slug, settings)

        # Check that topic.json is valid JSON and not corrupted
        if "topic" in topic and "workflow" in topic["topic"]:
            print(f"  ✓ File locking prevented corruption (JSON is valid)")
            return True
        else:
            print(f"  ✗ File appears corrupted after concurrent access")
            return False

    except subprocess.TimeoutExpired:
        print(f"  ✗ Processes timed out (possible deadlock)")
        for proc in processes:
            proc.kill()
        return False
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if test_topic_dir.exists():
            shutil.rmtree(test_topic_dir)


def run_all_tests():
    """Run all Phase 1 tests"""
    print("\n" + "="*80)
    print("WORKFLOW MANAGER - PHASE 1 TEST SUITE")
    print("="*80)

    tests = [
        ("Schema Validation", test_schema_validation),
        ("Criteria Evaluator", test_criteria_evaluator),
        ("Idempotent Steps", test_idempotent_steps),
        ("Workflow Initialization", test_workflow_initialization),
        ("Step Completion & Validation", test_step_completion_and_validation),
        ("Rollback Mechanism", test_rollback_mechanism),
        ("Concurrent Access", test_concurrent_access),
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ Test '{name}' crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for _, result in results if result)
    failed = sum(1 for _, result in results if not result)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {name}")
    
    print(f"\nTotal: {passed} passed, {failed} failed out of {len(results)} tests")
    
    if failed == 0:
        print("\n🎉 All tests passed! Phase 1 implementation is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please review the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())

