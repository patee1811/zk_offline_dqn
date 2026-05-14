.PHONY: smoke unit

smoke:
	python -m compileall zk_offline_dqn scripts src tests

unit:
	python -m unittest discover tests
