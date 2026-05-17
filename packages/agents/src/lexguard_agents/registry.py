from lexguard_ai import AIClient, AISettings

from lexguard_agents.clause.agent import ClauseExtractionAgent
from lexguard_agents.consequence.agent import ConsequenceSimulationAgent
from lexguard_agents.negotiation.agent import NegotiationAgent


class AgentRegistry:
    """Registry of available LEXGUARD agents."""

    def __init__(
        self,
        ai_client: AIClient | None = None,
        ai_settings: AISettings | None = None,
    ) -> None:
        client = ai_client or AIClient(ai_settings)
        self._agents: dict[str, object] = {
            "clause_extraction": ClauseExtractionAgent(
                ai_client=client,
                settings=ai_settings,
            ),
            "consequence_simulation": ConsequenceSimulationAgent(
                ai_client=client,
                settings=ai_settings,
            ),
            "negotiation": NegotiationAgent(
                ai_client=client,
                settings=ai_settings,
            ),
        }

    def get(self, name: str) -> object:
        if name not in self._agents:
            raise KeyError(f"Unknown agent: {name}")
        return self._agents[name]

    def list_agents(self) -> list[str]:
        return list(self._agents.keys())

    @property
    def clause_extraction(self) -> ClauseExtractionAgent:
        agent = self._agents["clause_extraction"]
        assert isinstance(agent, ClauseExtractionAgent)
        return agent

    @property
    def consequence_simulation(self) -> ConsequenceSimulationAgent:
        agent = self._agents["consequence_simulation"]
        assert isinstance(agent, ConsequenceSimulationAgent)
        return agent

    @property
    def negotiation(self) -> NegotiationAgent:
        agent = self._agents["negotiation"]
        assert isinstance(agent, NegotiationAgent)
        return agent
