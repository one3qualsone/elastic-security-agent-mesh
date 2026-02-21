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
| `LLM_CONNECTOR_ID` | The LLM connector ID for agent-to-agent calls. We recommend **Claude Opus 4.5** (`Anthropic-Claude-Opus-4-5`) for best results, or **Claude Sonnet 4.5** (`Anthropic-Claude-Sonnet-4-5`) for lower cost. When Elastic 9.4 ships (April 2026), this can be updated to Claude Opus 4.6. Find your connector ID by running `GET kbn:/api/actions/connectors` in Kibana Dev Tools. |

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

### Deployment Overview

Deployment is a two-phase process. Phase 1 is fully automated and creates the infrastructure — indices, workflows, and initial agents. Phase 2 involves three manual steps in the Kibana UI (tools that can't be created via API), followed by a quick re-sync to attach those tools to agents automatically.

> **Why two phases?** The `agent-registry` Index Search tool requires the `agent-registry` index to already exist — Elastic won't let you create an Index Search tool against a non-existent index. So we create the indices first, then the manual tools, then sync agents.

### Phase 1: Automated Deploy

#### GitHub Actions (Recommended)

The easiest way to deploy — no local Python or dependencies required.

1. **Fork this repository** (or push to your own)

2. **Add secrets** in your repo: Settings > Secrets and variables > Actions > New repository secret
   - Add `ELASTIC_CLOUD_URL`, `KIBANA_URL`, `ES_API_KEY`, `KIBANA_API_KEY`
   - Add `KIBANA_SPACE` and `INFERENCE_ENDPOINT_ID` if using non-defaults
   - Add `VIRUSTOTAL_API_KEY` and `ABUSEIPDB_API_KEY` if you have them

3. **Run the action**: Actions > "Deploy Security Agent Mesh" > Run workflow
   - Choose `full-setup` for first deployment

This creates all indices, seeds governance policies, imports workflows, creates workflow tools, creates all 7 agents, and registers them in the mesh. Agents will deploy **without** the manual tools — that's expected. We attach those in Phase 2.

#### Local Deploy (Alternative)

```bash
export ELASTIC_CLOUD_URL=https://your-deployment.es.region.gcp.cloud.es.io
export KIBANA_URL=https://your-deployment.kb.region.gcp.cloud.es.io
export ES_API_KEY=your-elasticsearch-api-key
export KIBANA_API_KEY=your-kibana-api-key
export KIBANA_SPACE=your-space-id
export INFERENCE_ENDPOINT_ID=.multilingual-e5-small-elasticsearch

pip install requests pyyaml
python scripts/setup.py
```

#### What Phase 1 creates

1. Elasticsearch indices: `agent-registry`, `investigation-contexts`, `action-policies`, all `kb-*` knowledge bases
2. Default governance policies (Tier 0/1/2)
3. All workflow YAML files imported into Kibana
4. All workflow-based tools in Agent Builder
5. All 7 agents with system prompts and workflow tool assignments
6. Agent registry entries for semantic mesh discovery

### Phase 2: Manual Tools + Sync

After Phase 1 completes, three tools require manual setup in the Kibana UI. Complete all three, then run the sync step to attach them to agents automatically.

#### Step 1: Create the Agent Registry Tool (Required)

The Agent Builder API does not support creating `index_search` tools — this must be done in the UI. **This tool is critical** — without it, the orchestrator cannot discover which agent to route requests to, and agents cannot find each other for cross-domain collaboration.

1. Navigate to **Agent Builder > Tools > Create a new tool**
2. Set **Type** to `Index Search`
3. Set **Target pattern** to `agent-registry`
4. Set **Tool ID** to `security-mesh.agent-registry`
5. Set **Description** to `Search the agent registry to discover specialist agents by capability, domain, or natural language description`
6. Set **Custom instructions** to:

```
Search the agent registry to find specialist agents by capability, domain, or task description. The index contains one document per agent with the following fields:

- agent_name: The agent's display name
- agent_id: The Agent Builder ID (use this when calling a subagent)
- domain: The agent's area of expertise (e.g., detection_engineering, threat_intel, triage, forensics, compliance, soc_ops, orchestrator)
- capabilities: Comma-separated list of what the agent can do
- description: Natural language description of the agent's role and strengths
- keywords: Search terms associated with the agent

When searching, use natural language that describes what you need — the semantic_summary field enables semantic matching. For example, searching "enrich a suspicious IP address" will match the Threat Intelligence agent. Return the agent_name and agent_id from the results so you can route work using the Call Subagent tool.
```

7. Add label `security-mesh`
8. Save the tool

#### Step 2: Set Up Web Search via MCP (Optional but Recommended)

Web search gives agents the ability to research current threats, regulatory updates, and technical documentation. This is provided via an MCP server you bring yourself. Without it, agents will still function but cannot access the web.

See the [Web Search Integration](#web-search-integration-mcp--optional-but-recommended) section below for full setup instructions.

#### Step 3: Configure LLM Connector

The LLM connector is needed in two places:

**a) Agent Builder UI** — for interactive chat with agents:

1. Navigate to **Agent Builder** in Kibana
2. Open each agent and select your LLM connector in the chat/model dropdown

**b) GitHub Actions secret** — for agent-to-agent calls via workflows:

