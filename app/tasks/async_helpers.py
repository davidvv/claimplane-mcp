"""
Shared async utilities for Celery tasks.

This module provides a centralized run_async helper to avoid duplication
across all task files.
"""
import asyncio
import logging

logger = logging.getLogger(__name__)


def run_async(coro):
    """
    Helper function to run async code in Celery tasks.
    
    Creates a new event loop, runs the coroutine, and ensures proper cleanup
    of all pending tasks before closing the loop.
    
    Args:
        coro: Coroutine to execute
        
    Returns:
        Result of the coroutine
        
    Example:
        result = run_async(my_async_function(arg1, arg2))
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        # Clean up any pending tasks to prevent resource leaks
        pending = asyncio.all_tasks(loop)
        for task in pending:
            task.cancel()
            logger.debug(f"Cancelled pending task: {task.get_name()}")
        
        # Run one more iteration to handle cancellations gracefully
        if pending:
            loop.run_until_complete(
                asyncio.gather(*pending, return_exceptions=True)
            )
        
        # Close the loop to free resources
        loop.close()
        
        # Reset event loop to None to prevent accidental reuse
        asyncio.set_event_loop(None)
