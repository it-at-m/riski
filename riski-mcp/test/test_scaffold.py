"""Scaffold smoke tests (issue #01).

These confirm the module is importable and the project skeleton is wired up.
Real tests for the client, tools, and app land in issue #10.
"""


def test_package_imports() -> None:
    import riski_mcp

    assert riski_mcp.__version__ == "0.0.1"


def test_submodules_import() -> None:
    # Placeholder modules must at least import cleanly.
    from riski_mcp import agui_client, config, tools  # noqa: F401
