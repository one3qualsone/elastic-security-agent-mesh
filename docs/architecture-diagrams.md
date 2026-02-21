# Architecture Diagrams

Visual reference for the Security Agent Mesh architecture. All diagrams use [Mermaid](https://mermaid.js.org/) syntax and render natively in GitHub, GitLab, Notion, and most Markdown viewers.

---

## Table of Contents

- [High-Level Architecture](#high-level-architecture)
- [Agent Mesh Topology](#agent-mesh-topology)
- [Request Routing Flow](#request-routing-flow)
- [Alert-Triggered Investigation Flow](#alert-triggered-investigation-flow)
- [Investigation Context Lifecycle](#investigation-context-lifecycle)
- [Governance Decision Flow](#governance-decision-flow)
- [Feedback Loops](#feedback-loops)
- [Detection Engineering Agent Toolchain](#detection-engineering-agent-toolchain)
- [Knowledge Base Architecture](#knowledge-base-architecture)
- [Index Relationships](#index-relationships)
- [Deployment Pipeline](#deployment-pipeline)

---

## High-Level Architecture

The six layers of the mesh, from user-facing to infrastructure.

```mermaid
graph TB
    subgraph "Layer 1 — Orchestrator"
        ORCH[Orchestrator Agent]
    end

    subgraph "Layer 2 — Specialist Agents"
        DE[Detection Engineering]
        TI[Threat Intelligence]
        L1[L1 Triage Analyst]
        L2[L2 Investigation Analyst]
        FO[Forensics]
        CO[Compliance]
        SO[SOC Operations]
    end

    subgraph "Layer 3 — Shared Tool Workflows"
        ENR[Enrichment<br/>IP, Hash, Domain]
        SRC[Search<br/>Semantic, Web]
        CAS[Cases<br/>Create, Update]
        VT[VirusTotal<br/>Hash, IP, URL, Domain]
        ALR[Alerts<br/>Query, Tag]
        GOV[Governance<br/>Check, Approve, Log]
        INV[Investigation<br/>Create, Evidence, Status]
    end

    subgraph "Layer 4 — Knowledge Management"
        KB["kb-* indices<br/>(11 domain-specific knowledge bases)"]
    end

    subgraph "Layer 5 — Investigation Context"
        IC[investigation-contexts index]
    end

    subgraph "Layer 6 — Governance Framework"
        AP[action-policies index]
    end

    subgraph "Feedback Loops"
        FL1[Detection Quality]
        FL2[Noisy Rules]
        FL3[Incident Learning]
    end

    ORCH -->|semantic routing| DE & TI & L1 & L2 & FO & CO & SO
    DE & TI & L1 & L2 & FO & CO & SO --> ENR & SRC & CAS & VT & ALR & GOV & INV
    DE & TI & L1 & L2 & FO & CO & SO --> KB
    INV --> IC
    GOV --> AP
    FL1 & FL2 --> KB
    FL3 --> KB & IC

    style ORCH fill:#0077CC,color:#fff
    style DE fill:#00BFB3,color:#fff
    style TI fill:#00BFB3,color:#fff
    style L1 fill:#00BFB3,color:#fff
    style L2 fill:#00BFB3,color:#fff
    style FO fill:#00BFB3,color:#fff
    style CO fill:#00BFB3,color:#fff
    style SO fill:#00BFB3,color:#fff
    style IC fill:#F04E98,color:#fff
    style AP fill:#F04E98,color:#fff
    style KB fill:#FEC514,color:#000
```

---

## Agent Mesh Topology

How agents discover and invoke each other. Solid lines are direct invocations; dashed lines are semantic discovery via the registry.

```mermaid
graph LR
    REG[(agent-registry<br/>index)]

    ORCH[Orchestrator]
    DE[Detection<br/>Engineering]
    TI[Threat<br/>Intelligence]
    L1[L1 Triage<br/>Analyst]
    L2[L2 Investigation<br/>Analyst]
    FO[Forensics]
    CO[Compliance]
    SO[SOC Ops]

    ORCH -.->|search-agent-registry| REG
    REG -.->|returns best match| ORCH

    ORCH ==>|route| DE
    ORCH ==>|route| TI
    ORCH ==>|route| L1
    ORCH ==>|route| L2
    ORCH ==>|route| FO
    ORCH ==>|route| CO
    ORCH ==>|route| SO

    L1 -->|"escalate complex"| L2
    L2 -->|"enrich IOC"| TI
    L2 -->|"deep investigation"| FO
    L2 -->|"create rule"| DE
    DE -->|"check coverage"| TI
    FO -->|"notify team"| SO

    style REG fill:#FEC514,color:#000
    style ORCH fill:#0077CC,color:#fff
```

---

## Request Routing Flow

Three entry patterns into the mesh: user requests, alert triggers, and agent-to-agent handoffs.

```mermaid
flowchart TD
    subgraph "Entry Points"
        USER[User / Kibana Chat]
        ALERT[Security Alert]
        AGENT[Another Agent]
    end

    subgraph "Routing"
        ORCH[Orchestrator Agent]
        TRIAGE[mesh-automated-triaging.yaml]
        DIRECT[Direct Agent Invocation]
    end

    subgraph "Agent Registry"
        REG[(agent-registry)]
        SEM[Semantic Search<br/>on description + keywords]
    end

    subgraph "Specialist Agents"
        BEST[Best-Match Agent]
    end

    USER -->|"natural language request"| ORCH
    ALERT -->|"alert trigger"| TRIAGE
    AGENT -->|"kibana.post_agent_builder_converse"| DIRECT

    ORCH -->|"search-agent-registry.yaml"| SEM
    SEM --> REG
    REG -->|"top match"| ORCH
    ORCH -->|"invoke"| BEST

    TRIAGE -->|"search registry for analyst"| SEM
    TRIAGE -->|"invoke analyst"| BEST

    DIRECT --> BEST

    style USER fill:#0077CC,color:#fff
    style ALERT fill:#F04E98,color:#fff
    style AGENT fill:#00BFB3,color:#fff
```

---

## Alert-Triggered Investigation Flow

End-to-end flow from a security alert through triage, investigation, governance, case creation, and feedback.

```mermaid
sequenceDiagram
    participant Alert as Security Alert
    participant Triage as Triage Workflow
    participant IC as investigation-contexts
    participant Registry as agent-registry
    participant L1 as L1 Triage Analyst
    participant L2 as L2 Investigation Analyst
    participant TI as Threat Intel Agent
    participant Gov as Governance Workflows
    participant AP as action-policies
    participant Cases as Elastic Cases
    participant KB as kb-incidents

    Alert->>Triage: Alert triggers workflow
    Triage->>IC: Create investigation context
    Triage->>Registry: Search for triage agent
    Registry-->>Triage: Return L1 agent ID
    Triage->>L1: Invoke with alert details

    L1->>IC: Add initial triage evidence
    L1->>L1: Classify alert (TP/FP)
    Note over L1: Complex incident — escalate to L2
    L1->>L2: Escalate with triage context

    L2->>TI: Request IOC enrichment
    TI->>IC: Add enrichment evidence
    TI-->>L2: Return enrichment results

    L2->>Gov: check-action-policy("isolate_host")
    Gov->>AP: Look up policy
    AP-->>Gov: tier_2, requires_approval: true
    Gov-->>L2: Approval required

    L2->>IC: Add to pending_actions
    L2->>Gov: request-approval
    Gov->>Cases: Create approval case
    Note over Cases: Human reviews and approves in Kibana

    L2->>Gov: log-decision (approved)
    Gov->>IC: Record in actions_taken

    L2->>Cases: Create case with evidence
    L2->>IC: Update status → resolved

    Note over IC,KB: On resolution
    IC->>KB: record-incident-resolution
    KB->>KB: Store in kb-incidents
```

---

## Investigation Context Lifecycle

State transitions and which agents/workflows interact at each stage.

```mermaid
stateDiagram-v2
    [*] --> open: Triage workflow creates context

    open --> investigating: L1 or L2 agent assigned
    investigating --> investigating: Evidence added by any agent
    investigating --> escalated: Tier 2 action proposed
    escalated --> investigating: Approval granted, action taken
    escalated --> investigating: Approval denied, alternative path
    investigating --> resolved: Investigation complete
    resolved --> closed: Feedback captured

    closed --> [*]

    state open {
        [*] --> created
        created --> alert_fetched: Alert details retrieved
        alert_fetched --> agent_assigned: Registry search finds analyst
    }

    state investigating {
        [*] --> triaging
        triaging --> enriching: Agent requests enrichment
        enriching --> analysing: Evidence added
        analysing --> action_proposed: Agent proposes action
        action_proposed --> triaging: More investigation needed
    }

    state resolved {
        [*] --> case_created
        case_created --> summary_written: Semantic summary updated
    }

    state closed {
        [*] --> resolution_captured
        resolution_captured --> kb_updated: Written to kb-incidents
    }
```

---

## Governance Decision Flow

How agents check and execute actions through the governance framework.

```mermaid
flowchart TD
    AGENT[Agent wants to<br/>take an action]
    CHECK[check-action-policy.yaml]
    AP[(action-policies<br/>index)]

    AGENT -->|"action_type + agent_id"| CHECK
    CHECK --> AP
    AP --> CHECK

    CHECK --> T0{Tier 0?}
    CHECK --> T1{Tier 1?}
    CHECK --> T2{Tier 2?}

    T0 -->|"Yes"| EXEC0[Execute immediately]
    EXEC0 --> LOG0[log-decision.yaml]
    LOG0 --> IC0[(investigation-contexts)]

    T1 -->|"Yes"| THRESH{Confidence ≥ threshold?<br/>Blast radius ≤ limit?}
    THRESH -->|"Both met"| EXEC1[Execute with guardrails]
    EXEC1 --> LOG1[log-decision.yaml]
    LOG1 --> IC1[(investigation-contexts)]
    THRESH -->|"Not met"| QUEUE[Queue for review]

    T2 -->|"Yes"| PROPOSE[propose-action.yaml]
    PROPOSE --> IC2[(investigation-contexts<br/>pending_actions)]
    PROPOSE --> APPROVE[request-approval.yaml]
    APPROVE --> CASE[Elastic Case<br/>Approval Required]
    CASE -->|"Human approves"| EXEC2[Execute action]
    EXEC2 --> LOG2[log-decision.yaml]
    LOG2 --> IC3[(investigation-contexts)]
    CASE -->|"Human denies"| DENY[Log denial, suggest alternative]

    style AGENT fill:#00BFB3,color:#fff
    style AP fill:#F04E98,color:#fff
    style CASE fill:#0077CC,color:#fff
    style T0 fill:#22C55E,color:#fff
    style T1 fill:#F59E0B,color:#000
    style T2 fill:#EF4444,color:#fff
```

---

## Feedback Loops

Three automated loops that make the system self-improving.

```mermaid
flowchart LR
    subgraph "Detection Quality Loop"
        direction TB
        AQ1[".alerts-security*<br/>(TP/FP tags)"]
        AGG1[aggregate-detection-feedback.yaml<br/>Daily scheduled]
        KB1[(kb-detection-rules)]
        DE1[Detection Engineering Agent<br/>reads quality metrics]

        AQ1 -->|"query"| AGG1
        AGG1 -->|"write summary"| KB1
        KB1 -->|"informs rule tuning"| DE1
    end

    subgraph "Noisy Rule Loop"
        direction TB
        AQ2[".alerts-security*<br/>(alert volumes)"]
        AGG2[flag-noisy-rules.yaml<br/>Daily scheduled]
        KB2[(kb-detection-rules)]
        DE2[Detection Engineering Agent<br/>reviews flagged rules]

        AQ2 -->|"aggregate"| AGG2
        AGG2 -->|"write report"| KB2
        KB2 -->|"trigger review"| DE2
    end

    subgraph "Incident Learning Loop"
        direction TB
        IC[investigation-contexts<br/>status: resolved]
        RES[record-incident-resolution.yaml<br/>On resolution]
        KB3[(kb-incidents)]
        AGS[All agents<br/>search for similar cases]

        IC -->|"capture"| RES
        RES -->|"write outcome"| KB3
        KB3 -->|"semantic search"| AGS
    end

    style AQ1 fill:#F04E98,color:#fff
    style AQ2 fill:#F04E98,color:#fff
    style IC fill:#F04E98,color:#fff
    style KB1 fill:#FEC514,color:#000
    style KB2 fill:#FEC514,color:#000
    style KB3 fill:#FEC514,color:#000
```

---

## Detection Engineering Agent Toolchain

All tools available to the Detection Engineering Agent and how they connect.

```mermaid
flowchart TD
    DE[Detection Engineering Agent]

    subgraph "Detection Rule Lifecycle"
        LIST["list-detection-rules.yaml<br/>Browse existing rules"]
        GET["get-rule-details.yaml<br/>Full rule inspection"]
        CREATE["create-detection-rule.yaml<br/>Draft new rule — disabled"]
        TOGGLE["enable-disable-rule.yaml<br/>Toggle rule state"]
    end

    subgraph "Coverage Analysis"
        MITRE["evaluate-mitre-coverage.yaml<br/>Gap analysis vs ATT&CK"]
        SEARCH_T["search-rules-by-technique.yaml<br/>Find rules for a technique"]
        FIELD["check-field-availability.yaml<br/>Verify ECS fields in data"]
    end

    subgraph "Knowledge & Context"
        KBS["semantic-knowledge-search.yaml<br/>Search kb-detection-rules,<br/>kb-mitre-attack, kb-ecs-schema"]
        CINV["create-investigation.yaml<br/>Start investigation context"]
        AEVD["add-evidence.yaml<br/>Record findings"]
    end

    subgraph "Governance"
        CPOL["check-action-policy.yaml<br/>Verify action tier"]
    end

    subgraph "Kibana Detection Engine API"
        KAPI["/api/detection_engine/rules"]
    end

    subgraph "Elasticsearch"
        LOGS["logs-* indices"]
        KBIDX["kb-* indices"]
        ICIDX["investigation-contexts"]
    end

    DE --> LIST
    DE --> GET
    DE --> CREATE
    DE --> TOGGLE
    DE --> MITRE
    DE --> SEARCH_T
    DE --> FIELD
    DE --> KBS
    DE --> CINV
    DE --> AEVD
    DE --> CPOL

    LIST --> KAPI
    GET --> KAPI
    CREATE --> KAPI
    TOGGLE --> KAPI

    FIELD --> LOGS
    KBS --> KBIDX
    CINV --> ICIDX
    AEVD --> ICIDX
    MITRE --> KAPI
    MITRE --> KBIDX

    style DE fill:#00BFB3,color:#fff
    style KAPI fill:#0077CC,color:#fff
    style CPOL fill:#EF4444,color:#fff
```

---

## Knowledge Base Architecture

How knowledge bases are structured, accessed, and updated.

```mermaid
flowchart TD
    subgraph "Agents (Consumers & Producers)"
        DE[Detection Engineering]
        TI[Threat Intelligence]
        L1[L1 Triage Analyst]
        L2[L2 Investigation Analyst]
        FO[Forensics]
        CO[Compliance]
        SO[SOC Operations]
    end

    subgraph "Access Pattern"
        SEARCH[semantic-knowledge-search.yaml<br/>Parameterised by index_name]
        ADD[add-knowledge-document.yaml]
        UPD[update-knowledge-document.yaml]
        REM[remove-knowledge-document.yaml]
        STALE[check-knowledge-staleness.yaml]
    end

    subgraph "Knowledge Bases (Elasticsearch)"
        KB_DR[(kb-detection-rules)]
        KB_ECS[(kb-ecs-schema)]
        KB_MITRE[(kb-mitre-attack)]
        KB_TI[(kb-threat-intel)]
        KB_IOC[(kb-ioc-history)]
        KB_INC[(kb-incidents)]
        KB_PB[(kb-playbooks)]
        KB_FOR[(kb-forensics)]
        KB_COMP[(kb-compliance)]
        KB_OPS[(kb-soc-ops)]
        KB_RUN[(kb-runbooks)]
    end

    subgraph "Feedback Loops (Writers)"
        FL1[aggregate-detection-feedback]
        FL2[flag-noisy-rules]
        FL3[record-incident-resolution]
    end

    subgraph "Inference"
        E5["multilingual-e5-small<br/>inference endpoint"]
    end

    DE & TI & L1 & L2 & FO & CO & SO --> SEARCH & ADD & UPD
    SEARCH --> KB_DR & KB_ECS & KB_MITRE & KB_TI & KB_IOC & KB_INC & KB_PB & KB_FOR & KB_COMP & KB_OPS & KB_RUN
    ADD & UPD --> KB_DR & KB_ECS & KB_MITRE & KB_TI & KB_IOC & KB_INC & KB_PB & KB_FOR & KB_COMP & KB_OPS & KB_RUN

    FL1 --> KB_DR
    FL2 --> KB_DR
    FL3 --> KB_INC

    KB_DR & KB_ECS & KB_MITRE & KB_TI & KB_IOC & KB_INC & KB_PB & KB_FOR & KB_COMP & KB_OPS & KB_RUN ---|"semantic_summary field"| E5

    style E5 fill:#0077CC,color:#fff
    style SEARCH fill:#00BFB3,color:#fff
```

---

## Index Relationships

All Elasticsearch indices in the mesh and how they connect.

```mermaid
erDiagram
    AGENT-REGISTRY {
        keyword agent_name
        keyword domain
        keyword capabilities
        semantic_text semantic_description
        keyword keywords
        keyword agent_id
    }

    INVESTIGATION-CONTEXTS {
        keyword investigation_id
        keyword trigger_type
        keyword status
        text title
        nested evidence
        nested actions_taken
        nested pending_actions
        semantic_text semantic_summary
    }

    ACTION-POLICIES {
        keyword action_type
        keyword risk_tier
        keyword allowed_callers
        boolean requires_approval
        keyword approval_channel
        object auto_approve
        keyword rollback_workflow
    }

    KB-KNOWLEDGE-BASE {
        text title
        text content
        semantic_text semantic_summary
        keyword category
        keyword source
        keyword tags
        date created_at
        date updated_at
        object metadata
    }

    ELASTIC-CASES {
        keyword case_id
        text title
        text description
        keyword status
        keyword severity
        keyword tags
    }

    ALERTS-SECURITY {
        keyword rule_id
        keyword rule_name
        keyword severity
        keyword tags
        date timestamp
    }

    AGENT-REGISTRY ||--o{ INVESTIGATION-CONTEXTS : "agents participate in"
    INVESTIGATION-CONTEXTS ||--o{ ACTION-POLICIES : "actions checked against"
    INVESTIGATION-CONTEXTS ||--o| ELASTIC-CASES : "creates case when warranted"
    ALERTS-SECURITY ||--o{ INVESTIGATION-CONTEXTS : "triggers investigation"
    ALERTS-SECURITY ||--o{ KB-KNOWLEDGE-BASE : "feedback loops write to"
    INVESTIGATION-CONTEXTS ||--o{ KB-KNOWLEDGE-BASE : "resolution captured in"
```

---

## Deployment Pipeline

How the repository is deployed to an Elastic Cloud environment.

```mermaid
flowchart TD
    subgraph "Repository"
        YAML[Workflow YAML files]
        DEFS[Agent definition files]
        SCRIPT[scripts/setup.py]
    end

    subgraph "Environment Variables"
        ENV["ELASTIC_CLOUD_URL<br/>KIBANA_URL<br/>ES_API_KEY<br/>KIBANA_API_KEY<br/>INFERENCE_ENDPOINT_ID"]
    end

    subgraph "Automated (setup.py)"
        IDX[Create Elasticsearch indices<br/>agent-registry<br/>investigation-contexts<br/>action-policies<br/>kb-*]
        SEED[Seed governance policies<br/>Tier 0/1/2 defaults]
        IMP[Import workflows<br/>POST /api/workflows]
    end

    subgraph "Manual (post-setup)"
        ML[Deploy multilingual-e5-small<br/>ML > Trained Models]
        LLM[Create LLM connector<br/>Stack Management > Connectors]
        AB[Create agents in Agent Builder<br/>Using definition files]
        REG[Register agents in mesh<br/>Run register-agent workflow]
        POP[Seed knowledge bases<br/>MITRE, ECS, existing rules]
    end

    subgraph "Elastic Cloud"
        ES[(Elasticsearch)]
        KIB[Kibana]
        AGENTS[Agent Builder]
        WF[Workflows Engine]
    end

    ENV --> SCRIPT
    YAML --> SCRIPT
    SCRIPT --> IDX --> ES
    SCRIPT --> SEED --> ES
    SCRIPT --> IMP --> WF

    ML --> ES
    LLM --> KIB
    DEFS --> AB --> AGENTS
    AB --> REG --> ES

    style SCRIPT fill:#00BFB3,color:#fff
    style ES fill:#0077CC,color:#fff
    style KIB fill:#0077CC,color:#fff
```
