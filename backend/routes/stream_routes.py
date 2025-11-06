"""
WebSocket Stream Routes for FR#020 Interactive Agent Dashboard

Provides real-time streaming of agent workflow events via WebSocket.
"""

import asyncio
import logging
import time
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from typing import Optional
import uuid

from backend.models.stream_event_model import (
    WorkflowStreamRequest,
    WorkflowStreamResponse,
    ErrorType,
)
from backend.services.event_emitter import get_event_emitter_manager
from backend.agents.orchestrator_agent import OrchestratorAgent
from backend.models.context_model import SessionContext

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["streaming"])


@router.websocket("/navigate/stream")
async def stream_workflow(websocket: WebSocket):
    """
    WebSocket endpoint for real-time streaming of multi-agent workflow.

    Flow:
    1. Client connects with document
    2. Backend initializes orchestrator workflow
    3. Events are streamed as each agent processes
    4. Client receives real-time updates
    5. Final results sent when complete

    Expected client message format:
    {
        "document": "content to analyze",
        "content_type": "document|codebase",
        "include_metadata": true,
        "include_partial_results": true
    }
    """

    session_id = f"session_{uuid.uuid4().hex[:12]}"
    emitter_manager = get_event_emitter_manager()
    emitter = emitter_manager.create_emitter(session_id)

    logger.info(f"🔌 WebSocket connection initiated: {session_id}")

    try:
        # Accept the WebSocket connection
        await websocket.accept()
        logger.info(f"✅ WebSocket accepted: {session_id}")

        # Register client for event streaming
        client_queue = asyncio.Queue()
        emitter.register_client(client_queue)

        # Start background task to send events to client
        send_task = asyncio.create_task(_send_events_to_client(websocket, client_queue, session_id))

        try:
            # Receive initial request from client
            data = await websocket.receive_json()
            logger.debug(f"📨 Received data from client: {session_id}")

            # Validate request
            try:
                request = WorkflowStreamRequest(**data)
            except ValueError as e:
                logger.error(f"❌ Invalid request: {e}")
                error_event = {
                    "status": "error",
                    "payload": {
                        "error": "ValidationError",
                        "error_details": str(e),
                        "recoverable": False,
                    },
                }
                await websocket.send_json(error_event)
                return

            # Start workflow in background
            workflow_task = asyncio.create_task(
                _execute_stream_workflow(
                    session_id, request.document, request.content_type, emitter
                )
            )

            # Handle client commands
            while not workflow_task.done():
                try:
                    # Wait for client message or workflow completion
                    done, pending = await asyncio.wait(
                        [asyncio.create_task(websocket.receive_json()), workflow_task],
                        return_when=asyncio.FIRST_COMPLETED,
                        timeout=60.0,
                    )

                    # Check if workflow is done
                    if workflow_task in done:
                        logger.info(f"✅ Workflow completed: {session_id}")
                        break

                    # Process client command
                    for task in done:
                        if task != workflow_task:
                            try:
                                command = await task
                                await _handle_client_command(command, workflow_task, session_id)
                            except asyncio.TimeoutError:
                                logger.debug(f"⏱️  Client receive timeout: {session_id}")
                            except Exception as e:
                                logger.error(f"❌ Error processing command: {e}")

                except asyncio.TimeoutError:
                    logger.debug(f"⏱️  WebSocket timeout: {session_id}")
                    continue
                except Exception as e:
                    logger.error(f"❌ Error in event loop: {e}")
                    break

            # Wait for workflow to actually complete
            try:
                await asyncio.wait_for(workflow_task, timeout=300.0)
            except asyncio.TimeoutError:
                logger.error(f"❌ Workflow timeout: {session_id}")
                error_event = {
                    "status": "error",
                    "payload": {
                        "error": "WorkflowTimeout",
                        "error_details": "Workflow exceeded maximum execution time",
                        "recoverable": False,
                    },
                }
                await websocket.send_json(error_event)

        except WebSocketDisconnect:
            logger.info(f"🔌 Client disconnected: {session_id}")
        except Exception as e:
            logger.error(f"❌ WebSocket error: {e}")
            try:
                await websocket.send_json(
                    {
                        "status": "error",
                        "payload": {
                            "error": "InternalServerError",
                            "error_details": str(e),
                            "recoverable": False,
                        },
                    }
                )
            except Exception:
                pass
        finally:
            # Cleanup
            send_task.cancel()
            try:
                await send_task
            except asyncio.CancelledError:
                pass

    finally:
        # Unregister client and cleanup
        emitter.unregister_client(client_queue)
        emitter_manager.remove_emitter(session_id)
        logger.info(f"🧹 Cleaned up session: {session_id}")


