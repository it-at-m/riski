"""Gradio entrypoint for the RISKI MCP server (issue #06).

Wires the tools from ``riski_mcp.tools`` into a Gradio app that

1. launches the MCP server at the standard ``/gradio_api/mcp/`` endpoint
   (``demo.launch(mcp_server=True)``), discoverable by the Reachy Mini
   conversation app, and
2. offers a minimal human UI for manual testing / the Space landing page.

Run locally with ``python app.py`` (or ``uv run python app.py``).
"""

# ruff: noqa: E402  (truststore must be injected before httpx/ssl is imported)
import logging
import os

from truststore import inject_into_ssl

inject_into_ssl()

import gradio as gr
from riski_mcp.config import get_settings
from riski_mcp.tools import get_riski_capabilities, search_munich_ris

logger = logging.getLogger(__name__)

_DESCRIPTION = """\
# 🏛️ RISKI – RIS-Suche München

Stelle eine Frage zu Dokumenten und Beschlussvorlagen aus dem
**Ratsinformationssystem (RIS)** der Stadt München. Dieser Space ist außerdem ein
**MCP-Server** und kann als Tool in die Reachy-Mini-Conversation-App eingebunden
werden.
"""

_CONFIG_WARNING = """\
> ⚠️ **Nicht konfiguriert:** `RISKI_MCP__BACKEND_URL` ist nicht gesetzt. Die Suche
> wird fehlschlagen, bis das Backend konfiguriert ist (Space-Secret).
"""


def _backend_configured() -> bool:
    """Return whether the backend is configured, without raising."""
    try:
        get_settings()
        return True
    except Exception:  # noqa: BLE001 - a config error must not crash the landing page
        logger.warning("Backend not configured; UI will show a config warning.")
        return False


def build_demo() -> gr.Blocks:
    """Build the Gradio Blocks app exposing the MCP tools."""
    with gr.Blocks(title="RISKI RIS Search (MCP)") as demo:
        gr.Markdown(_DESCRIPTION)
        if not _backend_configured():
            gr.Markdown(_CONFIG_WARNING)

        question = gr.Textbox(
            label="Frage",
            placeholder="z. B. Welche Anträge gibt es zum Radverkehr in München?",
            lines=2,
        )
        ask_button = gr.Button("RISKI fragen", variant="primary")
        answer = gr.Textbox(label="Antwort", lines=6)

        # The button click is the discoverable MCP tool; the textbox submit reuses
        # the same function but is not registered again (avoids a duplicate tool).
        ask_button.click(search_munich_ris, inputs=question, outputs=answer, api_name="search_munich_ris")
        # api_name=False keeps this from registering a second (duplicate) MCP tool;
        # the Gradio type stub omits the bool overload, hence the ignore.
        question.submit(search_munich_ris, inputs=question, outputs=answer, api_name=False)  # ty: ignore[invalid-argument-type]

        # Expose the capabilities helper as an MCP tool without its own UI.
        gr.api(get_riski_capabilities, api_name="get_riski_capabilities")

    return demo


def main() -> None:
    """Launch the Gradio app and the MCP server."""
    logging.basicConfig(level=os.getenv("RISKI_MCP__LOG_LEVEL", "INFO").upper())
    demo = build_demo()
    # HF Spaces provides the port via GRADIO_SERVER_PORT (Gradio reads it itself);
    # honour a plain PORT as a fallback for other hosts.
    port = os.getenv("GRADIO_SERVER_PORT") or os.getenv("PORT")
    demo.launch(
        server_name="0.0.0.0",  # noqa: S104 - public Space must bind all interfaces
        server_port=int(port) if port else None,
        mcp_server=True,
    )


if __name__ == "__main__":
    main()
