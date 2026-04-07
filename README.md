# link-tracer

`link-tracer` is a Python package for tracing links in Obsidian notes back to source files in a vault. It targets two output modes:

- CLI output as JSON
- Python API output as a dictionary

## Development setup

```bash
uv sync --all-extras
```

## Quality checks

```bash
uv run ruff format src tests
uv run ruff check src tests
uv run mypy src
uv run pytest
```

## CLI

Use subcommands for single-note and vault-wide tracing:

```bash
uv run link-tracer note path/to/note.md --vault-root path/to/vault --depth 2
uv run link-tracer vault --vault-root path/to/vault
```

## Project layout

```text
.
├── pyproject.toml
├── src/
│   └── link_tracer/
│       ├── __init__.py
│       ├── api.py
│       ├── cli.py
│       └── models.py
├── tests/
│   ├── conftest.py
│   ├── fixtures.py
│   ├── test_api.py
│   ├── test_cli.py
│   └── test_integration.py
└── docs/
    └── index.md
```

## License

MIT. See `LICENSE`.
