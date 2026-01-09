from core.model.data_models import (
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
    Paper,
    PaperDirectionLink,
    PaperFileLink,
    PaperLocationLink,
    PaperOriginatorPersonLink,
    PaperRelatedPaper,
    PaperSubordinatedLink,
    PaperSuperordinatedLink,
    Person,
    PersonKeywordLink,
    PersonMembershipLink,
    Post,
    System,
)
from sqlmodel import select


# Test for the System class
def test_system_create(session, system):
    # Fetch system from DB with query
    statement = select(System).where(System.id == system.id)
    db_system = session.exec(statement).one()

    # Check for equality
    assert db_system.id == system.id
    assert db_system.name == system.name
    assert db_system.oparlVersion == system.oparlVersion
    assert db_system.created == system.created
    assert db_system.modified == system.modified


# Test for the MembershipKeyword class
# ----------------------
# MembershipKeyword
# ----------------------
def test_membership_keyword_create(session, membership, keyword):
    membership_keyword = MembershipKeyword(membership_id=membership.db_id, keyword_id=keyword.db_id)
    session.add(membership_keyword)
    session.commit()

    db_link = session.exec(select(MembershipKeyword).where(MembershipKeyword.membership_id == membership_keyword.membership_id)).one()
    assert db_link.membership_id == membership.db_id
    assert db_link.keyword_id == keyword.db_id


def test_meeting_aux_file_link_create(session, meeting, file):
    meeting_aux_file_link = FileMeetingLink(
        meeting_id=meeting.db_id,
        file_id=file.db_id,
    )
    session.add(meeting_aux_file_link)
    session.commit()

    statement = select(FileMeetingLink).where(FileMeetingLink.meeting_id == meeting.db_id)
    obj = session.exec(statement).one()

    assert obj.meeting_id == meeting.db_id
    assert obj.file_id == file.db_id


def test_location_bodies_create(session, location, body):
    location_bodies = LocationBodies(
        location_id=location.db_id,
        body_id=body.db_id,
    )
    session.add(location_bodies)
    session.commit()

    statement = select(LocationBodies).where(LocationBodies.location_id == location.db_id)
    obj = session.exec(statement).one()

    assert obj.location_id == location.db_id
    assert obj.body_id == body.db_id


def test_location_organizations_create(session, location, organization):
    location_organizations = LocationOrganizations(
        location_id=location.db_id,
        organization_id=organization.db_id,
    )
    session.add(location_organizations)
    session.commit()

    statement = select(LocationOrganizations).where(LocationOrganizations.location_id == location.db_id)
    obj = session.exec(statement).one()

    assert obj.location_id == location.db_id
    assert obj.organization_id == organization.db_id


def test_location_persons_create(session, location, person):
    location_persons = LocationPersons(
        location_id=location.db_id,
        person_id=person.db_id,
    )
    session.add(location_persons)
    session.commit()

    statement = select(LocationPersons).where(LocationPersons.location_id == location.db_id)
    obj = session.exec(statement).one()

    assert obj.location_id == location.db_id
    assert obj.person_id == person.db_id


def test_location_meetings_create(session, location, meeting):
    location_meetings = LocationMeetings(
        location_id=location.db_id,
        meeting_id=meeting.db_id,
    )
    session.add(location_meetings)
    session.commit()

    statement = select(LocationMeetings).where(LocationMeetings.location_id == location.db_id)
    obj = session.exec(statement).one()

    assert obj.location_id == location.db_id
    assert obj.meeting_id == meeting.db_id


def test_location_papers_create(session, location, paper):
    location_papers = LocationPapers(
        location_id=location.db_id,
        paper_id=paper.db_id,
    )
    session.add(location_papers)
    session.commit()

    statement = select(LocationPapers).where(LocationPapers.location_id == location.db_id)
    obj = session.exec(statement).one()

    assert obj.location_id == location.db_id
    assert obj.paper_id == paper.db_id


def test_location_keyword_create(session, location, keyword):
    location_keyword = LocationKeyword(
        location_id=location.db_id,
        keyword=keyword.db_id,
    )
    session.add(location_keyword)
    session.commit()

    statement = select(LocationKeyword).where(LocationKeyword.location_id == location.db_id)
    obj = session.exec(statement).one()

    assert obj.location_id == location.db_id
    assert obj.keyword == keyword.db_id


