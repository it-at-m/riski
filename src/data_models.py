from datetime import datetime
from enum import Enum
from typing import List, Optional

from dotenv import load_dotenv
from pydantic import BaseModel
from sqlalchemy import JSON
from sqlmodel import Column, Field, Relationship, Session, SQLModel, create_engine, select, text

from src.envtools import getenv_with_exception

load_dotenv()


class SYSTEM_OTHER_OPARL_VERSION(SQLModel, table=True, check_tables_exist=True):
    __tablename__ = "system_other_oparl_version"
    system_id: int = Field(foreign_key="system.db_id", primary_key=True)
    other_version_id: int = Field(foreign_key="system.db_id", primary_key=True)


class PaperType(SQLModel, table=True, check_tables_exist=True):
    __tablename__ = "paper_type"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(description="Bezeichnung des Paper-Typs")

    # Beziehung zu Subtypen
    subtypes: List["PaperSubtype"] = Relationship(back_populates="parent_type")


class PaperSubtype(SQLModel, table=True):
    __tablename__ = "paper_subtype"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(description="Bezeichnung des Paper-Subtyps")

    # FK auf PaperTypeEnum
    paper_type_id: int = Field(foreign_key="paper_type.id", description="Referenz auf den übergeordneten Paper-Typ")
    parent_type: PaperType = Relationship(back_populates="subtypes")


class PaperRelatedPaper(SQLModel, table=True, check_tables_exist=True):
    __tablename__ = "paper_related_paper"
    from_paper_id: int = Field(foreign_key="paper.db_id", primary_key=True)
    to_paper_id: int = Field(foreign_key="paper.db_id", primary_key=True)


class PaperSuperordinatedLink(SQLModel, table=True, check_tables_exist=True):
    __tablename__ = "paper_superordinated_paper"
    paper_id: int = Field(foreign_key="paper.db_id", primary_key=True)
    superordinated_paper_url: int = Field(description="Übergeordnete Drucksache", foreign_key="paper.db_id", primary_key=True)


class PaperSubordinatedLink(SQLModel, table=True, check_tables_exist=True):
    __tablename__ = "paper_subordinated_paper"
    paper_id: int = Field(foreign_key="paper.db_id", primary_key=True)
    subordinated_paper_url: int = Field(description="Untergeordnete Drucksache", foreign_key="paper.db_id", primary_key=True)


class PaperLocationLink(SQLModel, table=True, check_tables_exist=True):
    __tablename__ = "paper_location"
    paper_id: int = Field(foreign_key="paper.db_id", primary_key=True)
    location_id: int = Field(foreign_key="location.db_id", primary_key=True)


class PaperOriginatorPersonLink(SQLModel, table=True, check_tables_exist=True):
    __tablename__ = "paper_Originator_person"
    paper_id: int = Field(foreign_key="paper.db_id", primary_key=True)
    person_name: int = Field(description="Name der Person", foreign_key="person.db_id", primary_key=True)


class PaperOriginatorOrgLink(SQLModel, table=True, check_tables_exist=True):
    __tablename__ = "paper_originator_organization"
    paper_id: int = Field(foreign_key="paper.db_id", primary_key=True)
    organization_name: int = Field(description="Name der Organisation", foreign_key="organization.db_id", primary_key=True)


class PaperDirectionLink(SQLModel, table=True, check_tables_exist=True):
    __tablename__ = "paper_direction_link"
    paper_id: int = Field(foreign_key="paper.db_id", primary_key=True)
    direction_name: int = Field(foreign_key="organization.db_id", primary_key=True)


class PaperKeywordLink(SQLModel, table=True, check_tables_exist=True):
    __tablename__ = "paper_keyword"
    paper_id: int = Field(foreign_key="paper.db_id", primary_key=True)
    keyword: int = Field(foreign_key="keyword.db_id", primary_key=True)


class System(SQLModel, check_tables_exist=True, table=True):
    __tablename__ = "system"

    db_id: Optional[int] = Field(primary_key=True)
    id: str = Field(description="Die eindeutige URL dieses Objekts.")
    type: str | None = Field(
        None,
        description="Der feste Typ des Objekts: 'https://schema.oparl.org/1.1/System'.",
    )
    oparlVersion: str = Field(description="Die vom System unterstützte OParl-Version (z. B. 'https://schema.oparl.org/1.1/').")
    otherOparlVersions: str | None = Field(None, description="Dient der Angabe von System-Objekten mit anderen OParl-Versionen.")
    license: str | None = Field(
        None, description="Lizenz, unter der durch diese API abrufbaren Daten stehen, sofern nicht am einzelnen Objekt anders angegeben."
    )
    body: str = Field(description="Link zur Objektliste mit allen Körperschaften, die auf dem System existieren.")
    name: str | None = Field(None, description="Benutzerfreundlicher Name für das System.")
    contactEmail: str | None = Field(None, description="E-Mail-Adresse für Anfragen zur OParl-API.")
    contactName: str | None = Field(None, description="Name der Ansprechpartnerin bzw. des Ansprechpartners.")
    website: str | None = Field(None, description="URL der Website des parlamentarischen Informationssystems")
    vendor: str | None = Field(None, description="URL der Website des Softwareanbieters")
    product: str | None = Field(None, description="URL zu Informationen über die verwendete OParl-Server-Software")
    created: datetime | None = Field(None, description="Zeitpunkt der Erstellung dieses Objekts.")
    modified: datetime | None = Field(None, description="Zeitpunkt der letzten Änderung dieses Objekts.")
    web: str | None = Field(None, description="URL zur HTML-Ansicht dieses Objekts.")
    deleted: bool | None = Field(False, description="Markiert dieses Objekt als gelöscht (true).")
    other_oparl_versions: List["System"] = Relationship(
        link_model=SYSTEM_OTHER_OPARL_VERSION,
        sa_relationship_kwargs={
            "primaryjoin": "System.db_id==SYSTEM_OTHER_OPARL_VERSION.system_id",
            "secondaryjoin": "System.db_id==SYSTEM_OTHER_OPARL_VERSION.other_version_id",
            "foreign_keys": "[SYSTEM_OTHER_OPARL_VERSION.system_id, SYSTEM_OTHER_OPARL_VERSION.other_version_id]",
        },
    )


