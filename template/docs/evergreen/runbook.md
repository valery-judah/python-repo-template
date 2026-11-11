# Runbook

Commands and operational procedures for this project. First-time setup is in the [README](../../README.md).

## Command model

- `uv` manages environments and dependencies.
- `task <namespace>:<name>` runs developer workflows and setup commands.
- Bare `task` and `task help` list the available workflows.
- Composite tasks run sequentially and stop on failure.

Pass command arguments after `--`, preserving shell quotes:

```bash
task quality:test -- -k "smoke or cli"
```

## Task namespaces

| Namespace | Workflows |
| --- | --- |
| `repo:*` | Dependency sync, environment setup, Git hooks, and cleanup |
| `quality:*` | Formatting, linting, types, tests, verification, and full checks |
| `security:*` | Repository and staged secret scans |
| `app:*` | Run and build the generated application |

## Common commands

```bash
task quality:fmt
task quality:fmt:check
task quality:lint
task quality:type
task quality:test
task quality:verify
task app:run
task app:build
task repo:clean
task repo:hooks
```

`task quality:check` runs `task quality:verify`.

## Dependencies

- Add a runtime dependency: `uv add <package>`
- Add a dev dependency: `uv add --dev <package>`
- Sync lockfile + env: `uv sync --group dev`

## Secret scanning

This repo includes a local Gemini API key scan for strings that match the format-aware
`AIza[A-Za-z0-9_-]{35}` pattern. Version 1 scans only Gemini-style keys, has no allowlist, and
keeps CI `gitleaks` checks as separate defense in depth.

Run a repo-wide audit of tracked files:

```bash
task security:scan
```

Install the repo-managed pre-commit hook:

```bash
task repo:hooks
```

After installation, each commit scans staged added lines only. It does not scan unchanged old
lines, full git history, or non-staged working tree changes.

## Shared agent docs

On macOS or Linux, clone the shared Markdown repository into your home directory once:

```bash
git clone https://github.com/valery-judah/agent-docs.git ~/agent-docs
```

If `~/agent-docs` already exists, use the existing clone instead.
`task repo:init` creates an `agent-docs` symlink to that directory when it exists.
The link stays out of Git, and existing project entries are preserved.
This shares the files across projects without installing them as skills.

If you clone it after initializing this project, run this from the project directory:

```bash
task repo:agent-docs
```

You can also keep the clone elsewhere. For example:

```bash
git clone https://github.com/valery-judah/agent-docs.git ~/projects/agent-docs
```

Choose an existing parent directory. Then, from this project directory, create the link using the clone's path, provided no `agent-docs` entry exists:

```bash
ln -s ~/projects/agent-docs agent-docs
```

Later initialization preserves this link.

## Operations

Add deployment, troubleshooting, and other operational procedures here as the project needs them.
