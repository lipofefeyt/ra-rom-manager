VENV := .venv
PYTHON := $(VENV)/bin/python3
PIP := $(VENV)/bin/pip
PYTEST := $(VENV)/bin/pytest
RUFF := $(VENV)/bin/ruff

.PHONY: install test lint fix all

install: $(VENV)/bin/activate

$(VENV)/bin/activate:
	python3 -m venv $(VENV)
	$(PIP) install -e '.[dev]'

test: install
	$(PYTEST)

lint: install
	$(RUFF) check src tests

fix: install
	$(RUFF) check src tests --fix
	$(RUFF) format src tests

all: lint test
