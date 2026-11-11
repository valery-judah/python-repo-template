# Runbook

Procedures for using and maintaining this template. The quick start is in the [README](../README.md).

## Prerequisites

Python 3.11+, [uv](https://docs.astral.sh/uv/getting-started/installation/), and [Go Task v3](https://taskfile.dev/docs/installation) must be available on PATH.
Install Task with `brew install go-task` on macOS or `winget install Task.Task` on Windows; see the linked instructions for Linux.

## Customization

```bash
uvx copier copy --trust -l --vcs-ref HEAD gh:valery-judah/python-repo-template convert-pdf
```

- The destination folder supplies the project slug. Pass `-d repo_slug=another-name` to override it.
- Pass `-d description="One sentence about the project."` to set the description used in `AGENTS.md`, the README, and `pyproject.toml`. The default is a TODO placeholder.
- `-l` accepts defaults; omit it to answer prompts. See [copier.yml](../copier.yml) for all inputs and defaults.
- `--trust` allows Copier to run template tasks, including Git initialization.
- `--vcs-ref HEAD` uses the current GitHub branch tip. Omit it to use the latest release.
- For local development, replace the GitHub source with the path to your clone and keep `--vcs-ref HEAD` to include uncommitted edits.

## Creating projects from a local clone

On macOS or Linux, run `task repo:register` once in this clone. Then create a project from any directory:

```bash
newrepo ~/projects/convert-pdf
```

`newrepo` uses this clone, including uncommitted edits, and runs `task repo:init`.
The destination must not already exist. Keep the clone in place: the command links to [its launcher](../scripts/devex/newrepo).

## Shared agent docs

On macOS or Linux, clone the shared Markdown repository into your home directory once, before initializing a project:

```bash
git clone https://github.com/valery-judah/agent-docs.git ~/agent-docs
```

In generated projects, `task repo:init` links it as `agent-docs`, kept out of Git.
To link it later or keep the clone elsewhere, see [Shared agent docs](../template/docs/evergreen/runbook.md#shared-agent-docs) in the generated runbook.

## Maintaining the template

Edit [template/](../template/) to change generated projects. The [root Taskfile](../Taskfile.yml) defines template maintenance workflows; the [generated Taskfile](../template/Taskfile.yml.jinja) defines project workflows.

Set up and validate the template repository:

```bash
task repo:install
task quality:check
```

Run `task` to list all workflows. Pass arguments after `--`, for example:

```bash
task quality:test -- -k "smoke or cli"
```

## Releasing

Run `task quality:check` on the commit you want to tag, then inspect existing tags:

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
