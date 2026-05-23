"""Agent registry for looking up agent definitions."""

from fluentia.agents.base import AgentDefinition


class AgentRegistry:
    """Registry of available agent definitions. Agents register at startup."""

    def __init__(self) -> None:
        """Initialize an empty registry."""
        self._agents: dict[str, AgentDefinition] = {}

    def register(self, agent: AgentDefinition) -> None:
        """Register an agent definition."""
        self._agents[agent.name] = agent

    def get(self, name: str) -> AgentDefinition:
        """Look up an agent by name. Raises KeyError if not found."""
        if name not in self._agents:
            raise KeyError(f"Agent not found: {name}")
        return self._agents[name]

    def list_agents(self) -> list[AgentDefinition]:
        """Return all registered agents."""
        return list(self._agents.values())
