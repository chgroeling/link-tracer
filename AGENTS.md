# AGENTS.md

## Project Description

`vault-net` is a CLI and Python library that scans an Obsidian vault, resolves internal links to files in the vault,
and exposes index and graph representations through both programmatic APIs and CLI output formats.

## Layered Architecture

This project uses a clean, layered architecture with strict dependency direction:

```text
Outer layers can depend on inner layers.
Inner layers must never depend on outer layers.

interface -> application -> domain
infrastructure -> domain
```

### Dependency Rule (non-negotiable)

- Domain must not import from application, interface, or infrastructure.
- Application must not import from interface or infrastructure implementations.
- Infrastructure may implement domain protocols and use third-party libraries.
- Interface (CLI) composes concrete adapters and invokes application use cases.

## Source Layout

```text
.
├── AGENTS.md
├── README.md
├── pyproject.toml
├── src/
│   └── vault_net/
│       ├── __init__.py
│       ├── __main__.py
│       ├── consts.py
│       ├── logging.py
│       ├── application/
│       │   ├── __init__.py
│       │   ├── api.py
│       │   └── use_cases/
│       │       ├── __init__.py
│       │       ├── build_full_graph.py
│       │       ├── build_neighborhood_graph.py
│       │       ├── scan_vault.py
│       │       └── trace_note_links.py
│       ├── domain/
│       │   ├── __init__.py
│       │   ├── models.py
│       │   ├── protocols.py
│       │   └── services/
│       │       ├── __init__.py
│       │       ├── resolve_note_input.py
│       │       ├── slug_service.py
│       │       └── vault_registry.py
│       ├── infrastructure/
│       │   ├── __init__.py
│       │   ├── graph/
│       │   │   ├── __init__.py
│       │   │   ├── networkx_graph_builder.py
│       │   │   └── networkx_vault_digraph.py
│       │   └── scanner/
│       │       ├── __init__.py
│       │       └── matterify_scanner.py
│       └── interface/
│           ├── __init__.py
│           ├── cli/
│           │   ├── __init__.py
│           │   └── main.py
│           └── formatters/
│               ├── __init__.py
│               └── views.py
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── fixtures.py
    ├── domain/
    │   └── services/
    │       ├── test_registry.py
    │       ├── test_resolve_note_input.py
    │       └── test_slug.py
    ├── infrastructure/
    │   ├── graph/
    │   │   └── test_networkx_graph_builder.py
    │   └── scanner/
    │       └── test_matterify_scanner.py
    ├── integration/
    │   └── obsilink/
    │       └── test_extraction.py
    ├── interface/
    │   ├── formatters/
    │   │   └── test_views.py
    │   └── test_cli.py
    └── application/
        └── use_cases/
            ├── __init__.py
            └── test_trace_note_links.py
```

## Development Workflows

### UV Environment & Dependencies

- **Run** `uv run <program_name>`
- **Sync:** `uv sync` (add `--all-extras` for dev/docs).
- **Update:** `uv lock --upgrade`.
- **Management:** `uv add <pkg>` (use `--dev` for dev); `uv remove <pkg>`; `uv pip list`.
- **Strategy:** Use min constraints (e.g., `click>=8.1.0`) in `pyproject.toml`; rely on `uv.lock` for reproducibility. Avoid manual lock edits.

### Execution & Lifecycle

- **Run:** `uv run [matterify|python script.py|tool] [args]`.
- **Project:** `uv init` (setup); `uv check` (compat-check).
- **Dist:** `uv build` (wheel/sdist); `uv publish` (upload).

### Standards & 

- **Commits:** Follow Conventional Commits (e.g., `feat:`, `fix:`, `chore:`).
- **Automation:** **Never** commit autonomously; only execute on explicit user request.

## Testing & QA

### Coding Standards

