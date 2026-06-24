# riski-oparl

Publishes the RISKI database as an [OParl 1.1](https://oparl.org) REST API.

The data model in `riski-core` is already OParl-aligned; this service is the
read-only HTTP publishing layer on top of it.

## Design

- **Object ids** are derived from the database primary key (`db_id`) and the
  configured `base_url`, e.g. `…/oparl/v1/papers/<uuid>`. The original RIS source
  URL is published in the OParl `web` field.
- **Read-only:** only `GET` endpoints; the service never writes to the DB.
- **Shared DB config:** uses the same `RISKI__DB__*` environment variables as the
  rest of the stack (see `riski-core/src/core/settings/db.py`).

## Entry point

`GET /oparl/v1/system` — the OParl entry point. From there: `system.body` →
`/oparl/v1/bodies` → per-body external lists (`organizations`, `people`,
`meetings`, `papers`) and individual object endpoints.

## Endpoints

| Path | Description |
|------|-------------|
| `GET /healthz` | Liveness check |
| `GET /oparl/v1/system` | OParl System (entry point) |
| `GET /oparl/v1/bodies` | Paginated list of bodies |
| `GET /oparl/v1/bodies/{id}` | Single body |
| `GET /oparl/v1/bodies/{id}/organizations\|people\|meetings\|papers\|agendaItems\|consultations\|files\|locations\|memberships` | External lists (paginated, time-filterable) — the OParl 1.1 mandatory body lists |
| `GET /oparl/v1/{organizations\|people\|memberships\|meetings\|agendaItems\|papers\|files\|locations\|consultations\|legislativeTerms}/{id}` | Single objects |

External lists support OParl filtering via query params: `created_since`,
`created_until`, `modified_since`, `modified_until`, and `page`.

## Run locally

```bash
cd riski-oparl
uv sync
uv run main.py
# OParl entry point: http://localhost:8082/oparl/v1/system
```

Configuration (env, prefix `RISKI_OPARL__`):

| Variable | Default | Meaning |
|----------|---------|---------|
| `RISKI_OPARL__BASE_URL` | `http://localhost:8082/oparl/v1` | Public base URL; object ids derive from it |
| `RISKI_OPARL__SERVER_PORT` | `8082` | Bind port |
| `RISKI_OPARL__PAGE_SIZE` | `50` | Elements per list page |
| `RISKI_OPARL__CONTACT_EMAIL` / `__CONTACT_NAME` | – | Advertised in System/Body |

## Validate

Run the official [OParl validator](https://validator.oparl.org) against the
running entry point URL to check conformance.
