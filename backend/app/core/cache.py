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

    def get(self, key: Hashable, default: Any = None) -> Any:
        """Return a live entry without computing it, or ``default``.

        Used by the async services, where the value cannot be produced inside a
        synchronous ``get_or_set`` factory (the factory has to ``await``).
        """
        entry = self._store.get(key)
        if entry is None or (time.monotonic() - entry[0]) >= self._ttl:
            return default
        return entry[1]

    def set(self, key: Hashable, value: Any) -> None:
        if len(self._store) >= self._max_entries:
            self._store.clear()
        self._store[key] = (time.monotonic(), value)

    def clear(self) -> None:
        self._store.clear()
