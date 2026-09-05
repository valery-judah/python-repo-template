# Python Repo Template

```bash
uvx copier copy --trust -l --vcs-ref HEAD gh:valery-judah/python-repo-template convert-pdf
cd convert-pdf
task repo:init
task quality:verify
task app:run
```

A Python starter with `uv`, Go Task, tests, and an [agent contract](template/AGENTS.md).
The command above uses the current GitHub branch tip. Omit `--vcs-ref HEAD` to use the latest release once it includes these changes.

## Prerequisites

Python 3.11+, [uv](https://docs.astral.sh/uv/getting-started/installation/), and [Go Task v3](https://taskfile.dev/docs/installation) must be available on PATH.
Install Task with `brew install go-task` on macOS or `winget install Task.Task` on Windows; see the linked instructions for Linux.

## Customization

The destination folder supplies the project slug. `-l` accepts defaults; omit it for prompts or pass `-d repo_slug=another-name` to override the slug.
See [copier.yml](copier.yml) for all inputs and defaults.
`--trust` allows Copier to execute template tasks, including Git initialization.

For local development, replace the GitHub source with the path to your clone and keep `--vcs-ref HEAD` to include uncommitted edits.

## From a local clone

On macOS or Linux, run `task repo:register` once in this clone. Then create a project from any directory:

```bash
newrepo ~/projects/convert-pdf
```

`newrepo` uses this clone, including uncommitted edits, and runs `task repo:init`.
The destination must not already exist. Keep the clone in place: the command links to [its launcher](scripts/devex/newrepo).

Initialization also links `agent-docs` to `~/agent-docs` when that directory exists, providing a way to share Markdown files across projects without installing them as skills.

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

To release, run `task quality:check` on the commit you want to tag, then inspect existing tags:

```bash
git fetch origin --tags
git tag --list 'v*' --sort=-version:refname
```

Choose the next version and replace `vX.Y.Z` below with it:

```bash
git tag vX.Y.Z
git push origin vX.Y.Z
```

Pushing the tag starts the release validation workflow, which checks the tagged template
locally and from GitHub. Validation runs after publication; a failed check leaves the tag available.
