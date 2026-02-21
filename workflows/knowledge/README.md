# Knowledge Management Workflows

Generic Elasticsearch document CRUD workflows for maintaining knowledge bases. These are **agnostic** — they work with any Elasticsearch index and make no assumptions about field mappings or document structure. The calling agent or workflow provides the index name and document body.

## Workflows

| Workflow | Description |
|----------|-------------|
| **Add Knowledge Document** | Index a new document into any Elasticsearch index |
| **Update Knowledge Document** | Partial update of an existing document by ID |
| **Remove Knowledge Document** | Delete a document by ID (with existence check) |
| **Check Knowledge Staleness** | Search for documents where a date field is past due |

## Usage

These workflows are designed to be registered as **agent tools** in Elastic Agent Builder, giving agents the ability to read and write to their knowledge bases. They can also be invoked standalone or from other workflows.

### Example: Agent adding a new incident record

The L2 Investigation Analyst could call `Add Knowledge Document` with:

```yaml
index_name: "kb-incidents"
document:
  title: "Ransomware attempt on fileserver-01"
  content: "Detected via Elastic rule X, contained by isolating host, root cause was phishing email..."
  category: "incident_resolution"
  resolved_by: "analyst@company.com"
  created_at: "2026-02-19T10:00:00Z"
```

The document structure is entirely up to the agent — these workflows impose no schema.
