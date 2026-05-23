"""Tests for FastAPI application factory."""

from typing import Any
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from fluentia.app import create_app


@pytest.fixture
def client() -> TestClient:
    """Create a test client for the app."""
    with (
        patch("fluentia.app.GoogleProvider") as mock_google,
        patch("fluentia.app.BedrockProvider") as mock_bedrock,
    ):
        mock_google.return_value = MagicMock()
        mock_bedrock.return_value = MagicMock()
        app = create_app()
        with TestClient(app) as test_client:
            yield test_client


class TestHealthEndpoint:
    """Tests for the /health endpoint."""

    def test_health_returns_ok(self, client: TestClient):
        """Test that /health returns status ok."""
        response = client.get("/health")
        assert response.status_code == 200
        data: dict[str, Any] = response.json()
        assert data["status"] == "ok"
        assert "version" in data
        assert "uptime_seconds" in data


class TestReadyEndpoint:
    """Tests for the /ready endpoint."""

    def test_ready_returns_ready(self, client: TestClient):
        """Test that /ready returns status ready."""
        response = client.get("/ready")
        assert response.status_code == 200
        data: dict[str, Any] = response.json()
        assert data["status"] == "ready"
        assert "providers" in data


class TestAgentsEndpoint:
    """Tests for the /api/agents endpoint."""

    def test_list_agents(self, client: TestClient):
        """Test that /api/agents returns agent definitions with fields."""
        response = client.get("/api/agents")
        assert response.status_code == 200
        agents: list[dict[str, Any]] = response.json()
        assert isinstance(agents, list)
        assert len(agents) >= 1

        # Verify structure of first agent
        agent: dict[str, Any] = agents[0]
        assert "name" in agent
        assert "display_name" in agent
        assert "description" in agent
        assert "fields" in agent
        assert isinstance(agent["fields"], list)

        # Verify field structure
        field: dict[str, Any] = agent["fields"][0]
        assert "key" in field
        assert "label" in field
        assert "field_type" in field
        assert "default" in field


class TestGoogleModelsEndpoint:
    """Tests for the /api/google/models endpoint."""

    def test_list_google_models(self, client: TestClient):
        """Test that /api/google/models returns model catalog."""
        response = client.get("/api/google/models")
        assert response.status_code == 200
        models: list[dict[str, Any]] = response.json()
        assert isinstance(models, list)
        assert len(models) >= 2

        model: dict[str, Any] = models[0]
        assert "model_id" in model
        assert "display_name" in model
        assert "supports_proactivity" in model
        assert "supports_affective_dialog" in model
        assert "supports_tools" in model
        assert "is_default" in model

    def test_supports_tools_in_response(self, client: TestClient):
        """Test that supports_tools is correctly set per model."""
        response = client.get("/api/google/models")
        models: list[dict[str, Any]] = response.json()
        model_map: dict[str, dict[str, Any]] = {m["model_id"]: m for m in models}
        assert model_map["gemini-2.5-flash-native-audio-preview-12-2025"]["supports_tools"] is True
        assert model_map["gemini-3.1-flash-live-preview"]["supports_tools"] is False


class TestRenderPromptEndpoint:
    """Tests for the /api/agents/{name}/render-prompt endpoint."""

    def test_render_prompt_success(self, client: TestClient):
        """Test rendering a prompt for a known agent."""
        response = client.post(
            "/api/agents/english_teacher/render-prompt",
            json={"variables": {"teacher_name": "TestBot"}},
        )
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "TestBot" in response.text

    def test_render_prompt_unknown_agent(self, client: TestClient):
        """Test that unknown agent returns 404."""
        response = client.post("/api/agents/nonexistent/render-prompt", json={"variables": {}})
        assert response.status_code == 404
        data: dict[str, Any] = response.json()
        assert "detail" in data
