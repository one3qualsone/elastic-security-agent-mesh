#!/usr/bin/env python3
"""
Elastic Security Agent Mesh — Setup Script

Automates the deployment of indices, workflows, and agent registrations
to an Elastic Cloud deployment. Reads configuration from environment variables.

Set required variables before running (see README.md for full instructions):
    export ELASTIC_CLOUD_URL=https://your-deployment.es.region.gcp.cloud.es.io
    export KIBANA_URL=https://your-deployment.kb.region.gcp.cloud.es.io
    export ES_API_KEY=your-es-api-key
    export KIBANA_API_KEY=your-kibana-api-key

Usage:
    python scripts/setup.py                    # Run full setup
    python scripts/setup.py --indices-only     # Only create indices
    python scripts/setup.py --workflows-only   # Only import workflows
    python scripts/setup.py --seed-policies    # Only seed action policies
    python scripts/setup.py --delete-workflows # Delete all workflows then re-import
    python scripts/setup.py --validate         # Validate env vars without deploying

Workflow placeholder tokens (replaced at import time with env var values):
    __ES_URL__            ← ELASTIC_CLOUD_URL
    __ES_API_KEY__        ← ES_API_KEY
    __KIBANA_URL__        ← KIBANA_URL
    __KIBANA_API_KEY__    ← KIBANA_API_KEY
    __VT_API_KEY__        ← VIRUSTOTAL_API_KEY
    __ABUSEIPDB_API_KEY__ ← ABUSEIPDB_API_KEY
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

try:
    import requests
except ImportError:
    print("ERROR: 'requests' package required. Install with: pip install requests")
    sys.exit(1)

REPO_ROOT = Path(__file__).resolve().parent.parent

REQUIRED_ENV_VARS = ["ELASTIC_CLOUD_URL", "KIBANA_URL", "ES_API_KEY", "KIBANA_API_KEY"]

KNOWLEDGE_BASE_INDICES = [
    "kb-detection-rules",
    "kb-ecs-schema",
    "kb-mitre-attack",
    "kb-threat-intel",
    "kb-ioc-history",
    "kb-incidents",
    "kb-playbooks",
    "kb-forensics",
    "kb-compliance",
    "kb-soc-ops",
    "kb-runbooks",
]

WORKFLOW_DIRS = [
    "agents/setup",
    "workflows/ai-agents",
    "workflows/feedback",
    "workflows/governance",
    "workflows/investigation",
    "workflows/knowledge",
    "workflows/mesh",
    "workflows/search",
    "workflows/security/detection",
    "workflows/security/enrichment",
    "workflows/security/response",
    "workflows/utilities",
]


def validate_env():
    """Check that all required environment variables are set."""
    missing = [v for v in REQUIRED_ENV_VARS if not os.environ.get(v)]
    if missing:
        print("ERROR: Missing required environment variables:")
        for v in missing:
            print(f"  - {v}")
        print()
        print("Set these variables before running setup. See README.md for instructions.")
        sys.exit(1)

    print("Environment validated:")
    print(f"  Elasticsearch: {os.environ['ELASTIC_CLOUD_URL']}")
    print(f"  Kibana:        {os.environ['KIBANA_URL']}")
    space = os.environ.get("KIBANA_SPACE", "default") or "default"
    print(f"  Space:         {space}")
    print()


def es_headers():
    return {
        "Content-Type": "application/json",
        "Authorization": f"ApiKey {os.environ['ES_API_KEY']}",
    }


def kibana_headers():
    return {
        "Content-Type": "application/json",
        "kbn-xsrf": "true",
        "x-elastic-internal-origin": "Kibana",
        "Authorization": f"ApiKey {os.environ['KIBANA_API_KEY']}",
    }


def kibana_base_url():
    base = os.environ["KIBANA_URL"].rstrip("/")
    space = os.environ.get("KIBANA_SPACE", "").strip()
    if space and space != "default":
        return f"{base}/s/{space}"
    return base


def index_exists(index_name):
    url = f"{os.environ['ELASTIC_CLOUD_URL']}/{index_name}"
    resp = requests.head(url, headers=es_headers(), timeout=15)
    return resp.status_code == 200


def create_index(index_name, mapping_body):
    if index_exists(index_name):
        print(f"  [skip] {index_name} already exists")
        return True

    url = f"{os.environ['ELASTIC_CLOUD_URL']}/{index_name}"
    resp = requests.put(url, headers=es_headers(), json=mapping_body, timeout=30)
    if resp.ok:
        print(f"  [created] {index_name}")
        return True
    else:
        print(f"  [FAILED] {index_name}: {resp.status_code} — {resp.text[:200]}")
        return False


def knowledge_base_mapping():
    inference_id = os.environ.get("INFERENCE_ENDPOINT_ID", ".multilingual-e5-small-elasticsearch")
    return {
        "settings": {"number_of_shards": 1, "number_of_replicas": 1},
        "mappings": {
            "properties": {
                "title": {"type": "text"},
                "content": {"type": "text"},
                "semantic_summary": {
                    "type": "semantic_text",
                    "inference_id": inference_id,
                },
                "category": {"type": "keyword"},
                "source": {"type": "keyword"},
                "tags": {"type": "keyword"},
                "created_at": {"type": "date"},
                "updated_at": {"type": "date"},
                "expires_at": {"type": "date"},
                "metadata": {"type": "object", "dynamic": True},
            }
        },
    }


def agent_registry_mapping():
    inference_id = os.environ.get("INFERENCE_ENDPOINT_ID", ".multilingual-e5-small-elasticsearch")
    return {
        "settings": {"number_of_shards": 1, "number_of_replicas": 1},
        "mappings": {
            "properties": {
                "agent_id": {"type": "keyword"},
                "agent_name": {
                    "type": "text",
                    "fields": {"keyword": {"type": "keyword"}},
                },
                "domain": {"type": "keyword"},
                "capabilities": {"type": "keyword"},
                "description": {"type": "text"},
                "semantic_description": {
                    "type": "semantic_text",
                    "inference_id": inference_id,
                },
                "keywords": {"type": "keyword"},
                "status": {"type": "keyword"},
                "version": {"type": "keyword"},
                "created_at": {"type": "date"},
                "updated_at": {"type": "date"},
            }
        },
    }


def investigation_contexts_mapping():
    inference_id = os.environ.get("INFERENCE_ENDPOINT_ID", ".multilingual-e5-small-elasticsearch")
    return {
        "settings": {"number_of_shards": 1, "number_of_replicas": 1},
        "mappings": {
            "properties": {
                "investigation_id": {"type": "keyword"},
                "trigger_type": {"type": "keyword"},
                "trigger_ref": {"type": "keyword"},
                "status": {"type": "keyword"},
                "risk_tier": {"type": "keyword"},
                "assigned_agent": {"type": "keyword"},
                "title": {"type": "text"},
                "summary": {"type": "text"},
                "semantic_summary": {
                    "type": "semantic_text",
                    "inference_id": inference_id,
                },
                "evidence": {
                    "type": "nested",
                    "properties": {
                        "agent_id": {"type": "keyword"},
                        "timestamp": {"type": "date"},
                        "evidence_type": {"type": "keyword"},
                        "content": {"type": "text"},
                        "confidence": {"type": "float"},
                        "references": {"type": "keyword"},
                    },
                },
                "actions_taken": {
                    "type": "nested",
                    "properties": {
                        "agent_id": {"type": "keyword"},
                        "action_type": {"type": "keyword"},
                        "target": {"type": "text"},
                        "timestamp": {"type": "date"},
                        "approved_by": {"type": "keyword"},
                        "result": {"type": "text"},
                        "risk_tier": {"type": "keyword"},
                    },
                },
                "pending_actions": {
                    "type": "nested",
                    "properties": {
                        "recommending_agent": {"type": "keyword"},
                        "action_type": {"type": "keyword"},
                        "risk_tier": {"type": "keyword"},
                        "justification": {"type": "text"},
                        "evidence_refs": {"type": "keyword"},
                    },
                },
                "created_at": {"type": "date"},
                "updated_at": {"type": "date"},
                "resolved_at": {"type": "date"},
                "tags": {"type": "keyword"},
            }
        },
    }


def action_policies_mapping():
    return {
        "settings": {"number_of_shards": 1, "number_of_replicas": 1},
        "mappings": {
            "properties": {
                "action_type": {"type": "keyword"},
                "risk_tier": {"type": "keyword"},
                "allowed_callers": {"type": "keyword"},
                "auto_approve": {
                    "type": "object",
                    "properties": {
                        "min_confidence": {"type": "float"},
                        "max_blast_radius": {"type": "integer"},
                        "required_evidence_count": {"type": "integer"},
                    },
                },
                "requires_approval": {"type": "boolean"},
                "approval_channel": {"type": "keyword"},
                "rollback_workflow": {"type": "keyword"},
                "ttl_minutes": {"type": "integer"},
                "description": {"type": "text"},
            }
        },
    }


def create_all_indices():
    print("=== Creating Indices ===\n")

    print("Agent registry:")
    create_index("agent-registry", agent_registry_mapping())

    print("\nInvestigation contexts:")
    create_index("investigation-contexts", investigation_contexts_mapping())

    print("\nAction policies:")
    create_index("action-policies", action_policies_mapping())

    print("\nKnowledge bases:")
    kb_mapping = knowledge_base_mapping()
    for idx in KNOWLEDGE_BASE_INDICES:
        create_index(idx, kb_mapping)

    print()


def seed_action_policies():
    """Seed default action policies into the action-policies index."""
    print("=== Seeding Action Policies ===\n")

    policies = [
        {
            "action_type": "tag_alert",
            "risk_tier": "tier_0",
            "allowed_callers": ["*"],
            "requires_approval": False,
            "description": "Tag an alert as true positive or false positive",
        },
        {
            "action_type": "close_alert",
            "risk_tier": "tier_0",
            "allowed_callers": ["*"],
            "requires_approval": False,
            "description": "Close a security alert",
        },
        {
            "action_type": "acknowledge_alert",
            "risk_tier": "tier_0",
            "allowed_callers": ["*"],
            "requires_approval": False,
            "description": "Acknowledge a security alert",
        },
        {
            "action_type": "create_note",
            "risk_tier": "tier_0",
            "allowed_callers": ["*"],
            "requires_approval": False,
            "description": "Add a note to an alert or case",
        },
        {
            "action_type": "add_knowledge",
            "risk_tier": "tier_0",
            "allowed_callers": ["*"],
            "requires_approval": False,
            "description": "Add a document to a knowledge base",
        },
        {
            "action_type": "search",
            "risk_tier": "tier_0",
            "allowed_callers": ["*"],
            "requires_approval": False,
            "description": "Search operations (Elasticsearch, knowledge base, web)",
        },
        {
            "action_type": "create_case",
            "risk_tier": "tier_1",
            "allowed_callers": ["*"],
            "auto_approve": {
                "min_confidence": 0.7,
                "max_blast_radius": 1,
                "required_evidence_count": 1,
            },
            "requires_approval": False,
            "description": "Create a security case for investigation",
        },
        {
            "action_type": "create_rule",
            "risk_tier": "tier_1",
            "allowed_callers": ["*"],
            "auto_approve": {
                "min_confidence": 0.8,
                "max_blast_radius": 1,
                "required_evidence_count": 2,
            },
            "requires_approval": False,
            "description": "Create a detection rule (disabled by default)",
        },
        {
            "action_type": "run_playbook_step",
            "risk_tier": "tier_1",
            "allowed_callers": ["*"],
            "auto_approve": {
                "min_confidence": 0.7,
                "max_blast_radius": 5,
                "required_evidence_count": 1,
            },
            "requires_approval": False,
            "description": "Execute a single playbook step",
        },
        {
            "action_type": "isolate_host",
            "risk_tier": "tier_2",
            "allowed_callers": ["*"],
            "requires_approval": True,
            "approval_channel": "cases",
            "rollback_workflow": "unisolate_host",
            "ttl_minutes": 30,
            "description": "Isolate a host from the network via Elastic Defend",
        },
        {
            "action_type": "enable_rule_production",
            "risk_tier": "tier_2",
            "allowed_callers": ["*"],
            "requires_approval": True,
            "approval_channel": "cases",
            "ttl_minutes": 60,
            "description": "Enable a detection rule in production",
        },
        {
            "action_type": "execute_command",
            "risk_tier": "tier_2",
            "allowed_callers": ["*"],
            "requires_approval": True,
            "approval_channel": "cases",
            "ttl_minutes": 15,
            "description": "Execute a command on an endpoint via response console",
        },
        {
            "action_type": "bulk_operation",
            "risk_tier": "tier_2",
            "allowed_callers": ["*"],
            "requires_approval": True,
            "approval_channel": "cases",
            "ttl_minutes": 60,
            "description": "Bulk operations affecting multiple hosts or rules",
        },
    ]

    url = f"{os.environ['ELASTIC_CLOUD_URL']}/action-policies/_bulk"
    bulk_body = ""
    for policy in policies:
        doc_id = policy["action_type"]
        bulk_body += json.dumps({"index": {"_id": doc_id}}) + "\n"
        bulk_body += json.dumps(policy) + "\n"

    resp = requests.post(
        url,
        headers={**es_headers(), "Content-Type": "application/x-ndjson"},
        data=bulk_body,
        timeout=30,
    )
    if resp.ok:
        result = resp.json()
        errors = sum(1 for item in result.get("items", []) if item.get("index", {}).get("error"))
        total = len(result.get("items", []))
        print(f"  Seeded {total - errors}/{total} policies")
        if errors:
            print(f"  {errors} failed (may already exist)")
    else:
        print(f"  [FAILED] {resp.status_code} — {resp.text[:200]}")

    print()


def build_replacements():
    """Build the token → value map for injecting secrets into workflow YAML."""
    return {
        "__ES_URL__": os.environ.get("ELASTIC_CLOUD_URL", ""),
        "__ES_API_KEY__": os.environ.get("ES_API_KEY", ""),
        "__KIBANA_URL__": os.environ.get("KIBANA_URL", ""),
        "__KIBANA_API_KEY__": os.environ.get("KIBANA_API_KEY", ""),
        "__VT_API_KEY__": os.environ.get("VIRUSTOTAL_API_KEY", ""),
        "__ABUSEIPDB_API_KEY__": os.environ.get("ABUSEIPDB_API_KEY", ""),
    }


def apply_replacements(yaml_content, replacements):
    """Replace placeholder tokens in YAML content with real values."""
    for placeholder, value in replacements.items():
        if value:
            yaml_content = yaml_content.replace(placeholder, value)
    return yaml_content


def delete_workflows():
    """Delete all workflows from Kibana so they can be re-imported cleanly."""
    print("=== Deleting Existing Workflows ===\n")

    base_url = kibana_base_url()
    headers = kibana_headers()

    resp = requests.get(
        f"{base_url}/api/workflows",
        headers=headers,
        timeout=30,
    )

    if not resp.ok:
        print(f"  [FAILED] Could not list workflows: {resp.status_code}")
        print(f"  {resp.text[:300]}")
        return

    workflows = resp.json()
    if not isinstance(workflows, list):
        workflows = workflows.get("data", workflows.get("items", []))

    if not workflows:
        print("  No existing workflows found.\n")
        return

    deleted = 0
    errors = 0
    for wf in workflows:
        wf_id = wf.get("id", "")
        wf_name = wf.get("name", wf_id)
        if not wf_id:
            continue

        del_resp = requests.delete(
            f"{base_url}/api/workflows/{wf_id}",
            headers=headers,
            timeout=15,
        )
        if del_resp.ok or del_resp.status_code == 204:
            print(f"  [deleted] {wf_name}")
            deleted += 1
        else:
            print(f"  [FAILED] {wf_name}: {del_resp.status_code}")
            errors += 1

        time.sleep(0.1)

    print(f"\n  Deleted {deleted} workflows ({errors} errors)\n")


def import_workflows():
    """Import all workflow YAML files into Kibana.

    For each file the script:
      1. Replaces placeholder tokens (__ES_URL__, __VT_API_KEY__, etc.)
         with real values from environment variables.
      2. POSTs the YAML to create the workflow.
      3. If the workflow already exists (409) it PUTs to update it instead,
         so re-running the script always converges to the repo state.
    """
    print("=== Importing Workflows ===\n")

    base_url = kibana_base_url()
    headers = kibana_headers()
    replacements = build_replacements()

    active_tokens = {k: ("set" if v else "NOT SET") for k, v in replacements.items()}
    print("  Placeholder injection:")
    for token, status in active_tokens.items():
        print(f"    {token}: {status}")
    print()

    success = 0
    updated = 0
    failed = 0

    for workflow_dir in WORKFLOW_DIRS:
        dir_path = REPO_ROOT / workflow_dir
        if not dir_path.exists():
            continue

        yaml_files = sorted(dir_path.glob("*.yaml"))
        if not yaml_files:
            continue

        print(f"  {workflow_dir}/")
        for yaml_file in yaml_files:
            with open(yaml_file) as f:
                yaml_content = f.read()

            yaml_content = apply_replacements(yaml_content, replacements)

            resp = requests.post(
                f"{base_url}/api/workflows",
                headers=headers,
                json={"yaml": yaml_content},
                timeout=30,
            )

            if resp.ok:
                data = resp.json()
                name = data.get("name", yaml_file.stem)
                print(f"    [imported] {name}")
                success += 1
            elif resp.status_code == 409:
                wf_id = resp.json().get("id", "")
                if wf_id:
                    put_resp = requests.put(
                        f"{base_url}/api/workflows/{wf_id}",
                        headers=headers,
                        json={"yaml": yaml_content},
                        timeout=30,
                    )
                    if put_resp.ok:
                        name = put_resp.json().get("name", yaml_file.stem)
                        print(f"    [updated] {name}")
                        updated += 1
                    else:
                        print(f"    [FAILED update] {yaml_file.name}: {put_resp.status_code}")
                        failed += 1
                else:
                    print(f"    [skip] {yaml_file.name} (exists, no id returned)")
                    updated += 1
            else:
                print(f"    [FAILED] {yaml_file.name}: {resp.status_code}")
                failed += 1

            time.sleep(0.3)

    print(f"\n  Total: {success} imported, {updated} updated, {failed} failed\n")


def print_manual_steps():
    """Print steps that must be done manually."""
    print("=== Manual Steps Required ===\n")
    print("The following cannot be automated and must be done in the Kibana UI:\n")
    print("  1. Deploy inference endpoint (multilingual-e5-small)")
    print("     Machine Learning > Trained Models > Deploy multilingual-e5-small")
    print()
    print("  2. Create LLM connector")
    print("     Stack Management > Connectors > Create connector")
    print("     (Use Claude Sonnet, GPT-4o, or your preferred model)")
    print()
    print("  3. Create agents in Agent Builder")
    print("     Use agent definitions in agents/definitions/ as reference for:")
    print("     - System instructions")
    print("     - Knowledge base attachments")
    print("     - Tool workflow registrations")
    print()
    print("  4. Register agents in the mesh")
    print("     After creating each agent in Agent Builder, note its agent_id")
    print("     and run the Register Agent workflow with the agent's details.")
    print()
    print("  5. Seed knowledge bases")
    print("     Populate kb-* indices with domain-specific data:")
    print("     - kb-mitre-attack: MITRE ATT&CK techniques")
    print("     - kb-ecs-schema: ECS field definitions")
    print("     - kb-detection-rules: Existing detection rules")
    print()


def main():
    parser = argparse.ArgumentParser(description="Elastic Security Agent Mesh setup")
    parser.add_argument("--validate", action="store_true", help="Validate env vars only")
    parser.add_argument("--indices-only", action="store_true", help="Only create indices")
    parser.add_argument("--workflows-only", action="store_true", help="Only import workflows")
    parser.add_argument("--seed-policies", action="store_true", help="Only seed action policies")
    parser.add_argument("--delete-workflows", action="store_true",
                        help="Delete all workflows from Kibana before importing")
    args = parser.parse_args()

    print()
    print("=" * 60)
    print("  Elastic Security Agent Mesh — Setup")
    print("=" * 60)
    print()

    validate_env()

    if args.validate:
        print("Validation complete.")
        return

    if args.delete_workflows:
        delete_workflows()
        if not (args.indices_only or args.workflows_only or args.seed_policies):
            import_workflows()
        return

    if args.indices_only:
        create_all_indices()
        return

    if args.workflows_only:
        import_workflows()
        return

    if args.seed_policies:
        seed_action_policies()
        return

    create_all_indices()
    seed_action_policies()
    import_workflows()
    print_manual_steps()

    print("=" * 60)
    print("  Setup complete!")
    print("=" * 60)
    print()


if __name__ == "__main__":
    main()