def test_organization_membership_create(session, organization, membership):
    organization_membership = OrganizationMembership(
        organization_id=organization.db_id,
        membership_id=membership.db_id,
    )
    session.add(organization_membership)
    session.commit()

    statement = select(OrganizationMembership).where(OrganizationMembership.organization_id == organization.db_id)
    obj = session.exec(statement).one()

    assert obj.organization_id == organization.db_id
    assert obj.membership_id == membership.db_id


def test_organization_post_create(session, organization, post):
    organization_post = OrganizationPost(
        organization_id=organization.db_id,
        post_str=post.db_id,
    )
    session.add(organization_post)
    session.commit()

    statement = select(OrganizationPost).where(OrganizationPost.organization_id == organization.db_id)
    obj = session.exec(statement).one()

    assert obj.organization_id == organization.db_id
    assert obj.post_str == post.db_id


def test_organization_sub_organization_create(session, organization):
    organization_sub_organization = OrganizationSubOrganization(
        organization_id=organization.db_id,
        sub_organization_id=organization.db_id,
    )
    session.add(organization_sub_organization)
    session.commit()

    statement = select(OrganizationSubOrganization).where(OrganizationSubOrganization.organization_id == organization.db_id)
    obj = session.exec(statement).one()

    assert obj.organization_id == organization.db_id
    assert obj.sub_organization_id == organization.db_id


def test_organization_keyword_create(session, organization, keyword):
    organization_keyword = OrganizationKeyword(
        organization_id=organization.db_id,
        keyword=keyword.db_id,
    )
    session.add(organization_keyword)
    session.commit()

    statement = select(OrganizationKeyword).where(OrganizationKeyword.organization_id == organization.db_id)
    obj = session.exec(statement).one()

    assert obj.organization_id == organization.db_id
    assert obj.keyword == keyword.db_id


def test_paper_originator_person_link_create(session, paper, person):
    paper_originator_person_link = PaperOriginatorPersonLink(
        paper_id=paper.db_id,
        person_id=person.db_id,
    )
    session.add(paper_originator_person_link)
    session.commit()

    statement = select(PaperOriginatorPersonLink).where(PaperOriginatorPersonLink.paper_id == paper.db_id)
    obj = session.exec(statement).one()

    assert obj.paper_id == paper.db_id
    assert obj.person_id == person.db_id


# ----------------------
# ConsultationKeywordLink
# ----------------------
def test_consultation_keyword_link_create(session, consultation, keyword):
    link = ConsultationKeywordLink(consultation_id=consultation.db_id, keyword_id=keyword.db_id)
    session.add(link)
    session.commit()

    db_link = session.exec(select(ConsultationKeywordLink).where(ConsultationKeywordLink.consultation_id == link.consultation_id)).one()
    assert db_link.consultation_id == consultation.db_id
    assert db_link.keyword_id == keyword.db_id


# ----------------------
# BodyEquivalentLink
# ----------------------
def test_body_equivalent_link_create(session, body):
    link = BodyEquivalentLink(body_id_a=body.db_id, body_id_b=body.db_id)
    session.add(link)
    session.commit()

    db_link = session.exec(select(BodyEquivalentLink).where(BodyEquivalentLink.body_id_a == link.body_id_a)).one()
    assert db_link.body_id_a == body.db_id
    assert db_link.body_id_b == body.db_id


# ----------------------
# PaperRelatedPaper
# ----------------------
def test_paper_related_paper_create(session, paper):
    link = PaperRelatedPaper(from_paper_id=paper.db_id, to_paper_id=paper.db_id)
    session.add(link)
    session.commit()

    db_link = session.exec(select(PaperRelatedPaper).where(PaperRelatedPaper.from_paper_id == link.from_paper_id)).one()
    assert db_link.from_paper_id == paper.db_id
    assert db_link.to_paper_id == paper.db_id


# ----------------------
# PaperSuperordinatedLink
# ----------------------
def test_paper_superordinated_link_create(session, paper):
    link = PaperSuperordinatedLink(paper_id=paper.db_id, superordinated_paper_url=paper.db_id)
    session.add(link)
    session.commit()

    db_link = session.exec(select(PaperSuperordinatedLink).where(PaperSuperordinatedLink.paper_id == link.paper_id)).one()
    assert db_link.paper_id == paper.db_id
    assert db_link.superordinated_paper_url == paper.db_id