async def _send_events_to_client(
    websocket: WebSocket, client_queue: asyncio.Queue, session_id: str
) -> None:
    """
    Background task that sends events from emitter to WebSocket client.

    Args:
        websocket: WebSocket connection to client
        client_queue: Queue containing events from emitter
        session_id: Session identifier for logging
    """
    try:
        while True:
            try:
                # Wait for event with timeout
                event = await asyncio.wait_for(
                    client_queue.get(), timeout=300.0  # 5 minute timeout
                )

                # Send event to client
                await websocket.send_json(event)
                logger.debug(f"📤 Event sent to client: {session_id}")

            except asyncio.TimeoutError:
                logger.warning(f"⏱️  Event queue timeout: {session_id}")
                break
            except Exception as e:
                logger.error(f"❌ Error sending event: {e}")
                break

    except asyncio.CancelledError:
        logger.debug(f"📛 Send task cancelled: {session_id}")
    except Exception as e:
        logger.error(f"❌ Error in send_events task: {e}")


async def _execute_stream_workflow(
    session_id: str, document: str, content_type: str, emitter
) -> None:
    """
    Execute the multi-agent workflow with event streaming.

    Args:
        session_id: Session identifier
        document: Document to analyze
        content_type: Type of content ("document" or "codebase")
        emitter: EventEmitter instance for sending events
    """
    try:
        logger.info(f"🚀 Starting workflow: {session_id}")
        start_time = time.time()

        # Create orchestrator with event emitter
        orchestrator = OrchestratorAgent(event_emitter=emitter)

        # Create session context
        context = SessionContext(
            session_id=session_id, content_type=content_type, raw_input=document
        )

        # Emit orchestrator queued event
        await emitter.emit_agent_queued(agent="orchestrator", step=1)

        # Emit orchestrator processing event
        await emitter.emit_agent_processing(
            agent="orchestrator", step=1, partial_results={"status": "initializing workflow"}
        )

        # Execute workflow through orchestrator
        # The orchestrator will emit events for each agent
        result_context = await orchestrator.execute_workflow(context)

        # Emit final complete event
        elapsed_seconds = time.time() - start_time
        await emitter.emit_agent_complete(
            agent="visualizer",
            step=4,
            summary=result_context.summary_text,
            entities=result_context.key_entities,
            relationships=(
                [r.model_dump() for r in result_context.relationships]
                if result_context.relationships
                else None
            ),
            visualization=result_context.graph_json,
            metrics={
                "total_execution_time_seconds": elapsed_seconds,
                "session_id": session_id,
                "status": "workflow_complete",
            },
        )

        logger.info(f"✅ Workflow completed successfully: {session_id} ({elapsed_seconds:.2f}s)")

    except asyncio.CancelledError:
        logger.info(f"📛 Workflow cancelled: {session_id}")
    except Exception as e:
        logger.error(f"❌ Workflow error: {e}", exc_info=True)

        # Emit error event
        try:
            await emitter.emit_agent_error(
                agent="orchestrator",
                step=1,
                error=type(e).__name__,
                error_type=ErrorType.WORKFLOW_ERROR,
                error_details=str(e),
                recoverable=False,
            )
        except Exception as emit_error:
            logger.error(f"❌ Failed to emit error event: {emit_error}")


async def _handle_client_command(
    command: dict, workflow_task: asyncio.Task, session_id: str
) -> None:
    """
    Handle commands sent by client during workflow.

    Args:
        command: Client command dictionary
        workflow_task: The running workflow task
        session_id: Session identifier
    """
    action = command.get("action")
    reason = command.get("reason", "No reason provided")

    logger.info(f"📋 Client command: {action} - {reason} ({session_id})")

    if action == "cancel":
        logger.info(f"🛑 Cancelling workflow: {session_id}")
        workflow_task.cancel()
    elif action == "pause":
        logger.info(f"⏸️  Pause requested: {session_id}")
        # Pause handling would require coordination with agents
        # For now, just log the request
    elif action == "resume":
        logger.info(f"▶️  Resume requested: {session_id}")
        # Resume handling would require coordination with agents
        # For now, just log the request
    else:
        logger.warning(f"⚠️  Unknown command: {action}")


@router.get("/stream/stats")
async def get_stream_stats():
    """
    Get statistics about all active streaming sessions.

    Returns:
        Dictionary with stats for each session
    """
    emitter_manager = get_event_emitter_manager()
    stats = emitter_manager.get_all_stats()

    return {"active_sessions": len(stats), "sessions": stats, "timestamp": time.time()}


@router.get("/stream/stats/{session_id}")
async def get_session_stats(session_id: str):
    """
    Get statistics for a specific session.

    Args:
        session_id: Session identifier

    Returns:
        Statistics for the session

    Raises:
        HTTPException: If session not found
    """
    emitter_manager = get_event_emitter_manager()
    emitter = emitter_manager.get_emitter(session_id)

    if not emitter:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "session_id": session_id,
        "stats": emitter.get_stats(),
        "events": emitter.get_event_history(),
    }


@router.post("/stream/cleanup")
async def cleanup_inactive_streams(max_age_seconds: int = 3600):
    """
    Clean up inactive streaming sessions.

    Args:
        max_age_seconds: Maximum age of session in seconds

    Returns:
        Number of sessions removed
    """
    emitter_manager = get_event_emitter_manager()
    removed = emitter_manager.cleanup_inactive_emitters(max_age_ms=max_age_seconds * 1000)

    return {"sessions_removed": removed, "max_age_seconds": max_age_seconds}
