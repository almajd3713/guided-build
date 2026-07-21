---
name: guided-build-milestone
description: Start or continue one approved Guided Build software milestone using adaptive learner, collaborative, agent, and deferred ownership. Use when the user explicitly asks to work through a Guided Build milestone, or when .guided-build/project.md is approved and they ask to start or continue its current milestone. Do not trigger for ordinary implementation work with no Guided Build contract.
---

# Guided Build Milestone

Deliver one approved capability bundle while keeping learning-critical work visible and user-controlled.

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
   - Read private status through the CLI; do not print private notes. Reuse stored guidance, granularity, verbosity, struggle, familiarity, and accepted concept evidence when relevant.
2. **Select one eligible milestone.**
   - Resume the active milestone when present.
   - Otherwise identify milestones whose delivery prerequisites are complete.
   - Run prerequisite mastery reviews before starting a dependent milestone.
3. **Confirm depth, granularity, and timebox.**
   - Ask the user to choose Fast, Balanced, or Deep for this milestone; prefill the contract default.
   - Use Adaptive, Lean, or Thorough granularity from private preference or the contract default. Ask only when the user wants to change it.
   - Treat depth as learner ownership, granularity as capability packing/gate density, and verbosity as response length. Never infer one axis from another.
   - Ask for a timebox only when it changes capability ownership or scope.
   - Persist the selected mode with `start-milestone`.
4. **Select the approved capability.**
   - Resume `active_capability`; otherwise choose the first capability whose declared capability prerequisites are complete.
   - Do not invent a dynamic capability. If repository evidence reveals genuinely new scope, propose a contract revision before assigning it.
   - Start it with `start-capability`. If evidence compaction blocks the transition, compact first.
5. **Inspect the implementation surface efficiently.**
   - Check semantic/code-graph freshness once per session when such a tool exists. Use at most two graph discovery calls per capability: one for an unknown symbol and one for relationships. Read targeted source once the symbol is known.
   - Reindex only after a meaningful code batch. Tool health or graph coverage is never learning evidence.
   - Identify the capability outcome, affected invariants, tests, risks, and future-stage boundaries.
6. **Calibrate concept readiness.**
   - Separate prerequisite concepts needed before the capability from target concepts learned through it.
   - Flag niche, project-specific, low-level, mathematical, concurrency, security, and unfamiliar-tool concepts for explicit calibration. Do not infer knowledge from milestone approval, job title, depth choice, or silence.
   - Reuse prior calibration for related concepts unless repository behavior contradicts it or retrieval is due. Do not ask familiarity for every capability.
   - When evidence is missing, ask one low-friction familiarity question and one small diagnostic grounded in an example. Let the learner answer `new`, `some exposure`, or `comfortable`; never present this as a grade.
   - Persist a supplied familiarity answer with `record-familiarity <milestone> <topic> new|some_exposure|comfortable`. Topics may be narrower than contract concepts. Never invent the answer or copy it into public evidence.
   - Use `set-preferences` when the learner explicitly chooses a durable guidance, granularity, verbosity, or struggle style. Ask about teaching order only when no useful preference exists and the concept is new or the diagnostic shows a gap.
7. **Teach to the entry point.**
   - Use the efficient-learning loop from `concept-readiness.md`: one diagnostic → one compact worked example when needed → one focused learner task → one acceptance check. Skip the lesson when the diagnostic is correct.
   - Do not ask the learner to design an interface, predict edge behavior, or write a test whose terms have not been introduced.
   - Continue when the learner can explain the immediate invariant or modify the worked example. After one unsuccessful retry in Lean mode, or two in other modes, offer a new example, pairing, a smaller task, or ownership transfer. Do not force transfer.
8. **Brief and partition.**
   - Connect the newly established mental model to actual repository symbols and expected behavior.
   - Ask one prediction or design question whose required background was just checked.
   - Present the capability and ownership table only after calibration. Require confirmation for learner-owned work and high-risk decisions.
   - Own conventional, reversible, low-risk choices as agent work. Do not spend a learner gate on naming, imports, fixture mechanics, or an already constrained interface.
9. **Execute adaptively.**
   - Let the learner complete their owned decision or implementation.
   - Use the hint ladder when stuck: direction → invariant → location/interface → pseudocode → partial code → full implementation on request.
   - Implement collaborative and agent-owned work, including imports, assertion mechanics, fixtures, wiring, and repetitive tests. Batch feedback on incidental mechanics into one response.
   - Never take learner-owned work silently or implement deferred/future scope.
   - Treat repeated confusion as feedback that the teaching or capability entry task is wrong. Pause, reteach, or offer the four recovery routes.
10. **Validate continuously.**
   - Run the narrowest relevant checks after each meaningful change.
   - Preserve the user's dirty worktree and distinguish pre-existing failures.
   - If automated tests do not exist, use contract-approved compilation, manual behavior, artifact inspection, or reference comparison.
11. **Update shared evidence.**
   - Create or update `.guided-build/evidence/<milestone-id>.md`.
   - Maintain an authoritative current snapshot under 600 words; retain at most five `Slice log` entries of at most 60 words each. Collapse older events into one capability outcome summary and rely on repository history.
   - Record successful decisions, accepted explanations, artifacts, commands/results, and deviations. Do not preserve raw attempts or a tutoring transcript.
   - Keep familiarity, confidence, misconceptions, guidance preferences, and private-state labels out of shared evidence.
12. **Complete or hand off.**
   - Mark the capability complete only after evidence lists it in `completed_capabilities`; compaction warnings do not prevent completing the active capability.
   - Keep capability delivery separate from concept mastery. A correct design response, learner artifact, or diagnosis may already satisfy the planned learning evidence.
   - Ask a final diagnostic only when required mastery evidence is still missing; never add one by ritual after accepted evidence.
   - Do not mark mastery `demonstrated` based only on passing tests or agent-authored explanations.
   - Invoke the Guided Build review workflow for the completion decision.

## Mid-capability interruption

Before yielding, persist the active capability and evidence already established. On resume, reconcile private state, evidence, working-tree changes, and current tests before continuing.

## Interaction budget

- Routine update: at most 60 words.
- Learner gate: at most 200 prose words, one primary question, and one code block.
- Adaptive and Lean normally use at most two pedagogical gates per capability. Adaptive may use a third only for high-risk work or when the learner explicitly asks to go deeper. Thorough may use at most four.
- Safety, destructive-action, and external-write approvals do not count as pedagogical gates.
- Clarify ambiguous terse answers with one focused question; do not infer acceptance or understanding.
- Do not narrate every search, test, or evidence write.
