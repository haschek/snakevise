.PHONY: install install-dev lint lint-python lint-md format help

# Default target
help:
	@echo "SnakeVISE Development Tasks:"
	@echo "  install      Install core dependencies"
	@echo "  install-dev  Install core and development dependencies"
	@echo "  lint         Run all linters with auto-fix"
	@echo "  lint-python  Run ruff linter with auto-fix"
	@echo "  lint-md      Run markdownlint with auto-fix"
	@echo "  format       Run code formatters"

install:
	pip install .

install-dev:
	pip install -e ".[dev]"
	pre-commit install

lint: lint-python lint-md

lint-python:
	ruff check . --fix

lint-md:
	pymarkdown --config .pymarkdown.json fix **/*.md

format:
	ruff format .
