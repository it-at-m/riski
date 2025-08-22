import os
import uuid
from datetime import datetime

import pytest
from dotenv import load_dotenv
from sqlmodel import Session, SQLModel, create_engine
from src.data_models import (
    AgendaItem,
    Body,
    BodyEquivalentLink,
    Consultation,
    ConsultationKeywordLink,
    File,
    FileAgendaItemLink,
    FileDerivativeLink,
    FileKeywordLink,
    FileMeetingLink,
    Keyword,
    LegislativeTerm,
    LegislativeTermKeyword,
    Location,
    LocationBodies,
    LocationKeyword,
    LocationMeetings,
    LocationOrganizations,
    LocationPapers,
    LocationPersons,
    Meeting,
    MeetingKeywordLink,
    MeetingParticipantLink,
    Membership,
    MembershipKeyword,
    Organization,
    OrganizationKeyword,
    OrganizationMembership,
    OrganizationPost,
    OrganizationSubOrganization,
    OrganizationType,
    Paper,
    PaperDirectionLink,
    PaperFileLink,
    PaperLocationLink,
    PaperOriginatorPersonLink,
    PaperRelatedPaper,
    PaperSubordinatedLink,
    PaperSubtype,
    PaperSuperordinatedLink,
    PaperType,
    Person,
    PersonKeywordLink,
    PersonMembershipLink,
    System,
    Title,
)