class LocationBodies(SQLModel, table=True, check_tables_exist=True):
    __tablename__ = "location_bodies"
    location_id: int = Field(foreign_key="location.db_id", primary_key=True)
    body_id: int = Field(foreign_key="body.db_id", primary_key=True)


class LocationOrganizations(SQLModel, table=True, check_tables_exist=True):
    __tablename__ = "location_organizations"
    location_id: int = Field(foreign_key="location.db_id", primary_key=True)
    organization_id: int = Field(foreign_key="organization.db_id", primary_key=True)


class LocationPersons(SQLModel, table=True, check_tables_exist=True):
    __tablename__ = "location_persons"
    location_id: int = Field(foreign_key="location.db_id", primary_key=True)
    person_id: int = Field(foreign_key="person.db_id", primary_key=True)


class LocationMeetings(SQLModel, table=True, check_tables_exist=True):
    __tablename__ = "location_meetings"
    location_id: int = Field(foreign_key="location.db_id", primary_key=True)
    meeting_id: int = Field(foreign_key="meeting.db_id", primary_key=True)


class LocationPapers(SQLModel, table=True, check_tables_exist=True):
    __tablename__ = "location_papers"
    location_id: int = Field(foreign_key="location.db_id", primary_key=True)
    paper_id: int = Field(foreign_key="paper.db_id", primary_key=True)


class LocationKeyword(SQLModel, table=True, check_tables_exist=True):
    __tablename__ = "location_keyword"
    location_id: int = Field(foreign_key="location.db_id", primary_key=True)
    keyword: int = Field(foreign_key="keyword.db_id", primary_key=True)


class Location(SQLModel, table=True, check_tables_exist=True):
    __tablename__ = "location"
    db_id: Optional[int] = Field(default=None, primary_key=True)
    id: str = Field(description="Die eindeutige URL des Orts.")
    type: str | None = Field(None, description="Typ des Orts")
    description: str | None = Field(None, description="Textuelle Beschreibung eines Orts, z. B. in Form einer Adresse.")
    geojson: dict | None = Field(
        default=None,
        sa_column=Column(JSON),
        description="Geodaten-Repräsentation des Orts als GeoJSON-Feature-Objekt.",
    )
    streetAddress: str | None = Field(None, description="Straße und Hausnummer der Anschrift.")
    room: str | None = Field(None, description="Raumangabe der Anschrift.")
    postalCode: str | None = Field(None, description="Postleitzahl der Anschrift.")
    subLocality: str | None = Field(None, description="Untergeordnete Ortsangabe der Anschrift, z.B. Stadtbezirk, Ortsteil oder Dorf.")
    locality: str | None = Field(None, description="Ortsangabe der Anschrift.")
    license: str | None = Field(None, description="Lizenz für die bereitgestellten Informationen.")
    created: datetime | None = Field(None, description="Erstellungszeitpunkt.")
    modified: datetime | None = Field(None, description="Letzte Änderung.")
    web: str | None = Field(None, description="HTML-Ansicht des Objekts.")
    deleted: bool | None = Field(False, description="Markiert dieses Objekt als gelöscht (true).")
    # Relationships
    bodies: List["Body"] = Relationship(link_model=LocationBodies)
    organizations: List["Organization"] = Relationship(link_model=LocationOrganizations)
    persons: List["Person"] = Relationship(link_model=LocationPersons)
    meetings: List["Meeting"] = Relationship(link_model=LocationMeetings)
    papers: List["Paper"] = Relationship(back_populates="locations", link_model=PaperLocationLink)
    keywords: List["Keyword"] = Relationship(back_populates="locations", link_model=LocationKeyword)


class LegislativeTermKeyword(SQLModel, table=True, check_tables_exist=True):
    __tablename__ = "legislative_term_keyword"
    legislative_term_id: int = Field(
        foreign_key="legislative_term.db_id", primary_key=True, description="URL der zugehörigen LegislativeTerm"
    )
    keyword: int = Field(foreign_key="keyword.db_id", primary_key=True, description="Zugehöriges Keyword")


class LegislativeTerm(SQLModel, table=True, check_tables_exist=True):
    __tablename__ = "legislative_term"
    db_id: Optional[int] = Field(default=None, primary_key=True)
    id: str = Field(description="Eindeutige URL der Wahlperiode.")
    type: str | None = Field(None, description="Typ des Objekts: 'https://schema.oparl.org/1.1/LegislativeTerm'.")
    body: str | None = Field(None, description="Verweis auf die Körperschaft, zu der die Wahlperiode gehört.")
    name: str | None = Field(None, description="Bezeichnung der Wahlperiode.")
    startDate: datetime | None = Field(None, description="Beginn der Wahlperiode.")
    endDate: datetime | None = Field(None, description="Ende der Wahlperiode.")
    license: str | None = Field(None, description="Lizenz für die bereitgestellten Informationen.")
    created: datetime | None = Field(None, description="Erstellungszeitpunkt.")
    modified: datetime | None = Field(None, description="Letzte Änderung.")
    web: str | None = Field(None, description="HTML-Ansicht des Objekts.")
    deleted: bool | None = Field(False, description="Markiert dieses Objekt als gelöscht (true).")
    keywords: List["Keyword"] = Relationship(back_populates="legislative_term", link_model=LegislativeTermKeyword)


class OrganizationType(SQLModel, table=True, check_tables_exist=True):
    __tablename__ = "organization_type"
    db_id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(description="Name des Organisationstyps")
    description: str | None = Field(None, description="Beschreibung des Typs")
    organizations: List["Organization"] = Relationship(back_populates="organizationType")


class OrganizationMembership(SQLModel, table=True, check_tables_exist=True):
    __tablename__ = "organization_membership"
    organization_id: int = Field(foreign_key="organization.db_id", primary_key=True)
    membership_id: int = Field(foreign_key="membership.db_id", primary_key=True)


class OrganizationPost(SQLModel, table=True, check_tables_exist=True):
    __tablename__ = "organization_post"
    organization_id: int = Field(foreign_key="organization.db_id", primary_key=True)
    post_str: int = Field(foreign_key="post.db_id", primary_key=True)


