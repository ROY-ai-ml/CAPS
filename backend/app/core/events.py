"""Asynchronous In-Memory Event Bus for Real-time Task Updates."""
import asyncio
from collections import defaultdict
from typing import Any, Callable, Dict, List, Set

from app.core.logging import logger


class EventBus:
    """Pub/Sub broker routing execution events to connected WebSocket clients and workers."""

    def __init__(self):
        self._subscribers: Dict[str, Set[asyncio.Queue]] = defaultdict(set)
        self._global_subscribers: Set[asyncio.Queue] = set()
        self._lock = asyncio.Lock()

    async def subscribe(self, task_id: str) -> asyncio.Queue:
        """Subscribe to a specific task's events."""
        queue: asyncio.Queue = asyncio.Queue()
        async with self._lock:
            self._subscribers[task_id].add(queue)
        return queue

    async def subscribe_global(self) -> asyncio.Queue:
        """Subscribe to all task events (for dashboard-level feeds)."""
        queue: asyncio.Queue = asyncio.Queue()
        async with self._lock:
            self._global_subscribers.add(queue)
        return queue

    async def unsubscribe(self, task_id: str, queue: asyncio.Queue):
        """Unsubscribe a client queue."""
        async with self._lock:
            if queue in self._subscribers[task_id]:
                self._subscribers[task_id].remove(queue)
            if queue in self._global_subscribers:
                self._global_subscribers.remove(queue)

    async def publish(self, task_id: str, event: Dict[str, Any]):
        """Publish an event to all subscribers."""
        async with self._lock:
            target_queues = list(self._subscribers[task_id])
            global_queues = list(self._global_subscribers)

        for q in target_queues + global_queues:
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                logger.warning(f"Queue full for task {task_id}, dropping event: {event.get('type')}")


event_bus = EventBus()
