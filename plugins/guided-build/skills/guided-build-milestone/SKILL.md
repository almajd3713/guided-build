---
name: guided-build-milestone
description: Start or continue one approved Guided Build software milestone using adaptive learner, collaborative, agent, and deferred ownership. Use when the user explicitly asks to work through a Guided Build milestone, or when .guided-build/project.md is approved and they ask to start or continue its current milestone. Do not trigger for ordinary implementation work with no Guided Build contract.
---

# Guided Build Milestone

Deliver one bounded slice while keeping learning-critical work visible and user-controlled.

## Required resources

Read completely:

- `references/depth-profiles.md` before asking for the milestone mode.
- `references/partitioning-and-gates.md` before assigning ownership.

Resolve the shared CLI at `../../scripts/guided_build.py` and evidence template at `../../assets/milestone-evidence.md` relative to this skill.

## Workflow

1. **Load authoritative context.**
   - Read applicable agent instructions and `.guided-build/project.md`.
   - Validate the contract and require `status: approved`.
   - Read private status through the CLI; do not print private notes.
2. **Select one eligible milestone.**
   - Resume the active milestone when present.
   - Otherwise identify milestones whose delivery prerequisites are complete.
   - Run prerequisite mastery reviews before starting a dependent milestone.
3. **Confirm depth and timebox.**
   - Ask the user to choose Fast, Balanced, or Deep for this milestone; prefill the contract default.
   - Ask for a timebox only when it affects slice size.
   - Persist the selected mode with `start-milestone`.
4. **Inspect the implementation surface.**
   - Prefer semantic/code-graph tools when available, then repository-native search.
   - Identify the smallest observable slice, affected invariants, tests, risks, and future-stage boundaries.
5. **Brief and partition.**
   - Give a focused concept brief, not a textbook chapter.
   - Ask one prediction or design question before coding.
   - Present the slice and ownership table. Require confirmation for learner-owned work and high-risk decisions.
6. **Execute adaptively.**
   - Let the learner complete their owned decision or implementation.
   - Use the hint ladder when stuck: direction → invariant → location/interface → pseudocode → partial code → full implementation on request.
   - Implement collaborative and agent-owned work, including mechanical tests and wiring.
   - Never take learner-owned work silently or implement deferred/future scope.
7. **Validate continuously.**
   - Run the narrowest relevant checks after each meaningful change.
   - Preserve the user's dirty worktree and distinguish pre-existing failures.
   - If automated tests do not exist, use contract-approved compilation, manual behavior, artifact inspection, or reference comparison.
8. **Update shared evidence.**
   - Create or update `.guided-build/evidence/<milestone-id>.md`.
   - Record scope, ownership, repository links, commands/results, learning evidence, and deviations.
   - Keep confidence and misconception notes private.
9. **Hand off to review.**
   - Do not mark mastery `demonstrated` based only on passing tests or agent-authored explanations.
   - Invoke the Guided Build review workflow for the completion decision.

## Mid-slice interruption

Before yielding, persist the active slice and evidence already established. On resume, reconcile private state, evidence, working-tree changes, and current tests before continuing.
