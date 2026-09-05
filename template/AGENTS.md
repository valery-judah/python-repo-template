# Agent Contract

## Canonical sources
- `docs/evergreen/mvp.md` - product scope
- `docs/evergreen/architecture.md` - architecture and current repo shape
- `docs/evergreen/api-contracts.md` - stable runtime interfaces
- `docs/evergreen/runbook.md` - local commands and operation
- `docs/README.md` - docs index

`docs/evergreen/` is canonical. `docs/delivery/` is reference-only.

Start the product base in `docs/product/spec.md` and `docs/product/concepts.md`. Promote stable
material into `docs/evergreen/` as it hardens.

## Commands
- Use `task <namespace>:<name>` as the workflow entrypoint for this repo. Keep `uv` for Python environments, dependencies, and tool execution.
- Use tasks defined in [`Taskfile.yml`](Taskfile.yml); otherwise use `uv run <tool>`.
- Do not use `pip`, `python -m pip`, `poetry`, `pipenv`, `npm`, or `npx` for repo workflows.
- For the full command catalog and operational guidance, use [`docs/evergreen/runbook.md`](docs/evergreen/runbook.md).
- To inspect the current command surface directly, use `task` or `task help`.

## Validation
- Docs-only change: no mandatory validation; run targeted checks only if docs affect commands or generated artifacts.
- Code change: `task quality:verify`

## Development Practices
- Save any temporary, exploratory, or developer-experience (devex) scripts into the `scripts/devex/` directory.
