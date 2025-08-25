import pytest
from config.config import Config, get_config
from dotenv import load_dotenv
from sqlmodel import SQLModel, create_engine

config: Config = get_config()


def pytest_addoption(parser):
    parser.addoption(
        "--db-url",
        action="store",
        help="Database URL (z.B. postgresql+psycopg://user:pass@host:5432/dbname)",
    )


@pytest.fixture(scope="module")
def engine(pytestconfig):
    load_dotenv()
    db_url = pytestconfig.getoption("--db-url")
    if not db_url:
        DB_USER = config.test_riski_db_user
        DB_PASSWORD = config.test_riski_db_password
        DB_NAME = config.test_riski_db_name
        DB_URL = config.test_database_url
        if DB_URL:
            db_url = DB_URL
        elif DB_USER and DB_PASSWORD and DB_NAME:
            db_url = f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@localhost:5432/{DB_NAME}"
        else:
            db_url = "sqlite:///:memory:"
    engine = create_engine(db_url, echo=True)
    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)
