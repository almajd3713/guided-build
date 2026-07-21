---
schema: guided-build/v2
project_id: "cycle"
title: "Cycle"
plan_sources: ["plan.md"]
default_depth: fast
default_granularity: lean
status: draft
---

# Cycle

## Outcomes

Expose a dependency cycle.

## Non-goals

None.

## Validation

Validator rejects this contract.

## Milestones

### M01 — First

#### Objective

First.

#### Prerequisites

- M02

#### Concepts

- First concept

#### Delivery scope

First.

#### Exclusions

None.

#### Validation

Inspect.

#### Learning evidence

Explain.

#### Dependent milestones

- M02

#### Capability bundles

##### M01.C01 — First capability

- Outcome: "First outcome"
- Concepts: ["First concept"]
- Prerequisites: []
- Deliverables: ["First delivery"]
- Validation: "Inspect first"

### M02 — Second

#### Objective

Second.

#### Prerequisites

- M01

#### Concepts

- Second concept

#### Delivery scope

Second.

#### Exclusions

None.

#### Validation

Inspect.

#### Learning evidence

Explain.

#### Dependent milestones

- M01

#### Capability bundles

##### M02.C01 — Second capability

- Outcome: "Second outcome"
- Concepts: ["Second concept"]
- Prerequisites: []
- Deliverables: ["Second delivery"]
- Validation: "Inspect second"
