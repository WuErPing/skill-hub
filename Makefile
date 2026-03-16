.PHONY: install test lint clean build

install:
	pip install -e .

test:
	pytest tests/

lint:
	ruff check src/ tests/

clean:
	rm -rf build/ dist/ *.egg-info .pytest_cache __pycache__ tests/__pycache__

build:
	python -m build

version-bump:
	qwen -y -i "execute skill version-bump"