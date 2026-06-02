#!/usr/bin/env python3
"""
Parallel Execution Engine for agenthero-ai workflow.
Supports independent steps running concurrently with dependency graph.

Phase 2 - Advanced Features
"""

import json
import sys
from typing import Dict, List, Any, Optional, Set, Callable
from datetime import datetime
from pathlib import Path
import threading
from concurrent.futures import ThreadPoolExecutor, Future, as_completed
from collections import defaultdict, deque


class DependencyGraph:
    """
    Dependency graph for workflow steps.
    Supports topological sorting and parallel execution planning.
    """
    
    def __init__(self):
        """Initialize dependency graph."""
        self.nodes: Set[str] = set()
        self.edges: Dict[str, Set[str]] = defaultdict(set)  # node -> dependencies
        self.reverse_edges: Dict[str, Set[str]] = defaultdict(set)  # node -> dependents
    
    def add_node(self, node_id: str):
        """Add a node to the graph."""
        self.nodes.add(node_id)
    
    def add_dependency(self, node_id: str, depends_on: str):
        """
        Add dependency: node_id depends on depends_on.
        
        Args:
            node_id: Node that has dependency
            depends_on: Node that must complete first
        """
        self.nodes.add(node_id)
        self.nodes.add(depends_on)
        self.edges[node_id].add(depends_on)
        self.reverse_edges[depends_on].add(node_id)
    
    def get_dependencies(self, node_id: str) -> Set[str]:
        """Get all dependencies for a node."""
        return self.edges.get(node_id, set())
    
    def get_dependents(self, node_id: str) -> Set[str]:
        """Get all nodes that depend on this node."""
        return self.reverse_edges.get(node_id, set())
    
    def get_ready_nodes(self, completed: Set[str]) -> Set[str]:
        """
        Get nodes that are ready to execute (all dependencies completed).
        
        Args:
            completed: Set of completed node IDs
            
        Returns:
            Set of node IDs ready to execute
        """
        ready = set()
        for node in self.nodes:
            if node in completed:
                continue
            
            dependencies = self.get_dependencies(node)
            if dependencies.issubset(completed):
                ready.add(node)
        
        return ready
    
    def topological_sort(self) -> List[str]:
        """
        Perform topological sort using Kahn's algorithm.
        
        Returns:
            List of node IDs in topological order
            
        Raises:
            ValueError: If graph has cycles
        """
        # Calculate in-degrees
        in_degree = {node: len(self.edges.get(node, set())) for node in self.nodes}
        
        # Queue of nodes with no dependencies
        queue = deque([node for node, degree in in_degree.items() if degree == 0])
        
        result = []
        
        while queue:
            node = queue.popleft()
            result.append(node)
            
            # Reduce in-degree for dependents
            for dependent in self.get_dependents(node):
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)
        
        # Check for cycles
        if len(result) != len(self.nodes):
            raise ValueError("Dependency graph has cycles")
        
        return result
    
    def get_execution_levels(self) -> List[Set[str]]:
        """
        Get execution levels for parallel execution.
        Each level contains nodes that can execute in parallel.
        
        Returns:
            List of sets, where each set contains nodes that can run in parallel
        """
        levels = []
        completed = set()
        
        while len(completed) < len(self.nodes):
            ready = self.get_ready_nodes(completed)
            if not ready:
                raise ValueError("Dependency graph has cycles or unreachable nodes")
            
            levels.append(ready)
            completed.update(ready)
        
        return levels


