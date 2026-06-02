#!/usr/bin/env python3
"""
Event Bus Pattern for agenthero-ai workflow system.
Provides pub/sub architecture to decouple hooks from workflow logic.

Phase 2 - Advanced Features
"""

import json
import sys
from typing import Dict, List, Callable, Any, Optional
from datetime import datetime
from pathlib import Path
import threading


class Event:
    """Represents a workflow event."""
    
    def __init__(self, event_type: str, data: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize event.
        
        Args:
            event_type: Type of event (e.g., 'step_started', 'phase_completed')
            data: Event data payload
            metadata: Optional metadata (timestamp, source, etc.)
        """
        self.event_type = event_type
        self.data = data
        self.metadata = metadata or {}
        
        # Auto-add timestamp if not provided
        if 'timestamp' not in self.metadata:
            self.metadata['timestamp'] = datetime.now().astimezone().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return {
            'event_type': self.event_type,
            'data': self.data,
            'metadata': self.metadata
        }
    
    def __repr__(self):
        return f"Event(type={self.event_type}, data={self.data})"


class EventHandler:
    """Wrapper for event handler functions."""
    
    def __init__(self, handler_id: str, callback: Callable[[Event], None], 
                 filter_func: Optional[Callable[[Event], bool]] = None,
                 priority: int = 0):
        """
        Initialize event handler.
        
        Args:
            handler_id: Unique identifier for this handler
            callback: Function to call when event is emitted
            filter_func: Optional filter function (return True to handle event)
            priority: Handler priority (higher = executed first)
        """
        self.handler_id = handler_id
        self.callback = callback
        self.filter_func = filter_func
        self.priority = priority
    
    def should_handle(self, event: Event) -> bool:
        """Check if this handler should handle the event."""
        if self.filter_func is None:
            return True
        return self.filter_func(event)
    
    def handle(self, event: Event):
        """Handle the event."""
        try:
            self.callback(event)
        except Exception as e:
            print(f"ERROR: Handler {self.handler_id} failed: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()


class EventBus:
    """
    Event bus for pub/sub pattern.
    Thread-safe implementation for concurrent event handling.
    """
    
    def __init__(self):
        """Initialize event bus."""
        self.handlers: Dict[str, List[EventHandler]] = {}
        self.lock = threading.Lock()
        self.event_history: List[Event] = []
        self.max_history = 1000  # Keep last 1000 events
        self.enabled = True
    
    def subscribe(self, event_type: str, handler: EventHandler):
        """
        Subscribe handler to event type.
        
        Args:
            event_type: Type of event to subscribe to (e.g., 'step_started')
            handler: EventHandler instance
        """
        with self.lock:
            if event_type not in self.handlers:
                self.handlers[event_type] = []
            
            # Check for duplicate handler_id
            existing_ids = [h.handler_id for h in self.handlers[event_type]]
            if handler.handler_id in existing_ids:
                print(f"WARNING: Handler {handler.handler_id} already subscribed to {event_type}", 
                      file=sys.stderr)
                return
            
            self.handlers[event_type].append(handler)
            
            # Sort by priority (highest first)
            self.handlers[event_type].sort(key=lambda h: h.priority, reverse=True)
    
    def unsubscribe(self, event_type: str, handler_id: str):
        """
        Unsubscribe handler from event type.
        
        Args:
            event_type: Type of event
            handler_id: ID of handler to remove
        """
        with self.lock:
            if event_type in self.handlers:
                self.handlers[event_type] = [
                    h for h in self.handlers[event_type] 
                    if h.handler_id != handler_id
                ]
    
    def emit(self, event: Event):
        """
        Emit event to all subscribed handlers.
        
        Args:
            event: Event to emit
        """
        if not self.enabled:
            return
        
        # Add to history
        with self.lock:
            self.event_history.append(event)
            if len(self.event_history) > self.max_history:
                self.event_history.pop(0)
        
        # Get handlers for this event type
        handlers = []
        with self.lock:
            if event.event_type in self.handlers:
                handlers = self.handlers[event.event_type].copy()
        
        # Execute handlers (outside lock to prevent deadlock)
        for handler in handlers:
            if handler.should_handle(event):
                handler.handle(event)
    
    def emit_event(self, event_type: str, data: Dict[str, Any], 
                   metadata: Optional[Dict[str, Any]] = None):
        """
        Convenience method to create and emit event.
        
        Args:
            event_type: Type of event
            data: Event data
            metadata: Optional metadata
        """
        event = Event(event_type, data, metadata)
        self.emit(event)
    
    def get_handlers(self, event_type: str) -> List[EventHandler]:
        """Get all handlers for event type."""
        with self.lock:
            return self.handlers.get(event_type, []).copy()
    
    def get_event_history(self, event_type: Optional[str] = None, 
                         limit: Optional[int] = None) -> List[Event]:
        """
        Get event history.
        
        Args:
            event_type: Optional filter by event type
            limit: Optional limit number of events
            
        Returns:
            List of events (most recent first)
        """
        with self.lock:
            events = self.event_history.copy()
        
        # Filter by type
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        # Reverse (most recent first)
        events.reverse()
        
        # Limit
        if limit:
            events = events[:limit]
        
        return events
    
    def clear_history(self):
        """Clear event history."""
        with self.lock:
            self.event_history.clear()
    
    def disable(self):
        """Disable event bus (no events will be emitted)."""
        self.enabled = False
    
    def enable(self):
        """Enable event bus."""
        self.enabled = True
    
    def get_stats(self) -> Dict[str, Any]:
        """Get event bus statistics."""
        with self.lock:
            return {
                'enabled': self.enabled,
                'total_handlers': sum(len(handlers) for handlers in self.handlers.values()),
                'event_types': list(self.handlers.keys()),
                'history_size': len(self.event_history),
                'max_history': self.max_history
            }


# Global event bus instance
_global_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """Get global event bus instance (singleton)."""
    global _global_event_bus
    if _global_event_bus is None:
        _global_event_bus = EventBus()
    return _global_event_bus


def reset_event_bus():
    """Reset global event bus (for testing)."""
    global _global_event_bus
    _global_event_bus = None


# Convenience functions for common workflow events

def emit_step_started(topic_slug: str, phase_id: str, step_id: str, **kwargs):
    """Emit step_started event."""
    bus = get_event_bus()
    bus.emit_event('step_started', {
        'topic_slug': topic_slug,
        'phase_id': phase_id,
        'step_id': step_id,
        **kwargs
    })


def emit_step_completed(topic_slug: str, phase_id: str, step_id: str, result: Dict[str, Any], **kwargs):
    """Emit step_completed event."""
    bus = get_event_bus()
    bus.emit_event('step_completed', {
        'topic_slug': topic_slug,
        'phase_id': phase_id,
        'step_id': step_id,
        'result': result,
        **kwargs
    })


def emit_step_failed(topic_slug: str, phase_id: str, step_id: str, error: str, **kwargs):
    """Emit step_failed event."""
    bus = get_event_bus()
    bus.emit_event('step_failed', {
        'topic_slug': topic_slug,
        'phase_id': phase_id,
        'step_id': step_id,
        'error': error,
        **kwargs
    })


def emit_phase_started(topic_slug: str, phase_id: str, **kwargs):
    """Emit phase_started event."""
    bus = get_event_bus()
    bus.emit_event('phase_started', {
        'topic_slug': topic_slug,
        'phase_id': phase_id,
        **kwargs
    })


def emit_phase_completed(topic_slug: str, phase_id: str, **kwargs):
    """Emit phase_completed event."""
    bus = get_event_bus()
    bus.emit_event('phase_completed', {
        'topic_slug': topic_slug,
        'phase_id': phase_id,
        **kwargs
    })


def emit_workflow_initialized(topic_slug: str, **kwargs):
    """Emit workflow_initialized event."""
    bus = get_event_bus()
    bus.emit_event('workflow_initialized', {
        'topic_slug': topic_slug,
        **kwargs
    })


def emit_workflow_started(topic_slug: str, total_steps: int, **kwargs):
    """Emit workflow_started event."""
    bus = get_event_bus()
    bus.emit_event('workflow_started', {
        'topic_slug': topic_slug,
        'total_steps': total_steps,
        **kwargs
    })


def emit_workflow_completed(topic_slug: str, **kwargs):
    """Emit workflow_completed event."""
    bus = get_event_bus()
    bus.emit_event('workflow_completed', {
        'topic_slug': topic_slug,
        **kwargs
    })


if __name__ == "__main__":
    # Simple test
    print("Event Bus - Simple Test")
    print("=" * 80)
    
    bus = get_event_bus()
    
    # Create test handler
    def test_handler(event: Event):
        print(f"Handler received: {event}")
    
    handler = EventHandler('test-handler', test_handler)
    bus.subscribe('step_started', handler)
    
    # Emit test event
    emit_step_started('test-topic', 'phase-1', 'parse-spec')
    
    # Show stats
    print("\nEvent Bus Stats:")
    print(json.dumps(bus.get_stats(), indent=2))
    
    # Show history
    print("\nEvent History:")
    for event in bus.get_event_history(limit=5):
        print(f"  {event}")

