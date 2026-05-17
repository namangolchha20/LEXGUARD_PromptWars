from lexguard_orchestrator.graph import AGENT_DEPENDENCIES, execution_layers
from lexguard_shared.schemas.orchestrator import AgentName


def test_execution_layers_parallel_risk_and_benchmark() -> None:
    layers = execution_layers(set(AgentName))
    layer_agents = [set(layer) for layer in layers]

    extraction_idx = next(i for i, layer in enumerate(layer_agents) if AgentName.EXTRACTION in layer)
    risk_idx = next(i for i, layer in enumerate(layer_agents) if AgentName.RISK in layer)
    benchmark_idx = next(i for i, layer in enumerate(layer_agents) if AgentName.BENCHMARK in layer)

    assert risk_idx == benchmark_idx
    assert risk_idx > extraction_idx
    assert AgentName.SIMULATION in layer_agents[risk_idx + 1]


def test_dependencies_defined_for_all_agents() -> None:
    for agent in AgentName:
        assert agent in AGENT_DEPENDENCIES
