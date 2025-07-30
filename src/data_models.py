from datetime import datetime
from enum import Enum
from typing import List, Optional

from dotenv import load_dotenv
from sqlalchemy import JSON
from sqlmodel import Column, Field, Relationship, Session, SQLModel, create_engine, select, text

from envtools import getenv_with_exception

load_dotenv()


class SYSTEM_OTHER_OPARL_VERSION(SQLModel, table=True):
    __tablename__ = "system_other_oparl_version"
    # Zusammengesetzter Primärschlüssel
    system_id: Optional[int] = Field(foreign_key="system.db_id", primary_key=True)
    other_version_id: Optional[int] = Field(foreign_key="system.db_id", primary_key=True)

    system: "System" = Relationship(
        back_populates="other_oparl_versions", sa_relationship_kwargs={"foreign_keys": "[SYSTEM_OTHER_OPARL_VERSION.system_id]"}
    )
    other_version: "System" = Relationship(
        back_populates="other_oparl_versions_reverse",
        sa_relationship_kwargs={"foreign_keys": "[SYSTEM_OTHER_OPARL_VERSION.other_version_id]"},
    )


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

    # Relationships
    other_oparl_versions: List[SYSTEM_OTHER_OPARL_VERSION] = Relationship(
        back_populates="system", sa_relationship_kwargs={"foreign_keys": "[SYSTEM_OTHER_OPARL_VERSION.system_id]"}
    )
    other_oparl_versions_reverse: List[SYSTEM_OTHER_OPARL_VERSION] = Relationship(
        back_populates="other_version", sa_relationship_kwargs={"foreign_keys": "[SYSTEM_OTHER_OPARL_VERSION.other_version_id]"}
    )


class Location(SQLModel, table=True, check_tables_exist=True):
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
    bodies: List["Body"] = Relationship(back_populates="location_bodies")
    organizations: List["Organization"] = Relationship(back_populates="location_organizations")
    persons: List["Person"] = Relationship(back_populates="location_persons")
    meetings: List["Meeting"] = Relationship(back_populates="location_meetings")
    papers: List["Paper"] = Relationship(back_populates="location_papers")  #
    keywords: List["LocationKeyword"] = Relationship(back_populates="location_keyword")


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
    keyword: str = Field(primary_key=True)


class LegislativeTerm(SQLModel, table=True, check_tables_exist=True):
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
    keywords: List["LegislativeTermKeyword"] = Relationship(back_populates="legislative_term_keyword")


class LegislativeTermKeyword(SQLModel, table=True, check_tables_exist=True):
    __tablename__ = "legislative_term_keyword"

    legislative_term_id: str = Field(foreign_key="legislative_term.id", primary_key=True, description="URL der zugehörigen LegislativeTerm")
    keyword: str = Field(primary_key=True, description="Zugehöriges Keyword")

    # Reverse Relationship
    legislative_term: List["LegislativeTerm"] = Relationship(back_populates="legislative_term")


class OrganizationType(SQLModel, table=True, check_tables_exist=True):
    __tablename__ = "organization_type"

    db_id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(description="Name des Organisationstyps")
    description: str | None = Field(None, description="Beschreibung des Typs")


class Organization(SQLModel, table=True, check_tables_exist=True):
    db_id: Optional[int] = Field(default=None, primary_key=True)
    id: str = Field(description="Eindeutige URL der Organisation.")
    type: str | None = Field(None, description="Typ des Objekts: 'https://schema.oparl.org/1.1/Organization'.")
    body: str | None = Field(None, description="Verweis auf die Körperschaft, zu der die Organisation gehört.")
    name: str | None = Field(None, description="Bezeichnung der Organisation.")
    meeting: str | None = Field(None, description="Liste der Sitzungen dieser Organisation.")
    shortName: str | None = Field(None, description="Abkürzung der Organisation.")
    subOrganizationOf: str | None = Field(None, description="Verweis auf die übergeordnete Organisation.")
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

    membership: List["Membership"] = Relationship(back_populates="organization_membership")
    post: List["OrganizationPost"] = Relationship(back_populates="organization_post")
    subOrganizations: List["Organization"] = Relationship(
        back_populates="parentOrganization",
    )
    parentOrganization: List["Organization"] = Relationship(back_populates="organization_sub_organization")
    keywords: List["OrganizationKeyword"] = Relationship(back_populates="organization_keyword")
    organizationType: OrganizationType = Relationship(back_populates="organization_type")


