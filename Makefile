.DEFAULT_GOAL := help

# --- Variables ---
UV_RUN := uv run
PYTHON := $(UV_RUN) python
RUFF   := $(UV_RUN) ruff
MYPY   := $(UV_RUN) mypy
PYTEST := $(UV_RUN) pytest

# --- Environment & Setup ---

.PHONY: help
help: ## Show this help message
	@echo "Usage: make <target>"
	@echo ""
	@echo "Targets:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST) | sort

.PHONY: ensure-uv
ensure-uv: ## Check if uv is installed
	@command -v uv >/dev/null 2>&1 || { \
		echo "Error: 'uv' is not installed or not on PATH."; \
		echo "Install with: curl -LsSf https://astral.sh/uv/install.sh | sh"; \
		exit 127; \
	}

.PHONY: install-git-hooks
install-git-hooks: ## Configure git to use repo-managed hooks
	git config core.hooksPath .githooks

.PHONY: sync
sync: ensure-uv ## Sync template-engine dependencies
	uv sync

.PHONY: install
install: sync install-git-hooks ## Prepare the local template-engine environment

# --- Code Quality ---

.PHONY: fmt
fmt: ensure-uv ## Format and auto-fix the template-engine code
	$(RUFF) format .
	$(RUFF) check . --fix

.PHONY: lint
lint: ensure-uv ## Run lint checks for the template-engine code
	$(RUFF) format . --check
	$(RUFF) check .

.PHONY: type
type: ensure-uv ## Run static type checks for template-engine code
	$(MYPY) copier_extensions.py scripts tests

# --- Testing ---

.PHONY: test
test: install ## Run template-engine unit tests
	$(PYTEST) tests

.PHONY: render-test
render-test: install ## Render fixture repos and run their checks
	$(PYTHON) scripts/render_validate.py --mode full-e2e

.PHONY: render-test-render
render-test-render: install ## Render fixture repos and run render-only assertions
	$(PYTHON) scripts/render_validate.py --mode render-only

.PHONY: render-test-init
render-test-init: install ## Render fixture repos, run make init, and verify init artifacts
	$(PYTHON) scripts/render_validate.py --mode init

.PHONY: check
check: fmt lint type test render-test ## Run all template-engine checks

# --- Security & Utilities ---

.PHONY: secret-scan
secret-scan: ## Scan tracked repository files for leaked Gemini API keys
	@$(PYTHON) scripts/secret_scan.py --scope repo

.PHONY: secret-scan-staged
secret-scan-staged: ## Scan staged added lines for leaked Gemini API keys
	@$(PYTHON) scripts/secret_scan.py --scope staged-added
