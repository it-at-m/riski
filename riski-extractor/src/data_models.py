import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel
from sqlalchemy import JSON
from sqlmodel import Column, Field, Relationship, Session, SQLModel, create_engine, select

from src.envtools import getenv_with_exception


class SYSTEM_OTHER_OPARL_VERSION(SQLModel, table=True):
    __tablename__ = "system_other_oparl_version"
    system_id: uuid.UUID = Field(foreign_key="system.db_id", primary_key=True)
    other_version_id: uuid.UUID = Field(foreign_key="system.db_id", primary_key=True)


class PaperType(SQLModel, table=True):
    __tablename__ = "paper_type"

    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(description="Designation of the paper type")

    # Relationship to subtypes
    subtypes: list["PaperSubtype"] = Relationship(back_populates="parent_type")


class PaperSubtype(SQLModel, table=True):
    __tablename__ = "paper_subtype"

    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(description="Designation of the paper subtype")

    # FK to PaperTypeEnum
    paper_type_id: uuid.UUID = Field(foreign_key="paper_type.id", description="Reference to the parent paper type")
    parent_type: PaperType = Relationship(back_populates="subtypes")


class PaperRelatedPaper(SQLModel, table=True):
    __tablename__ = "paper_related_paper"
    from_paper_id: uuid.UUID = Field(foreign_key="paper.db_id", primary_key=True)
    to_paper_id: uuid.UUID = Field(foreign_key="paper.db_id", primary_key=True)


class PaperSuperordinatedLink(SQLModel, table=True):
    __tablename__ = "paper_superordinated_paper"
    paper_id: uuid.UUID = Field(foreign_key="paper.db_id", primary_key=True)
    superordinated_paper_url: uuid.UUID = Field(description="Superordinated document", foreign_key="paper.db_id", primary_key=True)


class PaperSubordinatedLink(SQLModel, table=True):
    __tablename__ = "paper_subordinated_paper"
    paper_id: uuid.UUID = Field(foreign_key="paper.db_id", primary_key=True)
    subordinated_paper_url: uuid.UUID = Field(description="Subordinated document", foreign_key="paper.db_id", primary_key=True)


class PaperLocationLink(SQLModel, table=True):
    __tablename__ = "paper_location"
    paper_id: uuid.UUID = Field(foreign_key="paper.db_id", primary_key=True)
    location_id: uuid.UUID = Field(foreign_key="location.db_id", primary_key=True)


class PaperOriginatorPersonLink(SQLModel, table=True):
    __tablename__ = "paper_originator_person"
    paper_id: uuid.UUID = Field(foreign_key="paper.db_id", primary_key=True)
    person_id: uuid.UUID = Field(description="Name of the person", foreign_key="person.db_id", primary_key=True)


class PaperOriginatorOrgLink(SQLModel, table=True):
    __tablename__ = "paper_originator_organization"
    paper_id: uuid.UUID = Field(foreign_key="paper.db_id", primary_key=True)
    organization_id: uuid.UUID = Field(description="Name of the organization", foreign_key="organization.db_id", primary_key=True)


class PaperDirectionLink(SQLModel, table=True):
    __tablename__ = "paper_direction_link"
    paper_id: uuid.UUID = Field(foreign_key="paper.db_id", primary_key=True)
    direction_name: uuid.UUID = Field(foreign_key="organization.db_id", primary_key=True)


class PaperKeywordLink(SQLModel, table=True):
    __tablename__ = "paper_keyword"
    paper_id: uuid.UUID = Field(foreign_key="paper.db_id", primary_key=True)
    keyword: uuid.UUID = Field(foreign_key="keyword.db_id", primary_key=True)


class System(SQLModel, table=True):
    __tablename__ = "system"

    db_id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    id: str = Field(description="The unique URL of this object.")
    type: str | None = Field(
        None,
        description="The fixed type of the object: 'https://schema.oparl.org/1.1/System'.",
    )
    oparlVersion: str = Field(description="The OParl version supported by the system (e.g., 'https://schema.oparl.org/1.1/').")
    otherOparlVersions: str | None = Field(None, description="Used to specify system objects with other OParl versions.")
    license: str | None = Field(
        None,
        description="License under which the data retrievable through this API is provided, unless otherwise stated for individual objects.",
    )
    name: str | None = Field(None, description="User-friendly name for the system.")
    contactEmail: str | None = Field(None, description="Email address for inquiries about the OParl API.")
    contactName: str | None = Field(None, description="Name of the contact person.")
    website: str | None = Field(None, description="URL of the parliamentary information system's website")
    vendor: str | None = Field(None, description="URL of the software vendor's website")
    product: str | None = Field(None, description="URL for information about the used OParl server software")
    created: datetime | None = Field(None, description="Time of creation of this object.")
    modified: datetime | None = Field(None, description="Time of the last modification of this object.")
    web: str | None = Field(None, description="URL for the HTML view of this object.")
    deleted: bool | None = Field(False, description="Marks this object as deleted (true).")
    other_oparl_versions: list["System"] = Relationship(
        link_model=SYSTEM_OTHER_OPARL_VERSION,
        sa_relationship_kwargs={
            "primaryjoin": "System.db_id==SYSTEM_OTHER_OPARL_VERSION.system_id",
            "secondaryjoin": "System.db_id==SYSTEM_OTHER_OPARL_VERSION.other_version_id",
            "foreign_keys": "[SYSTEM_OTHER_OPARL_VERSION.system_id, SYSTEM_OTHER_OPARL_VERSION.other_version_id]",
        },
    )
    bodies: list["Body"] = Relationship(back_populates="system_link")


