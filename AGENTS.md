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
## Import Rules

- Allowed:
  - `vault_net.interface.*` -> `vault_net.application.*`, `vault_net.domain.*`
  - `vault_net.infrastructure.*` -> `vault_net.domain.*`
  - `vault_net.application.*` -> `vault_net.domain.*`
- Forbidden:
  - `vault_net.domain.*` -> anything outside `vault_net.domain.*`
  - `vault_net.application.*` -> `vault_net.infrastructure.*` (except in `application/api.py`, which is the package facade)

## Naming Conventions

- Prefer domain terms in domain/application function names (for example: `full_graph`, `neighborhood_graph`, `index`).
- Avoid infrastructure or library terms in domain/application names (for example: `networkx`, `digraph`, `ego`).
- Keep infrastructure-specific names only in infrastructure adapters (for example: `NetworkXGraphBuilder`).
- Use use-case class names in `VerbNounUseCase` form (for example: `BuildFullGraphUseCase`).
- Keep use-case module names aligned with class names and responsibility (for example: `build_full_graph.py`).
- Name service modules after their service role (for example: `vault_registry.py`, `slug_service.py`).

## Testing Strategy

- Unit tests focus on one layer at a time.
- Application tests should use fakes/mocks for domain ports.
- Infrastructure tests validate adapter behavior against real third-party integrations.
- CLI tests verify command behavior and output formatting.

### Test Layout

```text
tests/
├── domain/
│   └── services/
├── infrastructure/
│   ├── graph/
│   └── scanner/
├── integration/
│   └── obsilink/
└── interface/
```

## Layer Responsibilities

### Domain

- Contains pure entities and business rules.
- No library-specific behavior should leak into domain entities.
- Protocols define required behavior (`VaultScanner`, `GraphBuilder`) without binding to concrete tools.

### Application

- Contains orchestration logic as use cases.
- Receives dependencies via constructor injection.
- Coordinates domain services and ports, but does not parse CLI or call third-party libraries directly.
- `application/api.py` serves as the package facade that wires default infrastructure adapters to use cases.

### Infrastructure

- Implements domain protocols using third-party dependencies (`matterify`, `obsilink`, `networkx`).
- Converts external objects into domain models.
- May use third-party libraries but must not leak their types into domain models.

### Interface

- Handles user interaction and output formatting.
- Instantiates concrete infrastructure adapters and calls application use cases.
- Should be thin: validate input, invoke use case, render output.

## Rules

- Use skill `python-code-style` and `python-design-patterns` before adding/modifying python code.
- Use skill `python-testing-patterns` before adding/modifying pytest suites.
- Keep code ASCII by default.
- Prefer explicit, simple composition over meta-framework abstractions.
- Do not introduce layer-crossing imports for convenience.

## Design Patterns

### Note Identity Resolution

- Concerns the conversion of user input (slug, relative path, or absolute path) into a canonical slug.
- Implemented in the Domain layer (`VaultRegistry.resolve_to_slug`).
- Resolution order:
    1. Direct slug match.
    2. Vault-relative path match.
    3. Resolved absolute path (converted to vault-relative).
- Uses `.resolve()` on paths to handle shortest canonical representations.
- Log resolution attempts at `debug` level for traceability.
- Always perform resolution after vault scanning to avoid redundant I/O.

## Workflows

- Dependency management: `uv lock`, `uv sync --all-extras`, `uv add`, `uv remove`.
- Run CLI locally: `uv run python -m vault_net --help`.
- Packaging: `uv build`.

## Quality Gate

Run before completing a change:

`uv run ruff format src tests && uv run ruff check --fix src tests && uv run mypy src tests && uv run pytest`
