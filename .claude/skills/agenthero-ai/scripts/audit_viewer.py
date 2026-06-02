#!/usr/bin/env python3
"""
Audit Log Viewer for agenthero-ai workflow.
View and analyze audit logs with filtering and statistics.

Phase 3 - Polish & Optimization
"""

import json
import sys
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
from collections import defaultdict


class AuditLogViewer:
    """
    View and analyze workflow audit logs.
    Supports filtering by date, phase, step, event type.
    """
    
    def __init__(self, topic_file: Path):
        """
        Initialize audit log viewer.
        
        Args:
            topic_file: Path to topic.json
        """
        self.topic_file = topic_file
        self.topic_data = self._load_topic()
        self.audit_log = self.topic_data.get("workflow", {}).get("audit_log", [])
    
    def _load_topic(self) -> Dict[str, Any]:
        """Load topic.json file."""
        with open(self.topic_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def filter_logs(self, 
                   event_type: Optional[str] = None,
                   phase_id: Optional[str] = None,
                   step_id: Optional[str] = None,
                   start_date: Optional[str] = None,
                   end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Filter audit logs by criteria.
        
        Args:
            event_type: Filter by event type
            phase_id: Filter by phase ID
            step_id: Filter by step ID
            start_date: Filter by start date (ISO format)
            end_date: Filter by end date (ISO format)
            
        Returns:
            Filtered audit log entries
        """
        filtered = self.audit_log
        
        # Filter by event type
        if event_type:
            filtered = [e for e in filtered if e.get("event") == event_type]
        
        # Filter by phase
        if phase_id:
            filtered = [e for e in filtered if e.get("phase_id") == phase_id]
        
        # Filter by step
        if step_id:
            filtered = [e for e in filtered if e.get("step_id") == step_id]
        
        # Filter by date range
        if start_date:
            start_dt = datetime.fromisoformat(start_date)
            filtered = [e for e in filtered 
                       if datetime.fromisoformat(e.get("timestamp", "")) >= start_dt]
        
        if end_date:
            end_dt = datetime.fromisoformat(end_date)
            filtered = [e for e in filtered 
                       if datetime.fromisoformat(e.get("timestamp", "")) <= end_dt]
        
        return filtered
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get audit log statistics.
        
        Returns:
            Statistics dictionary
        """
        stats = {
            "total_entries": len(self.audit_log),
            "events_by_type": defaultdict(int),
            "events_by_phase": defaultdict(int),
            "events_by_step": defaultdict(int),
            "first_event": None,
            "last_event": None
        }
        
        if not self.audit_log:
            return stats
        
        # Count events by type
        for entry in self.audit_log:
            event_type = entry.get("event", "unknown")
            stats["events_by_type"][event_type] += 1
            
            phase_id = entry.get("phase_id")
            if phase_id:
                stats["events_by_phase"][phase_id] += 1
            
            step_id = entry.get("step_id")
            if step_id:
                stats["events_by_step"][step_id] += 1
        
        # Get first and last events
        stats["first_event"] = self.audit_log[0].get("timestamp")
        stats["last_event"] = self.audit_log[-1].get("timestamp")
        
        # Convert defaultdicts to regular dicts
        stats["events_by_type"] = dict(stats["events_by_type"])
        stats["events_by_phase"] = dict(stats["events_by_phase"])
        stats["events_by_step"] = dict(stats["events_by_step"])
        
        return stats
    
    def print_logs(self, logs: List[Dict[str, Any]], verbose: bool = False):
        """
        Print audit logs in human-readable format.
        
        Args:
            logs: Audit log entries to print
            verbose: Show full details
        """
        if not logs:
            print("No audit log entries found")
            return
        
        print(f"\nAudit Log Entries: {len(logs)}")
        print("="*80)
        
        for idx, entry in enumerate(logs, 1):
            timestamp = entry.get("timestamp", "unknown")
            event = entry.get("event", "unknown")
            phase_id = entry.get("phase_id", "")
            step_id = entry.get("step_id", "")
            
            # Format timestamp
            try:
                dt = datetime.fromisoformat(timestamp)
                timestamp_str = dt.strftime("%Y-%m-%d %H:%M:%S")
            except:
                timestamp_str = timestamp
            
            # Print entry
            print(f"\n{idx}. [{timestamp_str}] {event}")
            
            if phase_id:
                print(f"   Phase: {phase_id}")
            
            if step_id:
                print(f"   Step: {step_id}")
            
            if verbose:
                # Show full details
                details = entry.get("details", {})
                if details:
                    print(f"   Details: {json.dumps(details, indent=6)}")
    
    def print_statistics(self):
        """Print audit log statistics."""
        stats = self.get_statistics()
        
        print("\nAudit Log Statistics")
        print("="*80)
        print(f"Total Entries: {stats['total_entries']}")
        
        if stats['first_event']:
            print(f"First Event: {stats['first_event']}")
        
        if stats['last_event']:
            print(f"Last Event: {stats['last_event']}")
        
        print("\nEvents by Type:")
        for event_type, count in sorted(stats['events_by_type'].items()):
            print(f"  {event_type}: {count}")
        
        if stats['events_by_phase']:
            print("\nEvents by Phase:")
            for phase_id, count in sorted(stats['events_by_phase'].items()):
                print(f"  {phase_id}: {count}")
        
        if stats['events_by_step']:
            print("\nEvents by Step:")
            for step_id, count in sorted(stats['events_by_step'].items()):
                print(f"  {step_id}: {count}")
    
    def export_to_json(self, logs: List[Dict[str, Any]], output_file: Path):
        """
        Export filtered logs to JSON file.
        
        Args:
            logs: Audit log entries to export
            output_file: Output file path
        """
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(logs, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Exported {len(logs)} entries to {output_file}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="View and analyze agenthero-ai audit logs")
    parser.add_argument("topic_file", help="Path to topic.json")
    parser.add_argument("--event-type", help="Filter by event type")
    parser.add_argument("--phase", help="Filter by phase ID")
    parser.add_argument("--step", help="Filter by step ID")
    parser.add_argument("--start-date", help="Filter by start date (ISO format)")
    parser.add_argument("--end-date", help="Filter by end date (ISO format)")
    parser.add_argument("--stats", action="store_true", help="Show statistics only")
    parser.add_argument("--verbose", action="store_true", help="Show full details")
    parser.add_argument("--export", help="Export to JSON file")
    
    args = parser.parse_args()
    
    print("Audit Log Viewer")
    print("="*80)
    
    topic_file = Path(args.topic_file)
    
    if not topic_file.exists():
        print(f"✗ Topic file not found: {topic_file}")
        sys.exit(1)
    
    try:
        viewer = AuditLogViewer(topic_file)
        
        # Show statistics
        if args.stats:
            viewer.print_statistics()
            sys.exit(0)
        
        # Filter logs
        logs = viewer.filter_logs(
            event_type=args.event_type,
            phase_id=args.phase,
            step_id=args.step,
            start_date=args.start_date,
            end_date=args.end_date
        )
        
        # Export if requested
        if args.export:
            viewer.export_to_json(logs, Path(args.export))
        else:
            # Print logs
            viewer.print_logs(logs, verbose=args.verbose)
        
        print("\n" + "="*80)
        print(f"✓ Displayed {len(logs)} entries")
    
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

