"""FastAPI application factory."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi import Request
from fastapi import WebSocket
from fastapi.responses import JSONResponse
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles

from fluentia.agents.base import AgentDefinition
from fluentia.agents.english_teacher import english_teacher
from fluentia.agents.registry import AgentRegistry
from fluentia.config import GOOGLE_MODEL_CATALOG
from fluentia.config import AppConfig
from fluentia.observability.health import get_health
from fluentia.observability.health import get_readiness
from fluentia.observability.logging import configure_logging
from fluentia.observability.logging import log_config_summary
from fluentia.observability.metrics import LoggingMetricsCollector
from fluentia.providers.base import BaseProvider
from fluentia.providers.bedrock import BedrockProvider
from fluentia.providers.google import GoogleProvider
from fluentia.session.manager import SessionManager
from fluentia.tools import ToolProcessor
from fluentia.tools.implementations import GetDateAndTimeTool
from fluentia.tools.implementations import GetWeatherTool

logger: logging.Logger = logging.getLogger(__name__)

STATIC_DIR: Path = Path(__file__).parent / "static"

# Provider-specific tools that are not BaseTool instances
PROVIDER_TOOLS: list[dict[str, Any]] = [
    {
        "name": "google_search",
        "display_name": "Google Search",
        "description": "Search the web for information using Google.",
        "provider_restriction": "google",
    }
]


def build_agent_tools(
    agent: AgentDefinition, tool_processor: ToolProcessor
) -> list[dict[str, Any]]:
    """Build the tools metadata array for an agent."""
    tools: list[dict[str, Any]] = []

    for spec in tool_processor.get_tool_specs():
        tools.append(
            {
                "name": spec["name"],
                "display_name": spec.get("display_name", spec["name"]),
                "description": spec["description"],
                "enabled_by_default": spec["name"] in agent.enabled_tools,
                "provider_restriction": None,
            }
        )

    for pt in PROVIDER_TOOLS:
        tools.append({**pt, "enabled_by_default": pt["name"] in agent.enabled_tools})

    return tools


def create_app() -> FastAPI:
    """Create the FastAPI application."""
    config: AppConfig = AppConfig()
    configure_logging(config.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
        """Application lifespan: initialize and tear down resources."""
        log_config_summary(config)
        app.state.config = config

        # Tool processor
        tool_processor: ToolProcessor = ToolProcessor()
        tool_processor.register(GetDateAndTimeTool())
        tool_processor.register(GetWeatherTool())
        app.state.tool_processor = tool_processor

        # Agent registry
        agent_registry: AgentRegistry = AgentRegistry()
        agent_registry.register(english_teacher)
        app.state.agent_registry = agent_registry

        # Metrics
        metrics: LoggingMetricsCollector = LoggingMetricsCollector()
        app.state.metrics = metrics

        # Providers
        providers: dict[str, BaseProvider] = {
            "google": GoogleProvider(provider_config=config.google, tool_processor=tool_processor),
            "bedrock": BedrockProvider(
                provider_config=config.bedrock, tool_processor=tool_processor
            ),
        }
        app.state.providers = providers

        # Session manager
        session_manager: SessionManager = SessionManager(
            providers=providers,
            agent_registry=agent_registry,
            metrics=metrics,
            default_agent=config.default_agent,
        )
        app.state.session_manager = session_manager

        logger.info("Application started")
        yield
        logger.info("Application shutting down")

    app = FastAPI(
        title="Fluentia - Voice Agent Platform",
        description="Real-time bidirectional voice conversations",
        lifespan=lifespan,
    )

    # Health endpoints
    @app.get("/health")
    async def health() -> dict[str, Any]:
        """Liveness probe."""
        return get_health()

    @app.get("/ready")
    async def ready() -> dict[str, Any]:
        """Readiness probe."""
        return get_readiness(config)

    # Agent metadata endpoint
    @app.get("/api/agents")
    async def list_agents() -> JSONResponse:
        """Return available agent definitions with field metadata."""
        registry: AgentRegistry = app.state.agent_registry
        tp: ToolProcessor = app.state.tool_processor
        agents: list[dict[str, Any]] = [
            {
                "name": agent.name,
                "display_name": agent.display_name,
                "description": agent.description,
                "fields": agent.serialize_fields(),
                "tools": build_agent_tools(agent, tp),
            }
            for agent in registry.list_agents()
        ]
        return JSONResponse(content=agents)

    @app.get("/api/google/models")
    async def list_google_models() -> JSONResponse:
        """Return available Google Gemini models with capabilities."""
        models: list[dict[str, Any]] = [
            {
                "model_id": spec.model_id,
                "display_name": spec.display_name,
                "supports_proactivity": spec.supports_proactivity,
                "supports_affective_dialog": spec.supports_affective_dialog,
                "supports_tools": spec.supports_tools,
                "is_default": spec.is_default,
            }
            for spec in GOOGLE_MODEL_CATALOG.values()
        ]
        return JSONResponse(content=models)

    @app.post("/api/agents/{name}/render-prompt")
    async def render_prompt(name: str, request: Request) -> Response:
        """Render an agent's prompt template with the provided variables."""
        registry: AgentRegistry = app.state.agent_registry
        try:
            agent_def: AgentDefinition = registry.get(name)
        except KeyError:
            return JSONResponse(status_code=404, content={"detail": f"Agent not found: {name}"})

        body: dict[str, Any] = await request.json()
        variables: dict[str, Any] = body.get("variables", {})
        rendered: str = agent_def.render_prompt_highlighted(variables)
        return Response(content=rendered, media_type="text/html")

    # WebSocket endpoint
    @app.websocket("/ws/{provider}/{user_id}/{session_id}")
    async def websocket_endpoint(
        websocket: WebSocket, provider: str, user_id: str, session_id: str
    ) -> None:
        """Unified WebSocket endpoint for voice sessions."""
        session_manager: SessionManager = app.state.session_manager
        await session_manager.handle_websocket(
            websocket=websocket, provider_name=provider, user_id=user_id, session_id=session_id
        )

    # Mount static files last (so API/WS routes take priority)
    if STATIC_DIR.exists():
        app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")

    return app
