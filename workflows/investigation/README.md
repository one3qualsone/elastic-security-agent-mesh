# Investigation Workflows

Shared state management for multi-agent investigations. The `investigation-contexts` index tracks evidence chains, action logs, and pending governance approvals across agent handoffs.

## Prerequisites

- `investigation-contexts` index created via `agents/setup/create-investigation-index.yaml`
- Inference endpoint deployed for semantic search

## Workflows

| Workflow | Purpose |
|----------|---------|
| `create-investigation.yaml` | Create a new investigation context |
| `add-evidence.yaml` | Append evidence from any agent |
| `get-investigation.yaml` | Retrieve current investigation state |
| `update-investigation-status.yaml` | Change status, assignment, or risk tier |
| `propose-action.yaml` | Propose a high-risk action for approval |
| `search-similar-investigations.yaml` | Semantic search on past investigations |

## Usage Pattern

1. Alert or user request triggers an investigation: `create-investigation`
2. Assigned agent adds findings: `add-evidence` (enrichment, finding, recommendation)
3. Agent needs another specialist: `update-investigation-status` (reassign) + `add-evidence` (handoff context)
4. Agent wants to take high-risk action: `propose-action` (governance reviews)
5. Investigation complete: `update-investigation-status` (resolved/closed)
6. Future triage references past cases: `search-similar-investigations`