class LocationBodies(SQLModel, table=True):
    __tablename__ = "location_bodies"
    location_id: uuid.UUID = Field(foreign_key="location.db_id", primary_key=True)
    body_id: uuid.UUID = Field(foreign_key="body.db_id", primary_key=True)


class LocationOrganizations(SQLModel, table=True):
    __tablename__ = "location_organizations"
    location_id: uuid.UUID = Field(foreign_key="location.db_id", primary_key=True)
    organization_id: uuid.UUID = Field(foreign_key="organization.db_id", primary_key=True)


class LocationPersons(SQLModel, table=True):
    __tablename__ = "location_persons"
    location_id: uuid.UUID = Field(foreign_key="location.db_id", primary_key=True)
    person_id: uuid.UUID = Field(foreign_key="person.db_id", primary_key=True)


class LocationMeetings(SQLModel, table=True):
    __tablename__ = "location_meetings"
    location_id: uuid.UUID = Field(foreign_key="location.db_id", primary_key=True)
    meeting_id: uuid.UUID = Field(foreign_key="meeting.db_id", primary_key=True)


class LocationPapers(SQLModel, table=True):
    __tablename__ = "location_papers"
    location_id: uuid.UUID = Field(foreign_key="location.db_id", primary_key=True)
    paper_id: uuid.UUID = Field(foreign_key="paper.db_id", primary_key=True)


class LocationKeyword(SQLModel, table=True):
    __tablename__ = "location_keyword"
    location_id: uuid.UUID = Field(foreign_key="location.db_id", primary_key=True)
    keyword: uuid.UUID = Field(foreign_key="keyword.db_id", primary_key=True)


class Location(SQLModel, table=True):
    __tablename__ = "location"
    db_id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    id: str = Field(description="The unique URL of the location.")
    type: str | None = Field(None, description="Type of the location")
    description: str | None = Field(None, description="Textual description of a location, e.g., in the form of an address.")
    geojson: dict | None = Field(
        default=None,
        sa_column=Column(JSON),
        description="Geodata representation of the location as a GeoJSON feature object.",
    )
    streetAddress: str | None = Field(None, description="Street and house number of the address.")
    room: str | None = Field(None, description="Room specification of the address.")
    postalCode: str | None = Field(None, description="Postal code of the address.")
    subLocality: str | None = Field(
        None, description="Subordinate locality specification of the address, e.g., district, locality, or village."
    )
    locality: str | None = Field(None, description="Locality specification of the address.")
    license: str | None = Field(None, description="License for the provided information.")
    created: datetime | None = Field(None, description="Time of creation.")
    modified: datetime | None = Field(None, description="Last modification.")
    web: str | None = Field(None, description="HTML view of the object.")
    deleted: bool | None = Field(False, description="Marks this object as deleted (true).")
    # Relationships
    bodies: list["Body"] = Relationship(link_model=LocationBodies)
    organizations: list["Organization"] = Relationship(link_model=LocationOrganizations)
    persons: list["Person"] = Relationship(link_model=LocationPersons)
    meetings: list["Meeting"] = Relationship(link_model=LocationMeetings)
    papers: list["Paper"] = Relationship(back_populates="locations", link_model=PaperLocationLink)
    keywords: list["Keyword"] = Relationship(back_populates="locations", link_model=LocationKeyword)


class LegislativeTermKeyword(SQLModel, table=True):
    __tablename__ = "legislative_term_keyword"
    legislative_term_id: uuid.UUID = Field(
        foreign_key="legislative_term.db_id", primary_key=True, description="URL of the associated LegislativeTerm"
    )
    keyword: uuid.UUID = Field(foreign_key="keyword.db_id", primary_key=True, description="Associated keyword")


class LegislativeTerm(SQLModel, table=True):
    __tablename__ = "legislative_term"
    db_id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    id: str = Field(description="Unique URL of the legislative term.")
    type: str | None = Field(None, description="Type of the object: 'https://schema.oparl.org/1.1/LegislativeTerm'.")
    body: str | None = Field(None, description="Reference to the body to which the legislative term belongs.")
    name: str | None = Field(None, description="Designation of the legislative term.")
    startDate: datetime | None = Field(None, description="Start date of the legislative term.")
    endDate: datetime | None = Field(None, description="End date of the legislative term.")
    license: str | None = Field(None, description="License for the provided information.")
    created: datetime | None = Field(None, description="Time of creation.")
    modified: datetime | None = Field(None, description="Last modification.")
    web: str | None = Field(None, description="HTML view of the object.")
    deleted: bool | None = Field(False, description="Marks this object as deleted (true).")
    keywords: list["Keyword"] = Relationship(back_populates="legislative_term", link_model=LegislativeTermKeyword)


class OrganizationType(SQLModel, table=True):
    __tablename__ = "organization_type"
    db_id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(description="Name of the organization type")
    description: str | None = Field(None, description="Description of the type")
    organizations: list["Organization"] = Relationship(back_populates="organizationType")


