.PHONY: install pin test lint format format-check check fix run dry-run clean help

.DEFAULT_GOAL := help

install:          ## Install dependencies with UV
	uv sync

pin:              ## Update and freeze dependencies
	uv lock --upgrade

test:             ## Run test suite
	uv run pytest tests/ -v

lint:             ## Check code style with ruff
	uv run ruff check .

format:           ## Format code with ruff
	uv run ruff format .

format-check:     ## Check formatting without making changes
	uv run ruff format --check .

check:            ## Run linting and format checks
	$(MAKE) lint && $(MAKE) format-check

fix:              ## Automatically fix linting and format issues
	$(MAKE) format && uv run ruff check --fix .

run:              ## Run CLI application (requires CONFIG environment variable)
	@if [ -z "$(CONFIG)" ]; then \
		echo "Error: CONFIG environment variable not set"; \
		echo "Usage: make run CONFIG=path/to/config.yaml"; \
		exit 1; \
	fi
	uv run python main.py --config $(CONFIG)

dry-run:          ## Preview changes without applying (requires CONFIG environment variable)
	@if [ -z "$(CONFIG)" ]; then \
		echo "Error: CONFIG environment variable not set"; \
		echo "Usage: make dry-run CONFIG=path/to/config.yaml"; \
		exit 1; \
	fi
	uv run python main.py --config $(CONFIG) --dry-run

clean:            ## Remove build artefacts and cache
	rm -rf __pycache__ .pytest_cache .coverage htmlcov dist build *.egg-info .uv

help:             ## Display this help message
	@echo "Available commands:"
	@grep -E '^[a-z-]+:.*##' Makefile | sed 's/:.*##//' | while read cmd; do \
		desc=$$(grep "^$$cmd:.*##" Makefile | sed 's/^[^#]*## //'); \
		printf "  %-20s %s\n" "$$cmd" "$$desc"; \
	done
