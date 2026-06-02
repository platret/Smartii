#!/usr/bin/env python3
"""
Caching Layer for agenthero-ai workflow.
In-memory cache for settings.json and topic state to reduce I/O.

Phase 2 - Advanced Features
"""

import json
import sys
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import threading
import hashlib


class CacheEntry:
    """Represents a cached item with TTL and metadata."""
    
    def __init__(self, key: str, value: Any, ttl_seconds: int = 300):
        """
        Initialize cache entry.
        
        Args:
            key: Cache key
            value: Cached value
            ttl_seconds: Time-to-live in seconds (default: 5 minutes)
        """
        self.key = key
        self.value = value
        self.ttl_seconds = ttl_seconds
        self.created_at = datetime.now()
        self.last_accessed = datetime.now()
        self.access_count = 0
        self.file_hash: Optional[str] = None
    
    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        if self.ttl_seconds == 0:
            return False  # Never expires
        
        elapsed = (datetime.now() - self.created_at).total_seconds()
        return elapsed >= self.ttl_seconds
    
    def access(self) -> Any:
        """Access cached value and update metadata."""
        self.last_accessed = datetime.now()
        self.access_count += 1
        return self.value
    
    def update(self, value: Any):
        """Update cached value and reset TTL."""
        self.value = value
        self.created_at = datetime.now()
        self.last_accessed = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for stats."""
        return {
            "key": self.key,
            "ttl_seconds": self.ttl_seconds,
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat(),
            "access_count": self.access_count,
            "is_expired": self.is_expired(),
            "file_hash": self.file_hash
        }


class WorkflowCache:
    """
    In-memory cache for workflow data.
    Thread-safe with TTL and file hash validation.
    """
    
    def __init__(self):
        """Initialize cache."""
        self.cache: Dict[str, CacheEntry] = {}
        self.lock = threading.Lock()
        self.enabled = True
        
        # Cache statistics
        self.hits = 0
        self.misses = 0
        self.invalidations = 0
        
        # Default TTLs (in seconds)
        self.default_ttls = {
            "settings": 300,      # 5 minutes
            "topic_state": 60,    # 1 minute
            "workflow_status": 30 # 30 seconds
        }
    
    def _compute_file_hash(self, file_path: Path) -> Optional[str]:
        """
        Compute MD5 hash of file for cache invalidation.
        
        Args:
            file_path: Path to file
            
        Returns:
            MD5 hash string or None if file doesn't exist
        """
        try:
            if not file_path.exists():
                return None
            
            md5 = hashlib.md5()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    md5.update(chunk)
            return md5.hexdigest()
        except Exception:
            return None
    
    def get(self, key: str, file_path: Optional[Path] = None) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            file_path: Optional file path for hash validation
            
        Returns:
            Cached value or None if not found/expired/invalid
        """
        if not self.enabled:
            return None
        
        with self.lock:
            if key not in self.cache:
                self.misses += 1
                return None
            
            entry = self.cache[key]
            
            # Check if expired
            if entry.is_expired():
                del self.cache[key]
                self.misses += 1
                self.invalidations += 1
                return None
            
            # Check file hash if provided
            if file_path and entry.file_hash:
                current_hash = self._compute_file_hash(file_path)
                if current_hash != entry.file_hash:
                    # File changed, invalidate cache
                    del self.cache[key]
                    self.misses += 1
                    self.invalidations += 1
                    return None
            
            # Cache hit
            self.hits += 1
            return entry.access()
    
    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None, 
            file_path: Optional[Path] = None):
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Optional TTL override
            file_path: Optional file path for hash tracking
        """
        if not self.enabled:
            return
        
        with self.lock:
            # Determine TTL
            if ttl_seconds is None:
                # Try to infer from key
                for key_type, default_ttl in self.default_ttls.items():
                    if key_type in key:
                        ttl_seconds = default_ttl
                        break
                else:
                    ttl_seconds = 300  # Default 5 minutes
            
            # Create entry
            entry = CacheEntry(key, value, ttl_seconds)
            
            # Compute file hash if provided
            if file_path:
                entry.file_hash = self._compute_file_hash(file_path)
            
            self.cache[key] = entry
    
    def invalidate(self, key: str):
        """
        Invalidate specific cache entry.
        
        Args:
            key: Cache key to invalidate
        """
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                self.invalidations += 1
    
    def invalidate_pattern(self, pattern: str):
        """
        Invalidate all cache entries matching pattern.
        
        Args:
            pattern: Pattern to match (substring)
        """
        with self.lock:
            keys_to_delete = [k for k in self.cache.keys() if pattern in k]
            for key in keys_to_delete:
                del self.cache[key]
                self.invalidations += 1
    
    def clear(self):
        """Clear entire cache."""
        with self.lock:
            count = len(self.cache)
            self.cache.clear()
            self.invalidations += count
    
    def enable(self):
        """Enable caching."""
        self.enabled = True
    
    def disable(self):
        """Disable caching."""
        self.enabled = False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self.lock:
            total_requests = self.hits + self.misses
            hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
            
            return {
                "enabled": self.enabled,
                "entries": len(self.cache),
                "hits": self.hits,
                "misses": self.misses,
                "invalidations": self.invalidations,
                "total_requests": total_requests,
                "hit_rate_percent": round(hit_rate, 2),
                "cache_entries": [entry.to_dict() for entry in self.cache.values()]
            }
    
    def reset_stats(self):
        """Reset cache statistics."""
        with self.lock:
            self.hits = 0
            self.misses = 0
            self.invalidations = 0


# Global singleton instance
_workflow_cache: Optional[WorkflowCache] = None


def get_cache() -> WorkflowCache:
    """
    Get global cache instance (singleton).
    
    Returns:
        WorkflowCache instance
    """
    global _workflow_cache
    if _workflow_cache is None:
        _workflow_cache = WorkflowCache()
    return _workflow_cache


# Convenience functions for workflow_manager.py integration
def cache_settings(settings: Dict[str, Any], settings_path: Path):
    """Cache settings.json data."""
    cache = get_cache()
    cache.set("settings", settings, file_path=settings_path)


def get_cached_settings(settings_path: Path) -> Optional[Dict[str, Any]]:
    """Get cached settings.json data."""
    cache = get_cache()
    return cache.get("settings", file_path=settings_path)


def cache_topic_state(topic_slug: str, topic_data: Dict[str, Any], topic_file: Path):
    """Cache topic state data."""
    cache = get_cache()
    cache.set(f"topic_state:{topic_slug}", topic_data, file_path=topic_file)


def get_cached_topic_state(topic_slug: str, topic_file: Path) -> Optional[Dict[str, Any]]:
    """Get cached topic state data."""
    cache = get_cache()
    return cache.get(f"topic_state:{topic_slug}", file_path=topic_file)


def invalidate_topic_cache(topic_slug: str):
    """Invalidate all cache entries for a topic."""
    cache = get_cache()
    cache.invalidate_pattern(f"topic_state:{topic_slug}")


if __name__ == "__main__":
    # Test caching layer
    print("Testing Workflow Cache...")
    print("="*80)
    
    cache = get_cache()
    
    # Test 1: Basic set/get
    print("\n1. Basic Set/Get")
    cache.set("test_key", {"data": "test_value"}, ttl_seconds=10)
    result = cache.get("test_key")
    print(f"  Set: {{'data': 'test_value'}}")
    print(f"  Get: {result}")
    print(f"  ✓ Match: {result == {'data': 'test_value'}}")
    
    # Test 2: TTL expiration
    print("\n2. TTL Expiration")
    cache.set("expire_key", "will_expire", ttl_seconds=1)
    print(f"  Set with TTL=1s")
    import time
    time.sleep(2)
    result = cache.get("expire_key")
    print(f"  Get after 2s: {result}")
    print(f"  ✓ Expired: {result is None}")
    
    # Test 3: File hash validation
    print("\n3. File Hash Validation")
    test_file = Path("test_cache_file.json")
    test_file.write_text('{"version": 1}')
    
    cache.set("file_key", {"version": 1}, file_path=test_file)
    result1 = cache.get("file_key", file_path=test_file)
    print(f"  Initial get: {result1}")
    
    # Modify file
    test_file.write_text('{"version": 2}')
    result2 = cache.get("file_key", file_path=test_file)
    print(f"  After file change: {result2}")
    print(f"  ✓ Invalidated: {result2 is None}")
    
    test_file.unlink()  # Cleanup
    
    # Test 4: Pattern invalidation
    print("\n4. Pattern Invalidation")
    cache.set("topic_state:topic1", {"data": 1})
    cache.set("topic_state:topic2", {"data": 2})
    cache.set("other_key", {"data": 3})
    
    print(f"  Set 3 keys (2 with 'topic_state:' prefix)")
    cache.invalidate_pattern("topic_state:")
    
    r1 = cache.get("topic_state:topic1")
    r2 = cache.get("topic_state:topic2")
    r3 = cache.get("other_key")
    print(f"  After invalidate_pattern('topic_state:'):")
    print(f"    topic_state:topic1: {r1}")
    print(f"    topic_state:topic2: {r2}")
    print(f"    other_key: {r3}")
    print(f"  ✓ Pattern invalidated: {r1 is None and r2 is None and r3 is not None}")
    
    # Test 5: Statistics
    print("\n5. Cache Statistics")
    stats = cache.get_stats()
    print(f"  Hits: {stats['hits']}")
    print(f"  Misses: {stats['misses']}")
    print(f"  Hit Rate: {stats['hit_rate_percent']}%")
    print(f"  Invalidations: {stats['invalidations']}")
    
    print("\n" + "="*80)
    print("Cache Test Complete!")

