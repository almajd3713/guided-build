# Resume and Reconciliation

## Sources of truth

Use this precedence:

1. Current repository files and test behavior.
2. Approved `.guided-build/project.md`.
3. Committed/shared milestone evidence.
4. Private state.

Private state is a progress cache, not authority over the repository.

## Reconciliation procedure

1. Validate contract and evidence schemas.
2. Inspect the working tree and identify pre-existing/user changes.
3. Compare active slice and delivery status with actual changes.
4. Run the narrowest safe validation.
5. If work exists without evidence, summarize it and ask whether it belongs to the active slice.
6. If state claims completion but validation fails, return delivery to `in_progress` or `blocked`; preserve the prior record in evidence.
7. If the contract changed, add new milestones to state without deleting retired history. Current contract concepts control future gates; historical topic and concept records remain inert context. Ask before remapping IDs.
8. Resume only after the learner confirms material ambiguity.

## Corruption and migration

Do not overwrite unreadable private state. Report its path and recover from an explicit export or shared evidence. Unsupported schema majors require a migration; do not guess.

## Privacy

Default exports remove preferences and topic calibration, plus confidence, misconceptions, and session notes. Include them only with explicit `--include-private-notes`. Never paste private state wholesale into chat or committed files.
