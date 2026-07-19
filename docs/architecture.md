# Architecture

Guided Build separates workflow authoring, deterministic state, committed evidence, and optional capabilities.

```text
free-form plans
      │
      ▼
guided-build-onboard ──► .guided-build/project.md
                              │
                              ▼
guided-build-milestone ─► repository changes + shared evidence
                              │
                              ▼
guided-build-review ─────► delivery status + private mastery state
```

## Components

The plugin contains three skills with non-overlapping lifecycle triggers:

- Onboard compiles plans into a draft contract and stops for approval.
- Milestone selects depth, calibrates prerequisite knowledge, teaches to the slice entry point, partitions ownership, and delivers one bounded slice.
- Review reconciles repository truth, validates delivery, records mastery evidence, and schedules prerequisite reviews.

The Python CLI owns schema parsing, dependency validation, atomic private-state writes, redacted exports, and guarded transitions. Skills own interpretation, teaching, work selection, and interaction.

## State model

Delivery statuses are `not_started`, `in_progress`, `blocked`, and `complete`.

Mastery statuses are `unassessed`, `introduced`, `practiced`, `demonstrated`, and `revisit_due`.

Self-reported topic familiarity and coaching preferences are private calibration context, not mastery status. Topics may be narrower than contract concepts. They influence the explanation entry point but never establish evidence or prerequisite gates.

Contract concepts are the current authoritative prerequisite set. Historical concept keys remain in private state after a contract refinement, but retired keys do not keep gating later milestones.

They are intentionally independent. Delivery can complete while mastery remains pending. A later milestone is gated only when it declares a prerequisite whose concepts have not been demonstrated or need revisiting.

## Capability policy

Core operation requires repository and shell access only. When available, skills prefer semantic/code-graph discovery, exact-version local documentation, official versioned documentation, and read-only GitHub context. Absence must degrade gracefully.

No external integration may replace the mechanism a milestone intends to teach.