The Call Subagent, Orchestrator Router, and Mesh Automated Triaging workflows invoke agents programmatically via the converse API. They need a `connector_id` to specify which LLM to use.

1. Find your connector ID by running this in **Kibana Dev Tools**:

```
GET kbn:/api/actions/connectors
```

2. Look for your LLM connector in the response — the `id` field is what you need. Common built-in IDs:

| Connector | ID |
|-----------|-----|
| Claude Opus 4.5 | `Anthropic-Claude-Opus-4-5` |
| Claude Sonnet 4.5 | `Anthropic-Claude-Sonnet-4-5` |
| Gemini 2.5 Pro | `Google-Gemini-2-5-Pro` |
| GPT-5.2 | `OpenAI-GPT-5-2` |

3. Add it as `LLM_CONNECTOR_ID` in your GitHub Actions secrets (or export locally)

The setup script injects this into the workflow YAML files during deployment, just like API keys.

#### Step 4: Sync Agents

Re-run the setup with `agents-only` to automatically attach the agent-registry and MCP websearch tools to all agents that need them:

```bash
# Via GitHub Actions: select "agents-only" from the workflow dispatch menu

# Or locally:
python scripts/setup.py --agents-only
```

The script checks for each tool by ID. If `security-mesh.agent-registry`, `websearch.web_search`, and `websearch.fetch_webpage` now exist, they'll be attached to the relevant agents automatically. Any tools that don't exist are skipped gracefully — agents still work, just without those capabilities.

#### CLI Reference

```bash
python scripts/setup.py                  # Full setup (Phase 1)
python scripts/setup.py --validate       # Check environment variables only
python scripts/setup.py --agents-only    # Re-sync agents with current tools (Phase 2)
python scripts/setup.py --delete-all     # Delete everything and re-deploy from scratch
```

#### Agents and Tools Reference

The setup script creates the following agents and tools from `agents/definitions/`. Agent Builder supports four tool types: **Workflows**, **Index Search**, **ES|QL**, and **MCP**. This mesh uses Workflows, built-in platform tools, and MCP tools.

