.DEFAULT_GOAL := help

.PHONY: help
help: ## Show this help message
	@echo "Usage: make <target>"
	@echo ""
	@echo "Repo & Infrastructure Targets:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-25s %s\n", $$1, $$2}' $(MAKEFILE_LIST) | sort
	@echo ""
	@echo "Python developer tasks live in Poe."
	@echo "Run 'uv run poe --help' or 'uv run poe <task>' for fmt/lint/type/test/run/build/clean."

.PHONY: sync
sync: ## Sync project dependencies
	uv sync --group dev

.PHONY: init
init: sync install-git-hooks ## Prepare the local development environment

.PHONY: install-git-hooks
install-git-hooks: ## Configure git to use repo-managed hooks
	@if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then \
		git config core.hooksPath .githooks; \
	else \
		echo "Not in a git repository. Skipping git hooks setup."; \
	fi
