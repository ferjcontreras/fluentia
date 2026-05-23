"""Google ADK tool wrapper factory."""

import logging
from collections.abc import Awaitable
from collections.abc import Callable
from typing import Any
from uuid import uuid4

from fluentia.session.events import SessionEvent
from fluentia.session.events import SessionEventType
from fluentia.tools.base import BaseTool
from fluentia.tools.state import ToolResult
from fluentia.tools.state import ToolState

logger: logging.Logger = logging.getLogger(__name__)


def create_adk_tool_wrapper(
    tool: BaseTool, emit: Callable[[SessionEvent], Awaitable[None]]
) -> Callable[..., Awaitable[dict[str, Any]]]:
    """Create an ADK-compatible async function that wraps a BaseTool.

    The returned function uses **kwargs so ADK can call it with keyword
    arguments matching the tool's input_schema.  It emits TOOL_STARTED
    before execution and TOOL_COMPLETED or TOOL_FAILED after.
    """

    async def tool_wrapper(**kwargs: Any) -> dict[str, Any]:
        tool_use_id: str = str(uuid4())

        await emit(
            SessionEvent(
                type=SessionEventType.TOOL_STARTED,
                payload={"tool_id": tool_use_id, "tool_name": tool.name},
            )
        )

        try:
            result: ToolResult = await tool.execute(kwargs)

            if result.state == ToolState.COMPLETED:
                await emit(
                    SessionEvent(
                        type=SessionEventType.TOOL_COMPLETED,
                        payload={
                            "tool_id": tool_use_id,
                            "tool_name": tool.name,
                            "result": result.data or {},
                        },
                    )
                )
                return result.data or {}

            error_msg: str = result.message or "Tool execution failed"
            await emit(
                SessionEvent(
                    type=SessionEventType.TOOL_FAILED,
                    payload={"tool_id": tool_use_id, "tool_name": tool.name, "error": error_msg},
                )
            )
            return {"error": error_msg}

        except Exception as exc:
            logger.exception("Error executing tool %s via ADK wrapper", tool.name)
            await emit(
                SessionEvent(
                    type=SessionEventType.TOOL_FAILED,
                    payload={"tool_id": tool_use_id, "tool_name": tool.name, "error": str(exc)},
                )
            )
            return {"error": str(exc)}

    tool_wrapper.__name__ = tool.name
    tool_wrapper.__doc__ = tool.description

    return tool_wrapper
