# Guided Build Depth Profiles

## Fast

Use when delivery speed dominates but understanding still matters.

- Learner: one design prediction or trade-off.
- Agent: implementation and mechanical coverage.
- Review: focused code tour plus one debugging or counterexample exercise.
- Evidence: prediction, validation, and diagnostic result.

Fast mode may transfer learning-critical implementation to the agent, but it may not skip explanation, failure analysis, or milestone boundaries.

## Balanced

Default for most milestones.

- Learner: at least one learning-critical decision or implementation slice.
- Collaborative: public interface, invariant, primary behavioral test, and high-risk changes.
- Agent: scaffolding, repetitive cases, fixtures, wiring, and documentation mechanics.
- Review: code tour, explanation against real symbols, and one counterexample/debug exercise.

## Deep

Use when the milestone's mechanism is the primary learning objective.

- Learner: core behavior and its primary test.
- Agent: environment, scaffolding, fixtures, mechanical integration, and review.
- Guidance: progressive hint ladder; do not reveal full implementation unless requested or the learner changes mode.
- Review: multiple predictions/counterexamples and independent explanation.

## Mode changes

The learner may switch mode mid-milestone. Record the change and reason in evidence. Do not rewrite earlier ownership history. Engineering validation requirements never weaken when mode changes.