class OrganizationMembership(SQLModel, table=True, check_tables_exist=True):
    __tablename__ = "organization_membership"
    organization_id: int = Field(foreign_key="organization.db_id", primary_key=True)
    membership_id: int = Field(foreign_key="membership.db_id", primary_key=True)


class OrganizationPost(SQLModel, table=True, check_tables_exist=True):
    __tablename__ = "organization_post"
    organization_id: int = Field(foreign_key="organization.db_id", primary_key=True)
    post: str = Field(primary_key=True)


class OrganizationSubOrganization(SQLModel, table=True, check_tables_exist=True):
    __tablename__ = "organization_sub_organization"
    organization_id: int = Field(foreign_key="organization.db_id", primary_key=True)
    sub_organization_id: int = Field(foreign_key="organization.db_id", primary_key=True)


class OrganizationKeyword(SQLModel, table=True, check_tables_exist=True):
    __tablename__ = "organization_keyword"
    organization_id: int = Field(foreign_key="organization.db_id", primary_key=True)
    keyword: str = Field(primary_key=True)


class PersonTitleLink(SQLModel, table=True, check_tables_exist=True):
    __tablename__ = "person_title"
    person_id: int = Field(foreign_key="person.db_id", primary_key=True)
    title: str = Field(primary_key=True)
    person: "Person" = Relationship(back_populates="title_links")


class PersonPhoneLink(SQLModel, table=True, check_tables_exist=True):
    __tablename__ = "person_phone"
    person_id: int = Field(foreign_key="person.db_id", primary_key=True)
    phone: str = Field(primary_key=True)
    person: "Person" = Relationship(back_populates="phone_links")


class PersonEmailLink(SQLModel, table=True, check_tables_exist=True):
    __tablename__ = "person_email"
    person_id: int = Field(foreign_key="person.db_id", primary_key=True)
    email: str = Field(primary_key=True)
    person: "Person" = Relationship(back_populates="email_links")


class PersonStatusLink(SQLModel, table=True, check_tables_exist=True):
    __tablename__ = "person_status"
    person_id: int = Field(foreign_key="person.db_id", primary_key=True)
    status: str = Field(primary_key=True)
    person: "Person" = Relationship(back_populates="status_links")


class PersonMembershipLink(SQLModel, table=True, check_tables_exist=True):
    __tablename__ = "person_membership"
    person_id: int = Field(foreign_key="person.db_id", primary_key=True)
    membership_id: int = Field(foreign_key="membership.db_id", primary_key=True)
    person: "Person" = Relationship(back_populates="membership_links")


class PersonKeywordLink(SQLModel, table=True, check_tables_exist=True):
    __tablename__ = "person_keyword"
    person_id: int = Field(foreign_key="person.db_id", primary_key=True)
    keyword: str = Field(primary_key=True)
    person: "Person" = Relationship(back_populates="keyword_links")


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

    title: List[PersonTitleLink] = Relationship(back_populates="person")

    phone: List[PersonPhoneLink] = Relationship(back_populates="person_phone")

    email: List[PersonEmailLink] = Relationship(back_populates="person_email")

    status: List[PersonStatusLink] = Relationship(back_populates="person_status")

    keywords: List[PersonKeywordLink] = Relationship(back_populates="person_keyword")

    membership: List[PersonMembershipLink] = Relationship(back_populates="person_membership")