# ----------------------
# PaperSubordinatedLink
# ----------------------
def test_paper_subordinated_link_create(session, paper):
    link = PaperSubordinatedLink(paper_id=paper.db_id, subordinated_paper_url=paper.db_id)
    session.add(link)
    session.commit()

    db_link = session.exec(select(PaperSubordinatedLink).where(PaperSubordinatedLink.paper_id == link.paper_id)).one()
    assert db_link.paper_id == paper.db_id
    assert db_link.subordinated_paper_url == paper.db_id


# ----------------------
# PaperDirectionLink
# ----------------------
def test_paper_direction_link_create(session, paper, organization):
    link = PaperDirectionLink(paper_id=paper.db_id, direction_name=organization.db_id)
    session.add(link)
    session.commit()

    db_link = session.exec(select(PaperDirectionLink).where(PaperDirectionLink.paper_id == link.paper_id)).one()
    assert db_link.paper_id == paper.db_id
    assert db_link.direction_name == organization.db_id


# ----------------------
# PaperFileLink
# ----------------------
def test_paper_file_link_create(session, paper, file):
    link = PaperFileLink(paper_id=paper.db_id, file_id=file.db_id)
    session.add(link)
    session.commit()

    db_link = session.exec(select(PaperFileLink).where(PaperFileLink.paper_id == link.paper_id)).one()
    assert db_link.paper_id == paper.db_id
    assert db_link.file_id == file.db_id


# ----------------------
# PaperLocationLink
# ----------------------
def test_paper_location_link_create(session, paper, location):
    link = PaperLocationLink(paper_id=paper.db_id, location_id=location.db_id)
    session.add(link)
    session.commit()

    db_link = session.exec(select(PaperLocationLink).where(PaperLocationLink.paper_id == link.paper_id)).one()
    assert db_link.paper_id == paper.db_id
    assert db_link.location_id == location.db_id


# ----------------------
# FileKeywordLink
# ----------------------
def test_file_keyword_link_create(session, file, keyword):
    link = FileKeywordLink(file_id=file.db_id, keyword_id=keyword.db_id)
    session.add(link)
    session.commit()

    db_link = session.exec(select(FileKeywordLink).where(FileKeywordLink.file_id == link.file_id)).one()
    assert db_link.file_id == file.db_id
    assert db_link.keyword_id == keyword.db_id


# ----------------------
# FileAgendaItemLink
# ----------------------
def test_file_agenda_item_link_create(session, file, agenda_item):
    link = FileAgendaItemLink(file_id=file.db_id, agendaItem=agenda_item.db_id)
    session.add(link)
    session.commit()

    db_link = session.exec(select(FileAgendaItemLink).where(FileAgendaItemLink.file_id == link.file_id)).one()
    assert db_link.file_id == file.db_id
    assert db_link.agendaItem == agenda_item.db_id


# ----------------------
# FileMeetingLink
# ----------------------
def test_file_meeting_link_create(session, file, meeting):
    link = FileMeetingLink(file_id=file.db_id, meeting_id=meeting.db_id)
    session.add(link)
    session.commit()

    db_link = session.exec(select(FileMeetingLink).where(FileMeetingLink.file_id == link.file_id)).one()
    assert db_link.file_id == file.db_id
    assert db_link.meeting_id == meeting.db_id


# ----------------------
# FileDerivativeLink
# ----------------------
def test_file_derivative_link_create(session, file):
    link = FileDerivativeLink(file_id=file.db_id, derivative_file_id=file.db_id)
    session.add(link)
    session.commit()

    db_link = session.exec(select(FileDerivativeLink).where(FileDerivativeLink.file_id == link.file_id)).one()
    assert db_link.file_id == file.db_id
    assert db_link.derivative_file_id == file.db_id


# ----------------------
# LegislativeTermKeyword
# ----------------------
def test_legislative_term_keyword_create(session, legislative_term, keyword):
    link = LegislativeTermKeyword(legislative_term_id=legislative_term.db_id, keyword_id=keyword.db_id)
    session.add(link)
    session.commit()

    db_link = session.exec(
        select(LegislativeTermKeyword).where(LegislativeTermKeyword.legislative_term_id == link.legislative_term_id)
    ).one()
    assert db_link.legislative_term_id == legislative_term.db_id
    assert db_link.keyword_id == keyword.db_id


