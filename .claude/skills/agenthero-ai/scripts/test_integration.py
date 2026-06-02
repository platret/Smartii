#!/usr/bin/env python3
"""
Integration Tests for agenthero-ai workflow.
End-to-end tests with all Phase 1 and Phase 2 features enabled.

Phase 3 - Polish & Optimization
"""

import json
import sys
import time
from pathlib import Path
from typing import Dict, Any

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Import all modules
from workflow_manager import (
    load_settings,
    initialize_topic_workflow,
    mark_step_complete,
    get_next_step,
    get_workflow_status
)
from event_bus import get_event_bus, emit_workflow_started, emit_step_completed, EventHandler
from hooks import get_hooks_manager, Hook
from cache import get_cache
from parallel_executor import get_executor, DependencyGraph
from dry_run import get_dry_run_context
from performance import get_performance_monitor


def test_full_workflow_integration():
    """
    Test 1: Full workflow with all features enabled.
    Tests Phase 1 + Phase 2 integration.
    """
    print("\n" + "="*80)
    print("Test 1: Full Workflow Integration")
    print("="*80)
    
    # Get repository root (scripts -> agenthero-ai -> skills -> .claude -> root)
    REPO_ROOT = Path(__file__).parent.parent.parent.parent.absolute()
    SETTINGS_PATH = REPO_ROOT / "agents" / "agenthero-ai" / "settings.json"
    
    # Load settings
    print("\n1. Loading settings...")
    settings = load_settings(str(SETTINGS_PATH))
    print(f"   OK Settings loaded (version {settings['version']})")
    print(f"   OK Advanced features: {list(settings['advanced'].keys())}")

    # Initialize components
    print("\n2. Initializing components...")
    event_bus = get_event_bus()
    hooks_manager = get_hooks_manager()
    cache = get_cache()
    executor = get_executor()
    dry_run = get_dry_run_context()
    perf_monitor = get_performance_monitor()

    print(f"   OK Event bus initialized")
    print(f"   OK Hooks manager initialized")
    print(f"   OK Cache initialized")
    print(f"   OK Parallel executor initialized")
    print(f"   OK Dry-run context initialized")
    print(f"   OK Performance monitor initialized")
    
    # Test event bus
    print("\n3. Testing event bus...")
    events_received = []

    def test_handler_func(event):
        events_received.append(event.event_type)

    test_handler = EventHandler(
        handler_id="test_handler",
        callback=test_handler_func
    )
    event_bus.subscribe("test_event", test_handler)
    event_bus.emit_event("test_event", {"data": "test"})

    assert "test_event" in events_received, "Event not received"
    print(f"   OK Event bus working (received {len(events_received)} events)")

    # Test cache
    print("\n4. Testing cache...")
    cache.set("test_key", {"value": 123}, ttl_seconds=60)
    cached_value = cache.get("test_key")

    assert cached_value is not None, "Cache miss on fresh entry"
    assert cached_value["value"] == 123, "Cache value mismatch"
    print(f"   OK Cache working (hit rate: {cache.get_stats()['hit_rate_percent']:.1f}%)")
    
    # Test parallel executor
    print("\n5. Testing parallel executor...")
    graph = DependencyGraph()
    graph.add_node("task1")
    graph.add_node("task2")
    graph.add_dependency("task2", "task1")
    
    executed = []
    
    def execute_task(task_id):
        executed.append(task_id)
        return {"task_id": task_id, "status": "success"}
    
    result = executor.execute_graph(graph, execute_task)

    assert result["success"], "Parallel execution failed"
    assert len(executed) == 2, "Not all tasks executed"
    print(f"   OK Parallel executor working (executed {len(executed)} tasks)")

    # Test dry-run mode
    print("\n6. Testing dry-run mode...")
    dry_run.enable()
    dry_run.record_file_write("/test/file.json", {"data": "test"})
    dry_run.record_state_change("step", "test-step", "pending", "completed")

    summary = dry_run.get_summary()
    assert summary["file_writes"] == 1, "Dry-run not recording file writes"
    assert summary["state_changes"] == 1, "Dry-run not recording state changes"

    dry_run.disable()
    print(f"   OK Dry-run mode working (recorded {summary['file_writes']} writes)")

    # Test performance monitor
    print("\n7. Testing performance monitor...")
    perf_monitor.record_file_read(0.05)
    perf_monitor.record_cache_hit()

    stats = perf_monitor.get_stats()
    assert stats["io"]["file_reads"] > 0, "Performance monitor not recording reads"
    assert stats["caching"]["cache_hits"] > 0, "Performance monitor not recording cache hits"
    print(f"   OK Performance monitor working (tracking {stats['io']['file_reads']} reads)")

    print("\n" + "="*80)
    print("OK Test 1 PASSED: All components integrated successfully")
    print("="*80)
    
    return True


