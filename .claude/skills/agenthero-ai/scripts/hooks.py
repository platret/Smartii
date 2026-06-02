#!/usr/bin/env python3
"""
Hooks System for agenthero-ai workflow.
Event-driven callbacks that integrate with the event bus.

Phase 2 - Advanced Features
"""

import json
import sys
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from pathlib import Path
import threading

# Import event bus
from event_bus import Event, EventHandler, get_event_bus


class HookThrottler:
    """Throttles hook execution to prevent spam."""
    
    def __init__(self, throttle_seconds: int = 30):
        """
        Initialize throttler.
        
        Args:
            throttle_seconds: Minimum seconds between executions
        """
        self.throttle_seconds = throttle_seconds
        self.last_execution: Dict[str, datetime] = {}
        self.lock = threading.Lock()
    
    def should_execute(self, hook_id: str) -> bool:
        """
        Check if hook should execute (not throttled).
        
        Args:
            hook_id: Unique identifier for hook
            
        Returns:
            True if hook should execute, False if throttled
        """
        with self.lock:
            now = datetime.now()
            
            if hook_id not in self.last_execution:
                self.last_execution[hook_id] = now
                return True
            
            last_time = self.last_execution[hook_id]
            elapsed = (now - last_time).total_seconds()
            
            if elapsed >= self.throttle_seconds:
                self.last_execution[hook_id] = now
                return True
            
            return False
    
    def reset(self, hook_id: Optional[str] = None):
        """Reset throttle state."""
        with self.lock:
            if hook_id:
                self.last_execution.pop(hook_id, None)
            else:
                self.last_execution.clear()