class OrganizationSubOrganization(SQLModel, table=True, check_tables_exist=True):
    __tablename__ = "organization_sub_organization"
    organization_id: int = Field(foreign_key="organization.db_id", primary_key=True)
    sub_organization_id: int = Field(foreign_key="organization.db_id", primary_key=True)


class OrganizationKeyword(SQLModel, table=True, check_tables_exist=True):
    __tablename__ = "organization_keyword"
    organization_id: int = Field(foreign_key="organization.db_id", primary_key=True)
    keyword: int = Field(foreign_key="keyword.db_id")


class Post(SQLModel, table=True, check_tables_exist=True):
    __tablename__ = "post"

    db_id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(description="Eindeutige URL des Postens.")
    organization_id: Optional[int] = Field(default=None, foreign_key="organization.db_id")
    organizations: List["Organization"] = Relationship(back_populates="post", link_model=OrganizationPost)


class MeetingOrganizationLink(SQLModel, table=True, check_tables_exist=True):
    __tablename__ = "meeting_organization"
    meeting_id: int = Field(foreign_key="meeting.db_id", primary_key=True)
    organization_id: int = Field(foreign_key="organization.db_id", primary_key=True)


class Organization(SQLModel, table=True, check_tables_exist=True):
    __tablename__ = "organization"
    db_id: Optional[int] = Field(default=None, primary_key=True)
    id: str = Field(description="Eindeutige URL der Organisation.")
    type: str | None = Field(None, description="Typ des Objekts: 'https://schema.oparl.org/1.1/Organization'.")
    body: str | None = Field(None, description="Verweis auf die Körperschaft, zu der die Organisation gehört.")
    name: str | None = Field(None, description="Bezeichnung der Organisation.")
    meeting_id: str | None = Field(None, description="Liste der Sitzungen dieser Organisation.", foreign_key="meeting.db_id")
    shortName: str | None = Field(None, description="Abkürzung der Organisation.")
    subOrganizationOf: int | None = Field(default=None, foreign_key="organization.db_id", description="FK auf übergeordnete Organisation")
    classification: str | None = Field(None, description="Klassifizierung, z. B. gesetzlich, freiwillig.")
    startDate: datetime | None = Field(None, description="Beginn der Organisation.")
    endDate: datetime | None = Field(None, description="Beendigung der Organisation.")
    website: str | None = Field(None, description="Website der Organisation.")
    location: int | None = Field(None, description="Ort, an dem die Organisation ansässig ist.", foreign_key="location.db_id")
    externalBody: str | None = Field(None, description="Verweis auf eine externe Körperschaft (nur bei Importen).")
    license: str | None = Field(None, description="Lizenz für die veröffentlichten Daten.")
    created: datetime | None = Field(None, description="Erstellungszeitpunkt.")
    modified: datetime | None = Field(None, description="Letzte Änderung.")
    web: str | None = Field(None, description="HTML-Ansicht der Organisation.")
    deleted: bool | None = Field(False, description="Markiert dieses Objekt als gelöscht (true).")
    membership: List["Membership"] = Relationship(link_model=OrganizationMembership)
    post: List["Post"] = Relationship(back_populates="organizations", link_model=OrganizationPost)
    subOrganizationOf: Optional[int] = Field(default=None, foreign_key="organization.db_id")

    # Relationships
    parentOrganization: Optional["Organization"] = Relationship(
        back_populates="subOrganizations", sa_relationship_kwargs={"remote_side": "Organization.db_id"}
    )
    subOrganizations: List["Organization"] = Relationship(back_populates="parentOrganization")
    keywords: List["Keyword"] = Relationship(back_populates="organizations", link_model=OrganizationKeyword)
    organization_type_id: Optional[int] = Field(foreign_key="organization_type.db_id")
    organizationType: OrganizationType = Relationship(back_populates="organizations")
    papers: List["Paper"] = Relationship(back_populates="originator_orgs", link_model=PaperOriginatorOrgLink)
    directed_papers: List["Paper"] = Relationship(back_populates="under_direction_of", link_model=PaperDirectionLink)
    meetings: List["Meeting"] = Relationship(back_populates="organizations", link_model=MeetingOrganizationLink)


class Title(SQLModel, table=True, check_tables_exist=True):
    __tablename__ = "title"
    db_id: int = Field(primary_key=True)
    title: str = Field()
    person_links: List["PersonTitleLink"] = Relationship(back_populates="title")


class PersonTitleLink(SQLModel, table=True, check_tables_exist=True):
    __tablename__ = "person_title"
    person_id: int = Field(foreign_key="person.db_id", primary_key=True)
    title_id: int = Field(foreign_key="title.db_id", primary_key=True)

    person: "Person" = Relationship(back_populates="title_links")
    title: "Title" = Relationship(back_populates="person_links")


class PersonMembershipLink(SQLModel, table=True, check_tables_exist=True):
    __tablename__ = "person_membership"
    person_id: int = Field(foreign_key="person.db_id", primary_key=True)
    membership_id: int = Field(foreign_key="membership.db_id", primary_key=True)


class PersonKeywordLink(SQLModel, table=True, check_tables_exist=True):
    __tablename__ = "person_keyword"
    person_id: int = Field(foreign_key="person.db_id", primary_key=True)
    keyword: int = Field(foreign_key="keyword.db_id", primary_key=True)


class MeetingParticipantLink(SQLModel, table=True, check_tables_exist=True):
    """Verknüpfung Meeting <-> Teilnehmer (Personen)"""

    __tablename__ = "meeting_participant"
    id: Optional[int] = Field(default=None, primary_key=True)
    meeting_id: int = Field(foreign_key="meeting.db_id")
    person_name: int = Field(foreign_key="person.db_id", description="Name oder ID der Person")


