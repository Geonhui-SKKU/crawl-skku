UV ?= uv
HOST ?= 127.0.0.1
PORT ?= 8000

.DEFAULT_GOAL := help
.PHONY: help install env start dev test lint format format-check typecheck check

help:
	@printf '%s\n' \
		'make install       Install the locked dependencies and create .venv' \
		'make env           Create .env from .env.example if it does not exist' \
		'make start         Start the API server (HOST=127.0.0.1 PORT=8000)' \
		'make dev           Start the API server with automatic reload' \
		'make test          Run the local test suite' \
		'make lint          Run Ruff lint checks' \
		'make format        Format Python files with Ruff' \
		'make format-check  Check formatting without editing files' \
		'make typecheck     Run mypy' \
		'make check         Check formatting, lint, types, and tests'

install:
	$(UV) sync --locked

env:
	@if [ ! -e .env ] && [ ! -L .env ]; then (set -C; cat .env.example > .env); fi

start:
	$(UV) run --locked crawl-skku serve --host "$(HOST)" --port "$(PORT)"

dev:
	$(UV) run --locked uvicorn crawl_skku.api:app --reload --reload-dir src --host "$(HOST)" --port "$(PORT)"

test:
	$(UV) run --locked python -m unittest discover -s tests -v

lint:
	$(UV) run --locked ruff check .

format:
	$(UV) run --locked ruff format .

format-check:
	$(UV) run --locked ruff format --check .

typecheck:
	$(UV) run --locked mypy src

check: format-check lint typecheck test
