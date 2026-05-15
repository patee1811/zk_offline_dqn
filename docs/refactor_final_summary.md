# Refactor Final Summary

## Completed Phases

- Phase 1A/1B: established refactor groundwork and active import surface.
- Phase 2A-2G: extracted relation/verifier modules for membership, TD MVP,
  forward-TD MLP, one-step SGD tiny, minibatch TD, one-step update, and short
  trace checks.
- Phase 3: centralized artifact schema constants, JSON IO, manifest metadata,
  and field roles.
- Phase 4: added the unified CLI namespace.
- Phase 5: organized unit, golden, negative, and regression tests.
- Phase 6: added SP1/Python alignment helpers and Kaggle validation assets.
- Phase 6B: made Kaggle validation run against the current workspace and set up
  Rust/SP1 reliably.
- Phase 6C: validated SP1 proof generation on Kaggle for the TD MVP canonical
  vector.
- Phase 7: generated benchmark/reproducibility report snapshots from existing
  outputs.
- Phase 8: documented architecture, legacy status, reporting policy, and
  repository hygiene.
- Phase 9: aligned paper-facing claims with the implemented artifact and
  hardened the SP1 proof claim to TD MVP canonical-vector validation.

## Problems Addressed

- Relation logic is separated from artifact loading.
- Schema strings and JSON IO are centralized.
- CLI entrypoints are discoverable.
- Regression and negative tests are organized.
- SP1/Python alignment is documented and test-covered.
- Kaggle SP1 validation can use a local workspace archive.
- Paper-facing report files are generated with provenance.
- Legacy scripts are classified instead of deleted aggressively.
- Paper-facing SP1 claims are checked for overbroad wording.

## Remaining Limitations

- The project does not prove full DQN training.
- The validated SP1 proof claim is scoped to TD MVP on
  `zk_backend/test_vectors/td_mvp_case_0.json`.
- Python regression pass does not imply SP1 proof generation unless Kaggle or a
  Linux/SP1 environment has run the proof command.
- Legacy scripts remain because compatibility users still exist.
- Paper files were edited conservatively in Phase 9 to scope the validated SP1
  proof claim to the TD MVP canonical vector.

## Remaining Cleanup Work

- Audit each legacy script for direct users before considering retirement.
- Keep `.gitignore` aligned with generated output policy.
- Re-run report generation after any benchmark or Kaggle validation refresh.
- Record exact backend environments when creating release artifacts.
- Produce separate proof validation summaries before expanding paper claims to
  additional relations.
