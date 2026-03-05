# Python Repo Templating Plan

## Summary
- Turn `python-repo-template` itself into the Copier template source.
- Keep the template engine at the repo root and the generated starter payload under `template/`.
- Keep v1 as a single base Python starter template, not a multi-kind `service` / `library` / `cli` system.
- Preserve the current repository contract where practical: `uv`, `Makefile`-driven workflows, `src/` layout, editable installs, tests against installed-package behavior, and the repo-managed secret scan.
- Make the plan implementation-ready for templating this repo's concrete package/module names and documentation into generated repositories.

---

## Current repo baseline

This repository now has a split layout:
- root-level template engine files such as `copier.yml`, `copier_extensions.py`, `scripts/`, and the engine `Makefile`
- generated starter payload under `template/`
- payload package source under `template/src/{{ package_name }}/`
- payload project metadata in `template/pyproject.toml.jinja`
- payload docs and policy files under `template/`
- a payload-local secret scanning tool rendered under `<package_name>.devtools.secret_scan`

The plan should treat the `template/` directory as the generated repository contents and the repo root as engine and validation infrastructure.

---

## Goals and constraints
- **One-shot scaffolding**: generate a new repository once; no template update/rebase workflow is required.
- **Template source**: this repository is the Copier template source.
- **Project shape**: one general-purpose Python starter template for v1.
- **Dependency management**: `uv` only, with lockfile generated via standard commands.
- **Build/automation**: `Makefile` remains the main interface.
- **Packaging**: keep `src/` layout as the source of truth.
- **Tests**: generated projects must validate installed-package behavior and must not rely on path hacks.
- **Docs/policy files**: preserve repo-managed Markdown and instruction files unless they require templated identifiers.
- **Security checks**: generated projects must keep the current secret-scan workflow and related make targets.

---

## High-level approach

Use **Copier** to render this repository into a new repository. The root repo owns Copier configuration and validation; the `template/` subdirectory owns the rendered payload.

Example target workflow:

```bash
uvx copier copy --trust /path/to/python-repo-template ./my-new-repo \
  --data repo_slug=my-new-repo \
  --defaults
```

GitHub-hosted usage can remain a supported invocation mode later:

```bash
uvx copier copy --trust gh:<owner>/python-repo-template ./my-new-repo \
  --data repo_slug=my-new-repo \
  --defaults
```

The implementation should not run post-render install commands automatically. Generated repositories should be initialized explicitly by the user after render.

---

## Template contract

### Required template inputs
- `repo_slug`: kebab-case repository name, for example `my-new-repo`

### Derived or defaulted values
- `repo_name`: defaults to a display form derived from `repo_slug`, or to the slug itself if no better transformation is introduced
- `package_name`: derived from `repo_slug` and used for Python module/package paths
- `python_version`: default to the baseline this repo standardizes on during implementation

### `package_name` derivation rules
- lower-case the slug
- replace `-` with `_`
- strip characters outside `[a-z0-9_]`
- if the name does not start with `[a-z_]`, prefix `_`

The repo may keep a local Python helper for validation, but the actual Copier render path should prefer built-in templating where possible.

### Generated repository interface
- package source renders to `src/<package_name>/`
- `[project.name]` in `pyproject.toml` renders from the chosen repo/package naming policy
- console script entrypoint renders consistently with the package module path
- CLI labels and help text must not hard-code `template`
- tests must import from the rendered package name
- `Makefile` targets remain the canonical local workflow interface

---

## Files to template vs copy

### Templated files
The implementation should template the files that currently hard-code the concrete `template` project identity:
- `pyproject.toml`
- `README.md`
- package directory names under `src/`
- package imports in code and tests
- CLI program name and printed labels
- any docs that reference the concrete package/repo name and would be incorrect in generated repos

### Verbatim or near-verbatim copies
These should stay unchanged unless a repo-specific identifier forces a small template substitution:
- `AGENTS.md`
- `CONTRIBUTING.md`
- `SECURITY.md`
- most documentation content under `docs/`
- the secret scanning implementation and make target semantics

The implementation should prefer minimal templating. Only introduce substitutions where leaving `template` or repo-specific paths would make the generated repository incorrect.

---

## Repository changes required to support templating

### Add Copier metadata
- add `copier.yml` with the v1 question set centered on `repo_slug`
- keep `copier_extensions.py` only as local validation/support code if direct Copier templating is sufficient
- add a short usage section for rendering the template, either in `README.md` or a dedicated template-usage doc

### Convert the current package layout into templated form
- keep the concrete payload inside `template/` and render it to the destination repo root
- rename the concrete package path from `template/src/template` to a templated package path in the template source
- convert code imports and test imports to use templated package names
- render the console script and module entrypoint from the same package variable

### Keep the current workflow contract
- preserve `make sync`, `make install`, `make fmt`, `make lint`, `make type`, `make test`, `make run`, and `make secret-scan`
- provide explicit `make lock` and `make sync` workflow so generated repos can create/populate `uv.lock`
- ensure generated repositories do not require `PYTHONPATH` manipulation

### Preserve the current security workflow
- keep the local Gemini-format secret scanner
- preserve `make secret-scan` and `make secret-scan-staged`
- preserve repo-managed git hook installation if it remains useful in generated repositories

---

## Explicit non-goals for v1
- no `project_kind` switch
- no conditional `service` / `library` / `cli` directory trees
- no template update/rebase workflow for already-generated repositories
- no automatic post-render `uv sync`
- no requirement to add CI, pre-commit, or GitHub automation in the first templating pass unless separately prioritized

These can be follow-on enhancements after the base template is rendering correctly.

---

## Validation and acceptance criteria

The templating work is done when:
- this repo can render a new repository from Copier without manual code edits
- generated repositories contain no hard-coded `template` package/import references
- generated repositories preserve the same local development workflow exposed by the current `Makefile`
- generated repositories keep deterministic lock generation and editable install behavior
- generated repositories keep the secret scan commands working with the rendered package path

### Required validation scenarios
- render a repo from a normal slug such as `sample-app`
- render a repo from a slug that exercises derivation, such as `99-fast-api`
- in each rendered repo, run:
  - `make install`
  - `make test`
  - `make lint`
  - `make type`
  - `make secret-scan`

### Expected checks
- package imports resolve from the rendered `src/<package_name>` path
- console script and `python -m` entrypoint use the rendered package name
- tests do not rely on source-tree path hacks
- the generated README and project metadata no longer mention `template`

---

## Implementation order
1. Add Copier configuration and package-name derivation.
2. Convert package paths, imports, and metadata to templated values.
3. Template the user-facing docs and CLI labels that currently hard-code the concrete repo identity.
4. Validate generated repos with at least two slugs, including one edge-case slug.
5. Refine any remaining repo-specific docs only where incorrect carry-over remains.

---

## Assumptions
- `python-repo-template` is the long-term template source rather than a staging repo for a different template repository.
- v1 should optimize for a clean, reliable base Python starter template rather than breadth of scaffolding options.
- Existing `Makefile` commands, `uv` usage, `src/` layout, and secret-scan behavior are part of the intended generated-repo contract.
- CI and pre-commit standardization are optional follow-up work, not blockers for the initial templating conversion.
