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

## DB-backed OParl Contract Tests

The OParl DB contract tests in `test/integration/test_oparl_db_contract.py` run against a real PostgreSQL instance.
They are skipped by default unless `RISKI_TEST_DB_ASYNC_URL` is set.

1. **Start PostgreSQL locally (Docker)**

    ```powershell
    docker run --name riski-test-postgres -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=riski_test -p 5432:5432 -d pgvector/pgvector:pg16
    ```

2. **Set test DB URL and run the contract tests**

    ```powershell
    $env:RISKI_TEST_DB_ASYNC_URL = "postgresql+psycopg://postgres:postgres@localhost:5432/riski_test"
    uv run pytest test/integration/test_oparl_db_contract.py
    ```

3. **Stop and remove the local test database**

    ```powershell
    docker rm -f riski-test-postgres
    ```
