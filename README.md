# Python Repo Template

A [Copier](https://copier.readthedocs.io/) template for Python projects with `uv`, Go Task, tests, and an [agent contract](template/AGENTS.md.jinja).

## Prerequisites

Python 3.11+, [uv](https://docs.astral.sh/uv/getting-started/installation/), and [Go Task v3](https://taskfile.dev/docs/installation) on PATH.

## Create a project

Replace `convert-pdf` with your repo name.

Create the project:

```bash
uvx copier copy --trust -l --vcs-ref HEAD gh:valery-judah/python-repo-template convert-pdf
```

Set it up and run it:

```bash
cd convert-pdf
task repo:init
task quality:verify
task app:run
```

The generated project's [README](template/README.md.jinja) and [runbook](template/docs/evergreen/runbook.md) cover its workflows.

## Main commands

For working on this template repository:

| Command | Purpose |
| --- | --- |
| `task` | List all workflows |
| `task repo:install` | Set up the development environment |
| `task quality:verify` | Format check, lint, types, and unit tests |
| `task render:test` | Render fixture projects and run their checks |
| `task quality:check` | Run both of the above |
| `task repo:register` | Install the `newrepo` launcher in `~/.local/bin` |

## More

The [runbook](docs/runbook.md) covers:

- [Customizing the copy command](docs/runbook.md#customization)
- [Creating projects from a local clone](docs/runbook.md#creating-projects-from-a-local-clone)
- [Shared agent docs](docs/runbook.md#shared-agent-docs)
- [Maintaining the template](docs/runbook.md#maintaining-the-template)
- [Releasing](docs/runbook.md#releasing)