class MembershipKeyword(SQLModel, table=True, check_tables_exist=True):
    __tablename__ = "membership_keyword"
    membership_id: int = Field(foreign_key="membership.db_id", primary_key=True)
    keyword: str = Field(primary_key=True)

    membership: "Membership" = Relationship(back_populates="keywords")


class Membership(SQLModel, table=True, check_tables_exist=True):
    db_id: Optional[int] = Field(default=None, primary_key=True)
    id: str = Field(description="Eindeutige URL der Mitgliedschaft.")
    type: str | None = Field(None, description="Typ der Mitgliedschaft")
    person: str | None = Field(
        None,
        description="Rückverweis auf die Person, die Mitglied ist. Wird nur ausgegeben, wenn das Membership-Objekt einzeln abgerufen wird.",
        foreign_key="person.db_id",
    )
    organization: str | None = Field(
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
    keywords: List[MembershipKeyword] = Relationship(back_populates="membership")


class FileDerivativeLink(SQLModel, table=True):
    __tablename__ = "file_derivative_link"
    file_id: int = Field(foreign_key="file.db_id", primary_key=True)
    FileDerivative_file: int = Field(foreign_key="file.db_id", primary_key=True)

    file: "File" = Relationship(back_populates="derivative_files")


class FileMeetingLink(SQLModel, table=True):
    file_id: int = Field(foreign_key="file.db_id", primary_key=True)
    meeting_id: int = Field(foreign_key="meeting.db_id", primary_key=True)

    file: "File" = Relationship(back_populates="meetings")


class FileAgendaItemLink(SQLModel, table=True):
    file_id: int = Field(foreign_key="file.db_id", primary_key=True)
    agendaItem: int = Field(foreign_key="agendaitem.db_id", primary_key=True)

    file: "File" = Relationship(back_populates="agenda_items")


class FilePaperLink(SQLModel, table=True):
    file_id: int = Field(foreign_key="file.db_id", primary_key=True)
    paper_id: int = Field(foreign_key="paper.db_id", primary_key=True)

    file: "File" = Relationship(back_populates="papers")


class FileKeywordLink(SQLModel, table=True):
    file_id: int = Field(foreign_key="file.db_id", primary_key=True)
    keyword: str = Field(primary_key=True)

    file: "File" = Relationship(back_populates="keywords")


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

    derivative_file: List[FileDerivativeLink] = Relationship(back_populates="file")
    meeting: List[FileMeetingLink] = Relationship(back_populates="file")
    agendaItem: List[FileAgendaItemLink] = Relationship(back_populates="file")
    paper: List[FilePaperLink] = Relationship(back_populates="file")
    keyword: List[FileKeywordLink] = Relationship(back_populates="file")


class AgendaItemKeywordLink(SQLModel, table=True, check_tables_exist=True):
    agendaitem_id: int = Field(foreign_key="agendaitem.db_id", primary_key=True)
    keyword: str = Field(primary_key=True)

    agendaitem: "AgendaItem" = Relationship(back_populates="keywords")


class AgendaItem(SQLModel, table=True, check_tables_exist=True):
    db_id: Optional[int] = Field(default=None, primary_key=True)
    id: str = Field(description="Eindeutige URL des Tagesordnungspunkt.")
    type: str | None = Field(None, description="Typ des Tagesordnungspunktes")
    meeting: str | None = Field(
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
    auxiliaryFile: List[FileAgendaItemLink] = Relationship(back_populates="file")

    keyword: List[AgendaItemKeywordLink] = Relationship(back_populates="agendaitem")


class PaperType(SQLModel, table=True, check_tables_exist=True):
    __tablename__ = "paper_type"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(description="Bezeichnung des Paper-Typs")

    # Beziehung zu Subtypen
    subtypes: List["PaperSubtype"] = Relationship(back_populates="parent_type")


class PaperSubtype(SQLModel, table=True):
    __tablename__ = "paper_subtype"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(..., description="Bezeichnung des Paper-Subtyps")

    # FK auf PaperTypeEnum
    paper_type_id: int = Field(foreign_key="paper_type.id", description="Referenz auf den übergeordneten Paper-Typ")
    parent_type: PaperType = Relationship(back_populates="subtypes")


class Paper(SQLModel, table=True, check_tables_exist=True):
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

    auxiliary_files: List["PaperFileLink"] = Relationship(back_populates="paper")
    related_papers: List["PaperRelatedLink"] = Relationship(back_populates="paper")
    super_papers: List["PaperSuperordinatedLink"] = Relationship(back_populates="paper")
    sub_papers: List["PaperSubordinatedLink"] = Relationship(back_populates="paper")
    locations: List["PaperLocationLink"] = Relationship(back_populates="paper")
    originator_persons: List["PaperOriginatorPersonLink"] = Relationship(back_populates="paper")
    originator_orgs: List["PaperOriginatorOrgLink"] = Relationship(back_populates="paper")
    under_direction_of: List["PaperDirectionLink"] = Relationship(back_populates="paper")
    keywords: List["PaperKeywordLink"] = Relationship(back_populates="paper")

    paper_type_id: Optional[int] = Field(foreign_key="paper_type.id", description="Typ des Dokuments")
    paper_type: PaperType = Relationship(back_populates="paper_types")

    paper_subtype_id: int = Field(foreign_key="paper_subtype.id", description="Subtyp des Dokuments")
    paper_subtype: PaperSubtype = Relationship(back_populates="paper_subtypes")


class PaperFileLink(SQLModel, table=True, check_tables_exist=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    paper_id: int = Field(foreign_key="paper.db_id")
    file_id: int = Field(foreign_key="file.db_id")

    paper: "Paper" = Relationship(back_populates="auxiliary_files")
    file: "File" = Relationship()


class PaperRelatedLink(SQLModel, table=True, check_tables_exist=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    paper_id: int = Field(foreign_key="paper.db_id")
    related_paper_url: str = Field(description="Verwandte Drucksache als URL")

    paper: "Paper" = Relationship(back_populates="related_papers")


class PaperSuperordinatedLink(SQLModel, table=True, check_tables_exist=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    paper_id: int = Field(foreign_key="paper.db_id")
    superordinated_paper_url: str = Field(description="Übergeordnete Drucksache")

    paper: "Paper" = Relationship(back_populates="super_papers")


class PaperSubordinatedLink(SQLModel, table=True, check_tables_exist=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    paper_id: int = Field(foreign_key="paper.db_id")
    subordinated_paper_url: str = Field(description="Untergeordnete Drucksache")

    paper: "Paper" = Relationship(back_populates="sub_papers")


class PaperLocationLink(SQLModel, table=True, check_tables_exist=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    paper_id: int = Field(foreign_key="paper.db_id")
    location_id: int = Field(foreign_key="location.db_id")

    paper: "Paper" = Relationship(back_populates="locations")
    location: "Location" = Relationship()


class PaperOriginatorPersonLink(SQLModel, table=True, check_tables_exist=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    paper_id: int = Field(foreign_key="paper.db_id")
    person_name: str = Field(description="Name der Person")

    paper: "Paper" = Relationship(back_populates="originator_persons")


class PaperOriginatorOrgLink(SQLModel, table=True, check_tables_exist=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    paper_id: int = Field(foreign_key="paper.db_id")
    organization_name: int = Field(description="Name der Organisation", foreign_key="organization.db_id")

    paper: "Paper" = Relationship(back_populates="originator_orgs")


class PaperDirectionLink(SQLModel, table=True, check_tables_exist=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    paper_id: int = Field(foreign_key="paper.db_id")
    direction_name: str = Field(description="Amt oder Abteilung, federführend")

    paper: "Paper" = Relationship(back_populates="under_direction_of")


class PaperKeywordLink(SQLModel, table=True, check_tables_exist=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    paper_id: int = Field(foreign_key="paper.db_id")
    keyword: str = Field(description="Schlagwort zur Drucksache")

    paper: "Paper" = Relationship(back_populates="keywords")


class BodyEquivalentLink(SQLModel, table=True, check_tables_exist=True):
    """Verknüpfung Body <-> weitere Körperschaften (equivalent)"""

    id: Optional[int] = Field(default=None, primary_key=True)
    body_id: int = Field(foreign_key="body.db_id")
    equivalent_url: str = Field(description="URL einer vergleichbaren Körperschaft")

    body: "Body" = Relationship(back_populates="equivalents")


class BodyKeywordLink(SQLModel, table=True, check_tables_exist=True):
    """Verknüpfung Body <-> Keywords"""

    id: Optional[int] = Field(default=None, primary_key=True)
    body_id: int = Field(foreign_key="body.db_id")
    keyword: str = Field(description="Schlagwort")

    body: "Body" = Relationship(back_populates="keywords")


class Body(SQLModel, table=True, check_tables_exist=True):
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
    equivalents: list[BodyEquivalentLink] = Relationship(back_populates="body")
    keywords: list[BodyKeywordLink] = Relationship(back_populates="body")


class MeetingOrganizationLink(SQLModel, table=True, check_tables_exist=True):
    """Verknüpfung Meeting <-> Organization"""

    id: Optional[int] = Field(default=None, primary_key=True)
    meeting_id: int = Field(foreign_key="meeting.db_id")
    organization_name: str = Field(description="Name oder ID der Organisation")

    meeting: "Meeting" = Relationship(back_populates="organizations")


class MeetingParticipantLink(SQLModel, table=True, check_tables_exist=True):
    """Verknüpfung Meeting <-> Teilnehmer (Personen)"""

    id: Optional[int] = Field(default=None, primary_key=True)
    meeting_id: int = Field(foreign_key="meeting.db_id")
    person_name: str = Field(description="Name oder ID der Person")

    meeting: "Meeting" = Relationship(back_populates="participants")


class MeetingAuxFileLink(SQLModel, table=True, check_tables_exist=True):
    """Verknüpfung Meeting <-> zusätzliche Dateien"""

    id: Optional[int] = Field(default=None, primary_key=True)
    meeting_id: int = Field(foreign_key="meeting.db_id")
    file_id: int = Field(foreign_key="file.db_id")

    meeting: "Meeting" = Relationship(back_populates="auxiliary_files")
    file: "File" = Relationship()


class MeetingAgendaItemLink(SQLModel, table=True, check_tables_exist=True):
    """Verknüpfung Meeting <-> AgendaItems (Reihenfolge relevant)"""

    id: Optional[int] = Field(default=None, primary_key=True)
    meeting_id: int = Field(foreign_key="meeting.db_id")
    agenda_item_id: int = Field(foreign_key="agendaitem.db_id")
    order: int | None = Field(None, description="Position des AgendaItems")

    meeting: "Meeting" = Relationship(back_populates="agenda_items")
    agenda_item: "AgendaItem" = Relationship()


class MeetingKeywordLink(SQLModel, table=True, check_tables_exist=True):
    """Verknüpfung Meeting <-> Keywords"""

    id: Optional[int] = Field(default=None, primary_key=True)
    meeting_id: int = Field(foreign_key="meeting.db_id")
    keyword: str = Field(description="Schlagwort")

    meeting: "Meeting" = Relationship(back_populates="keywords")


class Meeting(SQLModel, table=True, check_tables_exist=True):
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
    organizations: list[MeetingOrganizationLink] = Relationship(back_populates="meeting")
    participants: list[MeetingParticipantLink] = Relationship(back_populates="meeting")
    auxiliary_files: list[MeetingAuxFileLink] = Relationship(back_populates="meeting")
    agenda_items: list[MeetingAgendaItemLink] = Relationship(back_populates="meeting")
    keywords: list[MeetingKeywordLink] = Relationship(back_populates="meeting")


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
