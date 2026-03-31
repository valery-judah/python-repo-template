# Agent Contract

## Canonical Sources
- `README.md` - repository overview for the template engine and generated scaffold
- `pyproject.toml` - template-engine metadata and tool configuration
- `poe_tasks.toml` - template-engine Python developer task catalog
- `Makefile` - repo bootstrap and infrastructure wrapper surface
- `template/` - generated repository payload and its agent-facing defaults

The repository root files above are canonical for template-engine work. Files under `template/` define the generated project contract and must be updated with the root validation workflow when scaffold behavior changes.

## Commands
- Use `uv` as the Python command entrypoint for this repo.
- Prefer `uv run poe <task>` for template-engine Python workflows; otherwise use `uv run <tool>`.
- Do not use `pip`, `python -m pip`, `poetry`, or `pipenv` for repo workflows.
- Use `make` for repo setup and local infrastructure wrappers defined in [`Makefile`](/Users/val/projects/python-repo-template/Makefile).
- Common anchors: `uv sync --group dev`, `uv run poe verify`, `uv run poe render-test`, `make install`, `make install-git-hooks`.
- For the full command catalog and workflow guidance, use [`README.md`](/Users/val/projects/python-repo-template/README.md), [`poe_tasks.toml`](/Users/val/projects/python-repo-template/poe_tasks.toml), and [`Makefile`](/Users/val/projects/python-repo-template/Makefile).
- To inspect the current command surface directly, use `uv run poe --help` and `make help`.

## Validation
- Docs-only change: no mandatory validation; run targeted checks only if docs affect commands or generated artifacts.
- Template-engine code or config change: `uv run poe verify`
- Template payload or render-contract change: `uv run poe render-test`

## Development Practices
- Keep template-engine helper scripts in `scripts/`.
- Keep generated-project source code under `template/src/`.
- Keep render validation deterministic by updating tests and docs alongside scaffold contract changes.
