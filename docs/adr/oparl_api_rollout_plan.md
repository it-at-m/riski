# 05: OParl 1.1 API Implementation Plan

| Status   | proposed       |
| -------- | -------------- |
| Author   | mj/copilot     |
| Drafted  | 2026-05-28     |
| Timeline | phased rollout |

This document defines a practical implementation backlog for an OParl-compatible API in `riski-backend`.
It focuses on spec compliance, low rollout risk, and testable milestones.

## Goals

- Provide an OParl 1.1 compatible read-only API surface for all core entity types.
- Keep canonical URLs stable and predictable.
- Make list endpoints sync-friendly for external consumers.
- Ship in phases with clear acceptance criteria and tests.

## Non-Goals (Initial Rollout)

- No write/update/delete API for OParl resources.
- No schema-level refactor of `riski-core` models in phase 1.
- No perfect historical data backfill beyond what existing RIS ingestion provides.

## Compliance Contract (Phase 0)

Before coding endpoints, agree and document these server rules:

1. Canonical URL strategy

- One canonical public base URL (configurable) for all generated `id` and link fields.
- Stable path naming for object IDs and list endpoints.

1. OParl endpoint layout

- Versioned OParl routes under `/api/oparl/v1.1`.
- One `System` object as entrypoint for that version.

1. List endpoint semantics (all external lists)

- Required query params: `created_since`, `created_until`, `modified_since`, `modified_until`, `omit_internal`, `page`, `limit`.
- Stable ordering by immutable key (default: `db_id`).
- Link generation preserves active filters and pagination params.

1. Deleted object behavior

- Respect OParl soft-delete rules (`deleted`, `modified`, minimal required remaining fields).
- Include deleted objects in sync scenarios where required by spec (notably with `modified_since`).

1. Error response contract

- Keep HTTP status codes correct.
- Optionally provide OParl error body (`type`, `message`, `debug`) where applicable.

1. CORS for JSON endpoints

- Ensure `Access-Control-Allow-Origin: *` for JSON responses.

### Phase 0 Deliverables

- Architecture note documenting the above contract.
- Team approval of canonical URL and endpoint naming.
- Definition of "minimum compliant" vs "enhanced" output profile.

### Phase 0 Acceptance Criteria

- Contract document reviewed and signed off.
- No open ambiguity on ID URL shape, filters, or deleted-object behavior.

## Foundation (Phase 1)

## Scope

1. App and configuration foundation

- Add `oparl_base_url` setting (public canonical base).
- Add `oparl_page_size_default` and `oparl_page_size_max`.

1. Dependency and app state wiring

- Store `db_sessionmaker` in `app.state`.
- Add DB session dependency in `app/api/dependencies.py`.

1. OParl package skeleton

- `app/api/oparl/` with serializer and pagination modules.
- `app/api/routers/oparl.py` and router registration.

1. Shared response models

- Generic list envelope models aligned to OParl (`data`, `pagination`, `links`).
- Links model supports optional fields, including optional `web`.

1. First endpoints

- `GET /api/oparl/v1.1/system`
- `GET /api/oparl/v1.1/body`
- `GET /api/oparl/v1.1/body/{id}`

### Serializer Rules (Phase 1 baseline)

- Build OParl `id` from `oparl_base_url` + entity path + `db_id`.
- Preserve `type` from model data.
- Convert date/time values to ISO 8601.
- Exclude internal payload fields that should not leak (`content`, `embed`).
- Map model field names to OParl naming where required (for example `other_oparl_versions` -> `otherOparlVersions`).

### Phase 1 Acceptance Criteria

- All phase-1 endpoints return valid JSON and correct OParl envelope/object shape.
- `Body` contains required external list URLs and required embedded/linked fields per chosen compliance profile.
- Pagination links are canonical and stable.
- Unit and integration tests for `system` and `body` pass.

## Full Entity Coverage (Phase 2)

### Scope

Implement list + detail endpoints for all remaining entities:

- `organization`
- `person`
- `meeting`
- `agendaItem`
- `paper`
- `file`
- `consultation`
- `membership`
- `legislativeTerm`
- `location`

### Cross-Cutting Requirements

