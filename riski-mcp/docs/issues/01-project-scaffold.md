# Project scaffold & tooling

**Labels:** `mcp`, `chore`
**Depends on:** —

## Goal

Create the `riski-mcp/` module with the project layout, dependency management, and
lint/test tooling consistent with the rest of the repo (`uv`, `ruff`, `pytest`,
`ty`, `pre-commit`), so later issues have a place to land code.

## Tasks

- [ ] Create `riski-mcp/` with:
  - `app.py` — Gradio entrypoint (placeholder; real content in #06).
  - `src/riski_mcp/__init__.py`
  - `src/riski_mcp/config.py` (placeholder for #05)
  - `src/riski_mcp/agui_client.py` (placeholder for #03)
  - `src/riski_mcp/tools.py` (placeholder for #04)
  - `test/`
- [ ] `pyproject.toml` mirroring `riski-backend` conventions: `requires-python`,
      `uv` config, `add-bounds = "exact"`, dev group (`ruff`, `pytest`,
      `pytest-asyncio`, `pytest-cov`, `pre-commit`, `ty`). Runtime deps:
      `gradio[mcp]`, `httpx`, `pydantic`, `pydantic-settings`, `python-dotenv`,
      `truststore` (the backend uses truststore for corporate SSL — keep parity).
- [x] `requirements.txt` for the HF Space (HF Spaces build from `requirements.txt`,
      not the uv lockfile). **Auto-generated** from `uv.lock` via
      `uv export --no-dev --no-emit-project --no-hashes -o requirements.txt`, kept
      in sync by a pre-commit hook (`uv-export-riski-mcp-requirements`) — never
      hand-edited. This removes the drift risk entirely (was a concern in #11).
- [ ] `.env.example` for local dev (see #05 for keys).
- [ ] `Readme.md` stub (HF Space README front-matter handled in #08).
- [ ] Wire into existing repo tooling (root pre-commit, ruff config) if shared.

## Acceptance criteria

- [ ] `uv sync` succeeds in `riski-mcp/`.
- [ ] `uv run ruff check` and `uv run pytest` run (no tests yet is fine).
- [ ] Module imports cleanly: `python -c "import riski_mcp"`.

## Notes

- Decide the package name (`riski_mcp`) and Space slug early — the slug determines
  the tool namespace prefix the robot sees (slashes/dots/hyphens → underscores).
- HF Spaces install from `requirements.txt`; the `uv`/lockfile setup is for local
  dev and CI only. Both must list the same runtime deps.