# Document Pipeline — quick start

This service reads file blobs from the database, runs OCR, and stores extracted markdown back into the same DB. Below are the minimum steps to get a local database and seed data ready using the existing extractor.

## Prerequisites

- Docker or Podman (the repo uses `compose.yaml` at the repo root)
- Python toolchain used in this repo (`uv` suggested) and a populated `.env` in the repo root (see `.env.example`)

## 1) Start the database via Compose

From the repository root, start Postgres (and Adminer if you want a UI). Replace `podman` with `docker` if needed.

```powershell
podman compose up -d db adminer
```

Defaults (per `compose.yaml`): user `postgres`, password `password`, database `example_db`, exposed on `5432`.

## 2) Seed data with the extractor

The document pipeline expects data already ingested by the extractor. Run it once to populate the DB.

```powershell
cd riski-extractor
uv run python app.py
```

This will initialize the DB schema and insert entities/files, honoring your `.env` (e.g., date range, base URL). After it completes, the document pipeline can read and process documents from the same database.

## (Optional) Run the document pipeline

```powershell
cd riski-document-pipeline
uv run python main.py
```

Configure OCR-related env vars in `.env` (e.g., `RISKI_DOCUMENTS__MAX_DOCUMENTS_TO_PROCESS`, `RISKI_DOCUMENTS__OCR_MODEL_NAME`, OpenAI credentials) before running.
