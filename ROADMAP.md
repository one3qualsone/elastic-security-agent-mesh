# Security Agent Mesh — Roadmap

> **This is a living document.** Update it as agents are built, priorities shift, or new ideas emerge.

---

## Phase Overview

| Phase | Focus | Status |
|-------|-------|--------|
| **Phase 0** | Foundation — registry, knowledge management, orchestrator scaffold, investigation context, governance | In progress |
| **Phase 1** | Detection Engineering Agent | In progress |
| **Phase 2** | Threat Intelligence Agent + Web Search Agent | Not started |
| **Phase 3** | Security Analyst (Triage) Agent | Not started |
| **Phase 4** | Forensics Agent | Not started |
| **Phase 5** | Compliance Agent | Not started |
| **Phase 6** | SOC Operations Agent | Not started |
| **Phase 7** | Polish — cross-agent chaining, approval gates, dashboards | Not started |

---

## Phase 0 — Foundation

**Goal:** Build the shared infrastructure that every agent depends on.

### Deliverables

- [x] **Agent Registry index** (`agent-registry`)
  - Index mapping with `semantic_description` for routing
  - Setup workflow: `agents/setup/create-agent-registry.yaml`
  - Seed documents for initial agents as they're built
- [x] **Orchestrator agent** (Agent Builder definition)
  - System instructions for request classification and routing
  - Tool: `search-agent-registry.yaml` — semantic search on registry
  - Tool: `call-subagent-workflow.yaml` — invoke agent by ID
  - Router workflow: `orchestrator-router.yaml`
- [x] **Knowledge management workflows**
  - `add-knowledge-document.yaml` — index a document into any KB index
  - `update-knowledge-document.yaml` — update by document ID
  - `remove-knowledge-document.yaml` — delete by document ID
  - `check-knowledge-staleness.yaml` — scheduled staleness scan
- [x] **Shared knowledge base index template**
  - Consistent mapping across all `kb-*` indices
  - `semantic_summary` field for semantic search
  - `expires_at` for staleness management
  - Setup workflow: `agents/setup/create-knowledge-index.yaml`
- [x] **Investigation Context** (`investigation-contexts`)
  - Index with nested evidence, actions, and pending approvals
  - Setup workflow: `agents/setup/create-investigation-index.yaml`
  - CRUD workflows: create, add-evidence, get, update-status, propose-action, search-similar
- [x] **Governance Framework** (`action-policies`)
  - Index with risk tiers, approval rules, blast-radius limits
  - Setup workflow: `agents/setup/create-action-policies-index.yaml`
  - Governance workflows: check-action-policy, request-approval, log-decision
  - Default policies seeded via setup script
- [x] **Feedback Loop Workflows**
  - `aggregate-detection-feedback.yaml` — daily TP/FP ratio aggregation
  - `flag-noisy-rules.yaml` — daily noisy rule identification
  - `record-incident-resolution.yaml` — capture resolved investigations
- [x] **Semantic Knowledge Search parameterisation**
  - `index_name` is now an input, not hardcoded — agents can search their own `kb-*` indices
- [x] **Developer setup tooling**
  - Setup instructions in `README.md`
  - `scripts/setup.py` — automated index creation, policy seeding, workflow import
  - `.cursor/rules/project-context.mdc` — session grounding for AI assistants
- [x] **Mesh-aware triage bridge**
  - `mesh-automated-triaging.yaml` — alert-triggered workflow that creates investigation context and routes to analyst agent

### Decisions needed

- [ ] Confirm Elastic Agent Builder is available on the deployment
- [ ] Choose the LLM connector for agents (e.g., Claude Sonnet, GPT-4o)
- ~~Decide on human-in-the-loop gates for high-impact actions~~ → Implemented via governance framework (Tier 0/1/2)

---

## Phase 1 — Detection Engineering Agent

**Goal:** Build the first specialist agent — an expert in detection rule lifecycle.

### Deliverables

- [x] **Agent definition** (Agent Builder)
  - System instructions covering: rule creation, migration, gap analysis, ECS normalisation
  - Persona: senior detection engineer who thinks schema-first
  - Definition: `agents/definitions/detection-engineering.yaml`
