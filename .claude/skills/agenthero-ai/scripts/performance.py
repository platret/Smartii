#!/usr/bin/env python3
"""
Performance Optimization Module for agenthero-ai workflow.
Optimizes file I/O, reduces lock contention, improves cache hit rate.

Phase 3 - Polish & Optimization
"""

import json
import sys
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
import threading
import time
from collections import defaultdict


class PerformanceMonitor:
    """
    Monitor workflow performance metrics.
    Track I/O operations, lock contention, cache performance.
    """
    
    def __init__(self):
        """Initialize performance monitor."""
        self.lock = threading.Lock()
        self.enabled = True
        
        # I/O metrics
        self.file_reads = 0
        self.file_writes = 0
        self.total_read_time = 0.0
        self.total_write_time = 0.0
        
        # Lock metrics
        self.lock_acquisitions = 0
        self.lock_wait_time = 0.0
        self.lock_contentions = 0
        
        # Cache metrics
        self.cache_hits = 0
        self.cache_misses = 0
        
        # Operation timings
        self.operation_times: Dict[str, List[float]] = defaultdict(list)
    
    def record_file_read(self, duration: float):
        """Record file read operation."""
        with self.lock:
            self.file_reads += 1
            self.total_read_time += duration
    
    def record_file_write(self, duration: float):
        """Record file write operation."""
        with self.lock:
            self.file_writes += 1
            self.total_write_time += duration
    
    def record_lock_acquisition(self, wait_time: float, contended: bool = False):
        """Record lock acquisition."""
        with self.lock:
            self.lock_acquisitions += 1
            self.lock_wait_time += wait_time
            if contended:
                self.lock_contentions += 1
    
    def record_cache_hit(self):
        """Record cache hit."""
        with self.lock:
            self.cache_hits += 1
    
    def record_cache_miss(self):
        """Record cache miss."""
        with self.lock:
            self.cache_misses += 1
    
    def record_operation(self, operation: str, duration: float):
        """Record operation timing."""
        with self.lock:
            self.operation_times[operation].append(duration)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        with self.lock:
            total_io_time = self.total_read_time + self.total_write_time
            avg_read_time = self.total_read_time / self.file_reads if self.file_reads > 0 else 0
            avg_write_time = self.total_write_time / self.file_writes if self.file_writes > 0 else 0
            
            cache_total = self.cache_hits + self.cache_misses
            cache_hit_rate = (self.cache_hits / cache_total * 100) if cache_total > 0 else 0
            
            avg_lock_wait = self.lock_wait_time / self.lock_acquisitions if self.lock_acquisitions > 0 else 0
            contention_rate = (self.lock_contentions / self.lock_acquisitions * 100) if self.lock_acquisitions > 0 else 0
            
            # Calculate operation averages
            operation_averages = {}
            for op, times in self.operation_times.items():
                operation_averages[op] = {
                    "count": len(times),
                    "avg_ms": round(sum(times) / len(times) * 1000, 2),
                    "min_ms": round(min(times) * 1000, 2),
                    "max_ms": round(max(times) * 1000, 2)
                }
            
            return {
                "enabled": self.enabled,
                "io": {
                    "file_reads": self.file_reads,
                    "file_writes": self.file_writes,
                    "total_io_time_ms": round(total_io_time * 1000, 2),
                    "avg_read_time_ms": round(avg_read_time * 1000, 2),
                    "avg_write_time_ms": round(avg_write_time * 1000, 2)
                },
                "locking": {
                    "lock_acquisitions": self.lock_acquisitions,
                    "lock_contentions": self.lock_contentions,
                    "contention_rate_percent": round(contention_rate, 2),
                    "avg_lock_wait_ms": round(avg_lock_wait * 1000, 2),
                    "total_lock_wait_ms": round(self.lock_wait_time * 1000, 2)
                },
                "caching": {
                    "cache_hits": self.cache_hits,
                    "cache_misses": self.cache_misses,
                    "cache_hit_rate_percent": round(cache_hit_rate, 2)
                },
                "operations": operation_averages
            }
    
    def print_stats(self):
        """Print performance statistics."""
        stats = self.get_stats()
        
        print("\nPerformance Statistics")
        print("="*80)
        
        print("\nI/O Operations:")
        print(f"  File Reads: {stats['io']['file_reads']}")
        print(f"  File Writes: {stats['io']['file_writes']}")
        print(f"  Total I/O Time: {stats['io']['total_io_time_ms']:.2f}ms")
        print(f"  Avg Read Time: {stats['io']['avg_read_time_ms']:.2f}ms")
        print(f"  Avg Write Time: {stats['io']['avg_write_time_ms']:.2f}ms")
        
        print("\nLocking:")
        print(f"  Lock Acquisitions: {stats['locking']['lock_acquisitions']}")
        print(f"  Lock Contentions: {stats['locking']['lock_contentions']}")
        print(f"  Contention Rate: {stats['locking']['contention_rate_percent']:.2f}%")
        print(f"  Avg Lock Wait: {stats['locking']['avg_lock_wait_ms']:.2f}ms")
        print(f"  Total Lock Wait: {stats['locking']['total_lock_wait_ms']:.2f}ms")
        
        print("\nCaching:")
        print(f"  Cache Hits: {stats['caching']['cache_hits']}")
        print(f"  Cache Misses: {stats['caching']['cache_misses']}")
        print(f"  Cache Hit Rate: {stats['caching']['cache_hit_rate_percent']:.2f}%")
        
        if stats['operations']:
            print("\nOperation Timings:")
            for op, metrics in stats['operations'].items():
                print(f"  {op}:")
                print(f"    Count: {metrics['count']}")
                print(f"    Avg: {metrics['avg_ms']:.2f}ms")
                print(f"    Min: {metrics['min_ms']:.2f}ms")
                print(f"    Max: {metrics['max_ms']:.2f}ms")
    
    def reset(self):
        """Reset all metrics."""
        with self.lock:
            self.file_reads = 0
            self.file_writes = 0
            self.total_read_time = 0.0
            self.total_write_time = 0.0
            self.lock_acquisitions = 0
            self.lock_wait_time = 0.0
            self.lock_contentions = 0
            self.cache_hits = 0
            self.cache_misses = 0
            self.operation_times.clear()


