# Contributing

## Development setup
```bash
make init
```

## Quality checks
```bash
uv run poe verify
```

## Adding dependencies
- Runtime: `uv add <package>`
- Dev: `uv add --dev <package>`

## Pull requests
- Keep changes small and focused.
- Add/update tests for behavior changes.
- Ensure `uv run poe verify` passes.
