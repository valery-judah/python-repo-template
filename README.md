# Python Repo Template

This repository serves two audiences:
- template consumers who want to generate a new Python repository
- template maintainers who want to evolve the template itself

This repository contains two layers:
- the template engine at the repo root
- the generated Python starter payload under `template/`

## Requirements
- Python 3.11+
- `uv`

## Quickstart
Render a new repository from GitHub:

```bash
uvx copier copy --trust gh:<github-user-or-org>/python-repo-template ./my-new-repo \
  --data repo_slug=my-new-repo \
  --defaults
```

Bootstrap the generated repository:

```bash
cd my-new-repo
make init
make test
make run
```

Example: `repo_slug=my-new-repo` produces a package named `my_new_repo`.

## What This Template Provides
This template is an opinionated starting point for Python projects that are developed with coding agents as well as humans.

It provides three things out of the box:

- agent operating context via `AGENTS.md`
- local development and CI loops via standard `make` targets
- a minimal Python project baseline built around `uv`, `src/`, tests, and a `Makefile`

`AGENTS.md` establishes repository-specific rules, command policy, workflow expectations, and done criteria. That gives coding agents a fixed contract for how to work in the repository instead of relying on ad hoc instructions in each session.

The local command surface includes targets such as `make fmt`, `make lint`, `make type`, and `make test`. Those commands are meant to be used both by humans and by coding agents, locally and in CI, so validation stays consistent.

The generated project also includes a basic Python repository structure that is ready to extend rather than reinvent. The goal is not only to scaffold files, but to create a repository with a predefined execution model: agents know how to operate, contributors know which commands matter, and automation can enforce the same checks everywhere.

## Layout
```text
copier.yml
copier_extensions.py
scripts/
template/
  pyproject.toml.jinja
  Makefile.jinja
  src/
  tests/
```

Copier renders from the `template/` subdirectory into the destination repository root. The root-level files in this repo are for the template engine and validation workflow.

## Template Inputs
- `repo_slug`: repository directory and slug, for example `my-new-repo`
- `repo_name`: human-readable project name; defaults to `repo_slug`
- `python_version`: supported Python version; defaults to `3.11`
- `package_name`: derived automatically from `repo_slug`, for example `my_new_repo`

`--trust` is required because Copier needs permission to execute this template's helper code in [copier_extensions.py](/Users/val/projects/python-repo-template/copier_extensions.py).

## Using The Template
Render from GitHub after committing and pushing template changes:

```bash
uvx copier copy --trust gh:<github-user-or-org>/python-repo-template ./my-new-repo \
  --data repo_slug=my-new-repo \
  --defaults
```

To test the template from a local clone before pushing, render from the repo path instead:

```bash
uvx copier copy --trust /absolute/path/to/python-repo-template ./my-new-repo \
  --data repo_slug=my-new-repo \
  --defaults
```

Then bootstrap the generated repository:

```bash
cd my-new-repo
make init
make test
make run
```

## Maintaining The Template
Use these commands when working on the template engine and validation fixtures in this repository:

```bash
make sync
make test
make render-test-render
make render-test-init
make render-test
```

The render validation is split by depth:
- `make render-test-render`: render-only assertions for layout, identity, and templated content
- `make render-test-init`: render plus `make init`, including init artifact checks
- `make render-test`: full end-to-end validation of the generated repo commands

You can also run the script directly and select scenarios:

```bash
uv run python scripts/render_validate.py --mode render-only --scenario sample-app
uv run python scripts/render_validate.py --mode full-e2e
```
