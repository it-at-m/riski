import uuid
from datetime import datetime

import pytest
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
    MeetingAuxFileLink,
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


# Erstelle eine temporäre SQLite-Datenbank für die Tests
@pytest.fixture(scope="module")
def engine():
    engine = create_engine("sqlite:///:memory:", echo=True)
    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def session(engine):
    with Session(engine) as session:
        yield session


# Test für die System-Klasse
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


# Test für die Location-Klasse
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


# Test für die Body-Klasse
def test_body_create(session):
    # Dummy System erstellen
    system = System(
        id="https://example.org/system/1",
        oparlVersion="https://schema.oparl.org/1.1/",
        name="Test System",
        created=datetime.now(),
        modified=datetime.now(),
    )
    session.add(system)
    session.commit()

    # Dummy Organization erstellen
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
    # Dummy Person erstellen
    person = Person(
        id="https://example.org/person/1",
        name="Test Person",
        title=title.db_id,  # Erforderliches Feld
        created=datetime.now(),
        modified=datetime.now(),
    )
    session.add(person)
    session.commit()

    # Dummy Meeting erstellen
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

    # Dummy Paper erstellen
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

    # Dummy Legislative Term erstellen
    legislative_term = LegislativeTerm(
        id="https://example.org/legislative_term/1",
        name="Test Legislative Term",
        created=datetime.now(),
        modified=datetime.now(),
    )
    session.add(legislative_term)
    session.commit()

    # Dummy Agenda Item erstellen
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
        accessUrl="http://example.org/file/1",  # Erforderliches Feld
        created=datetime.now(),
        modified=datetime.now(),
    )
    session.add(file)
    session.commit()

    legislative_term_list = "https://example.org/legislative_term_list"
    membership = "https://example.org/membership/1"  # Dummy-Wert als URL
    # Body-Objekt erstellen
    body = Body(
        id="https://example.org/body/1",
        name="Test Body",
        organization=str(organization.id),  # Verweis auf das Dummy-Organization als String
        person=str(person.id),  # Verweis auf das Dummy-Person als String
        meeting=str(meeting.id),  # Verweis auf das Dummy-Meeting als String
        paper=str(paper.id),  # Verweis auf das Dummy-Paper als String
        legislativeTerm=str(legislative_term.id),  # Verweis auf das Dummy-LegislativeTerm als String
        agendaItem=str(agenda_item.id),  # Verweis auf das Dummy-AgendaItem als String
        system=str(system.db_id),  # Verweis auf das Dummy-System als String
        created=datetime.now(),
        modified=datetime.now(),
        file=str(file.id),
        legislativeTermList=legislative_term_list,
        membership=membership,
    )
    session.add(body)
    session.commit()

    # Überprüfen, ob das Body-Objekt erfolgreich erstellt wurde
    assert body.db_id is not None


# Test für die Meeting-Klasse
def test_meeting_create(session):
    # Dummy Location erstellen
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
        location=location.db_id,  # Verweis auf das Dummy-Location
    )
    session.add(meeting)
    session.commit()
    assert meeting.db_id is not None


# Test für die Paper-Klasse
def test_paper_create(session):
    # Dummy PaperType und PaperSubtype erstellen
    paper_type = PaperType(name="Test Paper Type")
    paper_subtype = PaperSubtype(name="Test Paper Subtype", paper_type_id=uuid.uuid4())
    session.add(paper_type)
    session.add(paper_subtype)
    session.commit()

    paper = Paper(
        id="https://example.org/paper/1",
        name="Test Paper",
        created=datetime.now(),
        modified=datetime.now(),
        paper_type=paper_type.id,  # Verweis auf das Dummy-PaperType
        paper_subtype=paper_subtype.id,  # Verweis auf das Dummy-PaperSubtype
    )
    session.add(paper)
    session.commit()
    assert paper.db_id is not None


# Test für die Organization-Klasse
def test_organization_create(session):
    organization_type = OrganizationType(name="Test Organization Type")
    session.add(organization_type)
    session.commit()

    organization = Organization(
        id="https://example.org/organization/1",
        name="Test Organization",
        created=datetime.now(),
        modified=datetime.now(),
        organization_type_id=organization_type.db_id,  # Verweis auf das Dummy-OrganizationType
    )
    session.add(organization)
    session.commit()
    assert organization.db_id is not None