class OrganizationMembership(SQLModel, table=True):
    __tablename__ = "organization_membership"
    organization_id: uuid.UUID = Field(foreign_key="organization.db_id", primary_key=True)
    membership_id: uuid.UUID = Field(foreign_key="membership.db_id", primary_key=True)


class OrganizationPost(SQLModel, table=True):
    __tablename__ = "organization_post"
    organization_id: uuid.UUID = Field(foreign_key="organization.db_id", primary_key=True)
    post_str: uuid.UUID = Field(foreign_key="post.db_id", primary_key=True)


class OrganizationSubOrganization(SQLModel, table=True):
    __tablename__ = "organization_sub_organization"
    organization_id: uuid.UUID = Field(foreign_key="organization.db_id", primary_key=True)
    sub_organization_id: uuid.UUID = Field(foreign_key="organization.db_id", primary_key=True)


class OrganizationKeyword(SQLModel, table=True):
    __tablename__ = "organization_keyword"
    organization_id: uuid.UUID = Field(foreign_key="organization.db_id", primary_key=True)
    keyword: uuid.UUID = Field(foreign_key="keyword.db_id", primary_key=True)


class Post(SQLModel, table=True):
    __tablename__ = "post"

    db_id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(description="Unique URL of the post.")
    organization_id: Optional[uuid.UUID] = Field(default=None, foreign_key="organization.db_id")
    organizations: list["Organization"] = Relationship(back_populates="post", link_model=OrganizationPost)


class MeetingOrganizationLink(SQLModel, table=True):
    __tablename__ = "meeting_organization"
    meeting_id: uuid.UUID = Field(foreign_key="meeting.db_id", primary_key=True)
    organization_id: uuid.UUID = Field(foreign_key="organization.db_id", primary_key=True)


class Organization(SQLModel, table=True):
    __tablename__ = "organization"
    db_id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    id: str = Field(description="Unique URL of the organization.")
    type: str | None = Field(None, description="Type of the object: 'https://schema.oparl.org/1.1/Organization'.")
    body: str | None = Field(None, description="Reference to the body to which the organization belongs.")
    name: str | None = Field(None, description="Designation of the organization.")
    meeting_id: uuid.UUID | None = Field(None, description="list of meetings of this organization.", foreign_key="meeting.db_id")
    shortName: str | None = Field(None, description="Abbreviation of the organization.")
    subOrganizationOf: uuid.UUID | None = Field(default=None, foreign_key="organization.db_id", description="FK to the parent organization")
    classification: str | None = Field(None, description="Classification, e.g., statutory, voluntary.")
    startDate: datetime | None = Field(None, description="Start date of the organization.")
    endDate: datetime | None = Field(None, description="End date of the organization.")
    website: str | None = Field(None, description="Website of the organization.")
    location: uuid.UUID | None = Field(None, description="Location where the organization is based.", foreign_key="location.db_id")
    externalBody: str | None = Field(None, description="Reference to an external body (only for imports).")
    license: str | None = Field(None, description="License for the published data.")
    created: datetime | None = Field(None, description="Time of creation.")
    modified: datetime | None = Field(None, description="Last modification.")
    web: str | None = Field(None, description="HTML view of the organization.")
    deleted: bool | None = Field(False, description="Marks this object as deleted (true).")
    membership: list["Membership"] = Relationship(link_model=OrganizationMembership)
    post: list["Post"] = Relationship(back_populates="organizations", link_model=OrganizationPost)
    # Relationships
    parentOrganization: Optional["Organization"] = Relationship(
        back_populates="subOrganizations", sa_relationship_kwargs={"remote_side": "Organization.db_id"}
    )
    subOrganizations: list["Organization"] = Relationship(back_populates="parentOrganization")
    keywords: list["Keyword"] = Relationship(back_populates="organizations", link_model=OrganizationKeyword)
    organization_type_id: Optional[uuid.UUID] = Field(foreign_key="organization_type.db_id")
    organizationType: OrganizationType = Relationship(back_populates="organizations")
    papers: list["Paper"] = Relationship(back_populates="originator_orgs", link_model=PaperOriginatorOrgLink)
    directed_papers: list["Paper"] = Relationship(back_populates="under_direction_of", link_model=PaperDirectionLink)
    meetings: list["Meeting"] = Relationship(back_populates="organizations", link_model=MeetingOrganizationLink)


class Title(SQLModel, table=True):
    __tablename__ = "title"
    db_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    title: str = Field()


class PersonMembershipLink(SQLModel, table=True):
    __tablename__ = "person_membership"
    person_id: uuid.UUID = Field(foreign_key="person.db_id", primary_key=True)
    membership_id: uuid.UUID = Field(foreign_key="membership.db_id", primary_key=True)


class PersonKeywordLink(SQLModel, table=True):
    __tablename__ = "person_keyword"
    person_id: uuid.UUID = Field(foreign_key="person.db_id", primary_key=True)
    keyword: uuid.UUID = Field(foreign_key="keyword.db_id", primary_key=True)


class MeetingParticipantLink(SQLModel, table=True):
    """Mapping Meeting <-> Participants (Persons)"""

    __tablename__ = "meeting_participant"
    meeting_id: uuid.UUID = Field(foreign_key="meeting.db_id", primary_key=True)
    person_id: uuid.UUID = Field(foreign_key="person.db_id", description="Name or ID of the person", primary_key=True)


