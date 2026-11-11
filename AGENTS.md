# Agent Contract

This repository is a Copier template for Python projects. `template/` is the generated project, `copier.yml` defines its inputs, and `scripts/render_validate.py` renders fixture projects to test it.

## Canonical sources
- `README.md` - creating a project, setting up this repository, and its workflows
- `copier.yml` - template inputs and defaults
- `template/AGENTS.md.jinja` - the agent contract for generated projects

## Commands
- Run workflows through `task`, otherwise `uv run <tool>`. Do not use `pip`, `python -m pip`, `poetry`, `pipenv`, `npm`, or `npx`.

## Validation
- Change under `scripts/` or `tests/`: `task quality:verify`.
- Change under `template/`, or to `copier.yml` or `copier_extensions.py`: `task render:test`. It renders fixture projects and runs their checks.
- Both of the above, or any other change: `task quality:check`.
- Change to root `README.md` or `AGENTS.md` only: none.

## Scratch scripts
- Put temporary, exploratory, and devex scripts in `scripts/devex/`.
