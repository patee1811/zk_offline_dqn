.PHONY: help setup check paper-checks reproduce-small reproduce-data-audit reproduce-smoke-sources reproduce-sp1-proofs reproduce-benchmarks reproduce-tamper reproduce-paper-tables artifact-manifest clean-artifacts smoke unit golden negative cli-smoke regression all-checks

PYTHON ?= python
REPRO_DIR := artifacts/reproducibility
DATA_AUDIT_DIR := $(REPRO_DIR)/data_audit/cartpole-phase10-small

help:
	@echo "Reviewer targets:"
	@echo "  make reproduce-small          Run fast artifact reproduction checks"
	@echo "  make reproduce-data-audit     Regenerate a tiny audited dataset commitment"
	@echo "  make reproduce-smoke-sources  Regenerate lightweight regression/report smoke sources"
	@echo "  make reproduce-sp1-proofs     Verify compact SP1 provenance; heavy prove is opt-in"
	@echo "  make reproduce-benchmarks     Validate or optionally rerun benchmarks"
	@echo "  make reproduce-tamper         Validate or optionally rerun tamper table"
	@echo "  make reproduce-paper-tables   Regenerate paper-facing report tables"
	@echo "  make artifact-manifest        Regenerate artifact_manifest.json and hash inventories"
	@echo ""
	@echo "Heavy reruns are gated by RUN_HEAVY_SP1=1, RUN_HEAVY_BENCHMARKS=1, or RUN_HEAVY_TAMPER=1."

setup:
	$(PYTHON) -m pip install -r requirements.lock || $(PYTHON) -m pip install -r requirements.txt
	$(PYTHON) -m pip install -e .

smoke:
	$(PYTHON) -m compileall zk_offline_dqn scripts tests

unit:
	$(PYTHON) -m unittest discover tests/unit

golden:
	$(PYTHON) -m unittest discover tests/golden

negative:
	$(PYTHON) -m unittest discover tests/negative

cli-smoke:
	$(PYTHON) -m unittest discover tests/regression

regression:
	$(PYTHON) scripts/experiments/run_full_regression.py

check:
	$(PYTHON) -m unittest discover tests
	$(PYTHON) scripts/experiments/check_paper_claims.py
	$(PYTHON) scripts/experiments/check_report_sources.py
	$(PYTHON) scripts/experiments/check_theorem_artifact_map.py

paper-checks:
	$(PYTHON) scripts/experiments/check_paper_claims.py
	$(PYTHON) scripts/experiments/check_report_sources.py
	$(PYTHON) scripts/experiments/check_theorem_artifact_map.py
	$(PYTHON) scripts/experiments/check_paper_numbers_against_final_ndss.py

reproduce-small: reproduce-data-audit reproduce-smoke-sources reproduce-sp1-proofs reproduce-benchmarks reproduce-tamper reproduce-paper-tables artifact-manifest check
	@echo "reproduce-small = passed"

reproduce-data-audit:
	mkdir -p $(REPRO_DIR)/data_audit
	$(PYTHON) scripts/data/collect_audited_dataset.py --env-id CartPole-v1 --dataset-id cartpole-phase10-small --policy random --num-episodes 1 --base-seed 12345 --max-steps-per-episode 5 --out-dir $(DATA_AUDIT_DIR) --audit-after-collect
	$(PYTHON) scripts/data/audit_replay_dataset.py --dataset-dir $(DATA_AUDIT_DIR)
	$(PYTHON) scripts/data/commit_audited_dataset.py --dataset-dir $(DATA_AUDIT_DIR)
	$(PYTHON) scripts/data/verify_dataset_commitment.py --dataset-dir $(DATA_AUDIT_DIR)
	@echo "dataset_audit_report = $(DATA_AUDIT_DIR)/replay_audit_report.json"

reproduce-smoke-sources:
	$(PYTHON) scripts/experiments/run_full_regression.py
	$(PYTHON) scripts/experiments/benchmark_distinct_td_sp1.py --skip-sp1 --out-dir artifacts/benchmarks/distinct_td_sp1_python_smoke
	$(PYTHON) scripts/experiments/benchmark_forward_td_mlp_sp1.py --skip-sp1 --out-dir artifacts/benchmarks/forward_td_mlp_sp1_python_smoke
	$(PYTHON) scripts/experiments/benchmark_one_step_sgd_tiny_sp1.py --skip-sp1 --out-dir artifacts/benchmarks/one_step_sgd_tiny_sp1_python_smoke

reproduce-sp1-proofs:
	$(PYTHON) scripts/experiments/check_report_sources.py
	@if [ "$$RUN_HEAVY_SP1" = "1" ]; then \
		echo "RUN_HEAVY_SP1=1: use scripts/experiments/run_phase8_2_proof_benchmark.py or relation-specific SP1 validation scripts for full proof reruns"; \
		$(PYTHON) scripts/experiments/check_sp1_environment.py; \
	else \
		echo "RUN_HEAVY_SP1 is not set; using committed compact SP1 provenance and public-input hashes."; \
	fi

reproduce-benchmarks:
	$(PYTHON) scripts/experiments/check_report_sources.py
	$(PYTHON) scripts/experiments/generate_paper_reports.py
	@if [ "$$RUN_HEAVY_BENCHMARKS" = "1" ]; then \
		echo "RUN_HEAVY_BENCHMARKS=1: run Phase 8 benchmark scripts explicitly for full refresh."; \
	else \
		echo "RUN_HEAVY_BENCHMARKS is not set; validated existing Table 1/Table 2 compact reports."; \
	fi

reproduce-tamper:
	$(PYTHON) scripts/experiments/check_report_sources.py
	@if [ "$$RUN_HEAVY_TAMPER" = "1" ]; then \
		$(PYTHON) scripts/experiments/run_phase8_3_tamper_benchmark.py --smoke --include-dataset-tamper --include-merkle-tamper --include-proof-public-input-tamper --run-python-reference --reuse-existing-provenance --out-dir artifacts/reports/final_ndss; \
	else \
		echo "RUN_HEAVY_TAMPER is not set; validated existing Table 3 compact report."; \
	fi

reproduce-paper-tables:
	$(PYTHON) scripts/experiments/generate_paper_reports.py
	$(PYTHON) scripts/experiments/check_paper_numbers_against_final_ndss.py

artifact-manifest:
	$(PYTHON) scripts/experiments/generate_artifact_manifest.py

clean-artifacts:
	rm -rf $(REPRO_DIR)/**/work $(REPRO_DIR)/**/tmp artifacts/reports/**/work artifacts/reports/**/tmp artifacts/reports/**/proofs

all-checks: smoke unit golden negative cli-smoke regression paper-checks