class PerformanceOptimizer:
    """
    Performance optimization recommendations and auto-tuning.
    """
    
    def __init__(self, monitor: PerformanceMonitor):
        """
        Initialize optimizer.
        
        Args:
            monitor: Performance monitor instance
        """
        self.monitor = monitor
    
    def analyze(self) -> Dict[str, Any]:
        """
        Analyze performance and provide recommendations.
        
        Returns:
            Analysis results with recommendations
        """
        stats = self.monitor.get_stats()
        recommendations = []
        
        # Check cache hit rate
        cache_hit_rate = stats['caching']['cache_hit_rate_percent']
        if cache_hit_rate < 50:
            recommendations.append({
                "severity": "high",
                "category": "caching",
                "issue": f"Low cache hit rate ({cache_hit_rate:.1f}%)",
                "recommendation": "Increase cache TTL or enable caching for more operations"
            })
        
        # Check lock contention
        contention_rate = stats['locking']['contention_rate_percent']
        if contention_rate > 20:
            recommendations.append({
                "severity": "high",
                "category": "locking",
                "issue": f"High lock contention ({contention_rate:.1f}%)",
                "recommendation": "Reduce lock scope or use finer-grained locking"
            })
        
        # Check I/O performance
        avg_read = stats['io']['avg_read_time_ms']
        avg_write = stats['io']['avg_write_time_ms']
        
        if avg_read > 100:
            recommendations.append({
                "severity": "medium",
                "category": "io",
                "issue": f"Slow file reads ({avg_read:.1f}ms avg)",
                "recommendation": "Enable caching or use faster storage"
            })
        
        if avg_write > 100:
            recommendations.append({
                "severity": "medium",
                "category": "io",
                "issue": f"Slow file writes ({avg_write:.1f}ms avg)",
                "recommendation": "Use buffered writes or async I/O"
            })
        
        return {
            "stats": stats,
            "recommendations": recommendations,
            "overall_health": "good" if len(recommendations) == 0 else "needs_attention"
        }
    
    def print_analysis(self):
        """Print performance analysis."""
        analysis = self.analyze()
        
        print("\nPerformance Analysis")
        print("="*80)
        print(f"Overall Health: {analysis['overall_health'].upper()}")
        
        if analysis['recommendations']:
            print(f"\nRecommendations ({len(analysis['recommendations'])}):")
            for idx, rec in enumerate(analysis['recommendations'], 1):
                severity_icon = "🔴" if rec['severity'] == "high" else "🟡"
                print(f"\n{idx}. {severity_icon} [{rec['category'].upper()}] {rec['issue']}")
                print(f"   → {rec['recommendation']}")
        else:
            print("\n✓ No performance issues detected")


# Global singleton instance
_performance_monitor: Optional[PerformanceMonitor] = None


def get_performance_monitor() -> PerformanceMonitor:
    """
    Get global performance monitor (singleton).
    
    Returns:
        PerformanceMonitor instance
    """
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor


if __name__ == "__main__":
    # Test performance monitoring
    print("Testing Performance Monitor...")
    print("="*80)
    
    monitor = get_performance_monitor()
    
    # Simulate operations
    print("\nSimulating operations...")
    monitor.record_file_read(0.05)
    monitor.record_file_read(0.03)
    monitor.record_file_write(0.08)
    monitor.record_lock_acquisition(0.001, contended=False)
    monitor.record_lock_acquisition(0.015, contended=True)
    monitor.record_cache_hit()
    monitor.record_cache_hit()
    monitor.record_cache_miss()
    monitor.record_operation("mark_step_complete", 0.12)
    monitor.record_operation("mark_step_complete", 0.15)
    
    # Print stats
    monitor.print_stats()
    
    # Analyze performance
    optimizer = PerformanceOptimizer(monitor)
    optimizer.print_analysis()
    
    print("\n" + "="*80)
    print("Performance Monitor Test Complete!")

