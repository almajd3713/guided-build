# Evidence-Backed Mastery Rubric

## Statuses

- `unassessed`: no learning evidence exists.
- `introduced`: learner received a briefing or code tour.
- `practiced`: learner made a decision, implementation, test, or guided diagnosis.
- `demonstrated`: learner independently explained or predicted behavior and resolved a relevant diagnostic/counterexample using repository evidence.
- `revisit_due`: previously practiced/demonstrated knowledge should be retrieved again because of time, milestone distance, or a dependency gate.

## Evidence rules

Passing tests proves delivery, not mastery. Self-confidence is useful private context, not proof. Agent-authored explanations and multiple-choice recognition cannot establish `demonstrated`.

Evidence may include:

- a prediction made before running code;
- a learner-owned implementation or test;
- explanation tied to real symbols and data flow;
- diagnosis of a failing test, trace, or counterexample;
- a design trade-off defended against an alternative.

To record `demonstrated`, require an independent explanation/prediction and one applied diagnostic or implementation item. Store evidence links; do not assign scores.

## Revisit scheduling

Schedule retrieval:

1. after one subsequent milestone;
2. after three subsequent milestones;
3. before any milestone that lists the concept's milestone as a prerequisite.

The earliest applicable review wins. A focused review can restore `demonstrated`.
