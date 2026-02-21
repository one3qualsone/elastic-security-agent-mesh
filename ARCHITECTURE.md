# Security Agent Mesh — Architecture

This document describes the architecture for a **mesh of specialised security AI agents** orchestrated through Elastic Workflows and the Elastic Agent Builder. Each agent is an expert in a narrow domain, backed by its own knowledge base and tooling, and reachable by any other agent through a shared routing layer.

---

## Table of Contents

- [Design Principles](#design-principles)
- [High-Level Architecture](#high-level-architecture)
- [Layer 1 — Orchestrator (Router)](#layer-1--orchestrator-router)
- [Layer 2 — Specialist Agents](#layer-2--specialist-agents)
- [Layer 3 — Shared Tool Workflows](#layer-3--shared-tool-workflows)
- [Layer 4 — Knowledge Management](#layer-4--knowledge-management)
- [Layer 5 — Investigation Context](#layer-5--investigation-context)
- [Layer 6 — Governance Framework](#layer-6--governance-framework)
- [Feedback Loops](#feedback-loops)
- [Agent Registry](#agent-registry)
- [Interaction Models](#interaction-models)
- [Cases Philosophy](#cases-philosophy)
- [Schema Normalisation Philosophy](#schema-normalisation-philosophy)
- [Security & Access Control](#security--access-control)
- [Repository Structure](#repository-structure)
- [Deployment Model](#deployment-model)

---

## Design Principles

| # | Principle | Rationale |
|---|-----------|-----------|
| 1 | **Single responsibility per agent** | Each agent is an expert in one domain. This keeps system instructions focused, knowledge bases lean, and hallucination risk low. |
| 2 | **Schema-first, not data-source-first** | Detections and queries target ECS/OCSF normalised fields, not specific integrations. This makes rules portable across data sources. |
| 3 | **Agents discover each other at runtime** | An `agent-registry` index means new agents can be added without modifying every other agent or workflow. |
| 4 | **Knowledge is mutable** | Agents can write back to their knowledge bases — adding documents from resolved incidents, removing stale content, and ingesting external sources on a schedule. |
| 5 | **Workflows are the glue** | Agent Builder agents own reasoning; workflows own orchestration, API calls, and side-effects (cases, host isolation, enrichment, etc.). |
| 6 | **Direct or orchestrated access** | Users can go straight to a specialist agent for focused work, or use the orchestrator to have the mesh figure out the right expert. |
| 7 | **Governance-first autonomy** | Every action type has a risk tier. Tier 0 actions are fully autonomous; Tier 1 requires confidence thresholds; Tier 2 requires human approval. No ungated high-risk actions. |
| 8 | **Feedback loops close the loop** | Scheduled workflows aggregate alert quality data, flag noisy rules, and capture incident resolutions — making the system self-improving, not just automated. |
| 9 | **Investigation context is shared state** | Multi-agent investigations use a shared `investigation-contexts` index so evidence, actions, and proposals flow between agents with full audit trail. |

---

## High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                          USER / TRIGGER                              │
│            (Kibana UI · Workflow API · Alert · Schedule)              │
└────────────────────────────┬─────────────────────────────────────────┘
                             │
                 ┌───────────▼────────────┐
                 │     ORCHESTRATOR       │
                 │   (Router Agent or     │
                 │    Router Workflow)     │
                 │                        │
                 │  1. Classify request   │
                 │  2. Search registry    │
                 │  3. Route to agent     │
                 └──┬──┬──┬──┬──┬──┬──┬──┘
                    │  │  │  │  │  │  │
       ┌────────────┘  │  │  │  │  │  └────────────┐
       ▼               ▼  ▼  ▼  ▼  ▼               ▼
  ┌─────────┐  ┌─────────────────────────┐  ┌───────────┐
  │Detection│  │Compliance│ThreatIntel│  │  │ Forensics │
  │Engineer │  │  Agent   │  Agent    │  │  │   Agent   │
  └────┬────┘  └────┬─────┴────┬──────┘  │  └─────┬─────┘
       │            │          │          │        │
       │    ┌───────┴──────────┴──────────┴────────┘
       │    │
       ▼    ▼
  ┌────────────────────────────────────────────────────┐
  │           INVESTIGATION CONTEXT                     │
  │  (Shared state · Evidence chain · Action log ·      │
  │   Pending approvals · Semantic search on history)   │
  └────────────────────────┬───────────────────────────┘
                           │
  ┌────────────────────────▼───────────────────────────┐
  │            GOVERNANCE FRAMEWORK                     │
  │  (Action policies · Risk tiers · Approval gates ·   │
  │   Decision logging · Blast-radius controls)         │
  └────────────────────────┬───────────────────────────┘
                           │
  ┌────────────────────────▼───────────────────────────┐
  │              SHARED TOOL WORKFLOWS                  │
  │  (Web Search · Enrichment · Case Mgmt ·             │
  │   Endpoint Actions · Knowledge CRUD · ES Queries)   │
  └────────────────────────┬───────────────────────────┘
                           │
  ┌────────────────────────▼───────────────────────────┐
  │              KNOWLEDGE BASES (ES Indices)           │
  │  kb-detection-rules · kb-compliance · kb-threat    │
  │  kb-incidents · kb-soc-ops · kb-forensics          │
  │  agent-registry · investigation-contexts ·         │
  │  action-policies                                   │
  └────────────────────────────────────────────────────┘
                           │
  ┌────────────────────────▼───────────────────────────┐
  │              FEEDBACK LOOPS (Scheduled)             │
  │  Detection quality · Noisy rule flagging ·          │
  │  Incident resolution capture · Knowledge refresh    │
  └────────────────────────────────────────────────────┘
```

---

## Layer 1 — Orchestrator (Router)

The orchestrator is the entry point when a user doesn't know (or care) which specialist to talk to. It can be implemented as either:

- **An Agent Builder agent** with a system instruction to classify and route, plus a "call sub-agent" tool workflow, or
- **A workflow** that uses an LLM classify step followed by a registry lookup and sub-agent invocation.

### How routing works

1. User sends a natural language request.
2. The orchestrator asks the LLM to classify the domain(s) involved (detection engineering, compliance, threat intel, etc.).
3. A semantic search is run against the `agent-registry` index to find the best matching agent(s).
4. The orchestrator invokes the chosen agent via `kibana.post_agent_builder_converse` (using the `call-subagent-workflow` pattern).
5. If the specialist determines it needs another agent (e.g., the detection engineering agent needs threat intel), it can invoke the orchestrator or call the sub-agent workflow directly with a known agent ID.

### Why an Agent Builder agent is preferred for the orchestrator

An Agent Builder agent can hold a conversation, remember prior context, and reason about which specialist to involve. A pure workflow is stateless per execution. For a routing layer that might need to ask clarifying questions or chain multiple specialists in a single conversation, an agent is the better fit.

---

## Layer 2 — Specialist Agents

Each specialist is created in Elastic Agent Builder with:

| Component | Purpose |
|-----------|---------|
| **System instructions** | Domain expertise, persona, constraints, output format expectations |
| **Knowledge bases** | One or more ES indices with semantic search fields |
| **Tool workflows** | Workflows registered as agent tools for taking action |

### Proposed Agents

#### 1. Detection Engineering Agent (Phase 1 — priority)

**Domain:** Detection rule lifecycle — creation, migration, gap analysis, schema normalisation.

**Knowledge bases:**
- `kb-detection-rules` — All current Elastic detection rules (name, description, query, MITRE mapping, severity, data sources, enabled status)
- `kb-ecs-schema` — ECS field definitions and mappings so the agent can normalise queries
- `kb-sigma-rules` — Sigma rule repository for cross-platform detection reference
- `kb-mitre-attack` — MITRE ATT&CK techniques and sub-techniques

**Tool workflows:**
- List all detection rules (with enabled/disabled status)
- Get rule details by ID or name
- Create a new detection rule
- Enable/disable a rule
- Search rules by MITRE technique
- Translate KQL/SPL/Sigma to ES|QL
- Evaluate MITRE coverage gaps
- Search logs for field availability (confirm data sources support a rule)

**Key behaviours:**
- When asked to migrate a rule from Sentinel/Splunk, it reads the source query, understands the detection logic, checks if an equivalent Elastic rule already exists, and if not, creates one using normalised ECS fields rather than integration-specific fields.
- When asked about coverage, it maps existing rules to MITRE ATT&CK and highlights gaps.
- Always prefers `logs-*` with ECS field filters over integration-specific index patterns.

#### 2. Compliance Agent

**Domain:** Regulatory frameworks, control mapping, audit readiness.

**Knowledge bases:**
- `kb-compliance` — DORA, ISO 27001, ISO 42001, GDPR, NIS2, PCI-DSS, SOX, NIST CSF, CIS Controls

**Tool workflows:**
- Semantic knowledge search (existing)
- Search detection rules (to map controls to detections)
- Web search (for regulatory updates)

**Key behaviours:**
- Maps regulatory controls to existing detection rules and identifies gaps.
- Answers "are we compliant with X?" by checking what controls are covered by our detections, logging, and response capabilities.

#### 3. Threat Intelligence Agent

**Domain:** IOC enrichment, threat research, campaign tracking.

**Knowledge bases:**
- `kb-threat-intel` — Known threat actors, campaigns, TTPs
- `kb-ioc-history` — Previously investigated IOCs and verdicts

**Tool workflows:**
- VirusTotal hash/IP lookup (existing)
- AbuseIPDB reputation check (existing)
- URLScan threat scan (existing)
- Web search / Brave search (existing)
- MITRE ATT&CK technique lookup

**Key behaviours:**
- When given an IOC, runs it through all available enrichment tools and returns a consolidated verdict.
- Can research emerging threats using web search and summarise findings.
- Maintains a history of investigated IOCs to avoid repeated lookups.

#### 4a. L1 Triage Analyst

**Domain:** High-volume alert triage, classification, escalation.

**Knowledge bases:**
- `kb-incidents` — Previously resolved incidents (what happened, how it was resolved, lessons learned)
- `kb-playbooks` — SOC playbooks and standard operating procedures

**Tool workflows:**
- Search alerts (builtin `security.alerts`)
- Tag alerts (TP/FP)
- Close/acknowledge alerts
- Create cases (for escalation)
- Link alerts to existing cases
- Get case details (to avoid duplicates)

**Key behaviours:**
- Fast first-responder for all alerts. Classifies quickly using playbooks and historical data.
- Creates cases when an alert warrants formal tracking, links related alerts to existing cases.
- Escalates to the L2 Investigation Analyst for complex incidents requiring deep investigation.

#### 4b. L2 Investigation Analyst

**Domain:** Deep investigation, case lifecycle management, cross-agent coordination.

**Knowledge bases:**
- `kb-incidents` — Previously resolved incidents (what happened, how it was resolved, lessons learned)
- `kb-playbooks` — SOC playbooks and standard operating procedures

**Tool workflows:**
- Full case lifecycle: create, update status/severity, add comments, get details
- Link alerts to cases for incident correlation
- Investigation context: create, get, update status, add evidence, search similar
- Record incident resolutions as knowledge for future reference
- Invoke Threat Intel Agent, Forensics Agent, Detection Engineering Agent

**Key behaviours:**
- Owns complex investigations from start to resolution. Tracks all progress in investigation contexts and case comments.
- Updates case severity when enrichment or investigation reveals new risk (e.g., medium → high after threat intel confirms active campaign).
- Coordinates with forensics for endpoint analysis and threat intel for IOC enrichment.
- Captures resolved investigations as knowledge for the L1 analyst to reference in future triage.

#### 5. Forensics Agent

**Domain:** Deep-dive forensics, evidence collection, malware analysis, endpoint response.

**Knowledge bases:**
- `kb-forensics` — Forensic procedures, evidence collection guides, Elastic Defend response console commands

**Tool workflows:**
- Execute command on endpoint (existing `execute.yaml`)
- Execute and retrieve results (existing `execute-and-retrieve.yaml`)
- Isolate host (existing pattern from triage workflows)
- Get endpoint action status (existing)
- Timeline search (ES|QL across `logs-*`)
- Caldera integration (for controlled attack simulation/validation)

**Key behaviours:**
- When investigating a compromised host, runs structured forensic commands via the response console.
- Collects evidence (process trees, network connections, file system artefacts) and documents findings.
- Can isolate hosts and initiate containment procedures.

#### 6. SOC Operations Agent

**Domain:** Team coordination, shift management, incident management.

**Knowledge bases:**
- `kb-soc-ops` — Team rota, escalation matrix, SLA definitions, contact details
- `kb-runbooks` — Operational runbooks for common scenarios

**Tool workflows:**
- Query on-call schedule (ES|QL on `on-call-schedule`)
- Create Slack channel (existing)
- Post to Slack (existing)
- Update knowledge base (add rota changes, lessons learned)

**Key behaviours:**
- Answers "who is on call?" by querying the schedule index.
- When told about rota changes, updates the `kb-soc-ops` index.
- Manages incident coordination — creating channels, notifying teams, tracking SLAs.

#### 7. Web Search Agent

**Domain:** Real-time information retrieval from the internet.

**Knowledge bases:** None (stateless, relies on live search).

**Tool workflows:**
- Brave web search (existing `web-search.yaml`)
- RSS feed ingestion (existing `rss-feed-ingest.yaml`)

**Key behaviours:**
- Pure utility agent; other agents invoke it when they need current information.
- Returns structured summaries of search results.

---

## Layer 3 — Shared Tool Workflows

These are workflows that multiple agents share. They live in the `workflows/` directory and are registered as tools in Agent Builder for the agents that need them.

| Category | Workflows |
|----------|-----------|
| **Enrichment** | VirusTotal (hash, IP), AbuseIPDB, URLScan, GeoIP |
| **Search** | Web search, semantic knowledge search, ES|QL query runner |
| **Case Management** | Create case, update case, add comment, attach alert |
| **Alert Management** | Tag TP/FP, close, acknowledge, add note |
| **Communication** | Slack (create channel, post message, invite users — optional integration), email |
| **Endpoint Actions** | Isolate, execute command, get action status |
| **Knowledge CRUD** | Add document, update document, remove document, check staleness |
| **Agent Routing** | Call sub-agent, search agent registry |

---

## Layer 4 — Knowledge Management

Knowledge is not static. Agents must be able to read and write to their knowledge bases.

### Knowledge CRUD Workflows

| Workflow | Purpose |
|----------|---------|
| `add-knowledge-document.yaml` | Index a new document into a specified knowledge base index |
| `update-knowledge-document.yaml` | Update an existing document by ID |
| `remove-knowledge-document.yaml` | Delete a document by ID |
| `check-knowledge-staleness.yaml` | Scheduled workflow that flags documents older than a threshold |

### How knowledge is structured

Each knowledge base index uses a consistent mapping:

```json
{
  "mappings": {
    "properties": {
      "title": { "type": "text" },
      "content": { "type": "text" },
      "semantic_summary": { "type": "semantic_text" },
      "category": { "type": "keyword" },
      "source": { "type": "keyword" },
      "created_at": { "type": "date" },
      "updated_at": { "type": "date" },
      "expires_at": { "type": "date" },
      "tags": { "type": "keyword" },
      "metadata": { "type": "object", "dynamic": true }
    }
  }
}
```

The `semantic_summary` field enables semantic search via the existing `semantic-knowledge-search.yaml` pattern. The `expires_at` field allows the staleness checker to flag documents for review.

### Examples of knowledge updates

- **SOC rota change:** SOC Operations Agent receives "John is covering Monday night shift next week" → indexes a document in `kb-soc-ops` with the rota change details and an `expires_at` of the end of the shift.
- **Incident resolution:** After a case is closed, the Analyst Agent summarises the incident and indexes it in `kb-incidents` for future reference.
- **New compliance regulation:** Compliance Agent ingests a new regulatory document into `kb-compliance`.
- **Stale threat intel:** A scheduled workflow checks `kb-threat-intel` for IOCs older than 90 days and flags them for review or removal.

---

## Layer 5 — Investigation Context

Multi-agent investigations need shared state. The `investigation-contexts` index tracks the lifecycle of an investigation from alert triage through to resolution, providing a single source of truth that all agents can read from and write to.

### Index: `investigation-contexts`

```json
{
  "mappings": {
    "properties": {
      "investigation_id": { "type": "keyword" },
      "trigger_type": { "type": "keyword" },
      "trigger_ref": { "type": "keyword" },
      "status": { "type": "keyword" },
      "risk_tier": { "type": "keyword" },
      "assigned_agent": { "type": "keyword" },
      "title": { "type": "text" },
      "summary": { "type": "text" },
      "semantic_summary": { "type": "semantic_text" },
      "evidence": {
        "type": "nested",
        "properties": {
          "agent_id": { "type": "keyword" },
          "timestamp": { "type": "date" },
          "evidence_type": { "type": "keyword" },
          "content": { "type": "text" },
          "confidence": { "type": "float" },
          "references": { "type": "keyword" }
        }
      },
      "actions_taken": {
        "type": "nested",
        "properties": {
          "agent_id": { "type": "keyword" },
          "action_type": { "type": "keyword" },
          "target": { "type": "text" },
          "timestamp": { "type": "date" },
          "approved_by": { "type": "keyword" },
          "result": { "type": "text" },
          "risk_tier": { "type": "keyword" }
        }
      },
      "pending_actions": {
        "type": "nested",
        "properties": {
          "recommending_agent": { "type": "keyword" },
          "action_type": { "type": "keyword" },
          "risk_tier": { "type": "keyword" },
          "justification": { "type": "text" },
          "evidence_refs": { "type": "keyword" }
        }
      },
      "created_at": { "type": "date" },
      "updated_at": { "type": "date" },
      "resolved_at": { "type": "date" },
      "tags": { "type": "keyword" }
    }
  }
}
```

### Investigation Workflows

| Workflow | Purpose |
|----------|---------|
| `create-investigation.yaml` | Create a new investigation context |
| `add-evidence.yaml` | Append evidence from any agent |
| `get-investigation.yaml` | Retrieve current investigation state |
| `update-investigation-status.yaml` | Change status, assignment, or risk tier |
| `propose-action.yaml` | Propose a Tier 1/2 action for approval |
| `search-similar-investigations.yaml` | Semantic search on past investigations |

### How it flows

1. Alert triggers `mesh-automated-triaging.yaml` → creates investigation context
2. Analyst agent triages, adds evidence, enriches via TI agent
3. TI agent adds enrichment results as evidence to the same investigation
4. If escalation needed, analyst proposes action via `propose-action.yaml`
5. Governance checks policy → auto-approve or request human approval
6. All actions logged in `actions_taken` for full audit trail
7. On resolution, `record-incident-resolution.yaml` captures learnings in `kb-incidents`

---

## Layer 6 — Governance Framework

Every action an agent can take has a risk tier. The `action-policies` index defines what tier each action belongs to, who can call it, and what conditions must be met for autonomous execution.

### Risk Tiers

| Tier | Autonomy | Examples | Approval |
|------|----------|----------|----------|
| **Tier 0** | Fully autonomous | Tag alert, search, add knowledge, create note | None |
| **Tier 1** | Guarded autonomous | Create case, create rule (disabled), run playbook step | Auto-approve if confidence + blast-radius thresholds met |
| **Tier 2** | Human-gated | Isolate host, enable rule in production, execute command | Elastic Case created for human review |

### Index: `action-policies`

```json
{
  "mappings": {
    "properties": {
      "action_type": { "type": "keyword" },
      "risk_tier": { "type": "keyword" },
      "allowed_callers": { "type": "keyword" },
      "auto_approve": {
        "type": "object",
        "properties": {
          "min_confidence": { "type": "float" },
          "max_blast_radius": { "type": "integer" },
          "required_evidence_count": { "type": "integer" }
        }
      },
      "requires_approval": { "type": "boolean" },
      "approval_channel": { "type": "keyword" },
      "rollback_workflow": { "type": "keyword" },
      "ttl_minutes": { "type": "integer" },
      "description": { "type": "text" }
    }
  }
}
```

### Governance Workflows

| Workflow | Purpose |
|----------|---------|
| `check-action-policy.yaml` | Look up policy for an action before execution |
| `request-approval.yaml` | Create an Elastic Case for Tier 2 approval |
| `log-decision.yaml` | Record action decision in investigation context |

### How agents use governance

1. Agent decides to take an action (e.g., isolate a host)
2. Agent calls `check-action-policy` with `action_type` and `agent_id`
3. Workflow returns risk tier and approval requirements
4. If Tier 0: proceed, log via `log-decision`
5. If Tier 1: check confidence and blast radius against thresholds, proceed or queue
6. If Tier 2: call `propose-action` + `request-approval` (creates a Case), wait for human review in Kibana

### Why tiers?

The governance tiers exist because **not all agent actions carry equal risk**. Categorising by blast radius creates a pragmatic framework for progressive autonomy:

- **Tier 0 — zero blast radius.** Searching, tagging, enriching, and writing notes cannot harm the environment. There is no value in gating these actions — doing so would create unnecessary friction and slow the mesh to human speed, defeating the purpose.

- **Tier 1 — recoverable actions.** Creating a case, drafting a detection rule (disabled), or running a contained playbook step has real impact but is reversible. These run autonomously *when* the agent demonstrates sufficient confidence and the scope stays within defined limits. If the confidence is low or the blast radius exceeds the threshold, the action queues for review.

- **Tier 2 — potentially destructive.** Isolating a host, enabling a rule in production across all environments, or executing a command on an endpoint could disrupt operations if wrong. These always require explicit human approval.

The goal is **progressive trust**: start with full Tier 0 autonomy and guarded Tier 1, measure agent accuracy over time via feedback loops, and expand Tier 1 thresholds (or promote actions down a tier) as agents prove reliable. The framework is designed so the mesh becomes *more* autonomous as it earns trust, not less.

---

## Feedback Loops

These scheduled workflows make the SOC self-sustaining by closing the learning loop between detection, triage, and improvement.

### 1. Detection Quality Feedback (daily)

```
Rule fires → Analyst tags TP/FP → aggregate-detection-feedback aggregates ratios →
Writes to kb-detection-rules → Detection Engineer reviews → Rule tuned or disabled
```

### 2. Noisy Rule Identification (daily)

```
flag-noisy-rules identifies high-volume and high-FP rules →
Writes to kb-detection-rules → Detection Engineer prioritises tuning
```

### 3. Incident Learning (on resolution)

```
Investigation resolved → record-incident-resolution captures resolution →
Writes to kb-incidents → Future triage searches past incidents for patterns
```

### Feedback Workflows

| Workflow | Schedule | Purpose |
|----------|----------|---------|
| `aggregate-detection-feedback.yaml` | Every 24h | TP/FP ratios per detection rule |
| `flag-noisy-rules.yaml` | Every 24h | High-volume and high-FP rule detection |
| `record-incident-resolution.yaml` | Manual/triggered | Capture investigation resolution as knowledge |

---

## Agent Registry

The registry is an Elasticsearch index (`agent-registry`) that maps domains and capabilities to agent IDs. This is how the orchestrator (and any agent that needs to call another) discovers available agents at runtime.

### Index mapping

```json
{
  "mappings": {
    "properties": {
      "agent_id": { "type": "keyword" },
      "agent_name": { "type": "text" },
      "domain": { "type": "keyword" },
      "capabilities": { "type": "keyword" },
      "description": { "type": "text" },
      "semantic_description": { "type": "semantic_text" },
      "keywords": { "type": "keyword" },
      "status": { "type": "keyword" },
      "version": { "type": "keyword" },
      "created_at": { "type": "date" },
      "updated_at": { "type": "date" }
    }
  }
}
```

### Lookup pattern

When the orchestrator needs to find an agent:

1. Classify the request domain with LLM.
2. Run a semantic search on `agent-registry` using the `semantic_description` field.
3. Filter by `status: "active"`.
4. Take the top result's `agent_id`.
5. Invoke via `kibana.post_agent_builder_converse`.

This means adding a new agent to the mesh is as simple as:
1. Create the agent in Agent Builder.
2. Index a document in `agent-registry` with its ID, domain, and description.

No other agents or workflows need to change.

---

## Interaction Models

### 1. Direct access

The user navigates to a specific agent in the Agent Builder UI or invokes it via a workflow with a known `agent_id`. Best for focused work where the user knows exactly which expert they need.

```
User → Detection Engineering Agent
```

### 2. Orchestrated access

The user talks to the orchestrator, which routes to the right specialist. Best for ambiguous or cross-domain questions.

```
User → Orchestrator → (classifies "compliance") → Compliance Agent
```

### 3. Agent-to-agent (chained)

During execution, one agent determines it needs another specialist. It invokes the sub-agent workflow with the target agent's ID (looked up from the registry or known).

```
User → Analyst Agent → (needs enrichment) → Threat Intel Agent → (result back) → Analyst Agent
```

### 4. Alert-triggered (automated)

An alert triggers a workflow that invokes the appropriate agent(s) automatically.

```
Alert → Triage Workflow → Analyst Agent → (escalates) → Forensics Agent
```

---

## Cases Philosophy

Elastic Cases are the **human-facing output** of the agent mesh, not the inter-agent state mechanism. The distinction is important:

| Concern | Mechanism | Where |
|---------|-----------|-------|
| Agent-to-agent state | `investigation-contexts` index | Elasticsearch |
| Human-facing record | Elastic Cases | Kibana |

### How cases fit into the flow

1. **Agents investigate autonomously** — shared state lives in `investigation-contexts`, where agents read each other's evidence, propose actions, and track progress.

2. **Cases are created when warranted** — once an investigation reaches a point that requires human visibility (confirmed attack, high-severity alert, Tier 2 escalation), the analyst or triage agent creates an Elastic Case via the Kibana Cases API.

3. **Cases accumulate context** — agents attach alerts, add comments with their analysis, and update case fields as the investigation progresses.

4. **Humans review and provide feedback** — security analysts review the case, tag true/false positives, add their own observations, and close the case with a resolution.

5. **Feedback flows back** — case resolutions are captured via the `record-incident-resolution` feedback workflow and written to `kb-incidents`, improving future agent decisions.

### Why not use cases as inter-agent state?

- Cases are optimised for human workflows (comments, assignees, tags) — they lack the structured nested data model agents need (evidence arrays, confidence scores, pending actions with risk tiers).
- Writing to `investigation-contexts` is fast and schema-controlled. Agents can query by status, search semantically, and update atomically.
- Cases remain a clean, readable output that doesn't get cluttered with machine-to-machine chatter.

---

## Schema Normalisation Philosophy

A core principle of this mesh is that detections should target the **common schema** (ECS), not specific data sources.

### Why

- **Portability:** A rule written against `process.name` and `event.action` works regardless of whether the data comes from Elastic Defend, Sysmon, CrowdStrike, or any other source that maps to ECS.
- **Migration-friendly:** When migrating from Sentinel/Splunk, the detection logic is preserved but the query is rewritten to use ECS fields and `logs-*` rather than integration-specific indices.
- **Future-proof:** New data sources that map to ECS are automatically covered by existing rules.

### How the Detection Engineering Agent enforces this

1. When translating a rule, it identifies the detection logic (what behaviour is being detected).
2. It maps source-specific fields to their ECS equivalents.
3. It writes the new rule against `logs-*` with ECS field filters.
4. It uses `WHERE` clauses on ECS fields to scope the data, not index patterns.
5. It documents any fields that don't have ECS mappings and flags them for review.

---

## Security & Access Control

| Concern | Approach |
|---------|----------|
| **API keys and secrets** | Stored in `.env` (gitignored), referenced as placeholders in workflow `consts`. Never committed to git. |
| **Agent permissions** | Each agent's tool workflows define what actions it can take. An agent without the "isolate host" tool cannot isolate hosts. |
| **Knowledge base access** | Agents can only read/write to knowledge bases explicitly provided to them via tool workflows. |
| **Governance tiers** | Every action type has a policy in `action-policies`. Tier 0 is autonomous, Tier 1 is guarded, Tier 2 requires human approval. Agents check policy before acting. |
| **Audit trail** | All workflow executions are logged by Elastic. Agent conversations are persisted via Agent Builder. Investigation contexts record every evidence addition and action decision. |
| **Human-in-the-loop** | Tier 2 actions (host isolation, rule enablement in production, command execution) require approval via Elastic Cases. Approval cases include justification and evidence references for review in Kibana. |
| **Blast-radius controls** | Tier 1 policies include `max_blast_radius` limits. Actions affecting more entities than the threshold are escalated to Tier 2. |

---

## Repository Structure

The repository separates **agnostic workflows** (reusable by anyone, suitable for the official Elastic workflows repo) from **mesh-specific infrastructure** (our agent architecture).

```
elastic-security-agent/
├── .cursor/rules/                  # Cursor IDE context rules
│   └── project-context.mdc
├── scripts/                        # Setup and deployment automation
│   ├── setup.py                    # Python setup script (cross-platform)
│   └── setup.sh                    # Bash wrapper
├── workflows/
│   ├── ai-agents/                  # Generic agent invocation patterns
│   │   ├── call-subagent-workflow.yaml
│   │   └── invoke-an-agent.yaml
│   ├── knowledge/                  # Generic ES document CRUD
│   │   ├── add-knowledge-document.yaml
│   │   ├── update-knowledge-document.yaml
│   │   ├── remove-knowledge-document.yaml
│   │   └── check-knowledge-staleness.yaml
│   ├── mesh/                       # MESH-SPECIFIC — agent routing
│   │   ├── orchestrator-router.yaml
│   │   └── search-agent-registry.yaml
│   ├── investigation/              # MESH-SPECIFIC — investigation context
│   │   ├── create-investigation.yaml
│   │   ├── add-evidence.yaml
│   │   ├── get-investigation.yaml
│   │   ├── update-investigation-status.yaml
│   │   ├── propose-action.yaml
│   │   └── search-similar-investigations.yaml
│   ├── governance/                 # MESH-SPECIFIC — risk-tiered controls
│   │   ├── check-action-policy.yaml
│   │   ├── request-approval.yaml
│   │   └── log-decision.yaml
│   ├── feedback/                   # MESH-SPECIFIC — feedback loops
│   │   ├── aggregate-detection-feedback.yaml
│   │   ├── flag-noisy-rules.yaml
│   │   └── record-incident-resolution.yaml
│   ├── search/                     # Search patterns (web, semantic, ES|QL)
│   ├── security/                   # Security operations
│   │   ├── detection/              # Detection rule lifecycle workflows
│   │   ├── enrichment/             # IOC and IP enrichment
│   │   └── response/               # Triage and response workflows
│   ├── integrations/               # Third-party (Slack, Splunk, etc.)
│   ├── utilities/                  # Utility workflows
│   └── ...
├── agents/                         # MESH-SPECIFIC — agent mesh infrastructure
│   ├── definitions/                # Codified agent configs
│   │   ├── orchestrator.yaml
│   │   ├── detection-engineering.yaml
│   │   ├── threat-intelligence.yaml
│   │   ├── l1-triage-analyst.yaml
│   │   ├── l2-investigation-analyst.yaml
│   │   ├── forensics.yaml
│   │   ├── compliance.yaml
│   │   └── soc-operations.yaml
│   └── setup/                      # Bootstrap workflows for deployment
│       ├── create-agent-registry.yaml
│       ├── create-knowledge-index.yaml
│       ├── create-investigation-index.yaml
│       ├── create-action-policies-index.yaml
│       └── register-agent.yaml
├── ARCHITECTURE.md                 # This document
├── ROADMAP.md                      # Phased delivery plan
└── docs/                           # Workflow schema and concept reference
```

### What can go to the official repo

Everything under `workflows/` **except** `workflows/mesh/`, `workflows/investigation/`, `workflows/governance/`, and `workflows/feedback/`. The knowledge CRUD workflows, the agent invocation patterns, and all the security/enrichment/integration workflows are fully agnostic.

### What stays in this repo

- `workflows/mesh/` — orchestrator and registry workflows
- `workflows/investigation/` — investigation context workflows
- `workflows/governance/` — governance and approval workflows
- `workflows/feedback/` — feedback loop workflows
- `agents/` — agent definitions and setup infrastructure
- `scripts/` — deployment automation
- `ARCHITECTURE.md` and `ROADMAP.md`

---

## Deployment Model

### Quick Start

```bash
# 1. Set environment variables (see README.md for full list)
export ELASTIC_CLOUD_URL=https://your-deployment.es.region.gcp.cloud.es.io
export KIBANA_URL=https://your-deployment.kb.region.gcp.cloud.es.io
export ES_API_KEY=your-es-api-key
export KIBANA_API_KEY=your-kibana-api-key

# 2. Run the setup script
python scripts/setup.py

# 3. Follow the manual steps printed at the end
```

### How a customer deploys the mesh

The agent definitions in `agents/definitions/` are the codified source of truth. The setup script (`scripts/setup.py`) automates most of the deployment:

**Automated by setup script:**

1. **Create agent registry** — `agent-registry` index with semantic routing
2. **Create investigation contexts index** — `investigation-contexts` for shared state
3. **Create action policies index** — `action-policies` for governance tiers
4. **Create all knowledge base indices** — All `kb-*` indices with semantic search
5. **Seed default action policies** — Tier 0/1/2 policies for all action types
6. **Import all workflows** — Via Kibana `POST /s/{space}/api/workflows`

**Manual steps (printed by setup script):**

1. **Deploy inference endpoint** — `multilingual-e5-small` via Kibana ML > Trained Models
2. **Create LLM connector** — Stack Management > Connectors (Claude Sonnet, GPT-4o, etc.)
3. **Create agents in Agent Builder** — Use definition files as reference
4. **Register agents** — Run Register Agent workflow for each agent
5. **Seed knowledge bases** — Populate `kb-*` indices with domain data

### Environment Configuration

All configuration is managed via environment variables (set in your shell, CI/CD secrets, or however suits your environment — never hardcoded). See the README for the full list. Key variables:

| Variable | Purpose |
|----------|---------|
| `KIBANA_URL` | Kibana API endpoint |
| `KIBANA_SPACE` | Target space for all workflows and agents |
| `ES_API_KEY` | Elasticsearch API key for index operations |
| `KIBANA_API_KEY` | Kibana API key for workflow import |
| `INFERENCE_ENDPOINT_ID` | Embedding model for semantic_text fields |

### What the setup workflows handle

| Concern | How it's handled |
|---------|-----------------|
| **Index creation** | Setup script creates all indices with correct mappings |
| **Inference endpoint** | Referenced by `INFERENCE_ENDPOINT_ID` — must be deployed manually first |
| **Agent registration** | `register-agent.yaml` indexes a document in `agent-registry` with semantic description |
| **Governance policies** | Setup script seeds default Tier 0/1/2 policies |
| **Workflow import** | Setup script imports all YAML files via Kibana API into the configured space |
| **Agent creation** | Manual in Agent Builder — definition files serve as the reference |

### What is NOT automated (yet)

- Agent Builder agent creation — must be done through the Kibana UI. The definition files document exactly what to configure.
- Inference endpoint deployment — manual step via Kibana ML.
- Knowledge base seeding — domain-specific and requires source data.
- GitHub Actions CI/CD — planned for Phase 7.
