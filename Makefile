.DEFAULT_GOAL := help

.PHONY: help
help: ## Show this help message
	@echo "Usage: make <target>"
	@echo ""
	@echo "Repo & Infrastructure Targets:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-25s %s\n", $$1, $$2}' $(MAKEFILE_LIST) | sort
	@echo ""
	@echo "Python developer tasks live in Poe."
	@echo "Run 'uv run poe --help' or 'uv run poe <task>' for fmt/lint/type/test/render-test."

.PHONY: sync
sync: ## Sync template-engine dependencies
	uv sync --group dev

.PHONY: install
install: sync install-git-hooks ## Prepare the local template-engine environment

.PHONY: install-git-hooks
install-git-hooks: ## Configure git to use repo-managed hooks
	git config core.hooksPath .githooks
