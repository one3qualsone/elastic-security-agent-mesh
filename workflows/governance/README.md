# Governance Workflows

Risk-tiered control framework for autonomous agent actions. Every action type has a policy that determines whether it can be auto-approved or requires human authorisation.

## Risk Tiers

| Tier | Autonomy | Examples | Approval |
|------|----------|----------|----------|
| **Tier 0** | Fully autonomous | Tag alert, search, add knowledge, create note | None |
| **Tier 1** | Guarded autonomous | Create case, create rule (disabled), run playbook step | Auto-approve if confidence/blast-radius thresholds met |
| **Tier 2** | Human-gated | Isolate host, enable rule in production, execute command | Elastic Case created for human review |

## Prerequisites

- `action-policies` index created via `agents/setup/create-action-policies-index.yaml`
- Seed data loaded via `python scripts/setup.py --seed-policies`

## Workflows

| Workflow | Purpose |
|----------|---------|
| `check-action-policy.yaml` | Look up policy before executing an action |
| `request-approval.yaml` | Create an Elastic Case for Tier 2 approval |
| `log-decision.yaml` | Record action decision in investigation context |

## Agent Integration

Agents should call `check-action-policy` before any action. The workflow returns:
- `risk_tier`: tier_0, tier_1, tier_2
- `requires_approval`: boolean
- `policy`: full policy document

If `requires_approval` is true, the agent should call `propose-action` (investigation workflow) and `request-approval` (governance workflow) instead of executing directly.
