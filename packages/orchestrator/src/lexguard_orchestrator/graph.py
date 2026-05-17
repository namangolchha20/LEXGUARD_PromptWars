from lexguard_shared.schemas.orchestrator import AgentName

AGENT_DEPENDENCIES: dict[AgentName, list[AgentName]] = {
    AgentName.INGESTION: [],
    AgentName.EXTRACTION: [AgentName.INGESTION],
    AgentName.RISK: [AgentName.EXTRACTION],
    AgentName.BENCHMARK: [AgentName.EXTRACTION],
    AgentName.SIMULATION: [AgentName.RISK],
    AgentName.NEGOTIATION: [AgentName.RISK, AgentName.BENCHMARK, AgentName.SIMULATION],
}

AGENT_WEIGHTS: dict[AgentName, float] = {
    AgentName.INGESTION: 0.15,
    AgentName.EXTRACTION: 0.20,
    AgentName.RISK: 0.15,
    AgentName.BENCHMARK: 0.15,
    AgentName.SIMULATION: 0.15,
    AgentName.NEGOTIATION: 0.20,
}


def execution_layers(agents: set[AgentName]) -> list[list[AgentName]]:
    """Return agents grouped by dependency layer for parallel execution."""
    remaining = set(agents)
    completed: set[AgentName] = set()
    layers: list[list[AgentName]] = []

    while remaining:
        ready = [
            agent
            for agent in remaining
            if all(
                dep in completed or dep not in agents
                for dep in AGENT_DEPENDENCIES[agent]
            )
        ]
        if not ready:
            raise ValueError(f"Circular dependency detected among: {remaining}")
        layers.append(ready)
        completed.update(ready)
        remaining -= set(ready)

    return layers