# Create a temporary SQLite database for the tests
@pytest.fixture(scope="module")
def engine():
    load_dotenv()
    DB_USER = os.getenv("RISKI_DB_USER")
    DB_PASSWORD = os.getenv("RISKI_DB_PASSWORD")
    DB_NAME = os.getenv("RISKI_DB_NAME")
    # engine = create_engine("sqlite:///:memory:", echo=True)
    engine = create_engine(f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@localhost:5432/{DB_NAME}", echo=True)
    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def session(engine):
    with Session(engine) as session:
        yield session


# Test for the System class
def test_system_create(session):
    system = System(
        id="https://example.org/system/1",
        oparlVersion="https://schema.oparl.org/1.1/",
        name="Test System",
        created=datetime.now(),
        modified=datetime.now(),
    )
    session.add(system)
    session.commit()
    assert system.db_id is not None


# Test for the Location class
def test_location_create(session):
    location = Location(
        id="https://example.org/location/1",
        description="Test Location",
        created=datetime.now(),
        modified=datetime.now(),
        web="http://example.org/location/1",
    )
    session.add(location)
    session.commit()
    assert location.db_id is not None


# Test for the Body class
def test_body_create(session):
    # Create a dummy System
    system = System(
        id="https://example.org/system/1",
        oparlVersion="https://schema.oparl.org/1.1/",
        name="Test System",
        created=datetime.now(),
        modified=datetime.now(),
    )
    session.add(system)
    session.commit()

    # Create a dummy Organization
    organization = Organization(
        id="https://example.org/organization/1",
        name="Test Organization",
        created=datetime.now(),
        modified=datetime.now(),
    )
    session.add(organization)
    session.commit()
    title = Title(title="MR.")
    session.add(title)
    session.commit()
    # Create a dummy Person
    person = Person(
        id="https://example.org/person/1",
        name="Test Person",
        title=title.db_id,  # Required field
        created=datetime.now(),
        modified=datetime.now(),
    )
    session.add(person)
    session.commit()

    # Create a dummy Meeting
    meeting = Meeting(
        id="https://example.org/meeting/1",
        name="Test Meeting",
        start=datetime.now(),
        end=datetime.now(),
        created=datetime.now(),
        modified=datetime.now(),
    )
    session.add(meeting)
    session.commit()

    # Create a dummy Paper
    papertyp = PaperType(name="dummy")
    session.add(papertyp)
    session.commit()
    papersubtyp = PaperSubtype(name="dummy", paper_type_id=papertyp.id)
    session.add(papersubtyp)
    session.commit()
    paper = Paper(
        id="https://example.org/paper/1",
        name="Test Paper",
        created=datetime.now(),
        modified=datetime.now(),
        paper_type=papertyp.id,
        paper_subtype=papersubtyp.id,
    )
    session.add(paper)
    session.commit()

    # Create a dummy Legislative Term
    legislative_term = LegislativeTerm(
        id="https://example.org/legislative_term/1",
        name="Test Legislative Term",
        created=datetime.now(),
        modified=datetime.now(),
    )
    session.add(legislative_term)
    session.commit()

    # Create a dummy Agenda Item
    agenda_item = AgendaItem(
        id="https://example.org/agenda_item/1",
        name="Test Agenda Item",
        created=datetime.now(),
        modified=datetime.now(),
    )
    session.add(agenda_item)
    session.commit()
    file = File(
        id="https://example.org/file/1",
        name="Test File",
        accessUrl="http://example.org/file/1",  # Required field
        created=datetime.now(),
        modified=datetime.now(),
    )
    session.add(file)
    session.commit()

    legislative_term_list = "https://example.org/legislative_term_list"
    membership = "https://example.org/membership/1"  # Dummy value as URL
    # Create Body object
    body = Body(
        id="https://example.org/body/1",
        name="Test Body",
        organization=organization.id,  # Reference to the dummy Organization as a string
        person=person.id,  # Reference to the dummy Person as a string
        meeting=meeting.id,  # Reference to the dummy Meeting as a string
        paper=paper.id,  # Reference to the dummy Paper as a string
        legislativeTerm=legislative_term.id,  # Reference to the dummy LegislativeTerm as a string
        agendaItem=agenda_item.id,  # Reference to the dummy AgendaItem as a string
        system=system.id,  # Reference to the dummy System as a string
        created=datetime.now(),
        modified=datetime.now(),
        file=file.id,
        legislativeTermList=legislative_term_list,
        membership=membership,
    )
    session.add(body)
    session.commit()

    # Check if the Body object was successfully created
    assert body.db_id is not None


# Test for the Meeting class
def test_meeting_create(session):
    # Create a dummy Location
    location = Location(
        id="https://example.org/location/1",
        description="Test Location",
        created=datetime.now(),
        modified=datetime.now(),
    )
    session.add(location)
    session.commit()

    meeting = Meeting(
        id="https://example.org/meeting/1",
        name="Test Meeting",
        start=datetime.now(),
        end=datetime.now(),
        created=datetime.now(),
        modified=datetime.now(),
        location=location.db_id,  # Reference to the dummy Location
    )
    session.add(meeting)
    session.commit()
    assert meeting.db_id is not None


# Test for the Paper class
def test_paper_create(session):
    # Create dummy PaperType and PaperSubtype
    paper_type = PaperType(name="Test Paper Type")
    session.add(paper_type)
    paper_subtype = PaperSubtype(name="Test Paper Subtype", paper_type_id=paper_type.id)
    session.add(paper_subtype)
    session.commit()

    paper = Paper(
        id="https://example.org/paper/1",
        name="Test Paper",
        created=datetime.now(),
        modified=datetime.now(),
        paper_type=paper_type.id,  # Reference to the dummy PaperType
        paper_subtype=paper_subtype.id,  # Reference to the dummy PaperSubtype
    )
    session.add(paper)
    session.commit()
    assert paper.db_id is not None


# Test for the Organization class
def test_organization_create(session):
    organization_type = OrganizationType(name="Test Organization Type")
    session.add(organization_type)
    session.commit()

    organization = Organization(
        id="https://example.org/organization/1",
        name="Test Organization",
        created=datetime.now(),
        modified=datetime.now(),
        organization_type_id=organization_type.db_id,  # Reference to the dummy OrganizationType
    )
    session.add(organization)
    session.commit()
    assert organization.db_id is not None


# Test for the Title class
def test_title_create(session):
    title = Title(title="Test Title")
    session.add(title)
    session.commit()
    assert title.db_id is not None


# Test for the Person class
def test_person_create(session):
    title = Title(title="Test Title")
    session.add(title)
    session.commit()

    person = Person(
        id="https://example.org/person/1",
        name="Test Person",
        created=datetime.now(),
        modified=datetime.now(),
        title=title.db_id,  # Reference to the dummy Title
    )
    session.add(person)
    session.commit()
    assert person.db_id is not None


# Test for the Membership class
def test_membership_create(session):
    organization_type = OrganizationType(name="Test Type")
    session.add(organization_type)
    session.commit()
    organization = Organization(
        id="https://example.org/organization/1",
        name="Test Organization",
        created=datetime.now(),
        modified=datetime.now(),
        organization_type_id=organization_type.db_id,  # Dummy value
    )
    session.add(organization)
    session.commit()

    membership = Membership(
        id="https://example.org/membership/1",
        role="Test Role",
        startDate=datetime.now(),
        created=datetime.now(),
        modified=datetime.now(),
        organization=organization.db_id,  # Reference to the dummy Organization
    )
    session.add(membership)
    session.commit()
    assert membership.db_id is not None


# Test for the Keyword class
def test_keyword_create(session):
    keyword = Keyword(name="Test Keyword")
    session.add(keyword)
    session.commit()
    assert keyword.db_id is not None


# Test for the File class
def test_file_create(session):
    file = File(
        id="https://example.org/file/1",
        name="Test File",
        accessUrl="http://example.org/file/1",  # Required field
        created=datetime.now(),
        modified=datetime.now(),
    )
    session.add(file)
    session.commit()
    assert file.db_id is not None


# Test for the AgendaItem class
def test_agenda_item_create(session):
    agenda_item = AgendaItem(
        id="https://example.org/agenda_item/1",
        name="Test Agenda Item",
        created=datetime.now(),
        modified=datetime.now(),
    )
    session.add(agenda_item)
    session.commit()
    assert agenda_item.db_id is not None


# Test for the PaperType class
def test_paper_type_create(session):
    paper_type = PaperType(name="Test Paper Type")
    session.add(paper_type)
    session.commit()
    assert paper_type.id is not None


# Test for the PaperSubtype class
def test_paper_subtype_create(session):
    # Create a dummy PaperType
    paper_type = PaperType(name="Test Paper Type")
    session.add(paper_type)
    session.commit()

    paper_subtype = PaperSubtype(
        name="Test Paper Subtype",
        paper_type_id=paper_type.id,  # Reference to the dummy PaperType
    )
    session.add(paper_subtype)
    session.commit()
    assert paper_subtype.id is not None


# Test for the LegislativeTerm class
def test_legislative_term_create(session):
    legislative_term = LegislativeTerm(
        id="https://example.org/legislative_term/1",
        name="Test Legislative Term",
        created=datetime.now(),
        modified=datetime.now(),
    )
    session.add(legislative_term)
    session.commit()
    assert legislative_term.db_id is not None


# Test for the OrganizationType class
def test_organization_type_create(session):
    organization_type = OrganizationType(name="Test Organization Type")
    session.add(organization_type)
    session.commit()
    assert organization_type.db_id is not None


# Test for the Consultation class
def test_consultation_create(session):
    consultation = Consultation(
        id="https://example.org/consultation/1",
        url="http://example.org/consultation/1",  # Required field
        created=datetime.now(),
        modified=datetime.now(),
    )
    session.add(consultation)
    session.commit()
    assert consultation.db_id is not None


# Test for the MembershipKeyword class
def test_membership_keyword_create(session):
    # Create actual entities
    organization = Organization(
        id="https://example.org/organization/1", name="Test Organization", created=datetime.now(), modified=datetime.now()
    )
    session.add(organization)
    session.commit()

    membership = Membership(
        id="https://example.org/membership/1",
        role="Test Role",
        created=datetime.now(),
        modified=datetime.now(),
        organization=organization.db_id,
    )
    session.add(membership)
    session.commit()

    keyword = Keyword(name="Test Keyword")
    session.add(keyword)
    session.commit()

    # Now create the link with valid references
    membership_keyword = MembershipKeyword(membership_id=membership.db_id, keyword=keyword.db_id)
    session.add(membership_keyword)
    session.commit()
    assert membership_keyword.membership_id is not None
    assert membership_keyword.keyword is not None


# Test for the ConsultationKeywordLink class
def test_consultation_keyword_link_create(session):
    consultation_keyword_link = ConsultationKeywordLink(consultation_id=uuid.uuid4(), keyword_id=uuid.uuid4())
    session.add(consultation_keyword_link)
    session.commit()
    assert consultation_keyword_link.consultation_id is not None


# Test for the BodyEquivalentLink class
def test_body_equivalent_link_create(session):
    body_equivalent_link = BodyEquivalentLink(body_id_a=uuid.uuid4(), body_id_b=uuid.uuid4())
    session.add(body_equivalent_link)
    session.commit()
    assert body_equivalent_link.body_id_a is not None


# Test for the PaperRelatedPaper class
def test_paper_related_paper_create(session):
    paper_related_paper = PaperRelatedPaper(from_paper_id=uuid.uuid4(), to_paper_id=uuid.uuid4())
    session.add(paper_related_paper)
    session.commit()
    assert paper_related_paper.from_paper_id is not None


# Test for the PaperSuperordinatedLink class
def test_paper_superordinated_link_create(session):
    paper_superordinated_link = PaperSuperordinatedLink(paper_id=uuid.uuid4(), superordinated_paper_url=uuid.uuid4())
    session.add(paper_superordinated_link)
    session.commit()
    assert paper_superordinated_link.paper_id is not None


# Test for the PaperSubordinatedLink class
def test_paper_subordinated_link_create(session):
    paper_subordinated_link = PaperSubordinatedLink(paper_id=uuid.uuid4(), subordinated_paper_url=uuid.uuid4())
    session.add(paper_subordinated_link)
    session.commit()
    assert paper_subordinated_link.paper_id is not None


# Test for the PaperDirectionLink class (if applicable)
def test_paper_direction_link_create(session):
    paper_direction_link = PaperDirectionLink(paper_id=uuid.uuid4(), direction_name=uuid.uuid4())
    session.add(paper_direction_link)
    session.commit()
    assert paper_direction_link.paper_id is not None


# Test for the PaperFileLink class
def test_paper_file_link_create(session):
    paper_file_link = PaperFileLink(paper_id=uuid.uuid4(), file_id=uuid.uuid4())
    session.add(paper_file_link)
    session.commit()
    assert paper_file_link.paper_id is not None


# Test for the PaperLocationLink class
def test_paper_location_link_create(session):
    paper_location_link = PaperLocationLink(paper_id=uuid.uuid4(), location_id=uuid.uuid4())
    session.add(paper_location_link)
    session.commit()
    assert paper_location_link.paper_id is not None


# Test for the FileKeywordLink class
def test_file_keyword_link_create(session):
    file_keyword_link = FileKeywordLink(file_id=uuid.uuid4(), keyword=uuid.uuid4())
    session.add(file_keyword_link)
    session.commit()
    assert file_keyword_link.file_id is not None


# Test for the FileAgendaItemLink class
def test_file_agenda_item_link_create(session):
    file_agenda_item_link = FileAgendaItemLink(file_id=uuid.uuid4(), agendaItem=uuid.uuid4())
    session.add(file_agenda_item_link)
    session.commit()
    assert file_agenda_item_link.file_id is not None


# Test for the FileMeetingLink class
def test_file_meeting_link_create(session):
    file_meeting_link = FileMeetingLink(file_id=uuid.uuid4(), meeting_id=uuid.uuid4())
    session.add(file_meeting_link)
    session.commit()
    assert file_meeting_link.file_id is not None


# Test for the FileDerivativeLink class
def test_file_derivative_link_create(session):
    file_derivative_link = FileDerivativeLink(file_id=uuid.uuid4(), derivative_file_id=uuid.uuid4())
    session.add(file_derivative_link)
    session.commit()
    assert file_derivative_link.file_id is not None


# Test for the LegislativeTermKeyword class
def test_legislative_term_keyword_create(session):
    legislative_term_keyword = LegislativeTermKeyword(legislative_term_id=uuid.uuid4(), keyword=uuid.uuid4())
    session.add(legislative_term_keyword)
    session.commit()
    assert legislative_term_keyword.legislative_term_id is not None


# Test for the PersonMembershipLink class
def test_person_membership_link_create(session):
    person_membership_link = PersonMembershipLink(person_id=uuid.uuid4(), membership_id=uuid.uuid4())
    session.add(person_membership_link)
    session.commit()
    assert person_membership_link.person_id is not None


# Test for the PersonKeywordLink class
def test_person_keyword_link_create(session):
    person_keyword_link = PersonKeywordLink(person_id=uuid.uuid4(), keyword=uuid.uuid4())
    session.add(person_keyword_link)
    session.commit()
    assert person_keyword_link.person_id is not None


# Test for the MeetingParticipantLink class
def test_meeting_participant_link_create(session):
    meeting_participant_link = MeetingParticipantLink(meeting_id=uuid.uuid4(), person_id=uuid.uuid4())
    session.add(meeting_participant_link)
    session.commit()
    assert meeting_participant_link.meeting_id is not None


# Test for the MeetingKeywordLink class
def test_meeting_keyword_link_create(session):
    meeting_keyword_link = MeetingKeywordLink(meeting_id=uuid.uuid4(), keyword=uuid.uuid4())
    session.add(meeting_keyword_link)
    session.commit()
    assert meeting_keyword_link.meeting_id is not None


# Test for the FileMeetingLink class
def test_meeting_aux_file_link_create(session):
    meeting_aux_file_link = FileMeetingLink(meeting_id=uuid.uuid4(), file_id=uuid.uuid4())
    session.add(meeting_aux_file_link)
    session.commit()
    assert meeting_aux_file_link.meeting_id is not None


# Test for the LocationBodies class
def test_location_bodies_create(session):
    location_bodies = LocationBodies(location_id=uuid.uuid4(), body_id=uuid.uuid4())
    session.add(location_bodies)
    session.commit()
    assert location_bodies.location_id is not None


# Test for the LocationOrganizations class
def test_location_organizations_create(session):
    location_organizations = LocationOrganizations(location_id=uuid.uuid4(), organization_id=uuid.uuid4())
    session.add(location_organizations)
    session.commit()
    assert location_organizations.location_id is not None


# Test for the LocationPersons class
def test_location_persons_create(session):
    location_persons = LocationPersons(location_id=uuid.uuid4(), person_id=uuid.uuid4())
    session.add(location_persons)
    session.commit()
    assert location_persons.location_id is not None


# Test for the LocationMeetings class
def test_location_meetings_create(session):
    location_meetings = LocationMeetings(location_id=uuid.uuid4(), meeting_id=uuid.uuid4())
    session.add(location_meetings)
    session.commit()
    assert location_meetings.location_id is not None


# Test for the LocationPapers class
def test_location_papers_create(session):
    location_papers = LocationPapers(location_id=uuid.uuid4(), paper_id=uuid.uuid4())
    session.add(location_papers)
    session.commit()
    assert location_papers.location_id is not None


# Test for the LocationKeyword class
def test_location_keyword_create(session):
    location_keyword = LocationKeyword(location_id=uuid.uuid4(), keyword=uuid.uuid4())
    session.add(location_keyword)
    session.commit()
    assert location_keyword.location_id is not None


# Test for the OrganizationMembership class
def test_organization_membership_create(session):
    organization_membership = OrganizationMembership(organization_id=uuid.uuid4(), membership_id=uuid.uuid4())
    session.add(organization_membership)
    session.commit()
    assert organization_membership.organization_id is not None


# Test for the OrganizationPost class
def test_organization_post_create(session):
    organization_post = OrganizationPost(organization_id=uuid.uuid4(), post_str=uuid.uuid4())
    session.add(organization_post)
    session.commit()
    assert organization_post.organization_id is not None
    assert organization_post.post_str is not None


# Test for the OrganizationSubOrganization class
def test_organization_sub_organization_create(session):
    organization_sub_organization = OrganizationSubOrganization(organization_id=uuid.uuid4(), sub_organization_id=uuid.uuid4())
    session.add(organization_sub_organization)
    session.commit()
    assert organization_sub_organization.organization_id is not None


# Test for the OrganizationKeyword class
def test_organization_keyword_create(session):
    organization_keyword = OrganizationKeyword(organization_id=uuid.uuid4(), keyword=uuid.uuid4())
    session.add(organization_keyword)
    session.commit()
    assert organization_keyword.organization_id is not None


# Test for the PaperOriginatorPersonLink class
def test_paper_originator_person_link_create(session):
    paper_originator_person_link = PaperOriginatorPersonLink(paper_id=uuid.uuid4(), person_id=uuid.uuid4())
    session.add(paper_originator_person_link)
    session.commit()
    assert paper_originator_person_link.paper_id is not None
