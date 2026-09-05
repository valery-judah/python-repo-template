# Contributing

## Development setup
Install `uv` and standalone Go Task v3 as described in [README.md](README.md).

```bash
task repo:init
```

## Quality checks
```bash
task quality:verify
```

## Adding dependencies
- Runtime: `uv add <package>`
- Dev: `uv add --dev <package>`

## Pull requests
- Keep changes small and focused.
- Add/update tests for behavior changes.
- Ensure `task quality:verify` passes.