- [ ] **Knowledge bases** (need seeding)
  - [ ] `kb-detection-rules` — populate from Elastic's prebuilt rules API
  - [ ] `kb-ecs-schema` — ECS field definitions and common mappings
  - [ ] `kb-mitre-attack` — MITRE ATT&CK techniques, sub-techniques, data sources
- [x] **Tool workflows**
  - [x] `list-detection-rules.yaml` — list all rules with enabled/disabled status
  - [x] `get-rule-details.yaml` — get full rule definition by rule_id
  - [x] `create-detection-rule.yaml` — create a new rule (disabled by default)
  - [x] `enable-disable-rule.yaml` — toggle rule status (Tier 2 for enabling)
  - [x] `search-rules-by-technique.yaml` — find rules mapped to a MITRE technique
  - [x] `evaluate-mitre-coverage.yaml` — gap analysis against ATT&CK matrix
  - [x] `check-field-availability.yaml` — field_caps query to verify fields exist
  - [ ] `translate-query-to-esql.yaml` — translate KQL/SPL/Sigma to ES|QL (LLM-assisted)
- [ ] **Create agent in Agent Builder** (manual step)
- [ ] **Register in agent-registry**

### SIEM Migration Workflow (sub-deliverable)

When migrating from Microsoft Sentinel, Splunk, or another SIEM:

1. Agent receives the source rule (KQL query, SPL query, or Sigma YAML)
2. Understands the detection logic (what behaviour, what TTPs)
3. Searches `kb-detection-rules` for existing equivalent coverage
4. If covered: advises which existing rule covers it
5. If not covered: creates a new rule using ECS-normalised fields on `logs-*`
6. Validates field availability against actual log data

---

## Phase 2 — Threat Intelligence + Web Search Agents

**Goal:** Add enrichment and real-time information gathering capabilities.

### Threat Intelligence Agent

- [ ] Agent definition (Agent Builder)
- [ ] Knowledge bases
  - [ ] `kb-threat-intel` — threat actors, campaigns, TTPs
  - [ ] `kb-ioc-history` — previously investigated IOCs and verdicts
- [ ] Tool workflows
  - Reuse existing: VT hash, VT IP, AbuseIPDB, URLScan
  - [ ] `consolidated-ioc-check.yaml` — fan-out to all enrichment sources
  - [ ] `research-threat-actor.yaml` — web search + KB lookup
  - [ ] `log-ioc-verdict.yaml` — write verdict to `kb-ioc-history`
- [ ] Register in agent-registry

### Web Search Agent

- [ ] Agent definition (Agent Builder)
- [ ] Tool workflows
  - Reuse existing: `web-search.yaml`, `rss-feed-ingest.yaml`
  - [ ] `search-and-summarise.yaml` — search + LLM summary
- [ ] Register in agent-registry

---

## Phase 3 — Security Analyst (Triage) Agent

**Goal:** Automate alert triage with historical context from past incidents.

- [ ] Agent definition (Agent Builder)
- [ ] Knowledge bases
  - [ ] `kb-incidents` — resolved incidents (populated post-case-closure)
  - [ ] `kb-playbooks` — SOC standard operating procedures
- [ ] Tool workflows
  - Reuse existing: alert tagging, case creation, enrichment
  - [ ] `search-similar-incidents.yaml` — semantic search on `kb-incidents`
  - [ ] `run-playbook-step.yaml` — execute a playbook step
  - [ ] `escalate-to-agent.yaml` — hand off to forensics or other specialist
  - [ ] `record-incident-resolution.yaml` — write to `kb-incidents` when case closes
- [ ] Alert-triggered triage workflow (builds on existing `ad-automated-triaging.yaml`)
- [ ] Register in agent-registry

---

## Phase 4 — Forensics Agent

**Goal:** Deep-dive investigation and endpoint forensics via Elastic Defend.

- [ ] Agent definition (Agent Builder)
- [ ] Knowledge bases
  - [ ] `kb-forensics` — forensic procedures, evidence collection checklists, response console command reference
- [ ] Tool workflows
  - Reuse existing: `execute.yaml`, `execute-and-retrieve.yaml`, isolate host
  - [ ] `collect-process-tree.yaml` — get process ancestry for a PID
  - [ ] `collect-network-connections.yaml` — get network activity for a host
  - [ ] `collect-file-artefacts.yaml` — get file hashes and paths
  - [ ] `timeline-search.yaml` — ES|QL timeline query for a host
  - [ ] `containment-workflow.yaml` — isolate + document + notify
