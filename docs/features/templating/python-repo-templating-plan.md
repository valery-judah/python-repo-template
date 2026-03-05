# Python Repo Templating Plan (one-shot scaffolding)

## Goals and constraints
- **One-shot scaffolding**: generate a new repository once; no template update/rebase workflow required.
- **Git hosting**: GitHub, created individually (no org policies assumed).
- **Project type**: Python-based, with a **switchable “kind”** of repo; **default = `service`**.
- **Dependency management**: `uv` with **committed `uv.lock` in every repo**.
- **Build/automation**: `Makefile`, **POSIX-only** targets, `make` calls `uv` directly.
- **Docs/agentic files**: copy a set of Markdown/agentic instruction files verbatim (e.g., `AGENTS.md` and related files).
- **Security checks**: include Python tooling and make targets for **secret scanning** / pre-commit scanning (e.g., `make secret-scan`).

---

## High-level approach
Use a dedicated GitHub repository that contains the template, rendered via **Copier** (template renderer) and invoked via **uvx** (so contributors don’t need a global install).

Why this fits:
- Works with **Git URL sources** (template repo lives on GitHub).
- Supports **templating variables** (repo name/slug/package name).
- Supports conditional file/directory generation for **repo “kinds”**.
- Supports a **non-interactive** mode using flags, with a clean path to **answers files** later.

---

## Developer experience (DX)

### Create a new repo locally (render from GitHub)
Example (non-interactive):
```bash
uvx copier copy --trust gh:<you>/<template-repo> ./<repo_slug> \
  --data repo_slug=<repo_slug> \
  --data repo_name="<Repo Name>" \
  --data project_kind=service \
  --defaults
```

Notes:
- `--defaults` uses default values for any non-specified variables.
- `--trust` allows `copier_extensions.py` (if used) to compute derived values like `package_name`.

### Optional: answers/config file (later, but supported now)
```bash
uvx copier copy --trust gh:<you>/<template-repo> ./<repo_slug> \
  --answers-file ./template-answers.yml \
  --defaults
```

---

## Template repo contents

### Suggested top-level layout
```
python-repo-template/
  copier.yml
  copier_extensions.py              # optional, for derived values (slug → package)
  .gitignore
  .editorconfig
  .python-version
  Makefile
  pyproject.toml.jinja
  uv.lock                           # committed baseline lockfile
  README.md.jinja
  AGENTS.md                         # copied verbatim (no templating suffix)
  agentic/                          # copied verbatim
    ...
  .github/
    workflows/
      ci.yml
  src/
    {{ package_name }}/
      __init__.py
      ...
  tests/
    ...
  service/                          # optional: service skeleton, conditionally included
    app.py
    ...
  library/                          # optional: library skeleton, conditionally included
    ...
  cli/                              # optional: cli skeleton, conditionally included
    ...
```

### File naming rules
- Use `.jinja` suffix for files that require variable substitution (e.g., `pyproject.toml.jinja`, `README.md.jinja`).
- Keep agentic files (e.g., `AGENTS.md`, instruction directories) as plain files so they are copied verbatim.
- Use Jinja templating in file and directory names where needed:
  - `src/{{ package_name }}/...`

---

## Variables and naming conventions (minimal set)

### Required user-provided
- `repo_slug` (kebab-case, e.g., `my-cool-service`)
- `repo_name` (display name; default: same as slug)

### Derived / computed
- `package_name` (snake_case; derived from slug, e.g., `my_cool_service`)

### Optional but recommended defaults
- `project_kind`: one of `service`, `library`, `cli` (**default: `service`**)
- `python_version`: default `3.12` (or whatever you standardize on)

### Derivation rules for `package_name`
Implement in `copier_extensions.py`:
- lower-case
- replace `-` with `_`
- strip characters not in `[a-z0-9_]`
- if it doesn’t start with `[a-z_]`, prefix with `_`

This prevents invalid import/module names from common repo slugs.

---

## Repo “kinds” (service/library/cli)

### Default = service
- Provide a minimal, opinionated skeleton for a typical service.
- Keep library/cli scaffolding available but optional via `project_kind`.

### Conditional file/directory inclusion
Use a simple conditional naming pattern in the template so only relevant folders render.
Typical pattern:
- Put kind-specific files under directories named with a conditional Jinja expression.
- When the expression renders to an empty string, Copier skips the path.

