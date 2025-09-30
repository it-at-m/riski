from config.config import Config, get_config
from sqlmodel import Session, SQLModel, create_engine, select
from src.data_models import OrganizationType, OrganizationTypeEnum, PaperSubtype, PaperSubtypeEnum, PaperType, PaperTypeEnum

config: Config = get_config()

_engine = None
_session = None


###########################################################
#############  Create Database Schema ###################
###########################################################
def get_engine():
    """Lazy initialization of database engine."""
    global _engine
    if _engine is None:
        _engine = create_engine(str(config.database_url), echo=True)
    return _engine


def get_session():
    """Lazy initialization of database session."""
    global _session
    if _session is None:
        _session = Session(get_engine())
    return _session


def create_db_and_tables():
    SQLModel.metadata.create_all(get_engine())


def check_tables_exist():
    engine = get_engine()
    with engine.connect() as conn:
        from sqlalchemy import inspect as _inspect

        inspector = _inspect(conn)
        # Only use 'public' schema for Postgres; None for others like SQLite
        schema = "public" if engine.url.get_backend_name() == "postgresql" else None
        tables = inspector.get_table_names(schema=schema)
        print("Existing tables:", tables)


def seed_organization_types(session: Session):
    existing = session.exec(select(OrganizationType)).all()
    if existing:
        return  # Table already populated

    for enum_value in OrganizationTypeEnum:
        org_type = OrganizationType(name=enum_value.value)
        session.add(org_type)
    session.commit()


def seed_paper_types(session: Session):
    existing = session.exec(select(PaperType)).all()
    if existing:
        return  # Table already populated

    for enum_value in PaperTypeEnum:
        paper_type = PaperType(name=enum_value.value)
        session.add(paper_type)
    session.commit()


def seed_paper_subtypes(session: Session):
    existing = session.exec(select(PaperSubtype)).all()
    if existing:
        return  # Table already populated

    # Get paper types first
    paper_types = {pt.name: pt for pt in session.exec(select(PaperType)).all()}

    # Map subtypes to parent types
    subtype_mapping = {
        # Council Proposal
        PaperSubtypeEnum.URGENT_PROPOSAL: PaperTypeEnum.COUNCIL_PROPOSAL,
        PaperSubtypeEnum.PROPOSAL: PaperTypeEnum.COUNCIL_PROPOSAL,
        PaperSubtypeEnum.REQUEST: PaperTypeEnum.COUNCIL_PROPOSAL,
        PaperSubtypeEnum.AMENDMENT_PROPOSAL: PaperTypeEnum.COUNCIL_PROPOSAL,
        # District Committee Proposal
        PaperSubtypeEnum.DISTRICT_COMMITTEE_PROPOSAL: PaperTypeEnum.DISTRICT_COMMITTEE_PROPOSAL,
        # Citizens' Assembly Recommendation
        PaperSubtypeEnum.CITIZENS_ASSEMBLY_RECOMMENDATION: PaperTypeEnum.CITIZENS_ASSEMBLY_RECOMMENDATION,
        # Citizens' Assembly Request
        PaperSubtypeEnum.CITIZENS_ASSEMBLY_REQUEST: PaperTypeEnum.CITIZENS_ASSEMBLY_REQUEST,
        # Meeting Templates
        PaperSubtypeEnum.RESOLUTION_TEMPLATE_VB: PaperTypeEnum.MEETING_TEMPLATE,
        PaperSubtypeEnum.RESOLUTION_TEMPLATE_SB: PaperTypeEnum.MEETING_TEMPLATE,
        PaperSubtypeEnum.RESOLUTION_TEMPLATE_SB_VB: PaperTypeEnum.MEETING_TEMPLATE,
        PaperSubtypeEnum.ANNOUNCEMENT: PaperTypeEnum.MEETING_TEMPLATE,
        PaperSubtypeEnum.DIRECT: PaperTypeEnum.MEETING_TEMPLATE,
        PaperSubtypeEnum.MEETING_TEMPLATE_DISTRICT_COMMITTEE: PaperTypeEnum.MEETING_TEMPLATE,
    }

    for enum_value in PaperSubtypeEnum:
        parent_type_enum = subtype_mapping.get(enum_value)
        if not parent_type_enum:
            raise ValueError(f"No parent type mapping for subtype {enum_value.value}")
        parent_type = paper_types.get(parent_type_enum.value)
        if not parent_type:
            raise ValueError(f"No parent type found for subtype {enum_value.value} (expected PaperType '{parent_type_enum.value}')")

        paper_subtype = PaperSubtype(
            name=enum_value.value,
            paper_type_id=parent_type.id,
        )
        session.add(paper_subtype)
    session.commit()


def seed_all_enums(session: Session):
    seed_organization_types(session)
    seed_paper_types(session)
    seed_paper_subtypes(session)


if __name__ == "__main__":
    try:
        create_db_and_tables()
        check_tables_exist()
    except Exception as e:
        print(f"Error initializing database: {e}")
        raise
