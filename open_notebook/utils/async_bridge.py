"""
Async bridge utilities for calling async functions from sync contexts.

This module provides a thread-safe way to run async coroutines from synchronous
code, with proper timeout handling and resource cleanup.

Used primarily by LangGraph nodes (which run synchronously) to call async
functions like model provisioning.
"""

import asyncio
import concurrent.futures
from typing import Any, Callable, Coroutine, TypeVar

from loguru import logger

T = TypeVar("T")

# Global thread pool for running async code in separate threads
# ThreadPoolExecutor is thread-safe and can be shared across all callers
_bridge_executor: concurrent.futures.ThreadPoolExecutor | None = None


def get_bridge_executor() -> concurrent.futures.ThreadPoolExecutor:
    """
    Get the global thread pool executor for async bridge operations.

    Lazily initializes a ThreadPoolExecutor with a fixed number of workers.
    The executor is shared across all bridge calls to avoid creating/destroying
    threads repeatedly.

    Returns:
        ThreadPoolExecutor instance for running async code in threads.
    """
    global _bridge_executor
    if _bridge_executor is None:
        # Use min(32, os.cpu_count() + 4) as default, matching ThreadPoolExecutor default
        _bridge_executor = concurrent.futures.ThreadPoolExecutor(
            thread_name_prefix="async_bridge",
            max_workers=min(32, (asyncio.os.cpu_count() or 1) + 4),
        )
        logger.debug("Initialized global async bridge thread pool")
    return _bridge_executor


def shutdown_bridge_executor(wait: bool = True) -> None:
    """
    Shutdown the global thread pool executor.

    Call this during application shutdown to clean up resources.

    Args:
        wait: If True, wait for pending futures to complete before shutdown.
    """
    global _bridge_executor
    if _bridge_executor is not None:
        _bridge_executor.shutdown(wait=wait)
        _bridge_executor = None
        logger.debug("Shutdown async bridge thread pool")


def _run_coroutine_in_new_loop(coro: Callable[[], Coroutine[Any, Any, T]]) -> T:
    """
    Run a coroutine in a new event loop within the current thread.

    This function is designed to be called within a thread pool thread.
    It creates a new event loop, runs the coroutine to completion, and
    properly cleans up resources.

    Args:
        coro: A callable that returns a coroutine when called.

    Returns:
        The result of the coroutine.

    Raises:
        Any exception raised by the coroutine.
    """
    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro())
    finally:
        try:
            # Clean up any remaining tasks
            pending = asyncio.all_tasks(loop)
            if pending:
                for task in pending:
                    task.cancel()
                loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            loop.close()
        finally:
            asyncio.set_event_loop(None)


def await_bridge(
    coro_factory: Callable[[], Coroutine[Any, Any, T]],
    *,
    timeout: float | None = 30.0,
) -> T:
    """
    Bridge from sync code to async coroutine with timeout support.

    This function allows synchronous code (like LangGraph nodes) to call
    async functions safely without creating nested event loops or thread
    starvation issues.

    The function detects whether it's being called from within an event loop:
    - If in an event loop: Runs the coroutine in a thread pool thread
    - If not in an event loop: Runs the coroutine directly using asyncio.run()

    Args:
        coro_factory: A callable that returns a coroutine when called.
                     Use a lambda to capture arguments: `lambda: async_func(arg1, arg2)`
        timeout: Maximum time to wait for the coroutine to complete (in seconds).
                Default is 30.0. Set to None to disable timeout.

    Returns:
        The result of the coroutine.

    Raises:
        TimeoutError: If the coroutine doesn't complete within the specified timeout.
        Any exception raised by the coroutine.

    Example:
        # From sync context (e.g., LangGraph node)
        model = await_bridge(
            lambda: provision_langchain_model(content, model_id, "chat"),
            timeout=30.0
        )
    """
    try:
        # Check if we're already in an event loop
        asyncio.get_running_loop()
        # If we are, we need to run in a separate thread to avoid nested loop issues
        executor = get_bridge_executor()
        future = executor.submit(_run_coroutine_in_new_loop, coro_factory)
        return future.result(timeout=timeout)
    except RuntimeError:
        # No event loop running in this thread, safe to use asyncio.run()
        # Note: asyncio.run() doesn't support timeout directly, so we use wait_for
        async def run_with_timeout() -> T:
            coro = coro_factory()
            if timeout is not None:
                return await asyncio.wait_for(coro, timeout=timeout)
            return await coro

        return asyncio.run(run_with_timeout())


def await_bridge_simple(
    coro: Coroutine[Any, Any, T],
    *,
    timeout: float | None = 30.0,
) -> T:
    """
    Simplified version of await_bridge that accepts a coroutine directly.

    This is a convenience wrapper for cases where you already have a coroutine
    object. Note that the coroutine is NOT started until await_bridge is called.

    Args:
        coro: The coroutine to run.
        timeout: Maximum time to wait for completion (in seconds). Default 30.0.

    Returns:
        The result of the coroutine.

    Raises:
        TimeoutError: If the coroutine doesn't complete within the timeout.
        Any exception raised by the coroutine.

    Example:
        # From sync context
        result = await_bridge_simple(async_function(arg1, arg2), timeout=10.0)
    """
    # We need to capture the coroutine in a lambda to prevent it from being
    # started in the current event loop
    return await_bridge(lambda: coro, timeout=timeout)