# Test für die Title-Klasse
def test_title_create(session):
    title = Title(title="Test Title")
    session.add(title)
    session.commit()
    assert title.db_id is not None


# Test für die Person-Klasse
def test_person_create(session):
    title = Title(title="Test Title")
    session.add(title)
    session.commit()

    person = Person(
        id="https://example.org/person/1",
        name="Test Person",
        created=datetime.now(),
        modified=datetime.now(),
        title=title.db_id,  # Verweis auf das Dummy-Title
    )
    session.add(person)
    session.commit()
    assert person.db_id is not None


# Test für die Membership-Klasse
def test_membership_create(session):
    organization = Organization(
        id="https://example.org/organization/1",
        name="Test Organization",
        created=datetime.now(),
        modified=datetime.now(),
        organization_type_id=uuid.uuid4(),  # Dummy Wert
    )
    session.add(organization)
    session.commit()

    membership = Membership(
        id="https://example.org/membership/1",
        role="Test Role",
        startDate=datetime.now(),
        created=datetime.now(),
        modified=datetime.now(),
        organization=organization.db_id,  # Verweis auf das Dummy-Organization
    )
    session.add(membership)
    session.commit()
    assert membership.db_id is not None


# Test für die Keyword-Klasse
def test_keyword_create(session):
    keyword = Keyword(name="Test Keyword")
    session.add(keyword)
    session.commit()
    assert keyword.db_id is not None


# Test für die File-Klasse
def test_file_create(session):
    file = File(
        id="https://example.org/file/1",
        name="Test File",
        accessUrl="http://example.org/file/1",  # Erforderliches Feld
        created=datetime.now(),
        modified=datetime.now(),
    )
    session.add(file)
    session.commit()
    assert file.db_id is not None


# Test für die AgendaItem-Klasse
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


# Test für die PaperType-Klasse
def test_paper_type_create(session):
    paper_type = PaperType(name="Test Paper Type")
    session.add(paper_type)
    session.commit()
    assert paper_type.id is not None


# Test für die PaperSubtype-Klasse
def test_paper_subtype_create(session):
    # Dummy PaperType erstellen
    paper_type = PaperType(name="Test Paper Type")
    session.add(paper_type)
    session.commit()

    paper_subtype = PaperSubtype(
        name="Test Paper Subtype",
        paper_type_id=paper_type.id,  # Verweis auf das Dummy-PaperType
    )
    session.add(paper_subtype)
    session.commit()
    assert paper_subtype.id is not None


# Test für die LegislativeTerm-Klasse
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


# Test für die OrganizationType-Klasse
def test_organization_type_create(session):
    organization_type = OrganizationType(name="Test Organization Type")
    session.add(organization_type)
    session.commit()
    assert organization_type.db_id is not None


# Test für die Consultation-Klasse
def test_consultation_create(session):
    consultation = Consultation(
        id="https://example.org/consultation/1",
        url="http://example.org/consultation/1",  # Erforderliches Feld
        created=datetime.now(),
        modified=datetime.now(),
    )
    session.add(consultation)
    session.commit()
    assert consultation.db_id is not None


# Test für die MembershipKeyword-Klasse
def test_membership_keyword_create(session):
    membership_keyword = MembershipKeyword(membership_id=uuid.uuid4(), keyword=uuid.uuid4())
    session.add(membership_keyword)
    session.commit()
    assert membership_keyword.membership_id is not None


# Test für die ConsultationKeywordLink-Klasse
def test_consultation_keyword_link_create(session):
    consultation_keyword_link = ConsultationKeywordLink(consultation_id=uuid.uuid4(), keyword_id=uuid.uuid4())
    session.add(consultation_keyword_link)
    session.commit()
    assert consultation_keyword_link.consultation_id is not None


# Test für die BodyEquivalentLink-Klasse
def test_body_equivalent_link_create(session):
    body_equivalent_link = BodyEquivalentLink(body_id_a=uuid.uuid4(), body_id_b=uuid.uuid4())
    session.add(body_equivalent_link)
    session.commit()
    assert body_equivalent_link.body_id_a is not None


