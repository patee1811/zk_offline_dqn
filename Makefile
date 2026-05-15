.PHONY: smoke unit golden negative cli-smoke regression all-checks

smoke:
	python -m compileall zk_offline_dqn scripts src tests

unit:
	python -m unittest discover tests/unit

golden:
	python -m unittest discover tests/golden

negative:
	python -m unittest discover tests/negative

cli-smoke:
	python -m unittest discover tests/regression

regression:
	python scripts/experiments/run_full_regression.py

all-checks:
	$(MAKE) smoke
	$(MAKE) unit
	$(MAKE) golden
	$(MAKE) negative
	$(MAKE) cli-smoke
	$(MAKE) regression
