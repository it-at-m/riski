from datetime import datetime

import pytest
from config.config import Config, get_config
from core.model.data_models import (
    AgendaItem,
    Body,
    Consultation,
    File,
    Keyword,
    LegislativeTerm,
    Location,
    Meeting,
    Membership,
    Organization,
    OrganizationClassificationEnum,
    OrganizationTypeEnum,
    Paper,
    PaperSubtypeEnum,
    PaperTypeEnum,
    Person,
    Post,
    System,
)
from sqlmodel import Session, SQLModel, create_engine

config: Config = get_config()


def pytest_addoption(parser):
    parser.addoption(
        "--db-url",
        action="store",
        help="Database URL (z.B. postgresql+psycopg://user:pass@host:5432/dbname)",
    )


@pytest.fixture(scope="module")
def engine(pytestconfig):
    db_url = pytestconfig.getoption("--db-url")
    if not db_url:
        DB_USER = config.test.db_user
        DB_PASSWORD = config.test.db_password
        DB_NAME = config.test.db_name
        DB_URL = config.test.database_url
        if DB_URL:
            db_url = str(DB_URL)
        elif DB_USER and DB_PASSWORD and DB_NAME:
            db_url = f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@localhost:5432/{DB_NAME}"
        else:
            db_url = "sqlite:///:memory:"
    engine = create_engine(db_url, echo=True)
    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def session(engine):
    with Session(engine) as session:
        yield session


@pytest.fixture(scope="function")
def system(session):
    obj = System(
        id="https://example.org/system/1",
        oparlVersion="https://schema.oparl.org/1.1/",
        name="Test System",
        created=datetime.now(),
        modified=datetime.now(),
    )
    session.add(obj)
    session.commit()
    return obj


@pytest.fixture(scope="function")
def location(session):
    obj = Location(
        id="https://example.org/location/1",
        description="Test Location",
        created=datetime.now(),
        modified=datetime.now(),
        web="http://example.org/location/1",
    )
    session.add(obj)
    session.commit()
    return obj


@pytest.fixture(scope="function")
def organization(session):
    obj = Organization(
        id="https://example.org/organization/1",
        name="Test Organization",
        organizationType=OrganizationTypeEnum.FACTION,
        classification=OrganizationClassificationEnum.FACTION,
        created=datetime.now(),
        modified=datetime.now(),
    )
    session.add(obj)
    session.commit()
    return obj


@pytest.fixture(scope="function")
def meeting(session):
    obj = Meeting(
        id="https://example.org/meeting/1",
        name="Test Meeting",
        start=datetime.now(),
        end=datetime.now(),
        created=datetime.now(),
        modified=datetime.now(),
    )
    session.add(obj)
    session.commit()
    return obj


@pytest.fixture(scope="function")
def paper(session):
    obj = Paper(
        id="https://example.org/paper/1",
        name="Test Paper",
        created=datetime.now(),
        modified=datetime.now(),
        paper_type=PaperTypeEnum.CITIZENS_ASSEMBLY_RECOMMENDATION,
        paper_subtype=PaperSubtypeEnum.AMENDMENT_PROPOSAL,
    )
    session.add(obj)
    session.commit()
    return obj


@pytest.fixture(scope="function")
def person(session):
    obj = Person(
        id="https://example.org/person/1",
        name="Test Person",
        title="Dr.",
        created=datetime.now(),
        modified=datetime.now(),
    )
    session.add(obj)
    session.commit()
    return obj


@pytest.fixture(scope="function")
def agenda_item(session, file, meeting):
    obj = AgendaItem(
        id="https://example.org/agenda_item/1",
        type="discussion",
        meeting=meeting.db_id,  # FK → Meeting
        number="10.1",
        order=1,
        name="Test Agenda Item",
        public=True,
        result="Adopted unchanged",
        resolutionText="Resolution text example",
        resolutionFile=file.db_id,  # FK → File
        start=datetime.now(),
        end=datetime.now(),
        license="CC-BY-4.0",
        created=datetime.now(),
        modified=datetime.now(),
        web="http://example.org/agenda_item/1",
        deleted=False,
    )
    session.add(obj)
    session.commit()
    return obj


@pytest.fixture(scope="function")
def file(session):
    obj = File(
        id="https://example.org/file/1",
        name="Test File",
        accessUrl="http://example.org/file/1",
        created=datetime.now(),
        modified=datetime.now(),
    )
    session.add(obj)
    session.commit()
    return obj


@pytest.fixture(scope="function")
def legislative_term(session):
    obj = LegislativeTerm(
        id="https://example.org/legislative_term/1",
        name="Test Legislative Term",
        created=datetime.now(),
        modified=datetime.now(),
    )
    session.add(obj)
    session.commit()
    return obj


@pytest.fixture(scope="function")
def membership(session, organization):
    obj = Membership(
        id="https://example.org/membership/1",
        role="Test Role",
        startDate=datetime.now(),
        created=datetime.now(),
        modified=datetime.now(),
        organization=organization.db_id,
    )
    session.add(obj)
    session.commit()
    return obj


@pytest.fixture(scope="function")
def keyword(session):
    obj = Keyword(name="Test Keyword")
    session.add(obj)
    session.commit()
    return obj


@pytest.fixture(scope="function")
def consultation(session):
    obj = Consultation(
        id="https://example.org/consultation/1",
        url="http://example.org/consultation/1",
        created=datetime.now(),
        modified=datetime.now(),
    )
    session.add(obj)
    session.commit()
    return obj


@pytest.fixture(scope="function")
def body(session, system, organization, person, meeting, paper, legislative_term, agenda_item, file):
    legislative_term_list = "https://example.org/legislative_term_list"
    membership = "https://example.org/membership/1"

    obj = Body(
        id="https://example.org/body/1",
        name="Test Body",
        organization=organization.id,
        person=person.id,
        meeting=meeting.id,
        paper=paper.id,
        legislativeTerm=legislative_term.id,
        agendaItem=agenda_item.id,
        system=system.db_id,
        created=datetime.now(),
        modified=datetime.now(),
        file=file.id,
        legislativeTermList=legislative_term_list,
        membership=membership,
    )
    session.add(obj)
    session.commit()
    return obj


@pytest.fixture(scope="function")
def post(session, organization):
    obj = Post(
        name="Dummy Post",
        organization_id=organization.db_id,
    )
    session.add(obj)
    session.commit()
    return obj