# Test für die PaperRelatedPaper-Klasse
def test_paper_related_paper_create(session):
    paper_related_paper = PaperRelatedPaper(from_paper_id=uuid.uuid4(), to_paper_id=uuid.uuid4())
    session.add(paper_related_paper)
    session.commit()
    assert paper_related_paper.from_paper_id is not None


# Test für die PaperSuperordinatedLink-Klasse
def test_paper_superordinated_link_create(session):
    paper_superordinated_link = PaperSuperordinatedLink(paper_id=uuid.uuid4(), superordinated_paper_url=uuid.uuid4())
    session.add(paper_superordinated_link)
    session.commit()
    assert paper_superordinated_link.paper_id is not None


# Test für die PaperSubordinatedLink-Klasse
def test_paper_subordinated_link_create(session):
    paper_subordinated_link = PaperSubordinatedLink(paper_id=uuid.uuid4(), subordinated_paper_url=uuid.uuid4())
    session.add(paper_subordinated_link)
    session.commit()
    assert paper_subordinated_link.paper_id is not None


# Test für die PaperFileLink-Klasse
def test_paper_file_link_create(session):
    paper_file_link = PaperFileLink(paper_id=uuid.uuid4(), file_id=uuid.uuid4())
    session.add(paper_file_link)
    session.commit()
    assert paper_file_link.paper_id is not None


# Test für die PaperLocationLink-Klasse
def test_paper_location_link_create(session):
    paper_location_link = PaperLocationLink(paper_id=uuid.uuid4(), location_id=uuid.uuid4())
    session.add(paper_location_link)
    session.commit()
    assert paper_location_link.paper_id is not None


# Test für die FileKeywordLink-Klasse
def test_file_keyword_link_create(session):
    file_keyword_link = FileKeywordLink(file_id=uuid.uuid4(), keyword=uuid.uuid4())
    session.add(file_keyword_link)
    session.commit()
    assert file_keyword_link.file_id is not None


# Test für die FileAgendaItemLink-Klasse
def test_file_agenda_item_link_create(session):
    file_agenda_item_link = FileAgendaItemLink(file_id=uuid.uuid4(), agendaItem=uuid.uuid4())
    session.add(file_agenda_item_link)
    session.commit()
    assert file_agenda_item_link.file_id is not None


# Test für die FileMeetingLink-Klasse
def test_file_meeting_link_create(session):
    file_meeting_link = FileMeetingLink(file_id=uuid.uuid4(), meeting_id=uuid.uuid4())
    session.add(file_meeting_link)
    session.commit()
    assert file_meeting_link.file_id is not None


# Test für die FileDerivativeLink-Klasse
def test_file_derivative_link_create(session):
    file_derivative_link = FileDerivativeLink(file_id=uuid.uuid4(), derivative_file_id=uuid.uuid4())
    session.add(file_derivative_link)
    session.commit()
    assert file_derivative_link.file_id is not None


# Test für die LegislativeTermKeyword-Klasse
def test_legislative_term_keyword_create(session):
    legislative_term_keyword = LegislativeTermKeyword(legislative_term_id=uuid.uuid4(), keyword=uuid.uuid4())
    session.add(legislative_term_keyword)
    session.commit()
    assert legislative_term_keyword.legislative_term_id is not None


# Test für die PersonMembershipLink-Klasse
def test_person_membership_link_create(session):
    person_membership_link = PersonMembershipLink(person_id=uuid.uuid4(), membership_id=uuid.uuid4())
    session.add(person_membership_link)
    session.commit()
    assert person_membership_link.person_id is not None


# Test für die PersonKeywordLink-Klasse
def test_person_keyword_link_create(session):
    person_keyword_link = PersonKeywordLink(person_id=uuid.uuid4(), keyword=uuid.uuid4())
    session.add(person_keyword_link)
    session.commit()
    assert person_keyword_link.person_id is not None


