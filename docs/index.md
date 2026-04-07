# link-tracer

`link-tracer` is a Python project intended to trace links found in Obsidian markdown notes
back to note files on disk.

## Scope

The project supports:

- package import and version metadata
- CLI subcommands for note-level and vault-level tracing
- typed data models for trace results
- API helpers to scan a vault and resolve links

## Output contract

Tracing outputs a structured graph containing:

- visited note nodes
- link edges between notes
- unresolved or invalid link errors
- traversal options and summary counts

## Development

```bash
uv sync --all-extras
uv run pytest
```
