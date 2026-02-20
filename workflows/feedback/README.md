# Feedback Loop Workflows

Scheduled and triggered workflows that close the autonomous learning loops. These are what make the SOC self-sustaining rather than just automated.

## Feedback Loops

### 1. Detection Quality (Scheduled — daily)

```
Rule fires -> Analyst tags TP/FP -> aggregate-detection-feedback aggregates ratios ->
Detection Engineer reads kb-detection-rules -> Tunes or disables rule
```

### 2. Noise Reduction (Scheduled — daily)

```
flag-noisy-rules identifies high-volume and high-FP rules ->
Writes to kb-detection-rules -> Detection Engineer reviews and tunes
```

### 3. Incident Learning (Manual/Triggered)

```
Investigation resolved -> record-incident-resolution captures resolution ->
Writes to kb-incidents -> Future triage searches past incidents for similar patterns
```

## Workflows

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `aggregate-detection-feedback.yaml` | Scheduled (24h) | TP/FP ratios per rule |
| `flag-noisy-rules.yaml` | Scheduled (24h) | High-volume and high-FP rule detection |
| `record-incident-resolution.yaml` | Manual | Capture resolved investigation as knowledge |
