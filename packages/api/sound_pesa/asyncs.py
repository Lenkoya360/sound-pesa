"""
Async helpers for running coroutines from synchronous (DRF) view code.

DRF's sync request handlers cannot hang on an awaited coroutine directly,
and creating a fresh event loop per request with ``asyncio.run()`` is both
wasteful and can fail when awaitables reference loop-bound state. Instead we
run coroutines on a single long-lived event loop that is created lazily and
reused for the lifetime of the process.
"""

import asyncio
import threading
from typing import Awaitable, TypeVar

import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


class _EventLoopRunner:
    """Owns a single event loop and dispatches coroutines onto it."""

    def __init__(self) -> None:
        self._loop: asyncio.AbstractEventLoop | None = None
        self._lock = threading.Lock()

    def _ensure_loop(self) -> asyncio.AbstractEventLoop:
        if self._loop is None or self._loop.is_closed():
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
        return self._loop

    def run(self, coro: Awaitable[T]) -> T:
        """Run an awaitable on the shared loop from a sync thread."""
        loop = self._ensure_loop()
        # Serialize access to the loop so concurrent request threads cannot
        # interleave run_until_complete calls on the same loop.
        with self._lock:
            return loop.run_until_complete(coro)


_runner = _EventLoopRunner()


def run_async(coro: Awaitable[T]) -> T:
    """
    Run an awaitable on the shared event loop and return its result.

    Safe to call from synchronous code such as DRF views and management
    commands. The underlying loop is reused across calls.
    """
    return _runner.run(coro)