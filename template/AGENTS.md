# Agent Contract

## Canonical Sources
- `README.md` - repository entry point and local workflow overview
- `pyproject.toml` - package metadata and tool configuration
- `poe_tasks.toml` - Python developer task catalog
- `Makefile` - repo bootstrap and future infrastructure wrapper surface

The repository root files above are canonical. This scaffold keeps most developer workflows in Poe and uses `make` for setup wrappers.

## Commands
- Use `uv` as the Python command entrypoint for this repo.
- Prefer `uv run poe <task>` for defined developer workflows; otherwise use `uv run <tool>`.
- Do not use `pip`, `python -m pip`, `poetry`, `pipenv`, `npm`, or `npx` for repo workflows.
- Use `make` for repo setup wrappers defined in [`Makefile`](Makefile).
- Common anchors: `make init`, `uv run poe verify`, `uv run poe run`, `uv run poe build`, `make install-git-hooks`.
- For the full command catalog and workflow guidance, use [`README.md`](README.md), [`poe_tasks.toml`](poe_tasks.toml), and [`Makefile`](Makefile).
- To inspect the current command surface directly, use `uv run poe --help` and `make help`.

## Validation
- Docs-only change: no mandatory validation; run targeted checks only if docs affect commands or generated artifacts.
- Code or config change: `uv run poe verify`
- Packaging validation: `uv run poe build`

## Development Practices
- Keep repo-level helper scripts in `scripts/`.
- Keep Python application code under `src/`.
