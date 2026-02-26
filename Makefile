.PHONY: lint format typecheck run all

PYTHON_FILES := main.py ai_utils.py schemas.py prompts.py

lint:
	ruff check $(PYTHON_FILES)

format:
	black $(PYTHON_FILES)

typecheck:
	mypy --ignore-missing-imports $(PYTHON_FILES)

check: format lint typecheck

run:
	uvicorn main:app --reload

all: check run
