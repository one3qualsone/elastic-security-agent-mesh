# Agent Mesh Setup

Workflows for bootstrapping the security agent mesh infrastructure on a new Elastic deployment. Run these **once** during initial setup (or when adding new agents).

## Setup order

### 1. Prerequisites

Before running any setup workflows:

- **Inference endpoint** — Deploy `multilingual-e5-small` from **Machine Learning > Trained Models** in Kibana. The default endpoint ID is `.multilingual-e5-small-elasticsearch`. This powers the `semantic_text` fields used for semantic search across all knowledge bases and the agent registry.

### 2. Create the agent registry

```
Run: agents/setup/create-agent-registry.yaml
```

This creates the `agent-registry` index with a `semantic_description` field for routing queries to the right specialist agent.

### 3. Create knowledge base indices

For each knowledge base needed by your agents:

```
Run: agents/setup/create-knowledge-index.yaml
  index_name: "kb-detection-rules"
  inference_endpoint_id: ".multilingual-e5-small-elasticsearch"
```

Repeat for each index: `kb-detection-rules`, `kb-ecs-schema`, `kb-mitre-attack`, `kb-compliance`, `kb-threat-intel`, `kb-ioc-history`, `kb-incidents`, `kb-playbooks`, `kb-forensics`, `kb-soc-ops`, `kb-runbooks`.

### 4. Populate knowledge bases

Seed the indices with initial data. This is domain-specific — for example:
- `kb-detection-rules`: Export rules from the Elastic Detection Engine API
- `kb-compliance`: Ingest regulatory framework documents
- `kb-mitre-attack`: Ingest from the MITRE ATT&CK STIX data

### 5. Create agents in Agent Builder

For each agent you want to deploy, use the definition file in `agents/definitions/` as a reference:
- Set the **system instructions** from the `system_instructions` field
- Attach the **knowledge bases** listed in the definition
- Register the **tool workflows** listed in the definition

### 6. Register agents in the mesh

For each agent created in step 5:

```
Run: agents/setup/register-agent.yaml
  agent_id: "<the agent ID from Agent Builder>"
  agent_name: "<from the definition file>"
  domain: "<from the definition file>"
  capabilities: <from the definition file>
  description: "<from the definition file>"
  keywords: <from the definition file>
```

## Workflows

| Workflow | Description |
|----------|-------------|
| **Create Knowledge Base Index** | Creates an ES index with the mesh's standard mapping (including `semantic_text`) |
| **Create Agent Registry** | Creates the `agent-registry` index for mesh routing |
| **Register Agent** | Adds a specialist agent to the registry for discovery |

## Index mapping

All knowledge base indices created by `create-knowledge-index.yaml` share this mapping:

| Field | Type | Purpose |
|-------|------|---------|
| `title` | text | Document title |
| `content` | text | Full content |
| `semantic_summary` | semantic_text | Semantic search via inference endpoint |
| `category` | keyword | Document type for filtering |
| `source` | keyword | Origin (manual, automated, external) |
| `tags` | keyword | Organisation tags |
| `created_at` | date | Creation timestamp |
| `updated_at` | date | Last modified |
| `expires_at` | date | Staleness review date |
| `metadata` | object (dynamic) | Flexible domain-specific fields |
