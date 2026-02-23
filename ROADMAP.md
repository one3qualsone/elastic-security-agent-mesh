# Roadmap

What's built today is an MVP. The mesh works — agents investigate, collaborate, and take actions with governance controls. But there's a lot more to do.

## Near-term

- **Alert-triggered automation** — workflows that fire when alerts land, running a full triage cycle without human initiation
- **Periodic agent reviews** — scheduled triggers for agents to review detection quality, knowledge staleness, and coverage gaps on their own
- **Knowledge base seeding** — bulk-load MITRE ATT&CK, ECS field definitions, and prebuilt rule metadata into the `kb-*` indices
- **Dashboard** — Kibana dashboard for agent activity, routing decisions, and knowledge base health
- **Cost and token monitoring** — track LLM usage per agent to understand operational cost

## Medium-term

- **Agent-created workflows** — agents observe patterns in their work and propose new reusable workflows (Elastic's skills concept)
- **Extended integrations** — Slack-based approval gates, PagerDuty escalation, Caldera adversary emulation
- **New specialist agents** — vulnerability management, cloud security posture, identity and access review
- **Bulk SIEM migration tooling** — dedicated mode for translating rule sets from Sentinel, Splunk, and QRadar at scale

## Long-term

- **Agents managing agents** — the mesh proposes new specialist agents with suggested instructions and tools when coverage gaps are identified
- **Self-modifying behaviour** — agents that reason about their own operating rules and propose changes to their instructions and governance policies
- **Shifting the human role** — from operator to supervisor to governor, with agents leading and humans setting boundaries
