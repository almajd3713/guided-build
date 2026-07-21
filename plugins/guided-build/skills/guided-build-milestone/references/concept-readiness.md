# Concept Readiness Before Ownership

The learner should encounter productive difficulty, not unexplained vocabulary. Depth controls ownership after orientation; it is not evidence of prior knowledge.

## 1. Build a concept map for the capability

Classify each learning-critical concept as:

- **Prerequisite:** needed to understand the task before work starts.
- **Target:** intended to be learned by doing this slice.
- **Incidental:** necessary tooling or syntax that does not deserve learner ownership.

Flag concepts that are niche, project-specific, unusually low-level, mathematical, security-sensitive, concurrency-sensitive, or likely absent from general application-development experience. Calibrate flagged concepts explicitly.

## 2. Use the efficient-learning loop

For each capability, prefer this sequence:

1. one concrete diagnostic;
2. one compact worked example only when the diagnostic reveals a gap;
3. one focused learner task;
4. one acceptance check tied to the invariant.

Skip the lesson when the diagnostic is correct. Reuse recent accepted evidence for the same or closely related concept instead of repeating familiarity questions. Respect the selected granularity budget.

## 3. Calibrate without turning it into an exam

Ask a compact question such as:

> Before I assign this slice, is unsigned 64-bit binary encoding new to you, something you have seen, or something you can explain comfortably?

Follow with one concrete diagnostic that reveals the learner's current mental model. Prefer explaining a tiny example over asking an open-ended architecture question. Do not use confidence alone as mastery evidence, and do not interpret an incorrect answer as failure.

When several concepts are involved, calibrate the smallest prerequisite cluster rather than asking a long questionnaire. If related familiarity or accepted evidence already exists, begin from it. A terse answer that could mean several things needs one focused clarification, not an assumed interpretation.

## 4. Choose an entry style

Offer one of these routes when background is missing:

- **Theory-first:** terms, invariant, representation, then an example.
- **Example-first:** trace one concrete input and output, then name the general rule.
- **Execution-first:** run or modify a tiny safe experiment, observe behavior, then explain it.

The route changes the explanation order, not the engineering invariant.

Store an explicitly chosen durable style privately with `set-preferences`. Do not ask again each slice when the stored choice still fits.

## 5. Teach the minimum viable model

Before learner ownership, cover:

1. **Why now:** what project behavior requires this concept.
2. **Vocabulary:** only the terms needed for the immediate slice.
3. **Mental model:** the smallest accurate explanation of the mechanism.
4. **Worked example:** actual values, bytes, control flow, or repository symbols.
5. **Failure model:** one boundary or counterexample and why it fails.
6. **Understanding check:** ask the learner to explain, predict, or modify the example.

Avoid a textbook dump. Link optional deeper material separately and return to the slice.

## 6. Readiness outcomes

- **Ready:** the learner explains the immediate invariant or correctly adapts the example. Assign the planned learner-owned task.
- **Ready with support:** keep the work collaborative, provide interface or test scaffolding, and use the hint ladder.
- **Not ready yet:** give another representation or smaller experiment; do not repeat the same explanation verbatim. After one unsuccessful retry in Lean, or two in Adaptive/Thorough, offer four explicit routes: a new example, pairing, a smaller task, or ownership transfer.
- **Declines this topic:** switch ownership or depth explicitly while preserving the engineering checks.

Readiness is local and temporary. It is not certification, and it does not by itself establish `demonstrated` mastery.

Scaffold incidental mechanics without a learner gate. Imports, assertion syntax, fixture construction, test wiring, and repetitive cases should not obscure the target concept. When several mechanical issues occur, explain and fix them together.

## Example: u64 codec

Do not begin with “decide what `encodeU64` accepts and `decodeU64` returns.” First establish:

- `u64` means an unsigned integer represented by exactly 64 bits, with values from `0` through `2^64 - 1`;
- JavaScript `number` cannot exactly represent every value in that range, while `bigint` can;
- a persistent codec must choose a fixed byte width and byte order;
- decoding fewer than eight bytes cannot produce a complete u64 value.

Then walk through a small value such as `258n` as eight bytes in the selected byte order and show one invalid input. Ask the learner to predict a neighboring example or explain why `number` is unsafe. If they already answer correctly, skip this lesson. Only after the check should the learner choose the public contract and boundary test.