class Person(SQLModel, table=True, check_tables_exist=True):
    __tablename__ = "person"

    db_id: Optional[int] = Field(default=None, primary_key=True)
    id: str = Field(description="Eindeutige URL der Person.")
    type: str | None = Field(None, description="Typ des Objekts")
    body: str | None = Field(None, description="Körperschaft")
    name: str | None = Field(None, description="Vollständiger Name")
    familyName: str | None = Field(None, description="Familienname")
    givenName: str | None = Field(None, description="Vorname")
    formOfAddress: str | None = Field(None, description="Anrede")
    affix: str | None = Field(None, description="Namenszusatz")
    gender: str | None = Field(None, description="Geschlecht")
    location: int | None = Field(foreign_key="location.db_id", description="Ort")
    life: str | None = Field(None, description="Lebensdaten")
    lifeSource: str | None = Field(None, description="Quelle der Lebensdaten")
    license: str | None = Field(None, description="Lizenz")
    created: datetime | None = Field(None, description="Erstellungszeitpunkt")
    modified: datetime | None = Field(None, description="Letzte Änderung")
    web: str | None = Field(None, description="HTML-Ansicht der Person")
    deleted: bool = Field(default=False, description="Markiert als gelöscht")

    title: int = Field(default=None, foreign_key="title.db_id")
    title_links: List["PersonTitleLink"] = Relationship(back_populates="person")
    phone: List[str] = Field(sa_column=Column(JSON), default=[])
    email: List[str] = Field(sa_column=Column(JSON), default=[])

    status: List[str] = Field(sa_column=Column(JSON), default=[])

    keywords: List["Keyword"] = Relationship(
        back_populates="persons",
        link_model=PersonKeywordLink,
    )

    membership: List["Membership"] = Relationship(back_populates="person", link_model=PersonMembershipLink)
    papers: List["Paper"] = Relationship(back_populates="originator_persons", link_model=PaperOriginatorPersonLink)
    meetings: List["Meeting"] = Relationship(back_populates="participants", link_model=MeetingParticipantLink)


class MembershipKeyword(SQLModel, table=True, check_tables_exist=True):
    __tablename__ = "membership_keyword"
    membership_id: int = Field(foreign_key="membership.db_id", primary_key=True)
    keyword: int = Field(foreign_key="keyword.db_id", primary_key=True)


class Membership(SQLModel, table=True, check_tables_exist=True):
    __tablename__ = "membership"
    db_id: Optional[int] = Field(default=None, primary_key=True)
    id: str = Field(description="Eindeutige URL der Mitgliedschaft.")
    type: str | None = Field(None, description="Typ der Mitgliedschaft")
    organization: int | None = Field(
        None, description="Die Gruppierung, in der die Person Mitglied ist oder war.", foreign_key="organization.db_id"
    )
    role: str | None = Field(
        None,
        description="Rolle der Person für die Gruppierung. Kann genutzt werden, um verschiedene Arten von Mitgliedschaften, z.B. in Gremien, zu unterscheiden.",
    )
    votingRight: bool | None = Field(None, description="Gibt an, ob die Person in der Gruppierung stimmberechtigtes Mitglied ist.")
    startDate: datetime | None = Field(None, description="Datum, an dem die Mitgliedschaft beginnt.")
    endDate: datetime | None = Field(None, description="Datum, an dem die Mitgliedschaft endet.")
    onBehalfOf: str | None = Field(
        None,
        description="Die Gruppierung, für die die Person in der unter organization angegebenen Organisation sitzt. Beispiel: Mitgliedschaft als Vertreter einer Ratsfraktion, einer Gruppierung oder einer externen Organisation.",
    )
    license: str | None = Field(None, description="Lizenz für die veröffentlichten Daten.")
    created: datetime | None = Field(None, description="Erstellungszeitpunkt.")
    modified: datetime | None = Field(None, description="Letzte Änderung.")
    web: str | None = Field(None, description="HTML-Ansicht der Person.")
    deleted: bool | None = Field(False, description="Markiert dieses Objekt als gelöscht (true).")
    keywords: List["Keyword"] = Relationship(back_populates="memberships", link_model=MembershipKeyword)
    organizations: Organization = Relationship(link_model=OrganizationMembership)
    person: List["Person"] = Relationship(back_populates="membership", link_model=PersonMembershipLink)


class FileDerivativeLink(SQLModel, table=True):
    __tablename__ = "file_derivative_link"
    file_id: int = Field(foreign_key="file.db_id", primary_key=True)
    derivative_file_id: int = Field(foreign_key="file.db_id", primary_key=True)


class FileMeetingLink(SQLModel, table=True):
    __tablename__ = "file_meeting"
    file_id: int = Field(foreign_key="file.db_id", primary_key=True)
    meeting_id: int = Field(foreign_key="meeting.db_id", primary_key=True)


class FileAgendaItemLink(SQLModel, table=True):
    __tablename__ = "file_agenda"
    file_id: int = Field(foreign_key="file.db_id", primary_key=True)
    agendaItem: int = Field(foreign_key="agenda_item.db_id", primary_key=True)


class FilePaperLink(SQLModel, table=True):
    __tablename__ = "file_paper"
    file_id: int = Field(foreign_key="file.db_id", primary_key=True)
    paper_id: int = Field(foreign_key="paper.db_id", primary_key=True)


class FileKeywordLink(SQLModel, table=True):
    __tablename__ = "file_keyword"
    file_id: int = Field(foreign_key="file.db_id", primary_key=True)
    keyword: int = Field(foreign_key="keyword.db_id", primary_key=True)


class PaperFileLink(SQLModel, table=True, check_tables_exist=True):
    __tablename__ = "paper_file"
    paper_id: int = Field(foreign_key="paper.db_id", primary_key=True)
    file_id: int = Field(foreign_key="file.db_id", primary_key=True)