class Person(SQLModel, table=True):
    __tablename__ = "person"

    db_id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    id: str = Field(description="Unique URL of the person.")
    type: str | None = Field(None, description="Type of the object")
    body: str | None = Field(None, description="Body")
    name: str | None = Field(None, description="Full name")
    familyName: str | None = Field(None, description="Family name")
    givenName: str | None = Field(None, description="First name")
    formOfAddress: str | None = Field(None, description="Salutation")
    affix: str | None = Field(None, description="Name addition")
    gender: str | None = Field(None, description="Gender")
    location: uuid.UUID | None = Field(foreign_key="location.db_id", description="Location")
    life: str | None = Field(None, description="Life dates")
    lifeSource: str | None = Field(None, description="Source of life dates")
    license: str | None = Field(None, description="License")
    created: datetime | None = Field(None, description="Time of creation")
    modified: datetime | None = Field(None, description="Last modification")
    web: str | None = Field(None, description="HTML view of the person")
    deleted: bool = Field(default=False, description="Marked as deleted")

    title: uuid.UUID | None = Field(default=None, foreign_key="title.db_id")
    phone: list[str] = Field(sa_column=Column(JSON), default=[])
    email: list[str] = Field(sa_column=Column(JSON), default=[])

    status: list[str] = Field(sa_column=Column(JSON), default=[])

    keywords: list["Keyword"] = Relationship(
        back_populates="persons",
        link_model=PersonKeywordLink,
    )

    membership: list["Membership"] = Relationship(back_populates="person", link_model=PersonMembershipLink)
    papers: list["Paper"] = Relationship(back_populates="originator_persons", link_model=PaperOriginatorPersonLink)
    meetings: list["Meeting"] = Relationship(back_populates="participants", link_model=MeetingParticipantLink)
    title_obj: Optional["Title"] = Relationship()


class MembershipKeyword(SQLModel, table=True):
    __tablename__ = "membership_keyword"
    membership_id: uuid.UUID = Field(foreign_key="membership.db_id", primary_key=True)
    keyword: uuid.UUID = Field(foreign_key="keyword.db_id", primary_key=True)


class Membership(SQLModel, table=True):
    __tablename__ = "membership"
    db_id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    id: str = Field(description="Unique URL of the membership.")
    type: str | None = Field(None, description="Type of the membership")
    organization: uuid.UUID | None = Field(
        None, description="The grouping in which the person is or was a member.", foreign_key="organization.db_id"
    )
    role: str | None = Field(
        None,
        description="Role of the person for the grouping. Can be used to distinguish between different types of memberships, e.g., in committees.",
    )
    votingRight: bool | None = Field(None, description="Indicates whether the person is a voting member in the grouping.")
    startDate: datetime | None = Field(None, description="Date when the membership starts.")
    endDate: datetime | None = Field(None, description="Date when the membership ends.")
    onBehalfOf: str | None = Field(
        None,
        description="The grouping for which the person sits in the organization specified under organization. Example: Membership as a representative of a parliamentary faction, grouping, or external organization.",
    )
    license: str | None = Field(None, description="License for the published data.")
    created: datetime | None = Field(None, description="Time of creation.")
    modified: datetime | None = Field(None, description="Last modification.")
    web: str | None = Field(None, description="HTML view of the person.")
    deleted: bool | None = Field(False, description="Marks this object as deleted (true).")
    keywords: list["Keyword"] = Relationship(back_populates="memberships", link_model=MembershipKeyword)
    organizations: Organization = Relationship(link_model=OrganizationMembership)
    person: list["Person"] = Relationship(back_populates="membership", link_model=PersonMembershipLink)


class FileDerivativeLink(SQLModel, table=True):
    __tablename__ = "file_derivative_link"
    file_id: uuid.UUID = Field(foreign_key="file.db_id", primary_key=True)
    derivative_file_id: uuid.UUID = Field(foreign_key="file.db_id", primary_key=True)


class FileMeetingLink(SQLModel, table=True):
    __tablename__ = "file_meeting"
    file_id: uuid.UUID = Field(foreign_key="file.db_id", primary_key=True)
    meeting_id: uuid.UUID = Field(foreign_key="meeting.db_id", primary_key=True)


class FileAgendaItemLink(SQLModel, table=True):
    __tablename__ = "file_agenda"
    file_id: uuid.UUID = Field(foreign_key="file.db_id", primary_key=True)
    agendaItem: uuid.UUID = Field(foreign_key="agenda_item.db_id", primary_key=True)


class FilePaperLink(SQLModel, table=True):
    __tablename__ = "file_paper"
    file_id: uuid.UUID = Field(foreign_key="file.db_id", primary_key=True)
    paper_id: uuid.UUID = Field(foreign_key="paper.db_id", primary_key=True)


class FileKeywordLink(SQLModel, table=True):
    __tablename__ = "file_keyword"
    file_id: uuid.UUID = Field(foreign_key="file.db_id", primary_key=True)
    keyword: uuid.UUID = Field(foreign_key="keyword.db_id", primary_key=True)


class PaperFileLink(SQLModel, table=True):
    __tablename__ = "paper_file"
    paper_id: uuid.UUID = Field(foreign_key="paper.db_id", primary_key=True)
    file_id: uuid.UUID = Field(foreign_key="file.db_id", primary_key=True)


