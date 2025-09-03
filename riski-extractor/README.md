# Template Python @ KICC / LHM

Python-Template with relevant technologies.

[[_TOC_]]

## Prerequisites

- uv is installed: https://docs.astral.sh/uv/getting-started/installation/#standalone-installer

## Commands

### Pre-Commit Hooks

```bash
uv sync
# Initialize pre-commit
uv run pre-commit install

# Run pre-commit manually
uv run pre-commit run

# Update pre-commit hooks
uv run pre-commit autoupdate
```

### Package Management

```bash
# Sync environment
uv sync

# Add package
uv add <package>

# Remove package
uv remove <package>

# Add dev package (remove like above)
uv add --dev <package>

# Update packages
uv lock -U

# Manually generate requirements.txt
rm requirements.txt
uv pip compile --universal pyproject.toml -o requirements.txt
```

### Linting & Formatting

```bash
# Run linter manually incl. autofix
uv run ruff check --fix

# Run formatter manually
uv run ruff format
```

### Run application

```bash
# Applikation starten
uv run app.py -d
```

## Container Build

```bash
podman build --build-arg IMAGE_CREATED="$(date -u +%Y-%m-%dT%H:%M:%SZ)" --build-arg IMAGE_REVISION="$(git rev-parse HEAD)"   --build-arg IMAGE_VERSION="$(git describe --tags --always)" -t riski-extractor .
```