class File(SQLModel, table=True, check_tables_exist=True):
    __tablename__ = "file"
    db_id: Optional[int] = Field(default=None, primary_key=True)
    id: str = Field(description="Eindeutige URL des Dokuments.")
    type: str | None = Field(None, description="Typ der Datei")
    name: str | None = Field(None, description="Benutzerfreundlicher Name für das Objekt. Sollte keine Dateiendungen wie '.pdf' enthalten.")
    fileName: str | None = Field(
        None,
        description="Dateiname, unter dem die Datei in einem Dateisystem gespeichert werden kann (z.B. 'eineDatei.pdf'). Clients sollten sicherstellen, dass dieser Name den lokalen Anforderungen an Dateisysteme entspricht.",
    )
    mimeType: str | None = Field(None, description="MIME-Typ der Datei")
    date: datetime | None = Field(None, description="Datum, das als Ausgangspunkt für Fristen usw. verwendet wird.")
    size: int | None = Field(None, description="Größe der Datei in Bytes")
    sha1Checksum: str | None = Field(
        None,
        description="[Veraltet] SHA1-Prüfziffer des Dateiinhalt in hexadezimaler Schreibweise. Sollte nicht mehr verwendet werden, da SHA1 als unsicher gilt. Stattdessen sollte sha512Checksum verwendet werden.",
    )
    sha512Checksum: str | None = Field(None, description="SHA512-Prüfziffer des Dateiinhalt in hexadezimaler Schreibweise.")
    text: str | None = Field(
        None, description="Reine Textwiedergabe des Dateiinhalts, sofern dieser in Textform wiedergegeben werden kann."
    )
    accessUrl: str = Field(description="Zwingend erforderliche URL für den allgemeinen Zugriff auf die Datei.")
    downloadUrl: str | None = Field(None, description="URL zum Herunterladen der Datei.")
    externalServiceUrl: str | None = Field(
        None, description="Externe URL, die zusätzliche Zugriffsoptionen bietet (z.B. ein YouTube-Video)."
    )
    masterFile: str | None = Field(None, description="Datei, von der das aktuelle Objekt abgeleitet wurde.")
    fileLicense: str | None = Field(
        None,
        description="Lizenz, unter der die Datei angeboten wird. Wenn diese Eigenschaft nicht verwendet wird, ist der Wert von license oder die Lizenz eines übergeordneten Objektes maßgeblich.",
    )
    license: str | None = Field(None, description="Lizenz für die veröffentlichten Daten.")

    created: datetime | None = Field(None, description="Erstellungszeitpunkt.")
    modified: datetime | None = Field(None, description="Letzte Änderung.")
    web: str | None = Field(None, description="HTML-Ansicht der Person.")
    deleted: bool | None = Field(False, description="Markiert dieses Objekt als gelöscht (true).")
    derivative_files: List["File"] = Relationship(
        link_model=FileDerivativeLink,
        sa_relationship_kwargs={
            "primaryjoin": "File.db_id==FileDerivativeLink.file_id",
            "secondaryjoin": "File.db_id==FileDerivativeLink.derivative_file_id",
            "foreign_keys": [FileDerivativeLink.file_id, FileDerivativeLink.derivative_file_id],
        },
    )
    meetings: List["Meeting"] = Relationship(back_populates="auxiliary_files", link_model=FileMeetingLink)
    agendaItem: List["AgendaItem"] = Relationship(back_populates="auxiliaryFile", link_model=FileAgendaItemLink)
    paper: List["Paper"] = Relationship(back_populates="auxiliary_files", link_model=FilePaperLink)
    keywords: List["Keyword"] = Relationship(back_populates="files", link_model=FileKeywordLink)
    papers: List["Paper"] = Relationship(back_populates="auxiliary_files", link_model=PaperFileLink)


class AgendaItemKeywordLink(SQLModel, table=True, check_tables_exist=True):
    __tablename__ = "agendaitem_keyword"
    agendaitem_id: int = Field(foreign_key="agenda_item.db_id", primary_key=True)
    keyword: int = Field(foreign_key="keyword.db_id", primary_key=True)


class MeetingAgendaItemLink(SQLModel, table=True, check_tables_exist=True):
    """Verknüpfung Meeting <-> AgendaItems (Reihenfolge relevant)"""

    __tablename__ = "meeting_agenda_item"
    id: Optional[int] = Field(default=None, primary_key=True)
    meeting_id: int = Field(foreign_key="meeting.db_id")
    agenda_item_id: int = Field(foreign_key="agenda_item.db_id")


class AgendaItem(SQLModel, table=True, check_tables_exist=True):
    __tablename__ = "agenda_item"
    db_id: Optional[int] = Field(default=None, primary_key=True)
    id: str = Field(description="Eindeutige URL des Tagesordnungspunkt.")
    type: str | None = Field(None, description="Typ des Tagesordnungspunktes")
    meeting: int | None = Field(
        None,
        description="Rückverweis auf das Meeting, welches nur dann ausgegeben werden muss, wenn das AgendaItem-Objekt einzeln abgerufen wird.",
        foreign_key="meeting.db_id",
    )
    number: str | None = Field(
        None,
        description="Gliederungs-Nummer des Tagesordnungspunktes. Eine beliebige Zeichenkette, wie z. B. '10.', '10.1', 'C', 'c)' o. ä.",
    )
    order: int | None = Field(
        None,
        description="Die Position des Tagesordnungspunktes in der Sitzung, beginnend bei 0. Diese Nummer entspricht der Position in Meeting:agendaItem.",
    )
    name: str | None = Field(None, description="Das Thema des Tagesordnungspunktes.")
    public: bool | None = Field(
        None, description="Kennzeichnet, ob der Tagesordnungspunkt zur Behandlung in öffentlicher Sitzung vorgesehen ist/war."
    )
    result: str | None = Field(
        None,
        description="Kategorische Information über das Ergebnis der Beratung des Tagesordnungspunktes, z. B. 'Unverändert beschlossen' oder 'Geändert beschlossen'.",
    )
    resolutionText: str | None = Field(
        None, description="Text des Beschlusses, falls in diesem Tagesordnungspunkt ein Beschluss gefasst wurde."
    )
    resolutionFile: int | None = Field(
        None,
        description="Datei, die den Beschluss enthält, falls in diesem Tagesordnungspunkt ein Beschluss gefasst wurde.",
        foreign_key="file.db_id",
    )
    start: datetime | None = Field(None, description="Datum und Uhrzeit des Anfangszeitpunkts des Tagesordnungspunktes.")
    end: datetime | None = Field(None, description="Endzeitpunkt des Tagesordnungspunktes als Datum/Uhrzeit.")
    license: str | None = Field(None, description="Lizenz für die veröffentlichten Daten.")
    created: datetime | None = Field(None, description="Erstellungszeitpunkt.")
    modified: datetime | None = Field(None, description="Letzte Änderung.")
    web: str | None = Field(None, description="HTML-Ansicht der Person.")
    deleted: bool | None = Field(False, description="Markiert dieses Objekt als gelöscht (true).")
    auxiliaryFile: List["File"] = Relationship(back_populates="agendaItem", link_model=FileAgendaItemLink)
    keywords: List["Keyword"] = Relationship(back_populates="agenda_items", link_model=AgendaItemKeywordLink)
    meetings: List["Meeting"] = Relationship(back_populates="agenda_items", link_model=MeetingAgendaItemLink)


