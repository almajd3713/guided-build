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
- `references/concept-readiness.md` before asking a prediction or assigning learner work.

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
5. **Calibrate concept readiness.**
   - Separate prerequisite concepts needed before the slice from target concepts learned through the slice.
   - Flag niche, project-specific, low-level, mathematical, concurrency, security, and unfamiliar-tool concepts for explicit calibration. Do not infer knowledge from milestone approval, job title, depth choice, or silence.
   - For each learning-critical concept, ask a low-friction familiarity question and one small diagnostic grounded in an example. Let the learner answer `new`, `some exposure`, or `comfortable`; never present this as a grade.
   - When useful across sessions, persist only the learner's self-report with `record-concept <milestone> <concept> unassessed --familiarity new|some_exposure|comfortable`. Do not infer or invent it, and do not expose private status.
   - Ask whether they prefer theory-first, example-first, or execution-first guidance when the concept is new or the diagnostic shows a gap.
6. **Teach to the entry point.**
   - Follow `concept-readiness.md`: explain why the concept appears now, define essential vocabulary, give a concrete worked example, expose the relevant failure mode, and check understanding.
   - Do not ask the learner to design an interface, predict edge behavior, or write a test whose terms have not been introduced.
   - Continue when the learner can explain the immediate invariant or modify the worked example. Offer another example, a smaller task, or a mode/ownership change when they are not ready.
7. **Brief and partition.**
   - Connect the newly established mental model to actual repository symbols and expected behavior.
   - Ask one prediction or design question whose required background was just checked.
   - Present the slice and ownership table only after calibration. Require confirmation for learner-owned work and high-risk decisions.
8. **Execute adaptively.**
   - Let the learner complete their owned decision or implementation.
   - Use the hint ladder when stuck: direction → invariant → location/interface → pseudocode → partial code → full implementation on request.
   - Implement collaborative and agent-owned work, including mechanical tests and wiring.
   - Never take learner-owned work silently or implement deferred/future scope.
   - Treat repeated confusion as feedback that the teaching or slice size is wrong. Pause, reteach, or repartition.
9. **Validate continuously.**
   - Run the narrowest relevant checks after each meaningful change.
   - Preserve the user's dirty worktree and distinguish pre-existing failures.
   - If automated tests do not exist, use contract-approved compilation, manual behavior, artifact inspection, or reference comparison.
10. **Update shared evidence.**
   - Create or update `.guided-build/evidence/<milestone-id>.md`.
   - Record scope, ownership, repository links, commands/results, learning evidence, and deviations.
   - Keep confidence and misconception notes private.
11. **Hand off to review.**
   - Do not mark mastery `demonstrated` based only on passing tests or agent-authored explanations.
   - Invoke the Guided Build review workflow for the completion decision.

## Mid-slice interruption

Before yielding, persist the active slice and evidence already established. On resume, reconcile private state, evidence, working-tree changes, and current tests before continuing.