class File(SQLModel, table=True):
    __tablename__ = "file"
    db_id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    id: str = Field(description="Unique URL of the document.")
    type: str | None = Field(None, description="Type of the file")
    name: str | None = Field(None, description="User-friendly name for the object. Should not contain file extensions like '.pdf'.")
    fileName: str | None = Field(
        None,
        description="Filename under which the file can be saved in a file system (e.g., 'aFile.pdf'). Clients should ensure that this name meets local file system requirements.",
    )
    mimeType: str | None = Field(None, description="MIME type of the file")
    date: datetime | None = Field(None, description="Date used as a reference point for deadlines, etc.")
    size: int | None = Field(None, description="Size of the file in bytes")
    sha1Checksum: str | None = Field(
        None,
        description="[Deprecated] SHA1 checksum of the file content in hexadecimal notation. Should not be used anymore as SHA1 is considered insecure. Instead, sha512Checksum should be used.",
    )
    sha512Checksum: str | None = Field(None, description="SHA512 checksum of the file content in hexadecimal notation.")
    text: str | None = Field(None, description="Plain text representation of the file content, if it can be represented in text form.")
    accessUrl: str = Field(description="Mandatory URL for public access to the file.")
    downloadUrl: str | None = Field(None, description="URL for downloading the file.")
    externalServiceUrl: str | None = Field(
        None, description="External URL that provides additional access options (e.g., a YouTube video)."
    )
    masterFile: str | None = Field(None, description="File from which the current object is derived.")
    fileLicense: str | None = Field(
        None,
        description="License under which the file is offered. If this property is not used, the value of license or the license of a parent object is decisive.",
    )
    license: str | None = Field(None, description="License for the published data.")

    created: datetime | None = Field(None, description="Time of creation.")
    modified: datetime | None = Field(None, description="Last modification.")
    web: str | None = Field(None, description="HTML view of the person.")
    deleted: bool | None = Field(False, description="Marks this object as deleted (true).")
    derivative_files: list["File"] = Relationship(
        link_model=FileDerivativeLink,
        sa_relationship_kwargs={
            "primaryjoin": "File.db_id==FileDerivativeLink.file_id",
            "secondaryjoin": "File.db_id==FileDerivativeLink.derivative_file_id",
            "foreign_keys": [FileDerivativeLink.file_id, FileDerivativeLink.derivative_file_id],
        },
    )
    meetings: list["Meeting"] = Relationship(back_populates="auxiliary_files", link_model=FileMeetingLink)
    agendaItem: list["AgendaItem"] = Relationship(back_populates="auxiliaryFile", link_model=FileAgendaItemLink)
    paper: list["Paper"] = Relationship(back_populates="auxiliary_files", link_model=FilePaperLink)
    keywords: list["Keyword"] = Relationship(back_populates="files", link_model=FileKeywordLink)
    papers: list["Paper"] = Relationship(back_populates="auxiliary_files", link_model=PaperFileLink)


class AgendaItemKeywordLink(SQLModel, table=True):
    __tablename__ = "agendaitem_keyword"
    agendaitem_id: uuid.UUID = Field(foreign_key="agenda_item.db_id", primary_key=True)
    keyword: uuid.UUID = Field(foreign_key="keyword.db_id", primary_key=True)


class MeetingAgendaItemLink(SQLModel, table=True):
    """Mapping Meeting <-> AgendaItems (Order is relevant)"""

    __tablename__ = "meeting_agenda_item"
    meeting_id: uuid.UUID = Field(foreign_key="meeting.db_id", primary_key=True)
    agenda_item_id: uuid.UUID = Field(foreign_key="agenda_item.db_id", primary_key=True)


class AgendaItem(SQLModel, table=True):
    __tablename__ = "agenda_item"
    db_id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    id: str = Field(description="Unique URL of the agenda item.")
    type: str | None = Field(None, description="Type of the agenda item")
    meeting: uuid.UUID | None = Field(
        None,
        description="Reference to the meeting, which must only be output if the AgendaItem object is retrieved individually.",
        foreign_key="meeting.db_id",
    )
    number: str | None = Field(
        None,
        description="Outline number of the agenda item. Any string, such as '10.', '10.1', 'C', 'c)' etc.",
    )
    order: int | None = Field(
        None,
        description="The position of the agenda item in the meeting, starting from 0. This number corresponds to the position in Meeting:agendaItem.",
    )
    name: str | None = Field(None, description="The topic of the agenda item.")
    public: bool | None = Field(None, description="Indicates whether the agenda item is intended to be dealt with in a public meeting.")
    result: str | None = Field(
        None,
        description="Categorical information about the result of the discussion of the agenda item, e.g., 'Adopted unchanged' or 'Adopted with changes'.",
    )
    resolutionText: str | None = Field(None, description="Text of the resolution, if a resolution was made in this agenda item.")
    resolutionFile: uuid.UUID | None = Field(
        None,
        description="File containing the resolution, if a resolution was made in this agenda item.",
        foreign_key="file.db_id",
    )
    start: datetime | None = Field(None, description="Date and time of the start point of the agenda item.")
    end: datetime | None = Field(None, description="End point of the agenda item as date/time.")
    license: str | None = Field(None, description="License for the published data.")
    created: datetime | None = Field(None, description="Time of creation.")
    modified: datetime | None = Field(None, description="Last modification.")
    web: str | None = Field(None, description="HTML view of the person.")
    deleted: bool | None = Field(False, description="Marks this object as deleted (true).")
    auxiliaryFile: list["File"] = Relationship(back_populates="agendaItem", link_model=FileAgendaItemLink)
    keywords: list["Keyword"] = Relationship(back_populates="agenda_items", link_model=AgendaItemKeywordLink)
    meetings: list["Meeting"] = Relationship(back_populates="agenda_items", link_model=MeetingAgendaItemLink)


