# backend/streaming_steps.py
"""
Real-time step streaming for orchestrator progress
"""

import asyncio
from typing import Dict, Any
from collections import defaultdict

# Global dictionary to store step queues per session
_step_queues: Dict[str, asyncio.Queue] = {}


def ensure_step_queue(session_id: str) -> asyncio.Queue:
    """Get existing step queue or create a new one for a session"""
    if session_id not in _step_queues:
        _step_queues[session_id] = asyncio.Queue()
    return _step_queues[session_id]


def get_step_queue(session_id: str) -> asyncio.Queue:
    """Get the step queue for a session"""
    return _step_queues.get(session_id)


def emit_step(session_id: str, step: Dict[str, Any]):
    """Emit a step to the queue for streaming"""
    queue = _step_queues.get(session_id)
    if queue:
        try:
            queue.put_nowait(step)
        except asyncio.QueueFull:
            pass  # Skip if queue is full


def cleanup_queue(session_id: str):
    """Clean up the queue after streaming is complete"""
    if session_id in _step_queues:
        del _step_queues[session_id]


async def stream_steps(session_id: str, timeout: int = 300):
    """
    Stream steps from the queue
    
    Yields step dictionaries as they are added to the queue
    """
    # Ensure queue exists even if search hasn't started yet
    queue = ensure_step_queue(session_id)
    
    start_time = asyncio.get_event_loop().time()
    
    while True:
        try:
            # Check timeout
            if asyncio.get_event_loop().time() - start_time > timeout:
                yield {"type": "timeout", "message": "Step streaming timed out"}
                break
            
            # Try to get a step from the queue
            step = await asyncio.wait_for(queue.get(), timeout=1.0)
            
            # Check for completion sentinel
            if step.get("type") == "complete":
                yield step
                break
            
            yield step
            
        except asyncio.TimeoutError:
            # No step available, continue waiting
            continue
        except Exception as e:
            yield {"type": "error", "message": str(e)}
            break
    
    # Cleanup
    cleanup_queue(session_id)
