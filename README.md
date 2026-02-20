<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://images.contentstack.io/v3/assets/bltefdd0b53724fa2ce/blt5d10f3a91df97d15/620a9ac8849cd422f315b83d/logo-elastic-vertical-reverse.svg">
    <source media="(prefers-color-scheme: light)" srcset="https://images.contentstack.io/v3/assets/bltefdd0b53724fa2ce/blt36f2da8d650732a0/620a9ac8849cd4798f4a12c0/logo-elastic-vertical-color.svg">
    <img alt="Elastic Logo" src="https://images.contentstack.io/v3/assets/bltefdd0b53724fa2ce/blt36f2da8d650732a0/620a9ac8849cd4798f4a12c0/logo-elastic-vertical-color.svg" height="80">
  </picture>
</p>

<h1 align="center">Security Agent Mesh</h1>

<p align="center">
  A fully autonomous SOC built natively on Elastic — multi-agent mesh with specialist AI agents for detection engineering, threat intelligence, triage, forensics, compliance, and SOC operations.
</p>

<p align="center">
  <a href="#setup"><img src="https://img.shields.io/badge/Setup-2D2D2D?style=for-the-badge" alt="Setup"></a>&nbsp;
  <a href="./ARCHITECTURE.md"><img src="https://img.shields.io/badge/Architecture-2D2D2D?style=for-the-badge" alt="Architecture"></a>&nbsp;
  <a href="./ROADMAP.md"><img src="https://img.shields.io/badge/Roadmap-2D2D2D?style=for-the-badge" alt="Roadmap"></a>&nbsp;
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Elastic-9.3+-00BFB3?style=flat-square&logo=elastic&logoColor=white" alt="Elastic 9.3+">&nbsp;
  <img src="https://img.shields.io/badge/YAML-CB171E?style=flat-square&logo=yaml&logoColor=white" alt="YAML">&nbsp;
  <img src="https://img.shields.io/badge/License-Apache_2.0-D16C00?style=flat-square" alt="Apache 2.0">&nbsp;
</p>

---

## Overview

This project implements a **mesh of specialised security AI agents** on the Elastic platform. Each agent is an expert in one domain, backed by its own knowledge base, connected to shared tool workflows, and discoverable by other agents through a semantic registry.

| Agent | Domain | Status |
|-------|--------|--------|
| **Orchestrator** | Request routing and classification | Definition ready |
| **Detection Engineering** | Rule lifecycle, MITRE coverage, SIEM migration | Tools built |
| **Threat Intelligence** | IOC enrichment, threat research | Definition ready |
| **Security Analyst** | Alert triage, investigation, escalation | Definition ready |
| **Forensics** | Endpoint forensics, evidence collection | Definition ready |
| **Compliance** | Regulatory frameworks, control mapping | Definition ready |
| **SOC Operations** | Team coordination, shift management | Definition ready |

### Key Capabilities

- **Investigation Context** — shared state between agents with evidence chains, action logs, and governance approvals
- **Governance Framework** — risk-tiered controls (Tier 0: autonomous, Tier 1: guarded, Tier 2: human-approved) for every action type
- **Feedback Loops** — scheduled workflows that aggregate detection quality, flag noisy rules, and capture incident resolutions for continuous improvement
- **Cases as Output** — Elastic Cases are the human-facing record of agent investigations, where humans review decisions and improve agents over time

See [ARCHITECTURE.md](./ARCHITECTURE.md) for the full design and [ROADMAP.md](./ROADMAP.md) for delivery status.

---

## Setup

### Prerequisites

Complete these steps in the Kibana UI before running the setup script:

1. **Elastic Cloud deployment** with Kibana 9.3+ and Workflows enabled (via Advanced Settings)

2. **Deploy the embedding model** — `multilingual-e5-small`
   - Navigate to Machine Learning > Trained Models
   - Deploy `multilingual-e5-small`
   - Deploy for both Search and Ingestion (medium vCPU suggested, but dependent on size of deployment.)
   - Note the inference endpoint ID (default: `.multilingual-e5-small-elasticsearch`)