# ----------------------
# PersonMembershipLink
# ----------------------
def test_person_membership_link_create(session, person, membership):
    link = PersonMembershipLink(person_id=person.db_id, membership_id=membership.db_id)
    session.add(link)
    session.commit()

    db_link = session.exec(select(PersonMembershipLink).where(PersonMembershipLink.person_id == link.person_id)).one()
    assert db_link.person_id == person.db_id
    assert db_link.membership_id == membership.db_id


# ----------------------
# PersonKeywordLink
# ----------------------
def test_person_keyword_link_create(session, person, keyword):
    link = PersonKeywordLink(person_id=person.db_id, keyword_id=keyword.db_id)
    session.add(link)
    session.commit()

    db_link = session.exec(select(PersonKeywordLink).where(PersonKeywordLink.person_id == link.person_id)).one()
    assert db_link.person_id == person.db_id
    assert db_link.keyword_id == keyword.db_id


# ----------------------
# MeetingParticipantLink
# ----------------------
def test_meeting_participant_link_create(session, meeting, person):
    link = MeetingParticipantLink(meeting_id=meeting.db_id, person_id=person.db_id)
    session.add(link)
    session.commit()

    db_link = session.exec(select(MeetingParticipantLink).where(MeetingParticipantLink.person_id == link.person_id)).one()
    assert db_link.meeting_id == meeting.db_id
    assert db_link.person_id == person.db_id


# ----------------------
# MeetingKeywordLink
# ----------------------
def test_meeting_keyword_link_create(session, meeting, keyword):
    meeting_keyword_link = MeetingKeywordLink(
        meeting_id=meeting.db_id,
        keyword_id=keyword.db_id,
    )
    session.add(meeting_keyword_link)
    session.commit()

    obj = session.exec(select(MeetingKeywordLink).where(MeetingKeywordLink.meeting_id == meeting.db_id)).one()

    assert obj.meeting_id == meeting.db_id
    assert obj.keyword_id == keyword.db_id


# ----------------------
# Test Location
# ----------------------
def test_location_create(session, location):
    db_location = session.exec(select(Location).where(Location.db_id == location.db_id)).one()
    assert db_location.db_id == location.db_id
    assert db_location.id == location.id
    assert db_location.description == location.description
    assert db_location.created == location.created
    assert db_location.modified == location.modified
    assert db_location.web == location.web


# ----------------------
# Test Organization
# ----------------------
def test_organization_create(session, organization):
    db_org = session.exec(select(Organization).where(Organization.db_id == organization.db_id)).one()
    assert db_org.db_id == organization.db_id
    assert db_org.id == organization.id
    assert db_org.name == organization.name
    assert db_org.organizationType == organization.organizationType
    assert db_org.classification == organization.classification
    assert db_org.created == organization.created
    assert db_org.modified == organization.modified


# ----------------------
# Test Meeting
# ----------------------
def test_meeting_create(session, meeting):
    db_meeting = session.exec(select(Meeting).where(Meeting.db_id == meeting.db_id)).one()
    assert db_meeting.db_id == meeting.db_id
    assert db_meeting.id == meeting.id
    assert db_meeting.name == meeting.name
    assert db_meeting.start == meeting.start
    assert db_meeting.end == meeting.end
    assert db_meeting.created == meeting.created
    assert db_meeting.modified == meeting.modified


# ----------------------
# Test Paper
# ----------------------
def test_paper_create(session, paper):
    db_paper = session.exec(select(Paper).where(Paper.db_id == paper.db_id)).one()
    assert db_paper.db_id == paper.db_id
    assert db_paper.id == paper.id
    assert db_paper.name == paper.name
    assert db_paper.paper_type == paper.paper_type
    assert db_paper.paper_subtype == paper.paper_subtype
    assert db_paper.created == paper.created
    assert db_paper.modified == paper.modified


# ----------------------
# Test Person
# ----------------------
def test_person_create(session, person):
    db_person = session.exec(select(Person).where(Person.db_id == person.db_id)).one()
    assert db_person.db_id == person.db_id
    assert db_person.id == person.id
    assert db_person.name == person.name
    assert db_person.title == person.title
    assert db_person.created == person.created
    assert db_person.modified == person.modified


