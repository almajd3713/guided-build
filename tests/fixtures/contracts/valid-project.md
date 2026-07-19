---
schema: guided-build/v1
project_id: "sample-cli"
title: "Sample CLI"
plan_sources: ["../plans/python-cli.md"]
default_depth: balanced
status: approved
---

# Sample CLI Learning Contract

## Outcomes

Build a tested command-line task manager while learning parsing and persistence boundaries.

## Non-goals

Networking and multi-user synchronization are excluded.

## Validation

Run the unit tests and exercise the compiled CLI help and task lifecycle.

## Milestones

### M01 — Command model

#### Objective

Parse task commands into a validated internal command model.

#### Prerequisites

- None

#### Concepts

- Boundary validation

#### Delivery scope

Implement add and list command parsing with deterministic errors.

#### Exclusions

Persistence and update commands remain deferred.

#### Validation

Run parser unit tests and CLI help.

#### Learning evidence

Predict malformed-input behavior and implement or diagnose one parser edge case.

#### Dependent milestones

- M02

### M02 — File persistence

#### Objective

Persist tasks atomically in a local file.

#### Prerequisites

- M01

#### Concepts

- Atomic replacement

#### Delivery scope

Implement load, save, and recovery from a missing file.

#### Exclusions

Concurrent writers and remote storage remain excluded.

#### Validation

Run persistence tests including interrupted replacement.

#### Learning evidence

Explain the durable state transition and diagnose one simulated failure.

#### Dependent milestones

- None