3. **Create an LLM connector**
   - Navigate to Stack Management > Connectors > Create connector
   - Configure Claude Sonnet, GPT-4o, Gemini, or your preferred model
   - Note the connector ID

4. **Create API keys**

   *Elasticsearch API key* (for index creation and document CRUD):
   - Stack Management > API Keys > Create API key
   - Grant cluster and index permissions

   *Kibana API key* (for workflow import and agent API calls):
   - Needs: Workflows: All, Cases: All, Security: All

### Configuration

The setup requires environment variables for your Elastic deployment. You can provide these via **GitHub Actions secrets** (recommended) or **local shell exports**.

**Required:**

| Variable | Description |
|----------|-------------|
| `ELASTIC_CLOUD_URL` | Elasticsearch endpoint URL |
| `KIBANA_URL` | Kibana endpoint URL |
| `ES_API_KEY` | Elasticsearch API key (cluster + index permissions) |
| `KIBANA_API_KEY` | Kibana API key (Workflows, Cases, Security) |

**Recommended:**

| Variable | Default | Description |
|----------|---------|-------------|
| `KIBANA_SPACE` | *(default space)* | Target Kibana space for workflows and agents |
| `INFERENCE_ENDPOINT_ID` | `.multilingual-e5-small-elasticsearch` | Inference endpoint powering semantic_text fields |

**Optional (third-party integrations):**

| Variable | Description |
|----------|-------------|
| `VIRUSTOTAL_API_KEY` | Free tier: 4 lookups/min, 500/day |
| `ABUSEIPDB_API_KEY` | Free tier: 1000 checks/day |

### Deploy via GitHub Actions (Recommended)

The easiest way to deploy — no local Python or dependencies required.

1. **Fork this repository** (or push to your own)

2. **Add secrets** in your repo: Settings > Secrets and variables > Actions > New repository secret
   - Add `ELASTIC_CLOUD_URL`, `KIBANA_URL`, `ES_API_KEY`, `KIBANA_API_KEY`
   - Add `KIBANA_SPACE` and `INFERENCE_ENDPOINT_ID` if using non-defaults

3. **Run the action**: Actions > "Deploy Security Agent Mesh" > Run workflow
   - Choose `full-setup` for first deployment, or a specific step to re-run part of it

The action validates your configuration, creates all indices, seeds governance policies, and imports every workflow into Kibana. A summary is posted to the workflow run when complete.

### Deploy Locally (Alternative)

If you prefer to run locally:

```bash
# Set environment variables
export ELASTIC_CLOUD_URL=https://your-deployment.es.region.gcp.cloud.es.io
export KIBANA_URL=https://your-deployment.kb.region.gcp.cloud.es.io
export ES_API_KEY=your-elasticsearch-api-key
export KIBANA_API_KEY=your-kibana-api-key
export KIBANA_SPACE=your-space-id
export INFERENCE_ENDPOINT_ID=.multilingual-e5-small-elasticsearch

# Install dependency and run
pip install requests
python scripts/setup.py

# Or run specific steps
python scripts/setup.py --validate        # Check environment variables
python scripts/setup.py --indices-only    # Only create Elasticsearch indices
python scripts/setup.py --workflows-only  # Only import workflows into Kibana
python scripts/setup.py --seed-policies   # Only seed governance action policies
```

### What the setup does

1. Creates the `agent-registry` index (semantic agent discovery)
2. Creates the `investigation-contexts` index (shared investigation state)
3. Creates the `action-policies` index (governance tier definitions)
4. Creates all `kb-*` knowledge base indices
5. Seeds default governance policies (Tier 0/1/2)
6. Imports all workflow YAML files into Kibana

### Post-Setup (Manual)

After the script completes:

1. **Create agents in Agent Builder**
   - Use the definition files in `agents/definitions/` as reference
   - Configure system instructions, knowledge base attachments, and tool workflows
   - Note each agent's ID after creation

2. **Register agents in the mesh**
   - Run the Register Agent workflow for each agent with its ID, domain, and description
   - This enables semantic routing via the orchestrator

