# Privacy

## Shared data

The project contract and milestone evidence are intended for version control. They contain project goals, ownership history, repository references, commands/results, decisions, and technical debt.

They must not contain:

- familiarity or learner self-reports;
- confidence ratings;
- misconceptions or private reflections;
- guidance, verbosity, or struggle preferences;
- raw unsuccessful attempts or tutoring transcripts;
- private-state field labels;
- credentials or tokens;
- raw private-state dumps;
- unnecessary personal identifiers.

## Private data

Private state is stored in the platform state directory with restrictive permissions where supported. It includes concept status, topic-level familiarity and confidence provided by the learner, coaching preferences, misconceptions, evidence references, and resume notes.

State writes use a temporary file, flush and synchronize it, then atomically replace the target. Explicit imports and automatic v1-to-v2 migration create a timestamped backup before replacement.

Shared evidence exposes capability IDs and engineering delivery state, but not the learner calibration that influenced teaching. Evidence validation warns when the authoritative snapshot exceeds 600 words or the rolling log exceeds five 60-word entries.

Exports and normal status output omit preferences and topic calibration, and redact concept familiarity, confidence, misconceptions, and session notes unless `--include-private-notes` is explicitly supplied.

## Network and telemetry

Guided Build sends no telemetry and has no hosted backend. Optional Codex tools may have their own policies; the skill must disclose and request authorization before external writes.

## Reporting issues

Remove private state, credentials, repository secrets, and proprietary source before sharing logs or reproduction material.
