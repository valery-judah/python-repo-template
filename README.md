# Python Repo Template

```bash
uvx copier copy --trust -l -d repo_slug=convert-pdf --vcs-ref HEAD gh:valery-judah/python-repo-template convert-pdf
cd convert-pdf
task repo:init
task quality:verify
task app:run
```

A Python starter with `uv`, Go Task, tests, and an [agent contract](template/AGENTS.md).
The command above uses the current GitHub branch tip. Omit `--vcs-ref HEAD` to use the latest release once it includes the Task migration.

## Prerequisites

Python 3.11+, [uv](https://docs.astral.sh/uv/getting-started/installation/), and [Go Task v3](https://taskfile.dev/docs/installation) must be available on PATH.
Install Task with `brew install go-task` on macOS or `winget install Task.Task` on Windows; see the linked instructions for Linux.

## Customization

Pass the project slug with `-d repo_slug=another-name`. `-l` accepts the remaining defaults; omit it for prompts.
See [copier.yml](copier.yml) for all inputs and defaults.
`--trust` allows Copier to execute template tasks, including Git initialization.

For local development, replace the GitHub source with the path to your clone and keep `--vcs-ref HEAD` to include uncommitted edits.

## Workflows

Run `task` to list available workflows. Pass arguments after `--`, for example:

```bash
task quality:test -- -k "smoke or cli"
```

The [root Taskfile](Taskfile.yml) defines template maintenance workflows; the [generated Taskfile](template/Taskfile.yml.jinja) defines project workflows.

## Maintaining the template

Edit [template/](template/) to change generated projects. Set up and validate the template repository with:

```bash
task repo:install
task quality:check
```

Before releasing, preview the next tag with `task release:create -- patch --dry-run`.
For release options, run `task release:create -- --help`.
