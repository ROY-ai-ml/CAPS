"""WebSocket and Server-Sent Events Real-Time Streaming Endpoints."""
import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse

from app.core.events import event_bus
from app.core.logging import logger

router = APIRouter(tags=["Streaming"])


@router.websocket("/ws/tasks/{task_id}")
async def websocket_task_stream(websocket: WebSocket, task_id: str):
    """
    Real-time bidirectional WebSocket stream for specific task updates.
    Pushes state changes, live stdout, diagnosis, and validation events.
    """
    await websocket.accept()
    queue = await event_bus.subscribe(task_id)
    logger.info(f"WebSocket client connected to task {task_id}")

    try:
        while True:
            event = await queue.get()
            await websocket.send_json(event)
    except WebSocketDisconnect:
        logger.info(f"WebSocket client disconnected from task {task_id}")
    except Exception as e:
        logger.error(f"WebSocket error for task {task_id}: {e}")
    finally:
        await event_bus.unsubscribe(task_id, queue)


@router.websocket("/ws/tasks")
async def websocket_global_stream(websocket: WebSocket):
    """
    Global WebSocket stream for live platform dashboard events.
    """
    await websocket.accept()
    queue = await event_bus.subscribe_global()
    logger.info("WebSocket client connected to global dashboard feed")

    try:
        while True:
            event = await queue.get()
            await websocket.send_json(event)
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected from global feed")
    except Exception as e:
        logger.error(f"Global WebSocket error: {e}")
    finally:
        await event_bus.unsubscribe("global", queue)


@router.get("/stream/tasks/{task_id}")
async def sse_task_stream(task_id: str):
    """
    Server-Sent Events (SSE) fallback stream for task updates.
    """
    async def event_generator():
        queue = await event_bus.subscribe(task_id)
        try:
            while True:
                event = await queue.get()
                yield f"data: {json.dumps(event)}\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            await event_bus.unsubscribe(task_id, queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )
