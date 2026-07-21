# Evaluation Strategy

Guided Build is evaluated as a workflow, not only as Markdown syntax.

## Required fixture families

- A long educational systems roadmap with deep prerequisite chains.
- A small Python CLI plan with few milestones and no specialized tooling.
- A frontend application plan with user-facing validation and framework dependencies.

## Invariants

Evaluations must establish:

- onboarding preserves source plans and stops at draft approval;
- ordinary coding prompts do not trigger Guided Build;
- contracts contain no fixture-specific leakage;
- v1 contracts fail with an actionable regeneration path while v1 private state migrates with a backup;
- capability IDs, concepts, prerequisites, and evidence references cross-validate;
- integrated APIs such as varint exact/prefix/length decoding or CRC/framing remain one cohesive capability rather than function-sized slices;
- Fast, Balanced, and Deep assign materially different ownership;
- depth, granularity, and verbosity remain independent;
- milestone depth never substitutes for checking prerequisite knowledge;
- niche concepts receive familiarity calibration, a worked example, and an understanding check before learner ownership;
- a correct diagnostic skips unnecessary teaching;
- prior related familiarity is reused instead of re-asked per capability;
- correct design responses, learner artifacts, and diagnoses avoid a redundant final diagnostic;
- an ambiguous terse response receives one focused clarification;
- after two unsuccessful attempts, the learner is offered a new example, pairing, a smaller task, or ownership transfer;
- incidental mechanics are scaffolded and batched instead of becoming learner gates;
- routine updates and learner gates stay within the interaction budget;
- Adaptive and Lean normally use no more than two pedagogical gates per capability;
- over-budget evidence warns, compacts before the next capability, and still permits completion of the active capability;
- agents do not invent undeclared capabilities when implementation discovery changes scope;
- learners can enter new material theory-first, example-first, or execution-first without weakening validation;
- future milestones remain deferred;
- high-risk decisions remain collaborative;
- passing tests alone does not mark mastery demonstrated;
- prerequisite concepts gate dependent work;
- private fields, learner self-reports, and raw attempts never appear in committed evidence or default exports;
- missing semantic, documentation, or GitHub tools have local fallbacks;
- code-graph discovery is budgeted and graph health never becomes learning evidence;
- a fresh session can reconcile state, evidence, and repository truth.

## Forward testing

Use fresh Codex threads with raw fixture plans and prompts. Do not tell the testing agent the expected answer or suspected failure. Retain only sanitized outputs and convert every confirmed regression into a deterministic or prompt-level test.