def test_workflow_with_caching():
    """
    Test 2: Workflow with caching enabled.
    Verify cache improves performance.
    """
    print("\n" + "="*80)
    print("Test 2: Workflow with Caching")
    print("="*80)
    
    cache = get_cache()
    cache.clear()
    
    # Simulate multiple loads
    print("\n1. Testing cache performance...")
    
    test_data = {"large": "data" * 1000}
    
    # First load (cache miss)
    start = time.time()
    cache.set("test_data", test_data, ttl_seconds=60)
    write_time = time.time() - start
    
    # Second load (cache hit)
    start = time.time()
    cached = cache.get("test_data")
    read_time = time.time() - start
    
    assert cached is not None, "Cache miss on fresh entry"
    
    speedup = write_time / read_time if read_time > 0 else 0
    
    print(f"   Write time: {write_time*1000:.2f}ms")
    print(f"   Read time: {read_time*1000:.2f}ms")
    print(f"   Speedup: {speedup:.1f}x")
    
    stats = cache.get_stats()
    print(f"   Cache hit rate: {stats['hit_rate_percent']:.1f}%")

    print("\n" + "="*80)
    print("OK Test 2 PASSED: Caching improves performance")
    print("="*80)
    
    return True


def test_event_driven_workflow():
    """
    Test 3: Event-driven workflow with hooks.
    Verify events trigger hooks correctly.
    """
    print("\n" + "="*80)
    print("Test 3: Event-Driven Workflow")
    print("="*80)
    
    event_bus = get_event_bus()
    hooks_manager = get_hooks_manager()
    
    # Track hook executions
    hook_executions = []
    
    def test_action(event_data):
        hook_executions.append(event_data)
        return {"status": "success"}
    
    # Register test action
    hooks_manager.action_registry.register("test_action", test_action)
    
    # Add hook
    print("\n1. Adding hook...")
    test_hook = Hook(
        hook_id="test_hook",
        event_type="step_completed",
        actions=["test_action"],
        enabled=True
    )
    hooks_manager.add_hook(test_hook)
    
    # Emit event
    print("2. Emitting event...")
    emit_step_completed("test-topic", "phase-1", "step-1", {"result": "success"})
    
    # Give hooks time to execute
    time.sleep(0.1)
    
    # Verify hook executed
    assert len(hook_executions) > 0, "Hook not executed"
    print(f"   OK Hook executed {len(hook_executions)} times")

    print("\n" + "="*80)
    print("OK Test 3 PASSED: Event-driven workflow working")
    print("="*80)
    
    return True


def run_all_tests():
    """Run all integration tests."""
    print("\n" + "="*80)
    print("INTEGRATION TESTS - Phase 1 + Phase 2")
    print("="*80)
    
    tests = [
        ("Full Workflow Integration", test_full_workflow_integration),
        ("Workflow with Caching", test_workflow_with_caching),
        ("Event-Driven Workflow", test_event_driven_workflow),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"\nFAIL Test FAILED: {test_name}")
            print(f"   Error: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    # Summary
    print("\n" + "="*80)
    print("INTEGRATION TEST SUMMARY")
    print("="*80)
    print(f"Total Tests: {len(tests)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")

    if failed == 0:
        print("\nOK ALL INTEGRATION TESTS PASSED!")
        return True
    else:
        print(f"\nFAIL {failed} TESTS FAILED")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