- Shared filter handling (`created_*`, `modified_*`, `omit_internal`, `page`, `limit`).
- Stable sorting in all lists.
- Relationship fields emitted as URL references or embedded objects according to OParl expectations.
- Entity-specific embed/detail modes where spec differs for internal vs standalone representation.

### Phase 2 Acceptance Criteria

- All entities have list + detail routes.
- Filters and pagination behave consistently on every external list.
- `omit_internal=true` removes internal lists/objects where spec allows.
- Test suite covers at least one positive and one negative case per endpoint class.

## Hardening and Compatibility (Phase 3)

### Scope

1. Spec fidelity improvements

- Tighten field-level compliance against OParl 1.1 schema expectations.
- Add/validate optional but recommended fields where available.

1. Performance and reliability

- Add query optimization for high-volume lists (indexes, selected eager loading).
- Ensure deterministic pagination under load.

1. Operational concerns

- Add structured logs for OParl requests.
- Add basic metrics (request duration, response size, error rates).

1. Documentation

- Publish endpoint catalog and filter behavior.
- Provide migration guidance for downstream consumers.

### Phase 3 Acceptance Criteria

- Performance baseline documented for representative datasets.
- No known compliance blockers for OParl 1.1 minimum profile.
- Public docs include examples for common sync flows.

## Endpoint Backlog Matrix

| Entity | List | Detail | Filters | Pagination | Internal/Embedded Rules | Status |
| --- | --- | --- | --- | --- | --- | --- |
| System | n/a | yes | n/a | n/a | n/a | phase 1 |
| Body | yes | yes | yes | yes | yes | phase 1 |
| Organization | yes | yes | yes | yes | yes | phase 2 |
| Person | yes | yes | yes | yes | yes | phase 2 |
| Meeting | yes | yes | yes | yes | yes | phase 2 |
| AgendaItem | yes | yes | yes | yes | yes | phase 2 |
| Paper | yes | yes | yes | yes | yes | phase 2 |
| File | yes | yes | yes | yes | yes | phase 2 |
| Consultation | yes | yes | yes | yes | yes | phase 2 |
| Membership | yes | yes | yes | yes | yes | phase 2 |
| LegislativeTerm | yes | yes | yes | yes | yes | phase 2 |
| Location | yes | yes | yes | yes | yes | phase 2 |

## Test Matrix

Minimum tests to add in `riski-backend/test/`:

1. Routing and shape

- `system` endpoint returns OParl system object with canonical `id`.
- `body` list returns `data`, `pagination`, `links`.

1. Pagination

- `page` and `limit` boundaries.
- `next` absent on last page, present otherwise.
- Filter params preserved in link URLs.

1. Filtering

- `created_since` and `modified_since` reduce result set correctly.
- Combined filters are respected.

1. Internal output control

- `omit_internal=true` removes supported internal fields.
- Default mode includes internal fields where configured.

1. Soft delete and synchronization

- Deleted objects returned correctly for sync use cases.
- Required remaining fields retained for deleted entities.

1. Serialization consistency

- UUID-based URLs are canonical and stable.
- Date fields serialized as ISO 8601.
- Internal-only fields (`content`, `embed`) not leaked.

## Suggested Work Breakdown

1. Phase 0 contract and schema mapping workshop.

2. Implement phase 1 and ship behind feature flag if needed.

3. Add phase 2 entities in two batches:

- Batch A: Organization, Person, Membership, LegislativeTerm.
- Batch B: Meeting, AgendaItem, Paper, File, Consultation, Location.

1. Phase 3 hardening and public documentation pass.

## Risks and Mitigations

1. Risk: model/spec mismatch in field semantics.

- Mitigation: explicit per-entity serializer contracts and snapshot tests.

1. Risk: canonical URL drift behind reverse proxy.

- Mitigation: use explicit `oparl_base_url`, avoid deriving from bind host/port.

1. Risk: pagination instability on mutable datasets.

- Mitigation: deterministic order by immutable key and stable link generation.

1. Risk: large payloads from internal embedding.

- Mitigation: `omit_internal` support and conservative defaults.

## Definition of Done (Overall)

- All OParl entities available as list + detail where required.
- List/filter/pagination behavior consistent and tested.
- Canonical URLs stable.
- Documented compliance profile and known limitations.
