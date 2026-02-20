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
   - Add `VIRUSTOTAL_API_KEY` and `ABUSEIPDB_API_KEY` if you have it.  

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

### Post-Setup: Create Agents

After the automated setup completes, you create the agents in Agent Builder and register them in the mesh. The definition files in `agents/definitions/` contain the full system prompts, but this section gives you the concrete values to enter.

#### Step 1: Create Each Agent in Agent Builder

Navigate to **Agent Builder** in Kibana. For each agent, create a new agent with your LLM connector (Claude Sonnet, GPT-4o, Gemini, etc.) and assign the tools and knowledge bases listed below.

> **Tools are workflows.** In Agent Builder, when you add a "tool" to an agent, you select from the workflows imported in the previous step. The tool names below match the workflow names in Kibana.

| # | Agent Name | Tools (Workflow Names) | Knowledge Bases |
|---|-----------|------------------------|-----------------|
| 1 | **Security Mesh Orchestrator** | Search Agent Registry, Call Subagent | *None* |
| 2 | **Detection Engineering Agent** | List Detection Rules, Get Rule Details, Create Detection Rule, Enable/Disable Rule, Search Rules by MITRE Technique, Evaluate MITRE Coverage, Check Field Availability, Check Action Policy, Create Investigation, Add Evidence, Semantic Knowledge Search, Web Search, Add Knowledge Document, Call Subagent | kb-detection-rules, kb-ecs-schema, kb-mitre-attack |
| 3 | **Threat Intelligence Agent** | VT File Hash Report, VT File Upload, VT URL Scan, VT URL Report, VT Domain Report, VT IP Report, IP Reputation Check, Web Search, Semantic Knowledge Search, Add Knowledge Document | kb-threat-intel, kb-ioc-history |
| 4 | **Security Analyst Agent** | Semantic Knowledge Search, Tag Alert as True Positive, Tag Alert as False Positive, Close Alert, Acknowledge Alert, Create Case, Add Knowledge Document, VT File Hash Report, VT IP Report, VT Domain Report, IP Reputation Check, Call Subagent | kb-incidents, kb-playbooks |
| 5 | **Forensics Agent** | Execute Command on Endpoint, Execute and Retrieve, Get Action Status, Semantic Knowledge Search, Add Knowledge Document, VT File Hash Report, VT IP Report, Call Subagent | kb-forensics |
| 6 | **Compliance Agent** | Semantic Knowledge Search, Web Search, Add Knowledge Document, Call Subagent | kb-compliance |
| 7 | **SOC Operations Agent** | Semantic Knowledge Search, Add Knowledge Document, Update Knowledge Document, Remove Knowledge Document, Call Subagent | kb-soc-ops, kb-runbooks |

For each agent, copy the `system_instructions` from the corresponding file in `agents/definitions/`. These contain the agent's persona, principles, and behavioural guidance.

#### Step 2: Register Agents in the Mesh

After creating each agent in Agent Builder, note its **Agent ID** (visible in the browser URL bar when editing the agent, e.g., `/app/agent_builder/agents/<agent-id>`).

Run the **Register Agent** workflow in Kibana for each agent. This adds the agent to the `agent-registry` Elasticsearch index so the orchestrator can discover it via semantic search.

**Orchestrator:**
| Field | Value |
|-------|-------|
| agent_id | *paste from Agent Builder* |
| agent_name | Security Mesh Orchestrator |
| domain | orchestrator |
| capabilities | routing, classification, multi-agent-coordination |
| description | Routes user requests to specialist security agents. Understands detection engineering, compliance, threat intelligence, triage, forensics, and SOC operations domains. Use this agent when you don't know which specialist to talk to. |
| keywords | router, orchestrator, help, which agent, general question |

**Detection Engineering:**
| Field | Value |
|-------|-------|
| agent_id | *paste from Agent Builder* |
| agent_name | Detection Engineering Agent |
| domain | detection_engineering |
| capabilities | rule_creation, rule_migration, coverage_analysis, schema_normalisation, query_translation, siem_migration, mitre_mapping |
| description | Expert in Elastic Security detection rules, SIEM rule migration from Sentinel and Splunk, MITRE ATT&CK coverage gap analysis, and ECS schema normalisation. Helps create new rules, evaluate which rules to enable, translate queries between SIEM platforms, and ensure detections use common schema fields. |
| keywords | detection, rules, SIEM, migration, Sentinel, Splunk, Sigma, KQL, ESQL, MITRE, ATT&CK, coverage, ECS, schema |

