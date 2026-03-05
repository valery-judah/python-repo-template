# Contributing

## Development setup
```bash
make sync
make install
```

## Quality checks
```bash
make fmt
make lint
make type
make test
```

## Adding dependencies
- Runtime: `uv add <package>`
- Dev: `uv add --dev <package>`

## Pull requests
- Keep changes small and focused.
- Add/update tests for behavior changes.
- Ensure `make check` passes.

