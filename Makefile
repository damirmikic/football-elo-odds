.PHONY: help install test lint format clean

help:
	@echo "Available commands:"
	@echo "  make install    - Install dependencies"
	@echo "  make test       - Run tests with coverage"
	@echo "  make lint       - Run all linters"
	@echo "  make format     - Format code with black and isort"
	@echo "  make clean      - Remove cache and generated files"

install:
	pip install -r requirements.txt

test:
	pytest

lint:
	@echo "Running black..."
	black --check .
	@echo "Running isort..."
	isort --check-only .
	@echo "Running pylint..."
	pylint *.py

format:
	@echo "Formatting with black..."
	black .
	@echo "Sorting imports with isort..."
	isort .

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .coverage -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name htmlcov -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