**Threat Intelligence:**
| Field | Value |
|-------|-------|
| agent_id | *paste from Agent Builder* |
| agent_name | Threat Intelligence Agent |
| domain | threat_intel |
| capabilities | ioc_enrichment, threat_research, campaign_tracking, mitre_mapping, reputation_check |
| description | Enriches indicators of compromise (file hashes, IPs, domains, URLs) across VirusTotal, AbuseIPDB, and web search. Researches threat actors, campaigns, and malware families. Maintains a history of investigated IOCs. |
| keywords | IOC, threat, intelligence, VirusTotal, hash, IP, domain, reputation, malware, threat actor, campaign, enrichment |

**Security Analyst:**
| Field | Value |
|-------|-------|
| agent_id | *paste from Agent Builder* |
| agent_name | Security Analyst Agent |
| domain | triage |
| capabilities | alert_triage, incident_investigation, playbook_execution, escalation, case_management |
| description | Triages security alerts and investigates incidents. Searches past incident resolutions for similar patterns, follows SOC playbooks, enriches indicators, and manages alert lifecycle (tag, close, acknowledge, create cases). Escalates to forensics or other specialists when deep investigation is needed. |
| keywords | alert, triage, investigation, incident, case, playbook, escalate, true positive, false positive, SOC |

**Forensics:**
| Field | Value |
|-------|-------|
| agent_id | *paste from Agent Builder* |
| agent_name | Forensics Agent |
| domain | forensics |
| capabilities | endpoint_forensics, evidence_collection, host_isolation, timeline_analysis, process_investigation, containment, response_console |
| description | Performs deep-dive forensic investigation on endpoints using Elastic Defend. Executes commands via the response console, collects evidence (processes, files, network connections), builds event timelines, isolates hosts, and documents findings. |
| keywords | forensics, investigation, endpoint, isolate, evidence, response console, process tree, timeline, containment, malware analysis, Elastic Defend |

**Compliance:**
| Field | Value |
|-------|-------|
| agent_id | *paste from Agent Builder* |
| agent_name | Compliance Agent |
| domain | compliance |
| capabilities | regulatory_guidance, control_mapping, gap_analysis, audit_evidence, framework_comparison |
| description | Expert in regulatory compliance frameworks including DORA, ISO 27001, ISO 42001, GDPR, NIS2, PCI-DSS, SOX, NIST CSF, and CIS Controls. Maps regulatory controls to Elastic detection rules and security capabilities. Performs gap analysis and helps generate audit evidence. |
| keywords | compliance, regulation, DORA, ISO 27001, ISO 42001, GDPR, NIS2, PCI-DSS, SOX, NIST, CIS, audit, controls, gap analysis |

**SOC Operations:**
| Field | Value |
|-------|-------|
| agent_id | *paste from Agent Builder* |
| agent_name | SOC Operations Agent |
| domain | soc_ops |
| capabilities | shift_management, escalation, incident_coordination, runbook_guidance, cross_agent_coordination, knowledge_management |
| description | Manages SOC team operations — shift schedules, on-call rotas, escalation procedures, and incident coordination logistics. Can update knowledge bases with rota changes and new procedures. |
| keywords | SOC, operations, rota, on-call, schedule, escalation, runbook, incident management, team, shift |

#### Step 3: Seed Knowledge Bases

Populate the knowledge base indices with domain-specific data. Use the **Add Knowledge Document** workflow or bulk-index documents directly.

| Index | Content | Priority |
|-------|---------|----------|
| `kb-mitre-attack` | MITRE ATT&CK techniques with descriptions, data sources, and detection suggestions | High |
| `kb-ecs-schema` | ECS field definitions and field mappings from other schemas | High |
| `kb-detection-rules` | Your existing detection rules (name, query, MITRE mapping, severity) | High |
| `kb-compliance` | Regulatory framework text — DORA, ISO 27001, GDPR, etc. | Medium |
| `kb-playbooks` | SOC playbooks and standard operating procedures | Medium |
| `kb-soc-ops` | Team rota, escalation matrix, SLAs, contact details | Medium |
| `kb-forensics` | Forensic procedures, Elastic Defend command reference | Low |
| `kb-threat-intel` | Known threat actors, campaigns, TTPs | Low — agents populate over time |
| `kb-ioc-history` | Empty — populated by agents as IOCs are investigated | None |
| `kb-incidents` | Empty — populated by agents as incidents are resolved | None |
| `kb-runbooks` | Operational runbooks for common scenarios | Low |

Each document should include a `semantic_summary` field (used for semantic search) and a `category` field for filtering.

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
