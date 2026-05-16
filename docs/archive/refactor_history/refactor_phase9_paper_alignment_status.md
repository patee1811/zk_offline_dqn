# Refactor Phase 9 Paper Alignment Status

## Scope

Phase 9 audits and hardens paper-facing claims against the implemented
artifact. It does not change verifier logic, artifact schemas, benchmark
methodology, Rust/SP1 source code, or canonical artifacts.

## Files Created

- `docs/paper_alignment_audit.md`
- `docs/refactor_phase9_paper_alignment_status.md`
- `scripts/experiments/check_paper_claims.py`
- `tests/regression/test_paper_claims.py`

## Files Modified

- `paper/sections/abstract.tex`
- `paper/sections/introduction.tex`
- `paper/sections/formal_statements.tex`
- `paper/sections/sp1_backend.tex`
- `paper/sections/results.tex`
- `paper/sections/discussion.tex`
- `paper/sections/experimental_setup.tex`
- `paper/sections/conclusion.tex`
- `paper/sections/limitations.tex`
- `paper/sections/security_analysis.tex`
- `paper/sections/threat_model.tex`
- `paper/sections/zk_direction.tex`
- `paper/sections/appendix.tex`
- `paper/README.md`
- `paper/CHANGELOG.md`
- `scripts/experiments/check_paper_numbers_against_final_ndss.py`
- `docs/refactor_final_summary.md`
- `docs/reproducibility.md`
- `README.md`

## Claims Hardened

- Broad SP1 proof wording was replaced with the supported TD MVP canonical
  vector claim.
- Distinct TD, forward-TD MLP, and tiny one-step SGD are described as Python
  semantic-oracle/report-backed checks unless separate SP1 proof summaries are
  produced.
- The results proof table now reports only the validated TD MVP SP1 proof row
  from `artifacts/reports/final_ndss/paper_numbers.json`.
- The paper-number checker now validates scoped Phase 7 paper numbers instead
  of requiring the previous seven-row proof table.

## Supported SP1 Claim

```text
SP1 proof generation and verification passed on Kaggle for the TD MVP SP1
backend using zk_backend/test_vectors/td_mvp_case_0.json.
```

## Remaining Recommendations

- Do not claim SP1 proofs for other relations until separate validation
  summaries with proof generation and verification are available.
- Keep paper tables sourced from `artifacts/reports/final_ndss/paper_numbers.json`.
- Re-run `scripts/experiments/check_paper_claims.py` after any paper wording
  change.

## Command Status

Phase 9 validation completed:

```text
python -m compileall zk_offline_dqn scripts src tests
python -m unittest discover tests
python -m unittest discover tests/regression
python scripts/experiments/check_report_sources.py
python scripts/experiments/generate_paper_reports.py
python scripts/experiments/check_paper_claims.py
python scripts/experiments/check_paper_numbers_against_final_ndss.py
python scripts/experiments/run_full_regression.py
```

Results:

- Compile smoke: passed.
- Full unittest discovery: passed, 103 tests.
- Regression unittest discovery: passed, 23 tests.
- Report source check: passed.
- Report generation: passed.
- Paper claim check: passed.
- Paper number check: passed.
- Full regression: passed all 15 checks.

No SP1 proof was rerun in Phase 9.
