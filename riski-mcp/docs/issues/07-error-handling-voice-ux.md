# Error handling & spoken-answer UX

**Labels:** `mcp`, `ux`
**Depends on:** #03, #04

## Goal

Make every outcome — success, "nothing found", timeout, policy block, backend down —
return a short, natural sentence suitable for the robot to speak. No tracebacks, no
JSON, no German/English mismatch surprises.

## Backend error states to map (`error_info.error_type`)

| `error_type` | Spoken response (German, since backend is German-facing) |
|--------------|-----------------------------------------------------------|
| `no_tool_call` | "Dazu konnte ich nichts finden. Stelle die Frage gern etwas konkreter." |
| `no_documents_found` | "Ich habe keine passenden Dokumente im RIS gefunden." (+ optional suggestions) |
| `no_relevant_documents` | "Ich habe Dokumente gefunden, aber keines passte zur Frage." |
| `timeout` | "Die Suche hat zu lange gedauert. Bitte versuche es gleich noch einmal." |
| `content_policy_violation` | "Diese Anfrage kann ich leider nicht beantworten." |
| (RUN_ERROR / network) | "Es gab ein technisches Problem mit der RIS-Suche." |

## Tasks

- [ ] A formatter `format_answer(RiskiAnswer, max_sources) -> str` producing:
      answer sentence(s) → then up to `MAX_SOURCES` sources as
      "Quelle: <name>". Strip markdown, collapse whitespace, cap length.
- [ ] Map each `error_type` to a friendly sentence; append 1–2 `suggestions` when
      present (e.g. "Du könntest es mit … versuchen.").
- [ ] Network/timeout/HTTP errors from the client → the generic technical message.
- [ ] Decide and document the response **language** (default German to match the
      backend; optionally detect/echo the question language — note as a follow-up).
- [ ] Ensure secrets/internal details never appear in any user-facing string.

## Acceptance criteria

- [ ] Each `error_type` yields its mapped sentence (unit-tested with fixtures).
- [ ] A backend-down scenario returns the generic message, no exception bubbles to
      the MCP layer.
- [ ] Output contains no markdown/JSON and is within the length cap.

## Notes

- Keep messages short — they are spoken aloud by Reachy Mini.
- Coordinate wording with the backend's existing German user-facing messages for
  consistency.