class Paper(SQLModel, table=True):
    __tablename__ = "paper"
    db_id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    id: str = Field(description="Unique URL of the paper.")
    type: str | None = Field(None, description="Type of the paper")
    body: str | None = Field(None, description="Body to which the paper belongs.")
    name: str | None = Field(None, description="Title of the paper.")
    reference: str | None = Field(
        None,
        description="Identifier or file number of the paper, which can be uniquely referenced in parliamentary work.",
    )
    date: datetime | None = Field(None, description="Date used as a reference point for deadlines, etc.")
    paperType: str | None = Field(None, description="Type of the document, e.g., response to a query.")
    mainFile: uuid.UUID | None = Field(
        None,
        description="The main file for this paper. Example: The paper represents a resolution proposal and the main file contains the text of the resolution proposal. Should not be output if there is no unique main file.",
        foreign_key="file.db_id",
    )
    license: str | None = Field(None, description="License for the published data.")
    created: datetime | None = Field(None, description="Time of creation.")
    modified: datetime | None = Field(None, description="Last modification.")
    web: str | None = Field(None, description="HTML view of the person.")
    deleted: bool | None = Field(False, description="Marks this object as deleted (true).")

    auxiliary_files: list["File"] = Relationship(back_populates="paper", link_model=PaperFileLink)
    related_papers: list["Paper"] = Relationship(
        back_populates="related_to",
        link_model=PaperRelatedPaper,
        sa_relationship_kwargs={
            "primaryjoin": "Paper.db_id==PaperRelatedPaper.from_paper_id",
            "secondaryjoin": "Paper.db_id==PaperRelatedPaper.to_paper_id",
            "foreign_keys": "[PaperRelatedPaper.from_paper_id, PaperRelatedPaper.to_paper_id]",
        },
    )

    related_to: list["Paper"] = Relationship(
        back_populates="related_papers",
        link_model=PaperRelatedPaper,
        sa_relationship_kwargs={
            "primaryjoin": "Paper.db_id==PaperRelatedPaper.to_paper_id",
            "secondaryjoin": "Paper.db_id==PaperRelatedPaper.from_paper_id",
            "foreign_keys": "[PaperRelatedPaper.to_paper_id, PaperRelatedPaper.from_paper_id]",
        },
    )
    super_papers: list["Paper"] = Relationship(
        back_populates="sub_papers",
        link_model=PaperSuperordinatedLink,
        sa_relationship_kwargs={
            "primaryjoin": "Paper.db_id==PaperSuperordinatedLink.paper_id",
            "secondaryjoin": "Paper.db_id==PaperSuperordinatedLink.superordinated_paper_url",
            "foreign_keys": "[PaperSuperordinatedLink.paper_id, PaperSuperordinatedLink.superordinated_paper_url]",
        },
    )
    sub_papers: list["Paper"] = Relationship(
        back_populates="super_papers",
        link_model=PaperSuperordinatedLink,
        sa_relationship_kwargs={
            "primaryjoin": "Paper.db_id==PaperSuperordinatedLink.superordinated_paper_url",
            "secondaryjoin": "Paper.db_id==PaperSuperordinatedLink.paper_id",
            "foreign_keys": "[PaperSuperordinatedLink.superordinated_paper_url, PaperSuperordinatedLink.paper_id]",
        },
    )

    locations: list["Location"] = Relationship(back_populates="papers", link_model=PaperLocationLink)
    originator_persons: list["Person"] = Relationship(back_populates="papers", link_model=PaperOriginatorPersonLink)
    originator_orgs: list["Organization"] = Relationship(back_populates="papers", link_model=PaperOriginatorOrgLink)
    under_direction_of: list["Organization"] = Relationship(back_populates="directed_papers", link_model=PaperDirectionLink)
    keywords: list["Keyword"] = Relationship(back_populates="paper", link_model=PaperKeywordLink)

    paper_type: uuid.UUID | None = Field(default=None, foreign_key="paper_type.id", description="Type of the document")

    paper_subtype: uuid.UUID | None = Field(default=None, foreign_key="paper_subtype.id", description="Subtype of the document")


class BodyEquivalentLink(SQLModel, table=True):
    __tablename__ = "equivalent_bodies"
    body_id_a: uuid.UUID = Field(foreign_key="body.db_id", primary_key=True)
    body_id_b: uuid.UUID = Field(foreign_key="body.db_id", primary_key=True)


class BodyKeywordLink(SQLModel, table=True):
    """Mapping Body <-> Keywords"""

    __tablename__ = "body_keyword"
    body_id: uuid.UUID = Field(foreign_key="body.db_id", primary_key=True)
    keyword: uuid.UUID = Field(foreign_key="keyword.db_id", primary_key=True)


