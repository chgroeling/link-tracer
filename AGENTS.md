# AGENTS.md

## Project description

A command-line and Python library tool that scans an Obsidian vault, resolves all wikilinks and Markdown links to real files, and builds a structured representation of the vault’s notes and their relationships. It provides JSON and Python dataclass outputs for a raw vault index, per-note link graphs (with configurable depth, forward links, and backlinks), and a complete vault-wide graph.

## Project Structure
```text
project/
├── .python-version, pyproject.toml        # Runtime & packaging config
├── README.md, LICENSE, AGENTS.md          # Project docs
├── src/vault_net/                        # Source code
│   ├── __init__.py                        # Public surface: exports VaultGraph, VaultIndex, build_note_graph, build_vault_graph, scan_vault
│   ├── __main__.py                        # Module runner: python -m vault_net
│   ├── cli.py                             # Click CLI: note-graph, vault-graph, edges subcommands
│   ├── consts.py                          # Shared constants (_FILE_LINKS_KEY, _POSSIBLE_EXTENSIONS)
│   ├── logging.py                         # structlog + rich console configuration
│   ├── models.py                          # Frozen dataclasses: VaultIndex, VaultGraph, VaultLayered, LinkEdge, etc.
│   ├── note_graph.py                      # build_note_graph(): BFS-scoped subgraph for a single note
│   ├── scan.py                            # scan_vault(): matterify integration, VaultIndex builder
│   ├── transforms.py                      # to_layered() and build_vault_edge_list() output transforms
│   ├── utils.py                           # Link extraction helpers (_extract_file_links, _normalize_lookup_key, _path_for_response)
│   ├── vault_digraph.py                   # build_vault_digraph(): resolved slug digraph builder
│   ├── vault_graph.py                     # build_vault_graph(): full vault link resolution
│   └── vault_registry.py                  # VaultRegistry: slug/path bidirectional lookup
├── tests/                                  # Pytest suite
│   ├── __init__.py
│   ├── conftest.py                        # Autouse fixtures: env isolation, structlog suppression
│   ├── fixtures.py                        # Sample vaults, fake matterify dataclasses
│   ├── test_cli.py                        # CLI end-to-end tests (note-graph, vault-graph, edges)
│   ├── test_integration.py                # obsilink integration smoke test
│   ├── test_note_graph.py                 # build_note_graph unit tests (depth, backlinks, circular)
│   ├── test_scan.py                       # scan_vault delegation test
│   ├── test_transforms.py                 # to_layered BFS transform tests
│   ├── test_vault_digraph.py              # digraph and edge-list transform tests
│   └── test_vault_graph.py                # build_vault_graph resolution tests
└── docs/                                   # MkDocs source
```

## Coding Standards
- Use modern Python syntax for the configured interpreter version.
- Prefer `pathlib` over `os.path`.
- Keep modules cohesive and functions small.
- Add docstrings to public APIs.


## Development Workflows

### UV Environment & Dependencies
- **Lock:** `uv lock`
- **Sync:** `uv sync` (add `--all-extras` for dev/docs).
- **Update:** `uv lock --upgrade`.
- **Management:** `uv add <pkg>` (use `--dev` for dev); `uv remove <pkg>`; `uv pip list`.

### Execution & Lifecycle
- **Run:** `uv run python -m vault_net` or `uv run vault-net`.
- **Dist:** `uv build` (wheel/sdist).
- **Publish:** `uv publish` (or GitHub workflow-based trusted publishing).

### Standards & Git
- **Versioning:** SemVer (`MAJOR.MINOR.PATCH`).
- **Commits:** Conventional Commits (`feat:`, `fix:`, `chore:`, etc.).
- **Automation:** Never commit autonomously unless explicitly requested.

## Testing & QA

