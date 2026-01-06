"""
VANTAGE LRU Thumbnail Cache

Memory-efficient caching system for thumbnail images.
Implements LRU (Least Recently Used) eviction policy.
"""

from collections import OrderedDict
from typing import Optional, Tuple
import numpy as np
from dataclasses import dataclass
import threading

from config.constants import THUMBNAIL_CACHE_SIZE, THUMBNAIL_CACHE_MB


@dataclass
class CacheEntry:
    """Single cache entry with metadata."""
    thumbnail: np.ndarray
    size_bytes: int
    path: str


class ThumbnailCache:
    """
    LRU-based thumbnail cache for memory-efficient image handling.
    
    Maintains thumbnails in memory for visible images only,
    automatically evicting least recently used entries when
    cache limits are exceeded.
    
    Thread-safe for concurrent access from UI and worker threads.
    """
    
    def __init__(
        self,
        max_items: int = THUMBNAIL_CACHE_SIZE,
        max_memory_mb: int = THUMBNAIL_CACHE_MB
    ):
        """
        Initialize the cache.
        
        Args:
            max_items: Maximum number of thumbnails to cache
            max_memory_mb: Maximum memory usage in megabytes
        """
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._max_items = max_items
        self._max_memory = max_memory_mb * 1024 * 1024  # Convert to bytes
        self._current_memory = 0
        self._lock = threading.RLock()
        
        # Statistics
        self._hits = 0
        self._misses = 0
    
    def get(self, path: str) -> Optional[np.ndarray]:
        """
        Retrieve a thumbnail from cache.
        
        Args:
            path: Image file path (cache key)
            
        Returns:
            Thumbnail numpy array if cached, None otherwise
        """
        with self._lock:
            if path in self._cache:
                # Move to end (most recently used)
                self._cache.move_to_end(path)
                self._hits += 1
                return self._cache[path].thumbnail
            
            self._misses += 1
            return None
    
    def put(self, path: str, thumbnail: np.ndarray) -> None:
        """
        Add a thumbnail to cache.
        
        Args:
            path: Image file path (cache key)
            thumbnail: Thumbnail image as numpy array
        """
        with self._lock:
            # Calculate size
            size_bytes = thumbnail.nbytes
            
            # Remove existing entry if present
            if path in self._cache:
                old_entry = self._cache.pop(path)
                self._current_memory -= old_entry.size_bytes
            
            # Evict entries if needed
            self._evict_if_needed(size_bytes)
            
            # Add new entry
            entry = CacheEntry(
                thumbnail=thumbnail,
                size_bytes=size_bytes,
                path=path
            )
            self._cache[path] = entry
            self._current_memory += size_bytes
    
    def _evict_if_needed(self, incoming_size: int) -> None:
        """Evict oldest entries until cache limits are satisfied."""
        # Evict by count
        while len(self._cache) >= self._max_items:
            self._evict_oldest()
        
        # Evict by memory
        while (self._current_memory + incoming_size) > self._max_memory and self._cache:
            self._evict_oldest()
    
    def _evict_oldest(self) -> None:
        """Remove the least recently used entry."""
        if self._cache:
            _, entry = self._cache.popitem(last=False)
            self._current_memory -= entry.size_bytes
    
    def remove(self, path: str) -> bool:
        """
        Remove a specific entry from cache.
        
        Args:
            path: Image file path to remove
            
        Returns:
            True if entry was removed, False if not found
        """
        with self._lock:
            if path in self._cache:
                entry = self._cache.pop(path)
                self._current_memory -= entry.size_bytes
                return True
            return False
    
    def clear(self) -> None:
        """Clear all cached thumbnails."""
        with self._lock:
            self._cache.clear()
            self._current_memory = 0
    
    def contains(self, path: str) -> bool:
        """Check if a path is in the cache."""
        with self._lock:
            return path in self._cache
    
    @property
    def size(self) -> int:
        """Current number of cached items."""
        return len(self._cache)
    
    @property
    def memory_usage_mb(self) -> float:
        """Current memory usage in MB."""
        return self._current_memory / (1024 * 1024)
    
    @property
    def stats(self) -> dict:
        """Cache statistics."""
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0
        
        return {
            'items': len(self._cache),
            'memory_mb': self.memory_usage_mb,
            'max_items': self._max_items,
            'max_memory_mb': self._max_memory / (1024 * 1024),
            'hits': self._hits,
            'misses': self._misses,
            'hit_rate': hit_rate,
        }
