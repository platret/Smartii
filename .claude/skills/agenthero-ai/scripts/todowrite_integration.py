#!/usr/bin/env python3
"""
TodoWrite Integration for agenthero-ai workflow.
Integrates with hooks system to provide progress updates via TodoWrite tool.

Phase 2 - Advanced Features
"""

import json
import sys
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
import threading

# Import event bus and hooks
from event_bus import Event, get_event_bus
from hooks import HookThrottler


class TodoWriteIntegration:
    """
    Integrates TodoWrite tool with workflow events.
    Provides throttled progress updates with task prefix [A:orch].
    """
    
    def __init__(self, throttle_seconds: int = 30):
        """
        Initialize TodoWrite integration.
        
        Args:
            throttle_seconds: Minimum seconds between TodoWrite updates (default: 30)
        """
        self.throttler = HookThrottler(throttle_seconds)
        self.event_bus = get_event_bus()
        self.enabled = True
        self.task_prefix = "[A:orch]"  # Agent: orchestrator
        self.lock = threading.Lock()
        
        # Track current workflow state
        self.current_topic: Optional[str] = None
        self.current_phase: Optional[str] = None
        self.current_step: Optional[str] = None
        self.total_steps: int = 0
        self.completed_steps: int = 0
        
        # Subscribe to workflow events
        self._subscribe_to_events()
    
    def _subscribe_to_events(self):
        """Subscribe to relevant workflow events."""
        from event_bus import EventHandler
        
        # Phase events
        self.event_bus.subscribe('phase_started', EventHandler(
            handler_id='todowrite_phase_started',
            callback=self._on_phase_started,
            priority=10
        ))
        
        self.event_bus.subscribe('phase_completed', EventHandler(
            handler_id='todowrite_phase_completed',
            callback=self._on_phase_completed,
            priority=10
        ))
        
        # Step events
        self.event_bus.subscribe('step_started', EventHandler(
            handler_id='todowrite_step_started',
            callback=self._on_step_started,
            priority=10
        ))
        
        self.event_bus.subscribe('step_completed', EventHandler(
            handler_id='todowrite_step_completed',
            callback=self._on_step_completed,
            priority=10
        ))
        
        self.event_bus.subscribe('step_failed', EventHandler(
            handler_id='todowrite_step_failed',
            callback=self._on_step_failed,
            priority=10
        ))
        
        # Workflow events
        self.event_bus.subscribe('workflow_started', EventHandler(
            handler_id='todowrite_workflow_started',
            callback=self._on_workflow_started,
            priority=10
        ))
        
        self.event_bus.subscribe('workflow_completed', EventHandler(
            handler_id='todowrite_workflow_completed',
            callback=self._on_workflow_completed,
            priority=10
        ))
    
    def _on_workflow_started(self, event: Event):
        """Handle workflow started event."""
        if not self.enabled:
            return
        
        topic_slug = event.data.get('topic_slug')
        total_steps = event.data.get('total_steps', 0)
        
        with self.lock:
            self.current_topic = topic_slug
            self.total_steps = total_steps
            self.completed_steps = 0
        
        # Always send workflow start (not throttled)
        self._send_todowrite({
            "content": f"{self.task_prefix} Workflow started for topic: {topic_slug}",
            "status": "in_progress",
            "activeForm": f"Starting workflow ({total_steps} steps)"
        })
    
    def _on_workflow_completed(self, event: Event):
        """Handle workflow completed event."""
        if not self.enabled:
            return
        
        topic_slug = event.data.get('topic_slug')
        
        # Always send workflow completion (not throttled)
        self._send_todowrite({
            "content": f"{self.task_prefix} Workflow completed for topic: {topic_slug}",
            "status": "completed",
            "activeForm": "Workflow complete ✓"
        })
        
        with self.lock:
            self.current_topic = None
            self.current_phase = None
            self.current_step = None
            self.completed_steps = 0
    
    def _on_phase_started(self, event: Event):
        """Handle phase started event."""
        if not self.enabled:
            return
        
        phase_id = event.data.get('phase_id')
        phase_name = event.data.get('phase_name', phase_id)
        
        with self.lock:
            self.current_phase = phase_id
        
        # Throttled update
        if self.throttler.should_execute('phase_started'):
            progress = self._calculate_progress()
            self._send_todowrite({
                "content": f"{self.task_prefix} Phase: {phase_name}",
                "status": "in_progress",
                "activeForm": f"Starting phase ({progress}% complete)"
            })
    
    def _on_phase_completed(self, event: Event):
        """Handle phase completed event."""
        if not self.enabled:
            return
        
        phase_id = event.data.get('phase_id')
        phase_name = event.data.get('phase_name', phase_id)
        
        # Throttled update
        if self.throttler.should_execute('phase_completed'):
            progress = self._calculate_progress()
            self._send_todowrite({
                "content": f"{self.task_prefix} Phase completed: {phase_name}",
                "status": "in_progress",
                "activeForm": f"Phase complete ({progress}% overall)"
            })
    
    def _on_step_started(self, event: Event):
        """Handle step started event."""
        if not self.enabled:
            return
        
        step_id = event.data.get('step_id')
        step_name = event.data.get('step_name', step_id)
        
        with self.lock:
            self.current_step = step_id
        
        # Throttled update
        if self.throttler.should_execute('step_started'):
            progress = self._calculate_progress()
            self._send_todowrite({
                "content": f"{self.task_prefix} Step: {step_name}",
                "status": "in_progress",
                "activeForm": f"Executing step ({progress}% complete)"
            })
    
    def _on_step_completed(self, event: Event):
        """Handle step completed event."""
        if not self.enabled:
            return
        
        step_id = event.data.get('step_id')
        step_name = event.data.get('step_name', step_id)
        
        with self.lock:
            self.completed_steps += 1
        
        # Throttled update
        if self.throttler.should_execute('step_completed'):
            progress = self._calculate_progress()
            self._send_todowrite({
                "content": f"{self.task_prefix} Step completed: {step_name}",
                "status": "in_progress",
                "activeForm": f"Step complete ({progress}% overall)"
            })
    
    def _on_step_failed(self, event: Event):
        """Handle step failed event."""
        if not self.enabled:
            return
        
        step_id = event.data.get('step_id')
        step_name = event.data.get('step_name', step_id)
        error = event.data.get('error', 'Unknown error')
        
        # Always send failures (not throttled)
        self._send_todowrite({
            "content": f"{self.task_prefix} Step failed: {step_name}",
            "status": "failed",
            "activeForm": f"Error: {error}"
        })
    
    def _calculate_progress(self) -> int:
        """Calculate workflow progress percentage."""
        with self.lock:
            if self.total_steps == 0:
                return 0
            return int((self.completed_steps / self.total_steps) * 100)
    
    def _send_todowrite(self, todo_data: Dict[str, Any]):
        """
        Send TodoWrite update.
        
        Args:
            todo_data: Dictionary with content, status, activeForm
        """
        # In real implementation, this would call the TodoWrite tool
        # For now, we'll just print to stdout in JSON format
        # The agent can parse this and call TodoWrite
        
        output = {
            "type": "todowrite_update",
            "timestamp": datetime.now().astimezone().isoformat(),
            "data": todo_data
        }
        
        print(f"TODOWRITE: {json.dumps(output)}", flush=True)
    
    def enable(self):
        """Enable TodoWrite integration."""
        self.enabled = True
    
    def disable(self):
        """Disable TodoWrite integration."""
        self.enabled = False
    
    def reset_throttle(self):
        """Reset throttle state (useful for testing)."""
        self.throttler.reset()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get integration statistics."""
        with self.lock:
            return {
                "enabled": self.enabled,
                "current_topic": self.current_topic,
                "current_phase": self.current_phase,
                "current_step": self.current_step,
                "total_steps": self.total_steps,
                "completed_steps": self.completed_steps,
                "progress_percentage": self._calculate_progress(),
                "throttle_seconds": self.throttler.throttle_seconds
            }


# Global singleton instance
_todowrite_integration: Optional[TodoWriteIntegration] = None


def get_todowrite_integration(throttle_seconds: int = 30) -> TodoWriteIntegration:
    """
    Get global TodoWrite integration instance (singleton).
    
    Args:
        throttle_seconds: Throttle time (only used on first call)
        
    Returns:
        TodoWriteIntegration instance
    """
    global _todowrite_integration
    if _todowrite_integration is None:
        _todowrite_integration = TodoWriteIntegration(throttle_seconds)
    return _todowrite_integration


# Re-export convenience functions from event_bus
from event_bus import (
    emit_workflow_started,
    emit_workflow_completed,
    emit_phase_started,
    emit_phase_completed,
    emit_step_started,
    emit_step_completed,
    emit_step_failed
)


if __name__ == "__main__":
    # Test TodoWrite integration
    print("Testing TodoWrite Integration...")
    print("="*80)

    # Initialize integration
    integration = get_todowrite_integration(throttle_seconds=5)  # 5s for testing

    import time

    # Simulate workflow events
    print("\n1. Workflow Started")
    emit_workflow_started("test-topic", 10)
    time.sleep(1)

    print("\n2. Phase Started")
    emit_phase_started("test-topic", "phase-1", phase_name="Requirements Analysis")
    time.sleep(1)

    print("\n3. Step Started")
    emit_step_started("test-topic", "phase-1", "parse-spec", step_name="Parse Specification")
    time.sleep(1)

    print("\n4. Step Completed")
    emit_step_completed("test-topic", "phase-1", "parse-spec", {"spec_valid": True}, step_name="Parse Specification")
    time.sleep(1)

    print("\n5. Another Step (should be throttled - within 5s)")
    emit_step_started("test-topic", "phase-1", "extract-requirements", step_name="Extract Requirements")
    time.sleep(1)

    print("\n6. Wait for throttle to expire...")
    time.sleep(4)  # Total 6s since last step_started

    print("\n7. Another Step (after throttle)")
    emit_step_started("test-topic", "phase-1", "analyze-requirements", step_name="Analyze Requirements")
    time.sleep(1)

    print("\n8. Step Failed (always sent, not throttled)")
    emit_step_failed("test-topic", "phase-1", "analyze-requirements", "File not found", step_name="Analyze Requirements")
    time.sleep(1)

    print("\n9. Workflow Completed")
    emit_workflow_completed("test-topic")

    print("\n" + "="*80)
    print("TodoWrite Integration Stats:")
    print(json.dumps(integration.get_stats(), indent=2))

