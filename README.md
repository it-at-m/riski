# RISKI-Extraktor

Extraktionsskript, um die RIS-Daten aus dem Frontend zu scrapen und standardisiert als CSV zu speichern.

## Prerequisites

- uv ist installiert: https://docs.astral.sh/uv/getting-started/installation/#standalone-installer

## Commands

### Pre-Commit Hooks

```bash
# Pre-commit initalisieren
uv run pre-commit install

# Pre-commit manuell ausführen
uv run pre-commit run

# Pre-commit Hooks updaten
uv run pre-commit autoupdate
```

### Package Management

```bash
# Environment syncen
uv sync

# Package adden
uv add <package>

# Package entfernen
uv remove <package>

# Dev Package adden (remove gleich wie normal)
uv add --dev <package>

# Packages updaten
uv lock -U

# Manuell requirements.txt generieren
rm requirements.txt
uv pip compile --universal pyproject.toml -o requirements.txt
```

### Linting & Formatting

```bash
# Linter manuell ausführen inkl. autofix
uv run ruff check --fix

# Formatter manuell ausführen
uv run ruff format
```

### Applikation ausführen

```bash
# Applikation starten
uv run app.py -d
```