class Paper(SQLModel, table=True, check_tables_exist=True):
    __tablename__ = "paper"
    db_id: Optional[int] = Field(default=None, primary_key=True)
    id: str = Field(description="Eindeutige URL der Drucksache.")
    type: str | None = Field(None, description="Typ der Drucksache")
    body: str | None = Field(None, description="Körperschaft, zu der die Drucksache gehört.")
    name: str | None = Field(None, description="Titel der Drucksache.")
    reference: str | None = Field(
        None,
        description="Kennung bzw. Aktenzeichen der Drucksache, mit der sie in der parlamentarischen Arbeit eindeutig referenziert werden kann.",
    )
    date: datetime | None = Field(None, description="Datum, welches als Ausgangspunkt für Fristen usw. verwendet wird.")
    paperType: str | None = Field(None, description="Art der Drucksache, z. B. Beantwortung einer Anfrage.")
    mainFile: int | None = Field(
        None,
        description="Die Hauptdatei zu dieser Drucksache. Beispiel: Die Drucksache repräsentiert eine Beschlussvorlage und die Hauptdatei enthält den Text der Beschlussvorlage. Sollte keine eindeutige Hauptdatei vorhanden sein, wird diese Eigenschaft nicht ausgegeben.",
        foreign_key="file.db_id",
    )
    license: str | None = Field(None, description="Lizenz für die veröffentlichten Daten.")
    created: datetime | None = Field(None, description="Erstellungszeitpunkt.")
    modified: datetime | None = Field(None, description="Letzte Änderung.")
    web: str | None = Field(None, description="HTML-Ansicht der Person.")
    deleted: bool | None = Field(False, description="Markiert dieses Objekt als gelöscht (true).")

    auxiliary_files: List["File"] = Relationship(back_populates="paper", link_model=PaperFileLink)
    related_papers: List["Paper"] = Relationship(
        back_populates="related_to",
        link_model=PaperRelatedPaper,
        sa_relationship_kwargs={
            "primaryjoin": "Paper.db_id==PaperRelatedPaper.from_paper_id",
            "secondaryjoin": "Paper.db_id==PaperRelatedPaper.to_paper_id",
            "foreign_keys": "[PaperRelatedPaper.from_paper_id, PaperRelatedPaper.to_paper_id]",
        },
    )

    related_to: List["Paper"] = Relationship(
        back_populates="related_papers",
        link_model=PaperRelatedPaper,
        sa_relationship_kwargs={
            "primaryjoin": "Paper.db_id==PaperRelatedPaper.to_paper_id",
            "secondaryjoin": "Paper.db_id==PaperRelatedPaper.from_paper_id",
            "foreign_keys": "[PaperRelatedPaper.to_paper_id, PaperRelatedPaper.from_paper_id]",
        },
    )
    super_papers: List["Paper"] = Relationship(
        back_populates="sub_papers",
        link_model=PaperSuperordinatedLink,
        sa_relationship_kwargs={
            "primaryjoin": "Paper.db_id==PaperSuperordinatedLink.paper_id",
            "secondaryjoin": "Paper.db_id==PaperSuperordinatedLink.superordinated_paper_url",
            "foreign_keys": "[PaperSuperordinatedLink.paper_id, PaperSuperordinatedLink.superordinated_paper_url]",
        },
    )
    sub_papers: List["Paper"] = Relationship(
        back_populates="super_papers",
        link_model=PaperSuperordinatedLink,
        sa_relationship_kwargs={
            "primaryjoin": "Paper.db_id==PaperSuperordinatedLink.superordinated_paper_url",
            "secondaryjoin": "Paper.db_id==PaperSuperordinatedLink.paper_id",
            "foreign_keys": "[PaperSuperordinatedLink.superordinated_paper_url, PaperSuperordinatedLink.paper_id]",
        },
    )

    locations: List["Location"] = Relationship(back_populates="papers", link_model=PaperLocationLink)
    originator_persons: List["Person"] = Relationship(back_populates="papers", link_model=PaperOriginatorPersonLink)
    originator_orgs: List["Organization"] = Relationship(back_populates="papers", link_model=PaperOriginatorOrgLink)
    under_direction_of: List["Organization"] = Relationship(back_populates="directed_papers", link_model=PaperDirectionLink)
    keywords: List["Keyword"] = Relationship(back_populates="paper", link_model=PaperKeywordLink)

    paper_type: int = Field(foreign_key="paper_type.id", description="Typ des Dokuments")

    paper_subtype: int = Field(foreign_key="paper_subtype.id", description="Subtyp des Dokuments")


class BodyEquivalentLink(SQLModel, table=True, check_tables_exist=True):
    __tablename__ = "equivalent_bodies"
    body_id_a: int = Field(foreign_key="body.db_id", primary_key=True)
    body_id_b: int = Field(foreign_key="body.db_id", primary_key=True)


class BodyKeywordLink(SQLModel, table=True, check_tables_exist=True):
    """Verknüpfung Body <-> Keywords"""

    __tablename__ = "body_keyword"
    body_id: int = Field(foreign_key="body.db_id", primary_key=True)
    keyword: int = Field(foreign_key="keyword.db_id", primary_key=True)


