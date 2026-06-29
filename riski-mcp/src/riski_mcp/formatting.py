"""Spoken-answer formatting and error mapping (issue #07).

Turns a :class:`~riski_mcp.agui_client.RiskiAnswer` into one short, natural German
sentence (plus up to ``max_sources`` source references) suitable for Reachy Mini
to speak. Every outcome — success, "nothing found", timeout, policy block, backend
down — maps to a friendly sentence; no tracebacks, JSON or markdown ever reach the
robot.

Messages are German to match the backend's German-facing wording.
"""

from __future__ import annotations

import re

from riski_mcp.agui_client import ERROR_RUN_ERROR, ERROR_TIMEOUT, RiskiAnswer

__all__ = ["format_answer", "GENERIC_ERROR_MESSAGE", "MAX_ANSWER_CHARS"]

#: Cap on the answer body (sources are appended after this) — it is spoken aloud.
MAX_ANSWER_CHARS = 700

GENERIC_ERROR_MESSAGE = "Es gab ein technisches Problem mit der RIS-Suche."

# error_type -> spoken German sentence. Unknown types fall back to the generic
# technical message above.
_ERROR_MESSAGES: dict[str, str] = {
    "no_tool_call": "Dazu konnte ich nichts finden. Stelle die Frage gern etwas konkreter.",
    "no_documents_found": "Ich habe keine passenden Dokumente im RIS gefunden.",
    "no_relevant_documents": "Ich habe Dokumente gefunden, aber keines passte zur Frage.",
    "content_policy_violation": "Diese Anfrage kann ich leider nicht beantworten.",
    "server_error": GENERIC_ERROR_MESSAGE,
    ERROR_TIMEOUT: "Die Suche hat zu lange gedauert. Bitte versuche es gleich noch einmal.",
    ERROR_RUN_ERROR: GENERIC_ERROR_MESSAGE,
}

# Spoken when the run succeeded but produced no answer text and no error.
_EMPTY_ANSWER_MESSAGE = "Dazu konnte ich leider keine Antwort finden."

# Top-level keys that may hold a human-readable source name, in priority order.
# DocumentReference / ProposalReference / TrackedProposal all expose ``name``;
# proposals additionally carry ``subject`` (a short description).
_SOURCE_NAME_KEYS = (
    "name",
    "subject",
    "title",
    "betreff",
)

# Slim snapshot documents keep the title only inside their vector-store ``metadata``.
_METADATA_NAME_KEYS = (
    "name",
    "title",
    "betreff",
    "short_name",
    "filename",
)

_MAX_SUGGESTIONS = 2


def format_answer(answer: RiskiAnswer, max_sources: int = 3) -> str:
    """Format a :class:`RiskiAnswer` as a spoken-friendly German string.

    On error: the mapped sentence for ``error.error_type`` (generic technical
    message for unknown types), with up to two suggestions appended when present.
    On success: the cleaned answer text followed by up to ``max_sources`` sources
    rendered as ``Quelle: <name>``.

    Args:
        answer: The aggregated agent result.
        max_sources: Maximum number of source references to append.

    Returns:
        A single string with no markdown or JSON, capped for speech.
    """
    if answer.error is not None:
        sentence = _ERROR_MESSAGES.get(answer.error.error_type, GENERIC_ERROR_MESSAGE)
        return _append_suggestions(sentence, answer.error.suggestions)

    body = _clean_text(answer.answer)
    if not body:
        return _EMPTY_ANSWER_MESSAGE

    body = _truncate(body, MAX_ANSWER_CHARS)
    sources = _format_sources(answer.documents, answer.proposals, max_sources)
    if sources:
        return f"{body} {sources}"
    return body


def _append_suggestions(sentence: str, suggestions: list[str]) -> str:
    picked = [_clean_text(s) for s in suggestions[:_MAX_SUGGESTIONS]]
    picked = [s for s in picked if s]
    if not picked:
        return sentence
    joined = " ".join(s if s.endswith((".", "!", "?")) else f"{s}." for s in picked)
    return f"{sentence} Du könntest es zum Beispiel so versuchen: {joined}"


def _format_sources(documents: list[dict], proposals: list[dict], max_sources: int) -> str:
    if max_sources <= 0:
        return ""
    names: list[str] = []
    seen: set[str] = set()
    for item in (*documents, *proposals):
        name = _source_name(item)
        if not name:
            continue
        key = name.casefold()
        if key in seen:
            continue
        seen.add(key)
        names.append(name)
        if len(names) >= max_sources:
            break
    return " ".join(f"Quelle: {name}." for name in names)


def _source_name(item: dict) -> str:
    for key in _SOURCE_NAME_KEYS:
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return _truncate(_clean_text(value), 120)
    metadata = item.get("metadata")
    if isinstance(metadata, dict):
        for key in _METADATA_NAME_KEYS:
            value = metadata.get(key)
            if isinstance(value, str) and value.strip():
                return _truncate(_clean_text(value), 120)
    return ""


def _clean_text(text: str) -> str:
    """Strip markdown and collapse whitespace for clean speech output."""
    if not text:
        return ""
    # Images: ![alt](url) -> alt ; links: [text](url) -> text
    text = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    # Inline code / emphasis / heading & quote markers.
    text = re.sub(r"[`*_~#>]+", " ", text)
    # Bullet/list markers at line starts.
    text = re.sub(r"(?m)^\s*[-+]\s+", " ", text)
    # Collapse all whitespace runs (incl. newlines) to single spaces.
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _truncate(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0].rstrip(" ,.;:")
    return f"{cut}…"
