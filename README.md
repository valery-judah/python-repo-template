# Python Repo Template

This repository contains two layers:
- the template engine at the repo root
- the generated Python starter payload under `template/`

## Requirements
- Python 3.11+
- `uv`

## Layout
```text
copier.yml
copier_extensions.py
scripts/
template/
  pyproject.toml.jinja
  Makefile.jinja
  src/
  tests/
```

## Engine workflow
```bash
make sync
make test
make render-test
```

## Render the starter template
```bash
uv run copier copy --trust . ./my-new-repo --data repo_slug=my-new-repo --defaults
```

The rendered repository will receive the contents of `template/` at its own root.
