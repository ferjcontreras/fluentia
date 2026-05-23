"""Bedrock voice provider implementing BaseProvider."""

# pylint: disable=duplicate-code

import asyncio
import json
import logging
import time
from typing import Any

from fastapi import WebSocket
from fastapi import WebSocketDisconnect

from fluentia.config import BedrockProviderConfig
from fluentia.providers.base import BaseProvider
from fluentia.providers.base import SessionContext
from fluentia.providers.bedrock.client import NovaSonicClient
from fluentia.providers.bedrock.client import _InternalToolUseEvent
from fluentia.providers.bedrock.config import BedrockSessionConfig
from fluentia.session.events import SessionEvent
from fluentia.session.events import SessionEventType
from fluentia.tools import ToolProcessor
from fluentia.tools import ToolResult
from fluentia.tools import ToolState

logger: logging.Logger = logging.getLogger(__name__)


class BedrockProvider(BaseProvider):
    """AWS Bedrock Nova Sonic voice provider."""

    def __init__(
        self, provider_config: BedrockProviderConfig, tool_processor: ToolProcessor
    ) -> None:
        """Initialize the Bedrock provider."""
        self._provider_config: BedrockProviderConfig = provider_config
        self._tool_processor: ToolProcessor = tool_processor

    async def handle_session(self, websocket: WebSocket, session_context: SessionContext) -> None:
        """Run a complete Bedrock voice session."""
        agent_def = session_context.agent_definition
        prompt: str = agent_def.render_prompt()

        # Format tool specs for Bedrock (tools disabled for now)
        tool_specs: list[dict[str, Any]] = []
        logger.info("Bedrock tools disabled; skipping tool registration")

        # Create client
        session_config: BedrockSessionConfig = BedrockSessionConfig(
            region=self._provider_config.region,
            model_id=self._provider_config.model_id,
            voice_id=self._provider_config.voice_id,
            input_sample_rate=self._provider_config.input_sample_rate,
            output_sample_rate=self._provider_config.output_sample_rate,
            language=self._provider_config.language,
        )
        client: NovaSonicClient = NovaSonicClient(config=session_config)

        pending_tool_tasks: set[asyncio.Task[None]] = set()

        try:
            await client.connect(system_prompt=prompt, tool_specs=tool_specs)
            logger.info("Bedrock provider connected for session %s", session_context.session_id)

            async def upstream() -> None:
                """Receive audio from WebSocket and forward to Bedrock."""
                try:
                    while client.is_active:
                        message = await websocket.receive()
                        if "bytes" in message:
                            await client.send_audio(message["bytes"])
                except (WebSocketDisconnect, RuntimeError, asyncio.CancelledError):
                    pass

            async def downstream() -> None:
                """Receive events from Bedrock and emit as SessionEvents."""
                try:
                    async for event in client.receive_events():
                        if isinstance(event, _InternalToolUseEvent):
                            # Fire-and-forget: spawn tool execution as a background
                            # task so the event loop keeps processing audio and other
                            # events while the tool runs.  This matches the pattern
                            # used by the AWS Nova Sonic reference implementation.
                            task: asyncio.Task[None] = asyncio.create_task(
                                self._handle_tool_call(client, event, session_context)
                            )
                            pending_tool_tasks.add(task)
                            task.add_done_callback(pending_tool_tasks.discard)
                        elif isinstance(event, SessionEvent):
                            await session_context.emit(event)
                except (WebSocketDisconnect, RuntimeError, asyncio.CancelledError):
                    pass

            await asyncio.gather(upstream(), downstream())

        except (WebSocketDisconnect, asyncio.CancelledError):
            pass
        except Exception:
            logger.exception("Error in Bedrock session %s", session_context.session_id)
            await session_context.emit(
                SessionEvent(
                    type=SessionEventType.ERROR,
                    payload={
                        "code": "provider_error",
                        "message": "Bedrock session error",
                        "recoverable": False,
                    },
                )
            )
        finally:
            for task in pending_tool_tasks:
                task.cancel()
            await client.close()
            logger.info("Bedrock session ended: %s", session_context.session_id)

    def _format_tool_specs(self, enabled_tools: list[str]) -> list[dict[str, Any]]:
        """Format tool specs for Bedrock Nova Sonic API."""
        generic_specs: list[dict[str, Any]] = self._tool_processor.get_enabled_specs(enabled_tools)
        bedrock_specs: list[dict[str, Any]] = []
        for spec in generic_specs:
            bedrock_specs.append(
                {
                    "toolSpec": {
                        "name": spec["name"],
                        "description": spec["description"],
                        "inputSchema": {"json": json.dumps(spec["input_schema"])},
                    }
                }
            )
        return bedrock_specs

    async def _handle_tool_call(
        self, client: NovaSonicClient, event: _InternalToolUseEvent, session_context: SessionContext
    ) -> None:
        """Execute a tool and send the result back to Bedrock."""
        await session_context.emit(
            SessionEvent(
                type=SessionEventType.TOOL_STARTED,
                payload={
                    "tool_id": event.tool_use_id,
                    "tool_name": event.tool_name,
                    "message": f"Executing {event.tool_name}...",
                },
            )
        )

        start: float = time.monotonic()
        try:
            result: ToolResult = await self._tool_processor.execute(
                event.tool_name, event.tool_input
            )
            duration: float = time.monotonic() - start

            if result.state == ToolState.COMPLETED:
                await client.send_tool_result(event.tool_use_id, result.data or {})
                await session_context.emit(
                    SessionEvent(
                        type=SessionEventType.TOOL_COMPLETED,
                        payload={
                            "tool_id": event.tool_use_id,
                            "tool_name": event.tool_name,
                            "result": result.data or {},
                            "message": result.message or "Completed",
                            "duration": round(duration, 3),
                        },
                    )
                )
            else:
                error_result: dict[str, str] = {"error": result.message or "Tool failed"}
                await client.send_tool_result(event.tool_use_id, error_result)
                await session_context.emit(
                    SessionEvent(
                        type=SessionEventType.TOOL_FAILED,
                        payload={
                            "tool_id": event.tool_use_id,
                            "tool_name": event.tool_name,
                            "message": result.message or "Tool failed",
                        },
                    )
                )
        except KeyError:
            logger.error("Unknown tool: %s", event.tool_name)
            await client.send_tool_result(
                event.tool_use_id, {"error": f"Unknown tool: {event.tool_name}"}
            )
            await session_context.emit(
                SessionEvent(
                    type=SessionEventType.TOOL_FAILED,
                    payload={
                        "tool_id": event.tool_use_id,
                        "tool_name": event.tool_name,
                        "message": f"Unknown tool: {event.tool_name}",
                    },
                )
            )
        except Exception:
            logger.exception("Error executing tool %s", event.tool_name)
            try:
                await client.send_tool_result(
                    event.tool_use_id, {"error": f"Tool execution failed: {event.tool_name}"}
                )
                await session_context.emit(
                    SessionEvent(
                        type=SessionEventType.TOOL_FAILED,
                        payload={
                            "tool_id": event.tool_use_id,
                            "tool_name": event.tool_name,
                            "message": f"Tool execution failed: {event.tool_name}",
                        },
                    )
                )
            except Exception:
                logger.exception("Failed to send tool error response")