class Body(SQLModel, table=True, check_tables_exist=True):
    __tablename__ = "body"
    db_id: Optional[int] = Field(default=None, primary_key=True)
    id: str = Field(description="Eindeutige URL der Körperschaft.")
    type: str | None = Field(None, description="Typangabe: 'https://schema.oparl.org/1.1/Body'.")
    name: str = Field(description="Name der Körperschaft.")
    shortName: str | None = Field(None, description="Abkürzung der Körperschaft.")
    system: str | None = Field(None, description="Verweis auf das zugehörige System-Objekt.")
    website: str | None = Field(None, description="Offizielle Website der Körperschaft.")
    license: str | None = Field(None, description="Standardlizenz für Daten dieser Körperschaft.")
    licenseValidSince: datetime | None = Field(None, description="Zeitpunkt, seit dem die Lizenz gilt.")
    oparlSince: datetime | None = Field(None, description="Zeitpunkt, ab dem die API für diese Körperschaft bereitsteht.")
    ags: str | None = Field(None, description="Amtlicher Gemeindeschlüssel.")
    rgs: str | None = Field(None, description="Regionalschlüssel.")
    contactEmail: str | None = Field(None, description="E-Mail-Adresse der Körperschaft.")
    contactName: str | None = Field(None, description="Name des Ansprechpartners.")
    organization: str = Field(description="Liste der Organisationen der Körperschaft.")
    person: str = Field(description="Liste der Personen der Körperschaft.")
    meeting: str = Field(description="Liste der Sitzungen der Körperschaft.")
    paper: str = Field(description="Liste der Vorlagen dieser Körperschaft.")
    legislativeTerm: str = Field(description="Liste der Wahlperioden der Körperschaft.")
    agendaItem: str = Field(description="Liste aller Tagesordnungspunkte der Körperschaft.")
    file: str = Field(description="Liste aller Dateien der Körperschaft.")
    locationList: str | None = Field(None, description="Liste der Orte, die mit dieser Körperschaft verknüpft sind.")
    legislativeTermList: str = Field(description="Alternative URL zur Liste der Wahlperioden.")
    membership: str = Field(description="Liste der Mitgliedschaften in der Körperschaft.")
    classification: str | None = Field(None, description="Art der Körperschaft, z. B. 'Stadt' oder 'Kreis'.")
    location: str | None = Field(None, description="Ort der Verwaltung dieser Körperschaft.")
    created: datetime | None = Field(None, description="Erstellungszeitpunkt.")
    modified: datetime | None = Field(None, description="Letzte Änderung.")
    web: str | None = Field(None, description="HTML-Ansicht der Körperschaft.")
    deleted: bool | None = Field(False, description="Kennzeichnung als gelöscht.")
    equivalents: List["Body"] = Relationship(
        back_populates="equivalent_to",
        link_model=BodyEquivalentLink,
        sa_relationship_kwargs={
            "primaryjoin": "Body.db_id==BodyEquivalentLink.body_id_a",
            "secondaryjoin": "Body.db_id==BodyEquivalentLink.body_id_b",
            "foreign_keys": "[BodyEquivalentLink.body_id_a, BodyEquivalentLink.body_id_b]",
        },
    )

    equivalent_to: List["Body"] = Relationship(
        back_populates="equivalents",
        link_model=BodyEquivalentLink,
        sa_relationship_kwargs={
            "primaryjoin": "Body.db_id==BodyEquivalentLink.body_id_b",
            "secondaryjoin": "Body.db_id==BodyEquivalentLink.body_id_a",
            "foreign_keys": "[BodyEquivalentLink.body_id_b, BodyEquivalentLink.body_id_a]",
        },
    )
    keywords: list["Keyword"] = Relationship(back_populates="body", link_model=BodyKeywordLink)


class MeetingAuxFileLink(SQLModel, table=True, check_tables_exist=True):
    """Verknüpfung Meeting <-> zusätzliche Dateien"""

    __tablename__ = "meeting_aux_file"
    id: Optional[int] = Field(default=None, primary_key=True)
    meeting_id: int = Field(foreign_key="meeting.db_id")
    file_id: int = Field(foreign_key="file.db_id")


class MeetingKeywordLink(SQLModel, table=True, check_tables_exist=True):
    """Verknüpfung Meeting <-> Keywords"""

    __tablename__ = "meeting_keyword"
    meeting_id: int = Field(foreign_key="meeting.db_id", primary_key=True)
    keyword: int = Field(foreign_key="keyword.db_id", primary_key=True)


class Meeting(SQLModel, table=True, check_tables_exist=True):
    __tablename__ = "meeting"
    db_id: Optional[int] = Field(default=None, primary_key=True)
    id: str = Field(description="Eindeutige URL der Sitzung.")
    type: str | None = Field(None, description="Typ der Sitzung")
    name: str | None = Field(None, description="Name der Sitzung.")
    meetingState: str | None = Field(
        None,
        description="Aktueller Status der Sitzung. Empfohlene Werte sind 'terminiert' (geplant), 'eingeladen' (vor der Sitzung bis zur Freigabe des Protokolls) und 'durchgeführt' (nach Freigabe des Protokolls).",
    )
    cancelled: bool | None = Field(None, description="Wenn die Sitzung ausfällt, wird 'cancelled' auf true gesetzt.")
    start: datetime | None = Field(
        None,
        description="Datum und Uhrzeit des Anfangszeitpunkts der Sitzung. Bei einer zukünftigen Sitzung ist dies der geplante Zeitpunkt, bei einer stattgefundenen kann es der tatsächliche Startzeitpunkt sein.",
    )
    end: datetime | None = Field(
        None,
        description="Endzeitpunkt der Sitzung als Datum/Uhrzeit. Bei einer zukünftigen Sitzung ist dies der geplante Zeitpunkt, bei einer stattgefundenen kann es der tatsächliche Endzeitpunkt sein.",
    )
    location: int | None = Field(None, description="Sitzungsort.", foreign_key="location.db_id")

    invitation: int | None = Field(None, description="Einladungsdokument zur Sitzung.", foreign_key="file.db_id")
    resultsProtocol: int | None = Field(
        None,
        description="Ergebnisprotokoll zur Sitzung. Diese Eigenschaft kann selbstverständlich erst nach dem Stattfinden der Sitzung vorkommen.",
        foreign_key="file.db_id",
    )
    verbatimProtocol: int | None = Field(
        None,
        description="Wortprotokoll zur Sitzung. Diese Eigenschaft kann selbstverständlich erst nach dem Stattfinden der Sitzung vorkommen.",
        foreign_key="file.db_id",
    )
    license: str | None = Field(None, description="Lizenz für die veröffentlichten Daten.")
    created: datetime | None = Field(None, description="Erstellungszeitpunkt.")
    modified: datetime | None = Field(None, description="Letzte Änderung.")
    web: str | None = Field(None, description="HTML-Ansicht der Sitzung.")
    deleted: bool | None = Field(False, description="Markiert dieses Objekt als gelöscht (true).")
    organizations: List["Organization"] = Relationship(back_populates="meetings", link_model=MeetingOrganizationLink)
    participants: list["Person"] = Relationship(back_populates="meetings", link_model=MeetingParticipantLink)
    auxiliary_files: list["File"] = Relationship(back_populates="meetings", link_model=MeetingAuxFileLink)
    agenda_items: list["AgendaItem"] = Relationship(back_populates="meetings", link_model=MeetingAgendaItemLink)
    keywords: list["Keyword"] = Relationship(back_populates="meetings", link_model=MeetingKeywordLink)