class ParallelExecutor:
    """
    Parallel execution engine for workflow steps.
    Executes independent steps concurrently while respecting dependencies.
    """
    
    def __init__(self, max_workers: int = 4):
        """
        Initialize parallel executor.
        
        Args:
            max_workers: Maximum number of concurrent workers
        """
        self.max_workers = max_workers
        self.lock = threading.Lock()
        self.enabled = True
        
        # Execution state
        self.completed: Set[str] = set()
        self.failed: Set[str] = set()
        self.running: Set[str] = set()
        
        # Statistics
        self.total_executed = 0
        self.total_failed = 0
        self.execution_times: Dict[str, float] = {}
    
    def execute_graph(self, graph: DependencyGraph, 
                     executor_func: Callable[[str], Any],
                     on_complete: Optional[Callable[[str, Any], None]] = None,
                     on_error: Optional[Callable[[str, Exception], None]] = None) -> Dict[str, Any]:
        """
        Execute dependency graph in parallel.
        
        Args:
            graph: Dependency graph to execute
            executor_func: Function to execute for each node (takes node_id, returns result)
            on_complete: Optional callback when node completes (node_id, result)
            on_error: Optional callback when node fails (node_id, exception)
            
        Returns:
            Dictionary with execution results
        """
        if not self.enabled:
            raise RuntimeError("Parallel execution is disabled")
        
        # Reset state
        with self.lock:
            self.completed.clear()
            self.failed.clear()
            self.running.clear()
        
        results = {}
        start_time = datetime.now()
        
        # Get execution levels
        try:
            levels = graph.get_execution_levels()
        except ValueError as e:
            return {
                "success": False,
                "error": str(e),
                "completed": [],
                "failed": []
            }
        
        # Execute each level in parallel
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            for level_idx, level in enumerate(levels):
                print(f"Executing level {level_idx + 1}/{len(levels)}: {level}")
                
                # Submit all nodes in this level
                futures = {}
                for node_id in level:
                    with self.lock:
                        self.running.add(node_id)
                    
                    future = executor.submit(self._execute_node, node_id, executor_func)
                    futures[future] = node_id
                
                # Wait for all nodes in this level to complete
                for future in as_completed(futures):
                    node_id = futures[future]
                    
                    try:
                        result = future.result()
                        results[node_id] = result
                        
                        with self.lock:
                            self.completed.add(node_id)
                            self.running.discard(node_id)
                            self.total_executed += 1
                        
                        if on_complete:
                            on_complete(node_id, result)
                    
                    except Exception as e:
                        with self.lock:
                            self.failed.add(node_id)
                            self.running.discard(node_id)
                            self.total_failed += 1
                        
                        results[node_id] = {"error": str(e)}
                        
                        if on_error:
                            on_error(node_id, e)
                        else:
                            print(f"ERROR: Node {node_id} failed: {e}", file=sys.stderr)
                
                # If any node in this level failed, stop execution
                if self.failed:
                    break
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        return {
            "success": len(self.failed) == 0,
            "completed": list(self.completed),
            "failed": list(self.failed),
            "results": results,
            "duration_seconds": duration,
            "levels_executed": level_idx + 1,
            "total_levels": len(levels)
        }
    
    def _execute_node(self, node_id: str, executor_func: Callable[[str], Any]) -> Any:
        """
        Execute a single node.
        
        Args:
            node_id: Node to execute
            executor_func: Function to execute
            
        Returns:
            Execution result
        """
        start_time = datetime.now()
        
        try:
            result = executor_func(node_id)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            with self.lock:
                self.execution_times[node_id] = duration
            
            return result
        
        except Exception as e:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            with self.lock:
                self.execution_times[node_id] = duration
            
            raise
    
    def enable(self):
        """Enable parallel execution."""
        self.enabled = True
    
    def disable(self):
        """Disable parallel execution."""
        self.enabled = False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get execution statistics."""
        with self.lock:
            avg_time = sum(self.execution_times.values()) / len(self.execution_times) if self.execution_times else 0
            
            return {
                "enabled": self.enabled,
                "max_workers": self.max_workers,
                "total_executed": self.total_executed,
                "total_failed": self.total_failed,
                "currently_running": len(self.running),
                "average_execution_time": round(avg_time, 2),
                "execution_times": self.execution_times
            }


# Global singleton instance
_parallel_executor: Optional[ParallelExecutor] = None


def get_executor(max_workers: int = 4) -> ParallelExecutor:
    """
    Get global parallel executor instance (singleton).
    
    Args:
        max_workers: Maximum workers (only used on first call)
        
    Returns:
        ParallelExecutor instance
    """
    global _parallel_executor
    if _parallel_executor is None:
        _parallel_executor = ParallelExecutor(max_workers)
    return _parallel_executor


if __name__ == "__main__":
    # Test parallel executor
    print("Testing Parallel Executor...")
    print("="*80)
    
    # Create dependency graph
    graph = DependencyGraph()
    
    # Add nodes
    graph.add_node("step1")
    graph.add_node("step2")
    graph.add_node("step3")
    graph.add_node("step4")
    graph.add_node("step5")
    
    # Add dependencies
    # step3 depends on step1 and step2
    graph.add_dependency("step3", "step1")
    graph.add_dependency("step3", "step2")
    
    # step4 depends on step3
    graph.add_dependency("step4", "step3")
    
    # step5 depends on step2
    graph.add_dependency("step5", "step2")
    
    print("\nDependency Graph:")
    print("  step1 (no deps)")
    print("  step2 (no deps)")
    print("  step3 (depends on: step1, step2)")
    print("  step4 (depends on: step3)")
    print("  step5 (depends on: step2)")
    
    # Get execution levels
    levels = graph.get_execution_levels()
    print(f"\nExecution Levels: {len(levels)}")
    for idx, level in enumerate(levels):
        print(f"  Level {idx + 1}: {level}")
    
    # Define executor function
    import time
    import random
    
    def execute_step(step_id: str) -> Dict[str, Any]:
        """Simulate step execution."""
        duration = random.uniform(0.5, 1.5)
        print(f"  Executing {step_id}... (will take {duration:.2f}s)")
        time.sleep(duration)
        print(f"  ✓ {step_id} complete")
        return {"step_id": step_id, "status": "success", "duration": duration}
    
    # Execute graph
    print("\nExecuting graph in parallel...")
    executor = get_executor(max_workers=3)
    
    result = executor.execute_graph(
        graph,
        execute_step,
        on_complete=lambda node_id, result: print(f"  → {node_id} completed successfully"),
        on_error=lambda node_id, error: print(f"  → {node_id} failed: {error}")
    )
    
    print("\n" + "="*80)
    print("Execution Results:")
    print(f"  Success: {result['success']}")
    print(f"  Completed: {result['completed']}")
    print(f"  Failed: {result['failed']}")
    print(f"  Duration: {result['duration_seconds']:.2f}s")
    print(f"  Levels Executed: {result['levels_executed']}/{result['total_levels']}")
    
    print("\nExecutor Stats:")
    print(json.dumps(executor.get_stats(), indent=2))

