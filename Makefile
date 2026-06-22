VENV := .venv
PYTHON := $(VENV)/bin/python3
PIP := $(VENV)/bin/pip
PYTEST := $(VENV)/bin/python -m pytest
RUFF := $(VENV)/bin/ruff

.PHONY: install test lint fix all

install: $(VENV)/bin/activate

$(VENV)/bin/activate:
	/usr/local/bin/python3.12 -m venv $(VENV)
	$(PIP) install -e '.[dev]'

test: install
	$(PYTEST)

lint: install
	$(RUFF) check src tests

fix: install
	$(RUFF) check src tests --fix
	$(RUFF) format src tests

all: lint test