class Body(SQLModel, table=True):
    __tablename__ = "body"
    db_id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    id: str = Field(description="Unique URL of the body.")
    type: str | None = Field(None, description="Type indication: 'https://schema.oparl.org/1.1/Body'.")
    name: str = Field(description="Name of the body.")
    shortName: str | None = Field(None, description="Abbreviation of the body.")
    system: str | None = Field(None, description="Reference to the associated system object.")
    website: str | None = Field(None, description="Official website of the body.")
    license: str | None = Field(None, description="Standard license for data of this body.")
    licenseValidSince: datetime | None = Field(None, description="Time since when the license is valid.")
    oparlSince: datetime | None = Field(None, description="Time since the API has been available for this body.")
    ags: str | None = Field(None, description="Official municipality key.")
    rgs: str | None = Field(None, description="Regional key.")
    contactEmail: str | None = Field(None, description="Email address of the body.")
    contactName: str | None = Field(None, description="Name of the contact person.")
    organization: str = Field(description="list of organizations of the body.")
    person: str = Field(description="list of persons of the body.")
    meeting: str = Field(description="list of meetings of the body.")
    paper: str = Field(description="list of papers of the body.")
    legislativeTerm: str = Field(description="list of legislative terms of the body.")
    agendaItem: str = Field(description="list of all agenda items of the body.")
    file: str = Field(description="list of all files of the body.")
    locationList: str | None = Field(None, description="list of locations associated with this body.")
    legislativeTermList: str = Field(description="Alternative URL to the list of legislative terms.")
    membership: str = Field(description="list of memberships in the body.")
    classification: str | None = Field(None, description="Type of the body, e.g., 'City' or 'District'.")
    location: str | None = Field(None, description="Location of the administration of this body.")
    created: datetime | None = Field(None, description="Time of creation.")
    modified: datetime | None = Field(None, description="Last modification.")
    web: str | None = Field(None, description="HTML view of the body.")
    deleted: bool | None = Field(False, description="Marks this object as deleted.")
    equivalents: list["Body"] = Relationship(
        back_populates="equivalent_to",
        link_model=BodyEquivalentLink,
        sa_relationship_kwargs={
            "primaryjoin": "Body.db_id==BodyEquivalentLink.body_id_a",
            "secondaryjoin": "Body.db_id==BodyEquivalentLink.body_id_b",
            "foreign_keys": "[BodyEquivalentLink.body_id_a, BodyEquivalentLink.body_id_b]",
        },
    )

    equivalent_to: list["Body"] = Relationship(
        back_populates="equivalents",
        link_model=BodyEquivalentLink,
        sa_relationship_kwargs={
            "primaryjoin": "Body.db_id==BodyEquivalentLink.body_id_b",
            "secondaryjoin": "Body.db_id==BodyEquivalentLink.body_id_a",
            "foreign_keys": "[BodyEquivalentLink.body_id_b, BodyEquivalentLink.body_id_a]",
        },
    )
    keywords: list["Keyword"] = Relationship(back_populates="body", link_model=BodyKeywordLink)
    system_id: Optional[uuid.UUID] = Field(default=None, foreign_key="system.db_id")
    system_link: Optional["System"] = Relationship(back_populates="bodies")


class MeetingAuxFileLink(SQLModel, table=True):
    """Mapping Meeting <-> additional files"""

    __tablename__ = "meeting_aux_file"
    meeting_id: uuid.UUID = Field(foreign_key="meeting.db_id", primary_key=True)
    file_id: uuid.UUID = Field(foreign_key="file.db_id", primary_key=True)


class MeetingKeywordLink(SQLModel, table=True):
    """Mapping Meeting <-> Keywords"""

    __tablename__ = "meeting_keyword"
    meeting_id: uuid.UUID = Field(foreign_key="meeting.db_id", primary_key=True)
    keyword: uuid.UUID = Field(foreign_key="keyword.db_id", primary_key=True)


class Meeting(SQLModel, table=True):
    __tablename__ = "meeting"
    db_id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    id: str = Field(description="Unique URL of the meeting.")
    type: str | None = Field(None, description="Type of the meeting")
    name: str | None = Field(None, description="Name of the meeting.")
    meetingState: str | None = Field(
        None,
        description="Current status of the meeting. Recommended values are 'scheduled' (planned), 'invited' (before the meeting until the protocol is released), and 'conducted' (after the protocol is released).",
    )
    cancelled: bool | None = Field(None, description="If the meeting is canceled, 'cancelled' is set to true.")
    start: datetime | None = Field(
        None,
        description="Date and time of the start point of the meeting. For a future meeting, this is the planned time; for a past meeting, it can be the actual start time.",
    )
    end: datetime | None = Field(
        None,
        description="End point of the meeting as date/time. For a future meeting, this is the planned time; for a past meeting, it can be the actual end time.",
    )
    location: uuid.UUID | None = Field(None, description="Meeting location.", foreign_key="location.db_id")

    invitation: uuid.UUID | None = Field(None, description="Invitation document for the meeting.", foreign_key="file.db_id")
    resultsProtocol: uuid.UUID | None = Field(
        None,
        description="Results protocol for the meeting. This property can only occur after the meeting has taken place.",
        foreign_key="file.db_id",
    )
    verbatimProtocol: uuid.UUID | None = Field(
        None,
        description="Verbatim protocol for the meeting. This property can only occur after the meeting has taken place.",
        foreign_key="file.db_id",
    )
    license: str | None = Field(None, description="License for the published data.")
    created: datetime | None = Field(None, description="Time of creation.")
    modified: datetime | None = Field(None, description="Last modification.")
    web: str | None = Field(None, description="HTML view of the meeting.")
    deleted: bool | None = Field(False, description="Marks this object as deleted (true).")
    organizations: list["Organization"] = Relationship(back_populates="meetings", link_model=MeetingOrganizationLink)
    participants: list["Person"] = Relationship(back_populates="meetings", link_model=MeetingParticipantLink)
    auxiliary_files: list["File"] = Relationship(back_populates="meetings", link_model=MeetingAuxFileLink)
    agenda_items: list["AgendaItem"] = Relationship(back_populates="meetings", link_model=MeetingAgendaItemLink)
    keywords: list["Keyword"] = Relationship(back_populates="meetings", link_model=MeetingKeywordLink)