### Quality Checks
Prefix commands with `uv run`.
- **Format/Lint:** `ruff format src tests`, `ruff check src tests`
- **Types:** `mypy src`
- **Tests:** `pytest`
- **Pre-commit gate:**
  `uv run ruff format src tests && uv run ruff check src tests && uv run mypy src && uv run pytest`

### Test Guidelines
- Use public APIs in tests.
- Keep imports at the top of test files.
- Use `tmp_path` for filesystem tests.
- Add at least one focused test per non-trivial function.

## Tech Stack Defaults
- **Runtime:** Python 3.12+
- **Package management:** `uv`
- **Build backend:** `hatchling`
- **Formatting/Linting:** `ruff`
- **Type checking:** `mypy` (strict for `src/`)
- **Testing:** `pytest`
- **Docs:** `mkdocs` + Material theme

## Command line interface

**Subcommand `note-graph`:** Trace links for a single note.
- `NOTE` (positional): Path to the note file (must exist)
- `--vault-root`: Vault root directory (overrides `VAULT_ROOT` env var)
- `-d/--depth` (int, default=1): Traversal depth (0=source only, 1=direct links, 2+=recursive)
- `-o/--output`: Write JSON output to file instead of stdout
- `--format` (choice: `edges`|`layered`, default=`edges`): Graph representation
- `-e/--exclude-dir` (repeatable): Additional directory names to exclude from traversal
- `--no-default-excludes`: Disable built-in default exclusions
- `--debug`: Enable debug-level structured logging to stderr
- `--verbose`: Enable verbose console output via rich

**Subcommand `vault-graph`:** Trace links for every note in the vault.
- `--vault-root`: Vault root directory (overrides `VAULT_ROOT` env var)
- `-o/--output`: Write JSON output to file instead of stdout
- `-e/--exclude-dir` (repeatable): Additional directory names to exclude
- `--no-default-excludes`: Disable built-in default exclusions
- `--debug`, `--verbose`: Same as `note-graph`

**Subcommand `edges`:** Trace links for the whole vault as a slug edge list.
- `--vault-root`: Vault root directory (overrides `VAULT_ROOT` env var)
- `-o/--output`: Write JSON output to file instead of stdout
- `-e/--exclude-dir` (repeatable): Additional directory names to exclude
- `--no-default-excludes`: Disable built-in default exclusions
- `--debug`, `--verbose`: Same as `note-graph`
- **Output**: JSON flat list of `VaultFile` pairs (e.g. `[[{...}, {...}], ...]`). entries are lightweight (identity only).
- **Filtering**: Unresolved links are omitted; duplicate edges are merged; self-loops are skipped with a warning.

**Vault root resolution:** CLI `--vault-root` > `VAULT_ROOT` env var. Raises `UsageError` if neither is set or path doesn't exist.

**Helper functions:**
- `resolve_vault_root(cli_value: Path | None) -> Path` — Resolve vault root with precedence above
- `emit_json_output(payload: str, output: Path | None) -> None` — Write to stdout or file

**Output:** JSON is always pretty-printed with 2-space indentation.

**Supported link formats:**
- Wikilinks: `[[Note]]`, `[[Note|Alias]]`, `[[Page#Heading]]`, `[[Note^block]]`, `[[Page#Heading^block]]`, `![[Embed]]`
- Markdown links: `[Text](url)`, `![Image](path)`
- Plain URLs: `https://`, `http://`, `ftp://`, `file://`, `mailto:`

## Docstring Rules
- **Format:** Google Style (`Args:`, `Returns:`, `Raises:`).
- **Markup:** Markdown ONLY; NO reST/Sphinx directives (`:class:`, etc.).
- **Code/Links:** Backticks (single inline, triple block). MkDocs autorefs (`[MyClass][]`).
- **Types:** Rely on Python type hints; do not duplicate in docstrings.
- **Style:** PEP 257 imperative mood ("Return X", not "Returns X").
- **Length:** One-liners for simple/private. Multi-line/sections ONLY for complex/public APIs. Omit redundant `Args:`/`Returns:`.
- **Staleness:** Always update docstrings, inline comments, and class `Supported modes:` when implementing scaffolds. Treat stale "not yet implemented" text as a bug.

