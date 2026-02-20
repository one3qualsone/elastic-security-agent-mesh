# Mesh Workflows

Workflows specific to the security agent mesh architecture. These are **not agnostic** — they assume the mesh infrastructure (agent registry index, specialist agents) has been deployed. They should not be submitted to the official Elastic workflows repository.

## Workflows

| Workflow | Description |
|----------|-------------|
| **Orchestrator Router** | Routes user requests to the best specialist agent by searching the agent registry |
| **Search Agent Registry** | Semantic search on the `agent-registry` index to discover specialist agents |

## Prerequisites

- The `agent-registry` index must exist (created via `agents/setup/create-agent-registry.yaml`)
- At least one specialist agent must be registered in the registry
- Specialist agents must be created in Elastic Agent Builder
