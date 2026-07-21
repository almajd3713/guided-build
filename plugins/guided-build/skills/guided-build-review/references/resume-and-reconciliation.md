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
3. Compare active capability, per-capability delivery status, and milestone status with actual changes.
4. Run the narrowest safe validation.
5. If work exists without evidence, summarize it and ask whether it belongs to the active capability.
6. If state claims completion but validation fails, return delivery to `in_progress` or `blocked`; preserve the prior record in evidence.
7. If the contract changed, add new milestones/capabilities without deleting historical learning records. Current contract concepts and capability prerequisites control future gates. Ask before remapping stable IDs.
8. Resume only after the learner confirms material ambiguity.

## Corruption and migration

Do not overwrite unreadable private state. Report its path and recover from an explicit export or shared evidence. The CLI migrates private state v1 to v2 with a timestamped backup and initializes capability delivery conservatively. Unsupported versions still require an explicit migration; do not guess completion from old slices.

## Privacy

Default exports remove preferences and topic calibration, plus confidence, misconceptions, and session notes. Include them only with explicit `--include-private-notes`. Never paste private state wholesale into chat or committed files.
