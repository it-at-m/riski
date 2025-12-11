# Extraction Process

## Context

We extract data from the RIS as plain HTML without direct datastore access. Relations appear either as hyperlinks or plain text.

## Decision

Split the pipeline into two passes:

1) Entities pass: extract and persist entities without relations.
2) Relations pass: resolve and persist relations between existing entities.

If a relation targets a non-existent entity, log at ERROR and skip it.

## Consequences

- Pros: smaller, clearer extractors/parsers; simpler error handling.
- Cons: two iterations over pages/entities increase runtime.

## Entities

### Entity Extractor

Responsible only for fetching HTML for the specific entity.

### Entity Parser

Builds the DB object for that entity type; sets relations to None.

## Relations

### Relations Extractor

Finds DB records for involved entities and persists the new relation.

### Relations Parser

Extracts only relation data from HTML; ignores other entity details.

## Known Challenges

- Some entities (e.g., Locations) cannot be retrieved standalone from RIS and are only discoverable via Meetings. We need an initial pre-fill mechanism for such entities before linking relations.
- Not all relations are hyperlinks; some are plain text (e.g., “Herr STR Thomas Müller”). Names and roles are stored separately, so lookups must handle this.