# ----------------------
# Test Membership
# ----------------------
def test_membership_create(session, membership):
    db_membership = session.exec(select(Membership).where(Membership.db_id == membership.db_id)).one()
    assert db_membership.db_id == membership.db_id
    assert db_membership.id == membership.id
    assert db_membership.role == membership.role
    assert db_membership.startDate == membership.startDate
    assert db_membership.created == membership.created
    assert db_membership.modified == membership.modified
    assert db_membership.organization == membership.organization


# ----------------------
# Test Keyword
# ----------------------
def test_keyword_create(session, keyword):
    db_keyword = session.exec(select(Keyword).where(Keyword.db_id == keyword.db_id)).one()
    assert db_keyword.db_id == keyword.db_id
    assert db_keyword.name == keyword.name


# ----------------------
# Test File
# ----------------------
def test_file_create(session, file):
    db_file = session.exec(select(File).where(File.db_id == file.db_id)).one()
    assert db_file.db_id == file.db_id
    assert db_file.id == file.id
    assert db_file.name == file.name
    assert db_file.accessUrl == file.accessUrl
    assert db_file.created == file.created
    assert db_file.modified == file.modified


# ----------------------
# Test AgendaItem
# ----------------------
def test_agenda_item_create(session, agenda_item):
    db_agenda_item = session.exec(select(AgendaItem).where(AgendaItem.db_id == agenda_item.db_id)).one()
    assert db_agenda_item.db_id == agenda_item.db_id
    assert db_agenda_item.id == agenda_item.id
    assert db_agenda_item.name == agenda_item.name
    assert db_agenda_item.meeting == agenda_item.meeting
    assert db_agenda_item.number == agenda_item.number
    assert db_agenda_item.order == agenda_item.order
    assert db_agenda_item.type == agenda_item.type
    assert db_agenda_item.public == agenda_item.public
    assert db_agenda_item.result == agenda_item.result
    assert db_agenda_item.resolutionText == agenda_item.resolutionText
    assert db_agenda_item.resolutionFile == agenda_item.resolutionFile
    assert db_agenda_item.start == agenda_item.start
    assert db_agenda_item.end == agenda_item.end
    assert db_agenda_item.license == agenda_item.license
    assert db_agenda_item.created == agenda_item.created
    assert db_agenda_item.modified == agenda_item.modified
    assert db_agenda_item.web == agenda_item.web
    assert db_agenda_item.deleted == agenda_item.deleted


# ----------------------
# Test LegislativeTerm
# ----------------------
def test_legislative_term_create(session, legislative_term):
    db_term = session.exec(select(LegislativeTerm).where(LegislativeTerm.db_id == legislative_term.db_id)).one()
    assert db_term.db_id == legislative_term.db_id
    assert db_term.id == legislative_term.id
    assert db_term.name == legislative_term.name
    assert db_term.created == legislative_term.created
    assert db_term.modified == legislative_term.modified


# ----------------------
# Test Consultation
# ----------------------
def test_consultation_create(session, consultation):
    db_consult = session.exec(select(Consultation).where(Consultation.db_id == consultation.db_id)).one()
    assert db_consult.db_id == consultation.db_id
    assert db_consult.id == consultation.id
    assert db_consult.url == consultation.url
    assert db_consult.created == consultation.created
    assert db_consult.modified == consultation.modified


# ----------------------
# Test Body
# ----------------------
def test_body_create(session, body):
    db_body = session.exec(select(Body).where(Body.db_id == body.db_id)).one()
    assert db_body.db_id == body.db_id
    assert db_body.id == body.id
    assert db_body.name == body.name
    assert db_body.organization == body.organization
    assert db_body.person == body.person
    assert db_body.meeting == body.meeting
    assert db_body.paper == body.paper
    assert db_body.legislativeTerm == body.legislativeTerm
    assert db_body.agendaItem == body.agendaItem
    assert db_body.system == body.system
    assert db_body.created == body.created
    assert db_body.modified == body.modified
    assert db_body.file == body.file
    assert db_body.legislativeTermList == body.legislativeTermList
    assert db_body.membership == body.membership


# ----------------------
# Test Post
# ----------------------
def test_post_create(session, post):
    db_post = session.exec(select(Post).where(Post.db_id == post.db_id)).one()
    assert db_post.db_id == post.db_id
    assert db_post.name == post.name
    assert db_post.organization_id == post.organization_id