# Test für die MeetingParticipantLink-Klasse
def test_meeting_participant_link_create(session):
    meeting_participant_link = MeetingParticipantLink(meeting_id=uuid.uuid4(), person_name=uuid.uuid4())
    session.add(meeting_participant_link)
    session.commit()
    assert meeting_participant_link.meeting_id is not None


# Test für die MeetingKeywordLink-Klasse
def test_meeting_keyword_link_create(session):
    meeting_keyword_link = MeetingKeywordLink(meeting_id=uuid.uuid4(), keyword=uuid.uuid4())
    session.add(meeting_keyword_link)
    session.commit()
    assert meeting_keyword_link.meeting_id is not None


# Test für die MeetingAuxFileLink-Klasse
def test_meeting_aux_file_link_create(session):
    meeting_aux_file_link = MeetingAuxFileLink(meeting_id=uuid.uuid4(), file_id=uuid.uuid4())
    session.add(meeting_aux_file_link)
    session.commit()
    assert meeting_aux_file_link.meeting_id is not None


# Test für die LocationBodies-Klasse
def test_location_bodies_create(session):
    location_bodies = LocationBodies(location_id=uuid.uuid4(), body_id=uuid.uuid4())
    session.add(location_bodies)
    session.commit()
    assert location_bodies.location_id is not None


# Test für die LocationOrganizations-Klasse
def test_location_organizations_create(session):
    location_organizations = LocationOrganizations(location_id=uuid.uuid4(), organization_id=uuid.uuid4())
    session.add(location_organizations)
    session.commit()
    assert location_organizations.location_id is not None


# Test für die LocationPersons-Klasse
def test_location_persons_create(session):
    location_persons = LocationPersons(location_id=uuid.uuid4(), person_id=uuid.uuid4())
    session.add(location_persons)
    session.commit()
    assert location_persons.location_id is not None


# Test für die LocationMeetings-Klasse
def test_location_meetings_create(session):
    location_meetings = LocationMeetings(location_id=uuid.uuid4(), meeting_id=uuid.uuid4())
    session.add(location_meetings)
    session.commit()
    assert location_meetings.location_id is not None


# Test für die LocationPapers-Klasse
def test_location_papers_create(session):
    location_papers = LocationPapers(location_id=uuid.uuid4(), paper_id=uuid.uuid4())
    session.add(location_papers)
    session.commit()
    assert location_papers.location_id is not None


# Test für die LocationKeyword-Klasse
def test_location_keyword_create(session):
    location_keyword = LocationKeyword(location_id=uuid.uuid4(), keyword=uuid.uuid4())
    session.add(location_keyword)
    session.commit()
    assert location_keyword.location_id is not None


# Test für die OrganizationMembership-Klasse
def test_organization_membership_create(session):
    organization_membership = OrganizationMembership(organization_id=uuid.uuid4(), membership_id=uuid.uuid4())
    session.add(organization_membership)
    session.commit()
    assert organization_membership.organization_id is not None


# Test für die OrganizationPost-Klasse
def test_organization_post_create(session):
    organization_post = OrganizationPost(organization_id=uuid.uuid4(), post_str=uuid.uuid4())
    session.add(organization_post)
    session.commit()
    assert organization_post.organization_id is not None


# Test für die OrganizationSubOrganization-Klasse
def test_organization_sub_organization_create(session):
    organization_sub_organization = OrganizationSubOrganization(organization_id=uuid.uuid4(), sub_organization_id=uuid.uuid4())
    session.add(organization_sub_organization)
    session.commit()
    assert organization_sub_organization.organization_id is not None


# Test für die OrganizationKeyword-Klasse
def test_organization_keyword_create(session):
    organization_keyword = OrganizationKeyword(organization_id=uuid.uuid4(), keyword=uuid.uuid4())
    session.add(organization_keyword)
    session.commit()
    assert organization_keyword.organization_id is not None


# Test für die PaperOriginatorPersonLink-Klasse
def test_paper_originator_person_link_create(session):
    paper_originator_person_link = PaperOriginatorPersonLink(paper_id=uuid.uuid4(), person_name=uuid.uuid4())
    session.add(paper_originator_person_link)
    session.commit()
    assert paper_originator_person_link.paper_id is not None
