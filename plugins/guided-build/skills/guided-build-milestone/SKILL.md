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
   - Read private status through the CLI; do not print private notes. Reuse stored guidance, verbosity, and struggle preferences when present.
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
   - For the smallest prerequisite cluster, ask one low-friction familiarity question and one small diagnostic grounded in an example. Let the learner answer `new`, `some exposure`, or `comfortable`; never present this as a grade.
   - Persist a supplied familiarity answer with `record-familiarity <milestone> <topic> new|some_exposure|comfortable`. Topics may be narrower than contract concepts. Never invent the answer or copy it into public evidence.
   - Use `set-preferences` when the learner explicitly chooses a durable guidance, verbosity, or struggle style. Ask about teaching order only when no useful preference exists and the concept is new or the diagnostic shows a gap.
6. **Teach to the entry point.**
   - Use the efficient-learning loop from `concept-readiness.md`: one diagnostic → one compact worked example when needed → one focused learner task → one acceptance check. Skip the lesson when the diagnostic is correct.
   - Do not ask the learner to design an interface, predict edge behavior, or write a test whose terms have not been introduced.
   - Continue when the learner can explain the immediate invariant or modify the worked example. After two unsuccessful attempts, offer a new example, pairing, a smaller task, or ownership transfer. Do not force transfer.
7. **Brief and partition.**
   - Connect the newly established mental model to actual repository symbols and expected behavior.
   - Ask one prediction or design question whose required background was just checked.
   - Present the slice and ownership table only after calibration. Require confirmation for learner-owned work and high-risk decisions.
8. **Execute adaptively.**
   - Let the learner complete their owned decision or implementation.
   - Use the hint ladder when stuck: direction → invariant → location/interface → pseudocode → partial code → full implementation on request.
   - Implement collaborative and agent-owned work, including imports, assertion mechanics, fixtures, wiring, and repetitive tests. Batch feedback on incidental mechanics into one response.
   - Never take learner-owned work silently or implement deferred/future scope.
   - Treat repeated confusion as feedback that the teaching or slice size is wrong. Pause, reteach, or repartition.
9. **Validate continuously.**
   - Run the narrowest relevant checks after each meaningful change.
   - Preserve the user's dirty worktree and distinguish pre-existing failures.
   - If automated tests do not exist, use contract-approved compilation, manual behavior, artifact inspection, or reference comparison.
10. **Update shared evidence.**
   - Create or update `.guided-build/evidence/<milestone-id>.md`.
   - Maintain an authoritative current snapshot; use the optional `Slice log` only for short durable events.
   - Record successful decisions, accepted explanations, artifacts, commands/results, and deviations. Do not preserve raw attempts or a tutoring transcript.
   - Keep familiarity, confidence, misconceptions, guidance preferences, and private-state labels out of shared evidence.
11. **Hand off to review.**
   - Do not mark mastery `demonstrated` based only on passing tests or agent-authored explanations.
   - Invoke the Guided Build review workflow for the completion decision.

## Mid-slice interruption

Before yielding, persist the active slice and evidence already established. On resume, reconcile private state, evidence, working-tree changes, and current tests before continuing.

## Interaction budget

- Routine update: at most 60 words.
- Learner gate: at most 200 prose words, one primary question, and one code block.
- Normally use no more than four learner gates per slice.
- Clarify ambiguous terse answers with one focused question; do not infer acceptance or understanding.
- Do not narrate every search, test, or evidence write.