class ConsultationKeywordLink(SQLModel, table=True):
    consultation_id: uuid.UUID = Field(foreign_key="consultation.db_id", primary_key=True)
    keyword_id: uuid.UUID = Field(foreign_key="keyword.db_id", primary_key=True)


class Consultation(SQLModel, table=True):
    __tablename__ = "consultation"
    db_id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    id: str = Field(default=None)
    url: str = Field(default=None, description="URL of this Consultation object")
    paper: uuid.UUID | None = Field(default=None, foreign_key="paper.db_id")
    agenda_item: uuid.UUID | None = Field(default=None, foreign_key="agenda_item.db_id")
    meeting: uuid.UUID | None = Field(default=None, foreign_key="meeting.db_id")
    authoritative: bool = Field(default=False, description="Was a resolution made?")
    role: str | None = Field(default=None, description="Function of the consultation (e.g., hearing, preliminary consultation)")
    license: str | None = Field(default=None, description="License of the data")
    created: datetime | None = Field(default=None, description="Time of creation.")
    modified: datetime | None = Field(default=None, description="Last modification.")
    web: str | None = Field(default=None, description="HTML view of the meeting.")
    keywords: list["Keyword"] = Relationship(back_populates="consultations", link_model=ConsultationKeywordLink)


class Keyword(SQLModel, table=True):
    __tablename__ = "keyword"
    db_id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str
    locations: list["Location"] = Relationship(back_populates="keywords", link_model=LocationKeyword)
    legislative_term: list["LegislativeTerm"] = Relationship(back_populates="keywords", link_model=LegislativeTermKeyword)
    agenda_items: list["AgendaItem"] = Relationship(back_populates="keywords", link_model=AgendaItemKeywordLink)
    meetings: list["Meeting"] = Relationship(back_populates="keywords", link_model=MeetingKeywordLink)
    persons: list["Person"] = Relationship(back_populates="keywords", link_model=PersonKeywordLink)
    organizations: list["Organization"] = Relationship(back_populates="keywords", link_model=OrganizationKeyword)
    files: list["File"] = Relationship(back_populates="keywords", link_model=FileKeywordLink)
    paper: list["Paper"] = Relationship(back_populates="keywords", link_model=PaperKeywordLink)
    memberships: list["Membership"] = Relationship(back_populates="keywords", link_model=MembershipKeyword)
    body: list["Body"] = Relationship(back_populates="keywords", link_model=BodyKeywordLink)
    consultations: list["Consultation"] = Relationship(back_populates="keywords", link_model=ConsultationKeywordLink)


class ExtractArtifact(BaseModel):
    meetings: list[Meeting]


##############################################
################ Enums #######################
##############################################
class OrganizationTypeEnum(str, Enum):
    COUNCIL = "City Council"
    FACTION = "Faction"
    BV = "Citizens' Assembly"
    BA = "District Committee"
    OTHER = "Other"


class PaperTypeEnum(str, Enum):
    STR_ANTRAG = "Str-Proposal"
    BA_ANTRAG = "BA-Proposal"
    SITZUNGSVORLAGE = "Meeting Template"
    BV_EMPFEHLUNG = "BV-Recommendation"
    BV_ANFRAGE = "BV-Request"


class PaperSubtypeEnum(str, Enum):
    # Subtypes for Str-Proposal
    DRINGLICHKEITSANTRAG = "Urgent Proposal"
    ANTRAG = "Proposal"
    ANFRAGE = "Request"
    AENDERUNGSANTRAG = "Amendment Proposal"

    # Subtypes for BA-Proposal
    BA_ANTRAG = "BA-Proposal"

    # Subtypes for BV-Recommendation
    BV_EMPFEHLUNG = "BV-Recommendation"

    # Subtypes for BV-Request
    BV_ANFRAGE = "BV-Request"

    # Subtypes for Meeting Template
    BESCHLUSSVORLAGE_VB = "Resolution Template VB"
    BESCHLUSSVORLAGE_SB = "Resolution Template SB"
    BESCHLUSSVORLAGE_SB_VB = "Resolution Template SB VB"
    BEKANNTGABE = "Announcement"
    DIREKT = "Direct"
    SITZUNGSVORLAGE_DA = "Meeting Template for DA"


###########################################################
#############  Create Database Schema ###################
###########################################################

_engine = None


def get_engine():
    """Lazy initialization of database engine."""
    global _engine
    if _engine is None:
        load_dotenv()
        _engine = create_engine(getenv_with_exception("DATABASE_URL"), echo=True)
    return _engine


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

    for enum_value in PaperSubtypeEnum:
        paper_subtype = PaperSubtype(name=enum_value.value)
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
