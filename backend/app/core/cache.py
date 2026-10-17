"""Tiny in-memory TTL cache used to avoid recomputing aggregated series."""

from __future__ import annotations

import time
from typing import Any, Callable, Hashable


class TTLCache:
    def __init__(self, ttl_seconds: float, max_entries: int = 256) -> None:
        self._ttl = ttl_seconds
        self._max_entries = max_entries
        self._store: dict[Hashable, tuple[float, Any]] = {}

    def get_or_set(self, key: Hashable, factory: Callable[[], Any]) -> Any:
        now = time.monotonic()
        entry = self._store.get(key)
        if entry is not None and (now - entry[0]) < self._ttl:
            return entry[1]

        value = factory()
        if len(self._store) >= self._max_entries:
            self._store.clear()
        self._store[key] = (now, value)
        return value

    def clear(self) -> None:
        self._store.clear()
