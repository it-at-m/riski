"""Gradio entrypoint for the RISKI MCP server.

Placeholder scaffold — the real Gradio app and ``demo.launch(mcp_server=True)``
land in issue #06, wiring in the tools from issue #04 and the settings from
issue #05.
"""

# ruff: noqa: E402
from truststore import inject_into_ssl

inject_into_ssl()


def main() -> None:
    """Launch the Gradio app and MCP server (implemented in issue #06)."""
    raise NotImplementedError("The Gradio MCP app is implemented in issue #06.")


if __name__ == "__main__":
    main()
