PY ?= python3

.PHONY: accuracy test

accuracy:
	PYTHONPATH=src $(PY) -m dex_lips.eval

test:
	$(PY) -m unittest discover -s tests -v
