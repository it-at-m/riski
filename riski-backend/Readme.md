# RISKI Backend

## Quick Start

1. **Install dependencies**

    ```powershell
    uv sync
    ```

2. **Copy the local config template**

    ```powershell
    Copy-Item .\.env.example .\.env -Force
    ```

3. **Run the application**

    ```powershell
    uv run main.py
    ```

4. **Run the tests (coverage enabled by default)**

    ```powershell
    uv run pytest
    ```