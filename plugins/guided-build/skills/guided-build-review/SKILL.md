---
name: guided-build-review
description: Review, reconcile, or resume a Guided Build milestone using repository evidence, code tours, debugging exercises, and private mastery state. Use when the user asks to review understanding, complete a milestone, revisit a prerequisite concept, or resume a Guided Build project in a new session. Do not trigger for generic code review without a Guided Build contract.
---

# Guided Build Review

Verify delivery and learning as separate outcomes, then make the next session safe to resume.

## Required resources

Read completely:

- `references/mastery-rubric.md` before recording mastery.
- `references/resume-and-reconciliation.md` when state, evidence, and repository history may differ.

Resolve the shared CLI at `../../scripts/guided_build.py` relative to this skill.

## Workflow

1. **Reconcile current truth.**
   - Validate the contract and relevant evidence.
   - Read private status without exposing private notes.
   - Inspect the working tree, recent changes, tests, and active milestone.
   - Follow the reconciliation reference when sources disagree.
2. **Verify engineering delivery.**
   - Run the contract's relevant checks.
   - Inspect the diff for correctness, scope drift, cleanup, and missing tests.
   - Record delivery as `complete`, `blocked`, or `in_progress` independently of mastery.
3. **Create a code tour.**
   - Trace the request/data path through actual files and symbols.
   - Connect implementation decisions to the milestone invariant and tests.
   - Explain ownership, failure behavior, and what would break if the invariant were removed.
4. **Collect mastery evidence.**
   - Ask for an independent prediction or explanation.
   - Give one debugging, failure-analysis, or counterexample exercise.
   - Prefer the project's real behavior; use a hypothetical only when a real exercise would be destructive.
   - Apply the rubric without numerical grades.
5. **Update private state.**
   - Record concept status and evidence references through `record-concept`.
   - Record confidence and misconceptions only when the learner provides them.
   - Schedule revisit after one subsequent milestone, after three milestones, or before a declared dependency—whichever comes first.
6. **Update shared evidence.**
   - Record repository facts, validation, decisions, and accepted debt.
   - Never copy confidence, misconceptions, or private session notes into committed evidence.
7. **Apply prerequisite gates.**
   - Delivery may be complete while mastery remains pending.
   - Block only entry into a milestone that declares the unresolved concept as a prerequisite.
   - Offer a focused review that can clear the gate without repeating the full milestone.
8. **Hand off clearly.**
   - Report delivery status, mastery status by concept, evidence links, pending reviews, and the next eligible milestone.

Do not claim certification or durable mastery. Guided Build records evidence for future review.
