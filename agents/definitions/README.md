# Agent Definitions

This directory contains **codified definitions** for each specialist agent in the security mesh. These are not executable workflows — they are reference configurations that describe exactly how to create each agent in Elastic Agent Builder.

## What's in each definition file

Each YAML file documents:

| Field | Purpose |
|-------|---------|
| `agent_name` | Name as it appears in Agent Builder |
| `description` | What this agent does |
| `domain` | Primary domain for registry routing |
| `system_instructions` | The full system prompt for the agent |
| `knowledge_bases` | Which ES indices to attach as knowledge sources |
| `tools` | Which workflows to register as agent tools |
| `registry_entry` | The document to index in `agent-registry` for mesh discovery |

## How to deploy an agent

1. **Create knowledge base indices** — Run `agents/setup/create-knowledge-index.yaml` for each index listed in `knowledge_bases`.
2. **Populate knowledge bases** — Seed the indices with initial data (regulatory docs, rules, etc.).
3. **Import tool workflows** — Import each workflow listed in `tools` into Elastic via the Kibana UI or API.
4. **Create the agent in Agent Builder** — Use the `system_instructions` from the definition file. Attach the knowledge bases and tool workflows.
5. **Register the agent** — Run `agents/setup/register-agent.yaml` with the `registry_entry` values to make the agent discoverable by the orchestrator.

## Current agents

| Definition | Phase | Status |
|------------|-------|--------|
| `orchestrator.yaml` | 0 | Not deployed |
| `detection-engineering.yaml` | 1 | Not deployed |
| `threat-intelligence.yaml` | 2 | Not deployed |
| `security-analyst.yaml` | 3 | Not deployed |
| `forensics.yaml` | 4 | Not deployed |
| `compliance.yaml` | 5 | Not deployed |
| `soc-operations.yaml` | 6 | Not deployed |
