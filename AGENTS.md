# Agent Contract

## Canonical sources
- `docs/evergreen/mvp.md` - product scope
- `docs/evergreen/architecture.md` - architecture and current repo shape
- `docs/evergreen/api-contracts.md` - stable runtime interfaces
- `docs/evergreen/runbook.md` - local commands and operation
- `docs/README.md` - docs index

`docs/evergreen/` is canonical. `docs/delivery/` is reference-only.

For now, the `evergreen` directory is empty. We're working on the `docs/product/spec.md` and `docs/product/concepts.md` to build a product base.

## Commands
- Use `uv` as the Python command entrypoint for this repo.
- Prefer `uv run poe <task>` for defined developer workflows; otherwise use `uv run <tool>`.
- Do not use `pip`, `python -m pip`, `poetry`, `pipenv`, `npm`, or `npx` for repo workflows.
- Use `make` for local DevEx and infrastructure wrappers such as Docker, Docker Compose, observability stack operations, as defined in [`Makefile`](Makefile).
- For the full command catalog and operational guidance, use [`docs/evergreen/runbook.md`](docs/evergreen/runbook.md).
- To inspect the current command surface directly, use `uv run poe --help` and `make help`.

## Validation
- Docs-only change: no mandatory validation; run targeted checks only if docs affect commands or generated artifacts.
- Code change: `uv run poe verify`

## Development Practices
- Save any temporary, exploratory, or developer-experience (devex) scripts into the `scripts/devex/` directory.
