"""MCP tool definitions (issue #04).

Each function here is exposed by Gradio as an MCP tool: the **name**, the
**docstring** (→ tool description) and the **type hints** (→ input schema) are
what the robot's planner sees, so they are written to be precise and
LLM-friendly. Outputs are plain strings optimized for text-to-speech — short
answer first, then up to a few sources; never JSON, markdown tables or
tracebacks.

All tools are **stateless**: every call mints a fresh ``threadId``/``runId`` and
opens (and closes) its own backend connection.
"""

from __future__ import annotations

import logging

from riski_mcp.agui_client import AguiClient
from riski_mcp.config import Settings, get_settings
from riski_mcp.formatting import GENERIC_ERROR_MESSAGE, format_answer

__all__ = ["search_munich_ris", "get_riski_capabilities"]

logger = logging.getLogger(__name__)

# Static capability description. The backend computes its own capabilities via an
# internal ``get_agent_capabilities`` helper that is NOT exposed through the public
# API (openapi.json), so we mirror its user-facing wording here. Keep in sync with
# ``riski-backend`` AGENT_CAPABILITIES_PROMPT if it changes.
_CAPABILITIES = (
    "Ich beantworte Fragen zu Dokumenten und Beschlussvorlagen aus dem "
    "Rats-Informations-System (RIS) der Stadt München: Stadtratsanträge, "
    "Beschlüsse, Sitzungsprotokolle und weitere öffentliche Dokumente des "
    "Stadtrats, der Stadtverwaltung und der Bezirksausschüsse. Die Wissensbasis "
    "umfasst öffentliche Dokumente ab 2020. Ich kann keine statistischen "
    "Auswertungen vornehmen und keine Themen außerhalb des Münchner RIS beantworten."
)


def _auth_headers(settings: Settings) -> dict[str, str]:
    if settings.backend_auth_header:
        return {"Authorization": settings.backend_auth_header}
    return {}


async def search_munich_ris(question: str) -> str:
    """Beantwortet eine Frage zum Münchner Ratsinformationssystem (RIS).

    Nutze dieses Tool für Fragen zu Dokumenten und Beschlussvorlagen der Stadt
    München: Stadtratsanträgen, Beschlüssen, Sitzungsprotokollen und anderen
    öffentlichen Dokumenten des Stadtrats, der Stadtverwaltung oder der
    Bezirksausschüsse. Die Antwort ist kurz gehalten und für die Sprachausgabe
    geeignet; passende Quellen werden genannt.

    Args:
        question: Die Frage der Nutzerin oder des Nutzers in natürlicher Sprache
            (z. B. "Welche Anträge gibt es zum Radverkehr in München?").

    Returns:
        Eine kurze, gesprochene-freundliche Antwort inklusive bis zu einigen
        Quellen, oder ein freundlicher Hinweis, falls nichts gefunden wurde.
    """
    if not question or not question.strip():
        return "Bitte stelle eine Frage zum Münchner Ratsinformationssystem."

    try:
        settings = get_settings()
    except Exception:  # noqa: BLE001 - missing/invalid config must not crash the tool
        logger.exception("RISKI MCP server is not configured (RISKI_MCP__BACKEND_URL?)")
        return "Das RIS-Tool ist gerade nicht konfiguriert. Bitte wende dich an die Administration."

    try:
        async with AguiClient(
            settings.backend_base_url,
            request_timeout=settings.request_timeout_seconds,
            connect_timeout=settings.connect_timeout_seconds,
            headers=_auth_headers(settings),
            verify=settings.verify_ssl,
        ) as client:
            answer = await client.ask(question.strip())
    except Exception:  # noqa: BLE001 - never leak a traceback to the robot
        logger.exception("search_munich_ris failed unexpectedly")
        return GENERIC_ERROR_MESSAGE

    return format_answer(answer, max_sources=settings.max_sources)


async def get_riski_capabilities() -> str:
    """Beschreibt, welche Fragen das RISKI-RIS-Tool beantworten kann.

    Hilft dem Planer zu entscheiden, wann ``search_munich_ris`` aufgerufen werden
    sollte. Nimmt keine Parameter entgegen und ruft das Backend nicht auf.

    Returns:
        Eine kurze Beschreibung der Fähigkeiten und Grenzen des RIS-Agenten.
    """
    return _CAPABILITIES
