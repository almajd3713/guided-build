# Work Partitioning and Meaningful Gates

## Classification

Classify each candidate task on:

- learning value: does it implement a named milestone concept?
- delivery risk: security, data loss, compatibility, concurrency, or irreversibility;
- mechanicality: repetitive and already specified versus requiring a design;
- reversibility: cheap local change versus costly migration or external action;
- scope: current milestone versus future or unrelated work.

## Ownership mapping

| Condition | Fast | Balanced | Deep |
|---|---|---|---|
| High learning value | Agent + diagnostic review | Collaborative/learner | Learner |
| High delivery risk | Collaborative gate | Collaborative gate | Collaborative gate |
| Mechanical, low risk | Agent | Agent | Agent |
| Unclear design | Collaborative gate | Collaborative gate | Collaborative gate |
| Future milestone | Deferred | Deferred | Deferred |

## Required gates

Pause for:

- depth selection at milestone start;
- concept readiness before prediction questions or learner ownership;
- the initial prediction/design response when equivalent evidence does not already exist;
- learner-owned work;
- high-risk, destructive, external, or hard-to-reverse choices;
- transfer of learner-owned work to the agent;
- delivery acceptance and mastery review.

Do not pause merely to announce searches, routine tests, formatting, fixtures, or other mechanical work.

Ownership follows readiness. When a learner lacks prerequisite background, teach or scaffold first; do not downgrade engineering requirements or treat the initial gap as failed mastery.

## Capability sizing

Use the approved capability bundle as the stable delivery unit. Within it, choose the largest cohesive work packet that shares one outcome and validation gate. Keep related codecs, operations, or tests together when splitting them would create repeated calibration and acceptance conversations.

Split only when a different invariant, prerequisite cluster, risk class, or independent validation outcome begins. Do not use changed-line counts or one-function-per-task rules. If a split would require a new capability ID, revise the contract first.

## Granularity and gate budgets

| Granularity | Pedagogical gates | Recovery behavior |
|---|---:|---|
| Lean | At most 2 | One remediation, then offer scaffold/pair/transfer |
| Adaptive | Normally 2; third only for high risk or explicit depth request | Match demonstrated need |
| Thorough | At most 4 | Explore additional counterexamples when useful |

Approvals required for safety or external actions are outside this budget. A correct design response, accepted learner artifact, or diagnosis can satisfy the acceptance gate; do not require a redundant final diagnostic.
