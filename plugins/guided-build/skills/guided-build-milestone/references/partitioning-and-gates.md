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
- the initial prediction/design response;
- learner-owned work;
- high-risk, destructive, external, or hard-to-reverse choices;
- transfer of learner-owned work to the agent;
- delivery acceptance and mastery review.

Do not pause merely to announce searches, routine tests, formatting, fixtures, or other mechanical work.

Ownership follows readiness. When a learner lacks prerequisite background, teach or scaffold first; do not downgrade engineering requirements or treat the initial gap as failed mastery.

## Slice sizing

Choose the smallest slice that produces observable behavior and can be validated independently. Split when a different invariant, decision gate, or prerequisite concept begins. Do not use changed-line thresholds.