3. **Seed knowledge bases**
   - Populate `kb-mitre-attack` with MITRE ATT&CK techniques
   - Populate `kb-ecs-schema` with ECS field definitions
   - Populate `kb-detection-rules` with your existing detection rules
   - Other knowledge bases are populated by agents over time

### Web Search Integration (Optional)

Web search is not included in the core setup. The architecture supports plugging in your own web search capability — either as an MCP tool registered directly in Agent Builder, or as a workflow that calls your search API via HTTP. The existing `workflows/search/web-search.yaml` provides a template pattern using Brave Search that can be adapted to any provider.

---

## Repository Structure

```
elastic-security-agent/
├── .github/workflows/
│   └── deploy.yml                  # GitHub Actions deployment workflow
├── agents/
│   ├── definitions/                # Agent configs (system prompts, tools, KBs)
│   │   ├── orchestrator.yaml
│   │   ├── detection-engineering.yaml
│   │   ├── threat-intelligence.yaml
│   │   ├── security-analyst.yaml
│   │   ├── forensics.yaml
│   │   ├── compliance.yaml
│   │   └── soc-operations.yaml
│   └── setup/                      # Index creation and agent registration
├── workflows/
│   ├── mesh/                       # Agent routing and registry
│   ├── investigation/              # Investigation context CRUD
│   ├── governance/                 # Risk-tiered action controls
│   ├── feedback/                   # Feedback loop workflows
│   ├── security/detection/         # Detection rule lifecycle
│   ├── security/enrichment/        # IOC and IP enrichment
│   ├── security/response/          # Triage and response
│   ├── search/                     # Semantic and web search
│   ├── knowledge/                  # Knowledge base CRUD
│   ├── ai-agents/                  # Agent invocation patterns
│   ├── integrations/               # Slack, Splunk, Caldera, etc.
│   └── utilities/                  # Common operations
├── scripts/
│   ├── setup.py                    # Automated setup script
│   └── setup.sh                    # Bash wrapper
├── docs/
│   ├── schema.md                   # Workflow YAML schema reference
│   ├── concepts.md                 # Workflow concepts
│   └── importing.md                # Manual import instructions
├── ARCHITECTURE.md                 # Full architecture design
└── ROADMAP.md                      # Delivery phases and status
```

---

## Workflow Reference

### Workflow Schema

Every workflow follows a consistent YAML schema:

```yaml
name: "Workflow Name"           # Required
steps:                          # Required — at least one step
  - name: "Step Name"
    type: "action.type"
    with:
      key: value

description: "What this does"   # Optional
tags: [security, detection]     # Optional
triggers:                       # Optional — defaults to manual
  - type: scheduled
    with:
      every: "1d"
consts:                         # Optional — reusable constants
  api_key: "value"
inputs:                         # Optional — runtime parameters
  - name: query
    type: string
    required: true
```

### Action Types

| Action | Description |
|--------|-------------|
| `http` | HTTP requests to any API |
| `elasticsearch.search` | Search Elasticsearch indices |
| `elasticsearch.index` | Index documents |
| `elasticsearch.request` | Raw Elasticsearch API calls |
| `kibana.request` | Kibana API calls |
| `kibana.cases` | Case management |
| `kibana.post_agent_builder_converse` | Invoke an Agent Builder agent |
| `console` | Log output |
| `foreach` | Loop over arrays |
| `if` | Conditional execution |
| `parallel` | Parallel step execution |
| `wait` | Pause execution |

### Variable Syntax

```yaml
{{ consts.api_url }}                          # Constants
{{ inputs.target_ip }}                        # Runtime inputs
{{ steps.search.output.hits.total.value }}    # Step outputs
{{ foreach.item._source.host.name }}          # Loop items
```

See [docs/schema.md](./docs/schema.md) for the complete reference and [docs/importing.md](./docs/importing.md) for import instructions.

---

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

---

## License

Apache License 2.0 — see [LICENSE](./LICENSE.txt).