class Hook:
    """Represents a workflow hook."""
    
    def __init__(self, hook_id: str, event_type: str, 
                 actions: List[str], 
                 enabled: bool = True,
                 throttle_seconds: Optional[int] = None,
                 filter_func: Optional[Callable[[Event], bool]] = None,
                 priority: int = 0):
        """
        Initialize hook.
        
        Args:
            hook_id: Unique identifier
            event_type: Event type to hook into
            actions: List of action names to execute
            enabled: Whether hook is enabled
            throttle_seconds: Optional throttle time
            filter_func: Optional filter function
            priority: Execution priority
        """
        self.hook_id = hook_id
        self.event_type = event_type
        self.actions = actions
        self.enabled = enabled
        self.throttle_seconds = throttle_seconds
        self.filter_func = filter_func
        self.priority = priority
        self.throttler = HookThrottler(throttle_seconds) if throttle_seconds else None
        self.execution_count = 0
        self.last_execution_time: Optional[datetime] = None
    
    def should_execute(self, event: Event) -> bool:
        """Check if hook should execute for this event."""
        if not self.enabled:
            return False
        
        # Check filter
        if self.filter_func and not self.filter_func(event):
            return False
        
        # Check throttle
        if self.throttler and not self.throttler.should_execute(self.hook_id):
            return False
        
        return True
    
    def execute(self, event: Event, action_registry: 'ActionRegistry'):
        """
        Execute hook actions.
        
        Args:
            event: Event that triggered hook
            action_registry: Registry of available actions
        """
        if not self.should_execute(event):
            return
        
        self.execution_count += 1
        self.last_execution_time = datetime.now()
        
        for action_name in self.actions:
            try:
                action_registry.execute_action(action_name, event)
            except Exception as e:
                print(f"ERROR: Hook {self.hook_id} action {action_name} failed: {e}", 
                      file=sys.stderr)
                import traceback
                traceback.print_exc()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get hook statistics."""
        return {
            'hook_id': self.hook_id,
            'event_type': self.event_type,
            'enabled': self.enabled,
            'execution_count': self.execution_count,
            'last_execution': self.last_execution_time.isoformat() if self.last_execution_time else None,
            'throttle_seconds': self.throttle_seconds,
            'actions': self.actions
        }


class ActionRegistry:
    """Registry of available hook actions."""
    
    def __init__(self):
        """Initialize action registry."""
        self.actions: Dict[str, Callable[[Event], None]] = {}
    
    def register(self, action_name: str, action_func: Callable[[Event], None]):
        """
        Register an action.
        
        Args:
            action_name: Name of action
            action_func: Function to execute
        """
        self.actions[action_name] = action_func
    
    def unregister(self, action_name: str):
        """Unregister an action."""
        self.actions.pop(action_name, None)
    
    def execute_action(self, action_name: str, event: Event):
        """
        Execute an action.
        
        Args:
            action_name: Name of action to execute
            event: Event data
        """
        if action_name not in self.actions:
            print(f"WARNING: Action {action_name} not registered", file=sys.stderr)
            return
        
        try:
            self.actions[action_name](event)
        except Exception as e:
            print(f"ERROR: Action {action_name} failed: {e}", file=sys.stderr)
            raise
    
    def get_available_actions(self) -> List[str]:
        """Get list of available actions."""
        return list(self.actions.keys())


class HooksManager:
    """Manages workflow hooks and integrates with event bus."""
    
    def __init__(self, settings: Optional[Dict[str, Any]] = None):
        """
        Initialize hooks manager.
        
        Args:
            settings: Optional settings dict with hooks configuration
        """
        self.hooks: Dict[str, Hook] = {}
        self.action_registry = ActionRegistry()
        self.event_bus = get_event_bus()
        self.enabled = True
        
        # Register default actions
        self._register_default_actions()
        
        # Load hooks from settings if provided
        if settings:
            self.load_hooks_from_settings(settings)
    
    def _register_default_actions(self):
        """Register default workflow actions."""
        
        def log_to_audit(event: Event):
            """Log event to audit trail."""
            print(f"[AUDIT] {event.event_type}: {event.data}")
        
        def update_workflow_state(event: Event):
            """Update workflow state."""
            print(f"[STATE] Updating workflow state: {event.data}")
        
        def mark_step_complete(event: Event):
            """Mark step as complete."""
            print(f"[COMPLETE] Step completed: {event.data.get('step_id')}")
        
        def check_next_step(event: Event):
            """Check for next step."""
            print(f"[NEXT] Checking next step after: {event.data.get('step_id')}")
        
        self.action_registry.register('log_to_audit', log_to_audit)
        self.action_registry.register('update_workflow_state', update_workflow_state)
        self.action_registry.register('mark_step_complete', mark_step_complete)
        self.action_registry.register('check_next_step', check_next_step)
    
    def register_action(self, action_name: str, action_func: Callable[[Event], None]):
        """Register a custom action."""
        self.action_registry.register(action_name, action_func)
    
    def add_hook(self, hook: Hook):
        """
        Add a hook and subscribe to event bus.
        
        Args:
            hook: Hook to add
        """
        self.hooks[hook.hook_id] = hook
        
        # Create event handler that executes hook
        def hook_handler(event: Event):
            if self.enabled:
                hook.execute(event, self.action_registry)
        
        handler = EventHandler(
            handler_id=f"hook-{hook.hook_id}",
            callback=hook_handler,
            filter_func=hook.filter_func,
            priority=hook.priority
        )
        
        self.event_bus.subscribe(hook.event_type, handler)
    
    def remove_hook(self, hook_id: str):
        """Remove a hook."""
        if hook_id in self.hooks:
            hook = self.hooks[hook_id]
            self.event_bus.unsubscribe(hook.event_type, f"hook-{hook_id}")
            del self.hooks[hook_id]
    
    def enable_hook(self, hook_id: str):
        """Enable a hook."""
        if hook_id in self.hooks:
            self.hooks[hook_id].enabled = True
    
    def disable_hook(self, hook_id: str):
        """Disable a hook."""
        if hook_id in self.hooks:
            self.hooks[hook_id].enabled = False
    
    def load_hooks_from_settings(self, settings: Dict[str, Any]):
        """
        Load hooks from settings configuration.
        
        Args:
            settings: Settings dict with hooks configuration
        """
        hooks_config = settings.get('hooks', {})
        
        if not hooks_config.get('enabled', True):
            self.enabled = False
            return
        
        events_config = hooks_config.get('events', {})
        
        for event_type, event_config in events_config.items():
            if not event_config.get('enabled', True):
                continue
            
            hook = Hook(
                hook_id=event_type,
                event_type=event_type,
                actions=event_config.get('actions', []),
                enabled=event_config.get('enabled', True),
                throttle_seconds=event_config.get('throttle_seconds'),
                priority=event_config.get('priority', 0)
            )
            
            self.add_hook(hook)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get hooks manager statistics."""
        return {
            'enabled': self.enabled,
            'total_hooks': len(self.hooks),
            'enabled_hooks': sum(1 for h in self.hooks.values() if h.enabled),
            'available_actions': self.action_registry.get_available_actions(),
            'hooks': {hook_id: hook.get_stats() for hook_id, hook in self.hooks.items()}
        }
    
    def enable(self):
        """Enable hooks manager."""
        self.enabled = True
    
    def disable(self):
        """Disable hooks manager."""
        self.enabled = False


# Global hooks manager instance
_global_hooks_manager: Optional[HooksManager] = None


def get_hooks_manager(settings: Optional[Dict[str, Any]] = None) -> HooksManager:
    """Get global hooks manager instance (singleton)."""
    global _global_hooks_manager
    if _global_hooks_manager is None:
        _global_hooks_manager = HooksManager(settings)
    return _global_hooks_manager


def reset_hooks_manager():
    """Reset global hooks manager (for testing)."""
    global _global_hooks_manager
    _global_hooks_manager = None


if __name__ == "__main__":
    # Simple test
    print("Hooks System - Simple Test")
    print("=" * 80)
    
    # Create hooks manager
    manager = get_hooks_manager()
    
    # Add a test hook
    hook = Hook(
        hook_id='test-step-started',
        event_type='step_started',
        actions=['log_to_audit', 'update_workflow_state']
    )
    manager.add_hook(hook)
    
    # Emit test event
    from event_bus import emit_step_started
    emit_step_started('test-topic', 'phase-1', 'parse-spec')
    
    # Show stats
    print("\nHooks Manager Stats:")
    print(json.dumps(manager.get_stats(), indent=2))