Example conceptually:
- `{{ 'service' if project_kind == 'service' else '' }}/app.py`

(Exact implementation details can be adjusted once you finalize how you want “kinds” to be laid out.)

---

## Dependency management policy (uv + lockfiles)

### Policy
- `uv.lock` is committed for every repo.
- CI should **install using the lockfile** to avoid drift.

### pyproject structure
- Define runtime dependencies in `[project.dependencies]`
- Define dev/test tooling in `[dependency-groups]` (e.g., `dev`, `test`, `lint`), depending on how you prefer to split.

### Typical commands
- Local install:
  - `uv sync --dev`
- CI install:
  - `uv sync --locked --dev`

### Lockfile strategy in template
- Include a baseline `uv.lock` consistent with your default tooling (pytest/ruff/type checker).
- On first use per repo, maintainers can regenerate lock if needed:
  - `uv lock`

(Per your constraint: do **not** auto-run `uv sync` during template generation.)

---

## Makefile design (minimal surface, POSIX)

### Targets (recommended minimum)
- `install`: install deps for development
- `test`: run unit tests
- `lint`: run linter(s)
- `typecheck`: run type checker
- `fmt`: auto-format
- `secret-scan`: run secret scanning hooks/tools
- `precommit`: run pre-commit on the whole repo (optional but useful)

### Example semantics
- `install` → `uv sync --dev`
- `test` → `uv run pytest`
- `lint` → `uv run ruff check .`
- `fmt` → `uv run ruff format .`
- `typecheck` → `uv run mypy .` (or `pyright`)
- `secret-scan` → `uv run pre-commit run --all-files` (with secret-scanning hooks enabled)

---

## Pre-commit and secret scanning

### Recommended baseline
Include a `.pre-commit-config.yaml` with at least:
- basic hygiene hooks (trailing whitespace, end-of-file-fixer)
- Python checks (ruff)
- secret scanning hook(s)

Then:
- `make secret-scan` runs the secret scanning hook(s) across the repo.

You can start lightweight (only one scanner) and evolve later without changing the workflow interface.

---

## GitHub Actions CI (unit + lint/typecheck)

### Workflow goals
- Run on PRs and pushes to default branch.
- Jobs:
  - unit tests
  - lint
  - typecheck

### Recommended structure
- Use `actions/checkout`
- Use `astral-sh/setup-uv` to install uv and enable caching (optional but helpful).
- Use `uv sync --locked --dev`
- Run `make test`, `make lint`, `make typecheck` (this keeps CI aligned with local workflow).

### Python versions
Start with one version (e.g., 3.12). If you later want a version matrix, it is easy to add.

---

## Template rendering and initialization steps

### Local init (after copier renders files)
```bash
cd <repo_slug>
git init
git add -A
git commit -m "Initial commit"
```

### Optional: create GitHub repo and push (manual, explicit)
If you use GitHub CLI:
```bash
gh repo create <repo_slug> --public --source=. --remote=origin --push
```

(Keep this outside of Copier for now to stay within “one-shot scaffolding” and avoid tool coupling.)

---

## What is *not* included (by design)
- No “update template in existing repos” mechanism.
- No automatic post-render `uv sync`.
- No org-specific governance defaults yet (CODEOWNERS rules, branch protections, etc.)—can be added later.

---

## Suggested next steps (implementation order)
1. Create the GitHub template repo with the full file layout and baseline `pyproject.toml.jinja`, `Makefile`, and CI workflow.
2. Add `copier.yml` with minimal variables (`repo_slug`, `repo_name`, `project_kind`, `python_version`).
3. Add `copier_extensions.py` to derive `package_name`.
4. Implement `service` default skeleton, and stub `library`/`cli` skeletons.
5. Validate generation with:
   - a “weird” slug (hyphens, numbers) to confirm package name derivation
   - CI green on first push
6. Write a short `TEMPLATE_USAGE.md` in the template repo showing the canonical `uvx copier copy ...` command.

---

## References
- Copier: https://github.com/copier-org/copier
- uv GitHub Actions integration: https://docs.astral.sh/uv/guides/integration/github/
- uv dependency groups / project deps: https://docs.astral.sh/uv/concepts/projects/dependencies/