## Architecture & Mechanisms

### Pipeline Overview
The processing pipeline is: **scan → vault graph/edge list → note graph → transform → output**.
1. `scan_vault()` scans the vault directory via matterify with a callback that pre-extracts file links per note, returning a `VaultIndex` containing `VaultNote` entries.
2. `build_vault_graph()` or `build_vault_edge_list()` resolves extracted links across the entire vault.
3. `build_note_graph()` (optional) scopes the vault graph to a BFS neighborhood around a single note.
4. `to_layered()` (optional) reshapes the edge graph into a flat BFS depth-layer list.
5. CLI serializes the result as JSON.

### Scanning (`scan.py`)
`scan_vault()` calls `matterify.scan_directory()` with `compute_hash=True`, `compute_stats=True`, `compute_frontmatter=True`, and a `callback` that extracts file links via `obsilink`. The `ScanResults` are converted to a `VaultIndex` with `VaultNote` entries (each carrying pre-extracted `VaultLink` lists). Supports configurable directory exclusions via `extra_exclude_dir` and `no_default_excludes`.

### Vault Graph (`vault_graph.py`)
`build_vault_graph()` builds lookup maps (`name_to_file`, `stem_to_file`, `relative_path_to_file`) from the vault index, then resolves all extracted links to `LinkEdge` objects. Link resolution tries: relative path → direct name → name + extension candidates → stem match. Returns a `VaultGraph` with edges keyed by source note paths.

### Digraph (`vault_digraph.py`)
`build_vault_digraph()` resolves note links into a directed slug graph with unresolved links omitted and self-loops filtered with a warning.

### Edge List Transform (`transforms.py`)
`build_vault_edge_list()` converts the resolved slug digraph to a deduplicated list of lightweight `VaultFile` pairs using a `VaultRegistry`.

### Vault Registry (`vault_registry.py`)
`VaultRegistry` provides bidirectional lookup between slugs and `VaultNote` entries. It is instantiated from a `VaultIndex` and passed to functions that require note resolution, ensuring consistent slug-to-file mapping across the pipeline.

### Note Graph (`note_graph.py`)
`build_note_graph()` performs BFS from a source note through the vault graph, collecting forward edges and backlinks up to the specified depth. `depth=0` returns only the source; `depth=1` returns direct links and backlinks; higher depths traverse recursively. Circular links are handled safely via visited-set tracking.

### Transforms (`transforms.py`)
`to_layered()` reshapes a `VaultGraph` into a `VaultLayered` — a flat BFS depth-layer list where each note appears once at its shallowest reachable depth. Traverses both forward edges and backlinks. Unresolved edges are excluded.

### Link Extraction (`utils.py`)
`_extract_file_links()` uses `obsilink.extract_links()` to parse note content, filtering to `link.is_file` targets only. Each link is converted to a `VaultLink` dataclass for serialization.

### Models (`models.py`)
All models are frozen dataclasses with `slots=True`:
- `VaultIndex` — Scanned vault: `vault_root`, `metadata` (VaultIndexMetadata), `files` (list[VaultNote])
- `VaultFile` — Identity only: `slug`, `file_path`
- `VaultNote` — Rich entry: `VaultFile` + `status`, `error`, `file_hash`, `frontmatter`, `stats`, `links`
- `VaultLink` — Serialized link: type, target, alias, heading, blockid
- `VaultGraph` — Edge dict: `edges[source_note]` → list[LinkEdge]
- `LinkEdge` — Directed edge: link, resolved flag, target_note, unresolved_reason
- `VaultLayered` — BFS depth layers: source_note, metadata, list[LayerEntry]
- `LayerEntry` — Single note at a BFS depth