- [ ] Caldera integration for attack validation
- [ ] Register in agent-registry

---

## Phase 5 — Compliance Agent

**Goal:** Regulatory framework expertise with control-to-detection mapping.

- [ ] Agent definition (Agent Builder)
- [ ] Knowledge bases
  - [ ] `kb-compliance` — full text of DORA, ISO 27001, ISO 42001, GDPR, NIS2, PCI-DSS, SOX, NIST CSF, CIS Controls
- [ ] Tool workflows
  - Reuse existing: semantic knowledge search
  - [ ] `map-control-to-detections.yaml` — given a control, find matching detection rules
  - [ ] `compliance-gap-analysis.yaml` — given a framework, list unmet controls
  - [ ] `generate-audit-evidence.yaml` — pull logs/rules/configs proving a control is met
- [ ] Register in agent-registry

---

## Phase 6 — SOC Operations Agent

**Goal:** Team coordination, shift management, operational knowledge.

- [ ] Agent definition (Agent Builder)
- [ ] Knowledge bases
  - [ ] `kb-soc-ops` — team rota, escalation matrix, SLAs, contact details
  - [ ] `kb-runbooks` — operational runbooks
- [ ] Tool workflows
  - Reuse existing: Slack, on-call schedule query
  - [ ] `update-rota.yaml` — add/modify shift schedules in `kb-soc-ops`
  - [ ] `get-current-oncall.yaml` — who is on call right now
  - [ ] `escalation-workflow.yaml` — page the right person via Slack/PagerDuty
- [ ] Register in agent-registry

---

## Phase 7 — Polish & Cross-Cutting Concerns

- [ ] **Cross-agent chaining tests** — validate that agents can seamlessly invoke each other
- [ ] **Human-in-the-loop approval gates** — Slack-based approval for host isolation, rule creation in prod
- [ ] **Dashboard** — Kibana dashboard showing agent usage, routing decisions, knowledge base health
- [ ] **Scheduled knowledge refresh** — workflows to re-sync detection rules, MITRE data, compliance docs
- [ ] **Cost/token monitoring** — track LLM usage per agent
- [ ] **Error handling standardisation** — consistent retry/fallback patterns across all workflows

---

## Future Ideas (Backlog)

These are ideas that may become phases or fold into existing phases:

| Idea | Notes |
|------|-------|
| **Vulnerability Management Agent** | Integrates with vulnerability scanners (Qualys, Tenable), maps CVEs to assets and detection rules |
| **Cloud Security Agent** | Specialises in AWS/Azure/GCP misconfigurations, CSPM findings, cloud-native detections |
| **Identity & Access Agent** | Analyses IAM policies, detects privilege escalation paths, monitors identity providers |
| **Deception / Honeypot Agent** | Manages honeytokens and canary alerts, integrates with Caldera for adversary emulation |
| **Reporting Agent** | Generates executive summaries, KPI reports, board-level security posture documents |
| **Training / Simulation Agent** | Runs tabletop exercises, quizzes analysts on procedures, manages CTF challenges |
| **SIEM Migration Assistant** | Dedicated agent (or mode of Detection Engineering Agent) for bulk rule translation from Sentinel/Splunk/QRadar |
| **Alert Noise Reduction Agent** | Analyses alert volume, identifies noisy rules, suggests tuning, auto-suppresses known FPs |
| **Data Quality Agent** | Monitors ECS compliance of incoming logs, flags unmapped fields, suggests ingest pipeline fixes |

---

## Changelog

| Date | Change |
|------|--------|
| 2026-02-19 | Initial roadmap created |
| 2026-02-20 | Phase 0: Added investigation context index, workflows, and setup. Added governance framework (action-policies, check-policy, request-approval, log-decision). Added feedback loops (detection feedback, noisy rules, incident resolution). Added developer tooling (.env, setup script, Cursor rule). Fixed semantic search parameterisation. Phase 1: Built all 7 detection engineering tool workflows. Created mesh-aware triage bridge. Updated ARCHITECTURE.md with new layers. |