- **Typing:** Strict `mypy` for `src/`; relaxed for `tests/`.
- **Type Aliases:** Use PEP 695 `type X = ...` (Python 3.12+). **Avoid** `TypeAlias` (ruff `UP040`).
- **Format:** PEP8 via `ruff`; 100 char limit.
- **Testing:** ≥1 unit test/function; use `tmp_path` for FS.
- **UI/Logging:** CLI silent by default. Use `structlog` for internal debug logs and `rich` for verbose user feedback. **Strictly isolate** UI output from internal loggers.

### Docstring Rules

- **Format:** Google Style (`Args:`, `Returns:`, `Raises:`).
- **Markup:** Markdown ONLY; NO reST/Sphinx directives (`:class:`, etc.).
- **Code/Links:** Backticks (single inline, triple block). MkDocs autorefs (`[MyClass][]`).
- **Types:** Rely on Python type hints; do not duplicate in docstrings.
- **Style:** PEP 257 imperative mood ("Return X", not "Returns X").
- **Length:** One-liners for simple/private. Multi-line/sections ONLY for complex/public APIs. Omit redundant `Args:`/`Returns:`.
- **Staleness:** Always update docstrings, inline comments, and class `Supported modes:` when implementing scaffolds. Treat stale "not yet implemented" text as a bug.


### Testing Strategy

- Unit tests focus on one layer at a time.
- Application tests should use fakes/mocks for domain ports.
- Infrastructure tests validate adapter behavior against real third-party integrations.
- CLI tests verify command behavior and output formatting.

### Quality Checks

**Tools:** `ruff` (lint/fmt), `mypy` (types). Prefix cmds with `uv run`.
- **Fmt/Lint:** `ruff format [--check] src/ tests/`, `ruff check src/ tests/`
- **Types:** `mypy src/`
- **Pre-Commit Gate:** `uv run ruff format src/ tests/ && uv run ruff check src/ tests/ && uv run mypy src/ && uv run pytest`

### Tests (`uv run pytest`)

- **Exec:** `.` (all), `-v` (verbose), `tests/[file].py[::func]` (targeted), `--cov=matterify --cov-report=html` (coverage).
- **Structure:** `tests/` dir 1:1 mapping (`extractor.py`->`test_extractor.py`, `utils/__init__.py`->`test_utils.py`, `cli.py`->`test_cli.py`).
- **FS Rules:** Prioritize critical paths. Use `tmp_path`. Name staging dirs `project/` (avoids `src/src/` nesting).
- **Paths:** Stored paths include top-level prefix (`project/src/main.py`). Assert via `endswith()` or `rglob()`.
- **Public API only:** Never import or call private symbols (names starting with `_`) from `src/` in tests. Test behaviour exclusively through the public API.
- **No inline imports:** All imports must be at the top of the test file. `import` statements inside test functions are forbidden.

## Layer Responsibilities

### Domain

- Contains pure entities and business rules.
- Handles note identity resolution (slug vs path) via domain services.
- No library-specific behavior should leak into domain entities.
- Protocols define required behavior (`VaultScanner`, `GraphBuilder`) without binding to concrete tools.

### Application

- Contains orchestration logic as use cases.
- Receives dependencies via constructor injection.
- Coordinates domain services and ports, but does not parse CLI or call third-party libraries directly.

### Infrastructure

- Implements domain protocols using third-party dependencies (`matterify`, `obsilink`, `networkx`).
- Converts external objects into domain models.

### Interface

- Handles user interaction and output formatting.
- Instantiates concrete infrastructure adapters and calls application use cases.
- Should be thin: validate input, invoke use case, render output.

## Naming Conventions

- Prefer domain terms in domain/application function names (for example: `full_graph`, `neighborhood_graph`, `index`).
- Avoid infrastructure or library terms in domain/application names (for example: `networkx`, `digraph`, `ego`).
- Keep infrastructure-specific names only in infrastructure adapters (for example: `NetworkXGraphBuilder`).
- Use use-case class names in `VerbNounUseCase` form (for example: `BuildFullGraphUseCase`).
- Keep use-case module names aligned with class names and responsibility (for example: `build_full_graph.py`).
- Name service modules after their service role (for example: `vault_registry.py`, `slug_service.py`).