| # | Agent Name | Workflow Tools | Built-in / MCP Tools | Knowledge Bases |
|---|-----------|---------------|----------------------|-----------------|
| 1 | **Security Mesh Orchestrator** | Call Subagent | `platform.core.search`, `platform.core.cases` | *None* |
| 2 | **Detection Engineering Agent** | List Detection Rules, Get Rule Details, Create Detection Rule, Enable/Disable Rule, Search Rules by MITRE Technique, Evaluate MITRE Coverage, Check Field Availability, Check Action Policy, Create Investigation, Add Evidence, Get Investigation, Update Investigation Status, Log Decision, Semantic Knowledge Search, Add Knowledge Document, Call Subagent | `platform.core.execute_esql`, `platform.core.generate_esql`, `security.alerts`, `websearch.web_search`, `websearch.fetch_webpage` | kb-detection-rules, kb-ecs-schema, kb-mitre-attack |
| 3 | **Threat Intelligence Agent** | VT File Hash Report, VT File Upload, VT URL Scan, VT URL Report, VT Domain Report, VT IP Report, IP Reputation Check, Semantic Knowledge Search, Add Knowledge Document | `websearch.web_search`, `websearch.fetch_webpage` | kb-threat-intel, kb-ioc-history |
| 4 | **Security Analyst Agent** | Semantic Knowledge Search, Tag Alert as True Positive, Tag Alert as False Positive, Close Alert, Acknowledge Alert, Create Case, Create Alert Note, Create Investigation, Get Investigation, Update Investigation Status, Add Evidence, Propose Action, Search Similar Investigations, Record Incident Resolution, Check Action Policy, Log Decision, Request Approval, Add Knowledge Document, Call Subagent | `security.alerts` | kb-incidents, kb-playbooks |
| 5 | **Forensics Agent** | Execute Command on Endpoint, Execute and Retrieve, Get Action Status, Create Investigation, Get Investigation, Update Investigation Status, Add Evidence, Propose Action, Check Action Policy, Log Decision, Request Approval, Semantic Knowledge Search, Add Knowledge Document, VT File Hash Report, VT IP Report, Call Subagent | `platform.core.execute_esql`, `security.alerts` | kb-forensics |
| 6 | **Compliance Agent** | Semantic Knowledge Search, Add Knowledge Document, Call Subagent | `platform.core.search`, `websearch.web_search`, `websearch.fetch_webpage` | kb-compliance |
| 7 | **SOC Operations Agent** | Semantic Knowledge Search, Add Knowledge Document, Update Knowledge Document, Remove Knowledge Document, Check Knowledge Staleness, Call Subagent | `platform.core.cases`, `security.alerts` | kb-soc-ops, kb-runbooks |

For each agent, copy the `system_instructions` from the corresponding file in `agents/definitions/`. These contain the agent's persona, principles, and behavioural guidance.

#### Verify Mesh Registration

The setup script automatically registers all agents in the `agent-registry` index. Every agent with the **Agent Registry** index search tool can discover other agents via semantic search — the orchestrator uses it for routing, and specialist agents use it to find peers for cross-domain collaboration.

You can verify the registrations in Kibana Dev Tools:

```
GET agent-registry/_search
```

The registry entries below are created automatically. They're documented here for reference and customisation.

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

#### Seed Knowledge Bases

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

### Web Search Integration (MCP — Optional but Recommended)

Web search gives agents the ability to research current threats, regulations, and technical documentation in real time. It is provided via an **MCP (Model Context Protocol) server** that you bring yourself. Three agents reference web search tools: **Detection Engineering**, **Threat Intelligence**, and **Compliance**.

Without web search, these agents still function using their workflow tools and knowledge bases — but they cannot access the web for current information.

#### Setup

1. **Deploy an MCP-compatible web search server** — for example, a Vertex AI Cloud Run service with Google Search grounding, or any MCP server that provides web search capabilities.

2. **Create an MCP connector in Kibana**:
   - Navigate to **Stack Management > Connectors > Create connector**
   - Select **MCP** as the connector type
   - Configure the server URL and authentication (e.g., API key header)
   - Name it `websearch` (or your preferred name)

3. **Create the MCP tools in Agent Builder**:
   - Navigate to **Agent Builder > Tools > Create a new tool**
   - Create two tools:

   | Tool ID | Type | Description |
   |---------|------|-------------|
   | `websearch.web_search` | MCP | Search the web using your MCP server. Returns a grounded research summary with source URLs. Use for finding threat research, regulatory updates, technical documentation, or any public information. |
   | `websearch.fetch_webpage` | MCP | Fetch a web page and extract its readable text content. Use after `web_search` to read specific pages in full — articles, reports, documentation. Returns clean text with headings preserved. |

4. **Run `agents-only`** — the setup script automatically references these tool IDs when creating agents. After creating the tools, re-run the agent sync and they'll be attached to Detection Engineering, Threat Intelligence, and Compliance automatically.

#### Example: Vertex AI Cloud Run

Our reference implementation uses a Vertex AI Cloud Run service with Gemini + Google Search grounding. The MCP server exposes `web_search` and `fetch_webpage` tools, and authentication is handled via an API key header. This provides the same search quality as Google Search with AI-synthesised summaries and source citations.

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