class ConsultationKeywordLink(SQLModel, table=True):
    consultation_id: int = Field(foreign_key="consultation.db_id", primary_key=True)
    keyword_id: int = Field(foreign_key="keyword.db_id", primary_key=True)


class Consultation(SQLModel, table=True, check_tables_exist=True):
    __tablename__ = "consultation"
    db_id: Optional[int] = Field(default=None, primary_key=True)
    id: str = Field(default=None)
    url: str = Field(default=None, description="URL dieses Consultation-Objekts")
    paper: int | None = Field(default=None, foreign_key="paper.db_id")
    agenda_item: int | None = Field(default=None, foreign_key="agenda_item.db_id")
    meeting: int | None = Field(default=None, foreign_key="meeting.db_id")
    authoritative: bool = Field(default=False, description="Wurde ein Beschluss gefasst?")
    role: str | None = Field(default=None, description="Funktion der Beratung (z.B. Anhörung, Vorberatung)")
    license: str | None = Field(default=None, description="Lizenz der Daten")
    created: datetime | None = Field(None, description="Erstellungszeitpunkt.")
    modified: datetime | None = Field(None, description="Letzte Änderung.")
    web: str | None = Field(None, description="HTML-Ansicht der Sitzung.")
    keywords: list["Keyword"] = Relationship(back_populates="consultations", link_model=ConsultationKeywordLink)


class Keyword(SQLModel, table=True, check_tables_exist=True):
    __tablename__ = "keyword"
    db_id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    locations: List["Location"] = Relationship(back_populates="keywords", link_model=LocationKeyword)
    legislative_term: List["LegislativeTerm"] = Relationship(back_populates="keywords", link_model=LegislativeTermKeyword)
    agenda_items: List["AgendaItem"] = Relationship(back_populates="keywords", link_model=AgendaItemKeywordLink)
    meetings: List["Meeting"] = Relationship(back_populates="keywords", link_model=MeetingKeywordLink)
    persons: List["Person"] = Relationship(back_populates="keywords", link_model=PersonKeywordLink)
    organizations: List["Organization"] = Relationship(back_populates="keywords", link_model=OrganizationKeyword)
    files: List["File"] = Relationship(back_populates="keywords", link_model=FileKeywordLink)
    paper: List["Paper"] = Relationship(back_populates="keywords", link_model=PaperKeywordLink)
    memberships: List["Membership"] = Relationship(back_populates="keywords", link_model=MembershipKeyword)
    body: List["Body"] = Relationship(back_populates="keywords", link_model=BodyKeywordLink)
    consultations: List["Consultation"] = Relationship(back_populates="keywords", link_model=ConsultationKeywordLink)


class ExtractArtifact(BaseModel):
    meetings: list[Meeting]


##############################################
################ Enums #######################
##############################################
class OrganizationTypeEnum(str, Enum):
    COUNCIL = "Stadtrat"
    FACTION = "Faktion"
    BV = "Bürgerversammlung"
    BA = "Bezirksausschuss"
    OTHER = "Other"


class PaperTypeEnum(str, Enum):
    STR_ANTRAG = "Str-Antrag"
    BA_ANTRAG = "BA-Antrag"
    SITZUNGSVORLAGE = "Sitzungsvorlage"
    BV_EMPFEHLUNG = "BV-Empfehlung"
    BV_ANFRAGE = "BV-Anfrage"


class PaperSubtypeEnum(str, Enum):
    # Subtypen für Str-Antrag
    DRINGLICHKEITSANTRAG = "Dringlichkeitsantrag"
    ANTRAG = "Antrag"
    ANFRAGE = "Anfrage"
    AENDERUNGSANTRAG = "Änderungsantrag"

    # Subtypen für BA-Antrag
    BA_ANTRAG = "BA-Antrag"

    # Subtypen für BV-Empfehlung
    BV_EMPFEHLUNG = "BV-Empfehlung"

    # Subtypen für BV-Anfrage
    BV_ANFRAGE = "BV-Anfrage"

    # Subtypen für Sitzungsvorlage
    BESCHLUSSVORLAGE_VB = "Beschlussvorlage VB"
    BESCHLUSSVORLAGE_SB = "Beschlussvorlage SB"
    BESCHLUSSVORLAGE_SB_VB = "Beschlussvorlage SB+VB"
    BEKANNTGABE = "Bekanntgabe"
    DIREKT = "Direkt"
    SITZUNGSVORLAGE_DA = "Sitzungsvorlage zur DA"


###########################################################
#############  Datenbankschema erstellen ##################
###########################################################

engine = create_engine(getenv_with_exception("DATABASE_URL"), echo=True)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def check_tables_exist():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public'"))
        tables = [row[0] for row in result]
        print("Vorhandene Tabellen:", tables)


def seed_organization_types(session: Session):
    existing = session.exec(select(OrganizationType)).all()
    if existing:
        return  # Tabelle schon befüllt

    for enum_value in OrganizationTypeEnum:
        org_type = OrganizationType(name=enum_value.value)
        session.add(org_type)
    session.commit()


def seed_paper_types(session: Session):
    existing = session.exec(select(PaperType)).all()
    if existing:
        return  # Tabelle schon befüllt

    for enum_value in PaperTypeEnum:
        paper_type = PaperType(name=enum_value.value)
        session.add(paper_type)
    session.commit()


def seed_paper_subtypes(session: Session):
    existing = session.exec(select(PaperSubtype)).all()
    if existing:
        return  # Tabelle schon befüllt

    for enum_value in PaperSubtypeEnum:
        paper_subtype = PaperSubtype(name=enum_value.value)
        session.add(paper_subtype)
    session.commit()


def seed_all_enums(session: Session):
    seed_organization_types(session)
    seed_paper_types(session)
    seed_paper_subtypes(session)


if __name__ == "__main__":
    create_db_and_tables()
    check_tables_exist()
