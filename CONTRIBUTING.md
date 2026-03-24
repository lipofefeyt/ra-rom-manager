# Contributing

## Workflow

1. Pick an issue from the [Issues tab](https://github.com/lipofefeyt/ra-rom-manager/issues)
2. Create a feature branch: `git checkout -b feature/short-description`
3. Make your changes, write tests if applicable
4. Run the checks locally before pushing:
   ```bash
   ruff check .
   pytest
   ```
5. Open a PR targeting `main` and reference the issue (e.g. `Closes #5`)

## Branching

| Branch | Purpose |
|--------|---------|
| `main` | Stable, always passing CI |
| `feature/*` | New features or improvements |
| `fix/*` | Bug fixes |
| `chore/*` | Tooling, config, housekeeping |

## Issues

Issues are tracked via GitHub Issues and sourced from `issues.json` at the repo root. Milestones group issues into logical phases:

- **M1 - Clean Foundation**: repo hygiene, tooling, core refactors
- **M2 - Multi-Console & Caching**: performance, multi-system support
- **M3 - Achievement Tracking**: RA API progress features
- **M4 - Excel Output & Stats**: reporting and export

If you want to add a new issue, add it to `issues.json` first following the existing format, then create it via `gh issue create`.

## Code Style

This project uses [Ruff](https://docs.astral.sh/ruff/) for linting and formatting. Configuration is in `pyproject.toml`. There are no manual formatting rules to remember — just run `ruff check . --fix` and `ruff format .` before committing.

## Environment Setup

```bash
pip install -e '.[dev]'
cp .env.example .env
# Fill in RA_USERNAME, RA_API_KEY, ROM_PATH
```

Or open the repo in GitHub Codespaces — the dev container handles everything automatically.