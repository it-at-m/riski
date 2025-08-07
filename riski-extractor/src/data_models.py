from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, HttpUrl


class System(BaseModel):
    id: HttpUrl = Field(description="Die eindeutige URL dieses Objekts.")
    type: str | None = Field(None, description="Der feste Typ des Objekts: 'https://schema.oparl.org/1.1/System'.")
    oparlVersion: str = Field(description="Die vom System unterstützte OParl-Version (z. B. 'https://schema.oparl.org/1.1/').")
    otherOparlVersions: list[HttpUrl] | None = Field(None, description="Dient der Angabe von System-Objekten mit anderen OParl-Versionen.")
    license: HttpUrl | None = Field(
        None, description="Lizenz, unter der durch diese API abrufbaren Daten stehen, sofern nicht am einzelnen Objekt anders angegeben."
    )
    body: HttpUrl = Field(description="Link zur Objektliste mit allen Körperschaften, die auf dem System existieren.")
    name: str | None = Field(
        None,
        description="Benutzerfreundlicher Name für das System, mit dessen Hilfe Nutzerinnen und Nutzer das System erkennen und von anderen unterscheiden können.",
    )
    contactEmail: EmailStr | None = Field(
        None,
        description="E-Mail-Adresse für Anfragen zur OParl-API. Die Angabe einer E-Mail-Adresse dient sowohl NutzerInnen wie auch Entwickelnden von Clients zur Kontaktaufnahme mit dem Betreiber.",
    )
    contactName: str | None = Field(
        None,
        description="Name der Ansprechpartnerin bzw. des Ansprechpartners oder der Abteilung, die über die in contactEmail angegebene Adresse erreicht werden kann.",
    )
    website: HttpUrl | None = Field(None, description="URL der Website des parlamentarischen Informationssystems")
    vendor: HttpUrl | None = Field(None, description="URL der Website des Softwareanbieters, von dem die OParl-Server-Software stammt.")
    product: HttpUrl | None = Field(None, description="URL zu Informationen über die auf dem System genutzte OParl-Server-Software")
    created: datetime | None = Field(None, description="Zeitpunkt der Erstellung dieses Objekts.")
    modified: datetime | None = Field(None, description="Zeitpunkt der letzten Änderung dieses Objekts.")
    web: HttpUrl | None = Field(None, description="URL zur HTML-Ansicht dieses Objekts.")
    deleted: bool | None = Field(False, description="Markiert dieses Objekt als gelöscht (true).")


class Location(BaseModel):
    id: HttpUrl | None = Field(description="Die eindeutige URL des Orts.")
    type: str | None = Field(None, description="Typ des Orts")
    description: str | None = Field(None, description="Textuelle Beschreibung eines Orts, z. B. in Form einer Adresse.")
    geojson: dict | None = Field(
        None,
        description="Geodaten-Repräsentation des Orts. Muss der GeoJSON-Spezifikation entsprechen, d.h. es muss ein vollständiges Feature-Objekt ausgegeben werden.",
    )
    streetAddress: str | None = Field(None, description="Straße und Hausnummer der Anschrift.")
    room: str | None = Field(None, description="Raumangabe der Anschrift.")
    postalCode: str | None = Field(None, description="Postleitzahl der Anschrift.")
    subLocality: str | None = Field(None, description="Untergeordnete Ortsangabe der Anschrift, z.B. Stadtbezirk, Ortsteil oder Dorf.")
    locality: str | None = Field(None, description="Ortsangabe der Anschrift.")
    bodies: list[HttpUrl] | None = Field(
        None,
        description="Rückverweise auf Body-Objekte. Wird nur ausgegeben, wenn das Location-Objekt nicht als eingebettetes Objekt aufgerufen wird.",
    )
    organizations: list[HttpUrl] | None = Field(
        None,
        description="Rückverweise auf Organisation-Objekte. Wird nur ausgegeben, wenn das Location-Objekt nicht als eingebettetes Objekt aufgerufen wird.",
    )
    persons: list[HttpUrl] | None = Field(
        None,
        description="Rückverweise auf Person-Objekte. Wird nur ausgegeben, wenn das Location-Objekt nicht als eingebettetes Objekt aufgerufen wird.",
    )
    meetings: list[HttpUrl] | None = Field(
        None,
        description="Rückverweise auf Meeting-Objekte. Wird nur ausgegeben, wenn das Location-Objekt nicht als eingebettetes Objekt aufgerufen wird.",
    )
    papers: list[HttpUrl] | None = Field(
        None,
        description="Rückverweise auf Paper-Objekte. Wird nur ausgegeben, wenn das Location-Objekt nicht als eingebettetes Objekt aufgerufen wird.",
    )
    license: str | None = Field(None, description="Lizenz für die bereitgestellten Informationen.")
    keyword: list[str] | None = Field(None, description="Stichwörter zur Wahlperiode.")
    created: datetime | None = Field(None, description="Erstellungszeitpunkt.")
    modified: datetime | None = Field(None, description="Letzte Änderung.")
    web: HttpUrl | None = Field(None, description="HTML-Ansicht des Objekts.")
    deleted: bool | None = Field(False, description="Markiert dieses Objekt als gelöscht (true).")


class LegislativeTerm(BaseModel):
    id: HttpUrl = Field(description="Eindeutige URL der Wahlperiode.")
    type: str | None = Field(None, description="Typ des Objekts: 'https://schema.oparl.org/1.1/LegislativeTerm'.")
    body: HttpUrl | None = Field(None, description="Verweis auf die Körperschaft, zu der die Wahlperiode gehört.")
    name: str | None = Field(None, description="Bezeichnung der Wahlperiode.")
    startDate: datetime | None = Field(None, description="Beginn der Wahlperiode.")
    endDate: datetime | None = Field(None, description="Ende der Wahlperiode.")
    license: str | None = Field(None, description="Lizenz für die bereitgestellten Informationen.")
    keyword: list[str] | None = Field(None, description="Stichwörter zur Wahlperiode.")
    created: datetime | None = Field(None, description="Erstellungszeitpunkt.")
    modified: datetime | None = Field(None, description="Letzte Änderung.")
    web: HttpUrl | None = Field(None, description="HTML-Ansicht des Objekts.")
    deleted: bool | None = Field(False, description="Markiert dieses Objekt als gelöscht (true).")


class Organization(BaseModel):
    id: HttpUrl = Field(description="Eindeutige URL der Organisation.")
    type: str | None = Field(None, description="Typ des Objekts: 'https://schema.oparl.org/1.1/Organization'.")
    body: HttpUrl | None = Field(None, description="Verweis auf die Körperschaft, zu der die Organisation gehört.")
    name: str | None = Field(None, description="Bezeichnung der Organisation.")
    membership: list[HttpUrl] | None = Field(None, description="Liste der zugehörigen Mitgliedschaften.")
    meeting: HttpUrl | None = Field(None, description="Liste der Sitzungen dieser Organisation.")
    shortName: str | None = Field(None, description="Abkürzung der Organisation.")
    post: list[str] | None = Field(None, description="Posten oder Ämter, die in der Organisation existieren.")
    subOrganizationOf: HttpUrl | None = Field(None, description="Verweis auf die übergeordnete Organisation.")
    organizationType: str | None = Field(None, description="Typ der Organisation, z. B. Ausschuss, Fraktion.")
    classification: str | None = Field(None, description="Klassifizierung, z. B. gesetzlich, freiwillig.")
    startDate: datetime | None = Field(None, description="Beginn der Organisation.")
    endDate: datetime | None = Field(None, description="Beendigung der Organisation.")
    website: HttpUrl | None = Field(None, description="Website der Organisation.")
    location: HttpUrl | None = Field(None, description="Ort, an dem die Organisation ansässig ist.")
    externalBody: HttpUrl | None = Field(None, description="Verweis auf eine externe Körperschaft (nur bei Importen).")
    license: str | None = Field(None, description="Lizenz für die veröffentlichten Daten.")
    keyword: list[str] | None = Field(None, description="Stichwörter zur Organisation.")
    created: datetime | None = Field(None, description="Erstellungszeitpunkt.")
    modified: datetime | None = Field(None, description="Letzte Änderung.")
    web: HttpUrl | None = Field(None, description="HTML-Ansicht der Organisation.")
    deleted: bool | None = Field(False, description="Markiert dieses Objekt als gelöscht (true).")


class Person(BaseModel):
    id: HttpUrl = Field(description="Eindeutige URL der Person.")
    type: str | None = Field(None, description="Typ des Objekts: 'https://schema.oparl.org/1.1/Person'.")
    body: HttpUrl | None = Field(None, description="Verweis auf die Körperschaft, in der die Person aktiv ist.")
    name: str | None = Field(None, description="Vollständiger Name der Person.")
    familyName: str | None = Field(None, description="Nachname der Person.")
    givenName: str | None = Field(None, description="Vorname der Person.")
    formOfAddress: str | None = Field(None, description="Anrede der Person (z. B. Frau, Herr).")
    affix: str | None = Field(None, description="Namenszusatz (z. B. von, zu, Freiherr).")
    title: list[str] | None = Field(None, description="Titel der Person (z. B. Dr., Prof.).")
    gender: str | None = Field(None, description="Geschlecht der Person.")
    phone: list[str] | None = Field(None, description="Telefonnummer(n) der Person.")
    email: list[str] | None = Field(None, description="E-Mail-Adresse(n) der Person.")
    location: HttpUrl | None = Field(None, description="Verweis auf einen Ort, der mit der Person verknüpft ist.")
    status: list[str] | None = Field(None, description="Statusinformationen zur Person (z. B. Mandat ruhend).")
    membership: list[HttpUrl] | None = Field(None, description="Verweise auf Mitgliedschaften.")
    life: str | None = Field(None, description="Lebensdaten der Person (z. B. Geburtsdatum).")
    lifeSource: str | None = Field(None, description="Quelle der Lebensdaten.")
    license: str | None = Field(None, description="Lizenz für die veröffentlichten Daten.")
    keyword: list[str] | None = Field(None, description="Stichwörter zur Person.")
    created: datetime | None = Field(None, description="Erstellungszeitpunkt.")
    modified: datetime | None = Field(None, description="Letzte Änderung.")
    web: HttpUrl | None = Field(None, description="HTML-Ansicht der Person.")
    deleted: bool | None = Field(False, description="Markiert dieses Objekt als gelöscht (true).")


class Membership(BaseModel):
    id: HttpUrl = Field(description="Eindeutige URL der Mitgliedschaft.")
    type: str | None = Field(None, description="Typ der Mitgliedschaft")
    person: HttpUrl | None = Field(
        None,
        description="Rückverweis auf die Person, die Mitglied ist. Wird nur ausgegeben, wenn das Membership-Objekt einzeln abgerufen wird.",
    )
    organization: HttpUrl | None = Field(None, description="Die Gruppierung, in der die Person Mitglied ist oder war.")
    role: str | None = Field(
        None,
        description="Rolle der Person für die Gruppierung. Kann genutzt werden, um verschiedene Arten von Mitgliedschaften, z.B. in Gremien, zu unterscheiden.",
    )
    votingRight: bool | None = Field(None, description="Gibt an, ob die Person in der Gruppierung stimmberechtigtes Mitglied ist.")
    startDate: datetime | None = Field(None, description="Datum, an dem die Mitgliedschaft beginnt.")
    endDate: datetime | None = Field(None, description="Datum, an dem die Mitgliedschaft endet.")
    onBehalfOf: HttpUrl | None = Field(
        None,
        description="Die Gruppierung, für die die Person in der unter organization angegebenen Organisation sitzt. Beispiel: Mitgliedschaft als Vertreter einer Ratsfraktion, einer Gruppierung oder einer externen Organisation.",
    )
    license: str | None = Field(None, description="Lizenz für die veröffentlichten Daten.")
    keyword: list[str] | None = Field(None, description="Stichwörter zur Person.")
    created: datetime | None = Field(None, description="Erstellungszeitpunkt.")
    modified: datetime | None = Field(None, description="Letzte Änderung.")
    web: HttpUrl | None = Field(None, description="HTML-Ansicht der Person.")
    deleted: bool | None = Field(False, description="Markiert dieses Objekt als gelöscht (true).")


class File(BaseModel):
    id: HttpUrl = Field(description="Eindeutige URL des Dokuments.")
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
    accessUrl: HttpUrl = Field(description="Zwingend erforderliche URL für den allgemeinen Zugriff auf die Datei.")
    downloadUrl: HttpUrl | None = Field(None, description="URL zum Herunterladen der Datei.")
    externalServiceUrl: HttpUrl | None = Field(
        None, description="Externe URL, die zusätzliche Zugriffsoptionen bietet (z.B. ein YouTube-Video)."
    )
    masterFile: HttpUrl | None = Field(None, description="Datei, von der das aktuelle Objekt abgeleitet wurde.")
    derivativeFile: list[HttpUrl] | None = Field(None, description="Dateien, die von dem aktuellen Objekt abgeleitet wurden.")
    fileLicense: HttpUrl | None = Field(
        None,
        description="Lizenz, unter der die Datei angeboten wird. Wenn diese Eigenschaft nicht verwendet wird, ist der Wert von license oder die Lizenz eines übergeordneten Objektes maßgeblich.",
    )
    meeting: list[HttpUrl] | None = Field(
        None,
        description="Rückverweise auf Meeting-Objekte. Wird nur ausgegeben, wenn das File-Objekt nicht als eingebettetes Objekt aufgerufen wird.",
    )
    agendaItem: list[HttpUrl] | None = Field(
        None,
        description="Rückverweise auf AgendaItem-Objekte. Wird nur ausgegeben, wenn das File-Objekt nicht als eingebettetes Objekt aufgerufen wird.",
    )
    paper: list[HttpUrl] | None = Field(
        None,
        description="Rückverweise auf Paper-Objekte. Wird nur ausgegeben, wenn das File-Objekt nicht als eingebettetes Objekt aufgerufen wird.",
    )
    license: str | None = Field(None, description="Lizenz für die veröffentlichten Daten.")
    keyword: list[str] | None = Field(None, description="Stichwörter zur Person.")
    created: datetime | None = Field(None, description="Erstellungszeitpunkt.")
    modified: datetime | None = Field(None, description="Letzte Änderung.")
    web: HttpUrl | None = Field(None, description="HTML-Ansicht der Person.")
    deleted: bool | None = Field(False, description="Markiert dieses Objekt als gelöscht (true).")


class AgendaItem(BaseModel):
    id: HttpUrl = Field(description="Eindeutige URL des Tagesordnungspunkt.")
    type: str | None = Field(None, description="Typ des Tagesordnungspunktes")
    meeting: HttpUrl | None = Field(
        None,
        description="Rückverweis auf das Meeting, welches nur dann ausgegeben werden muss, wenn das AgendaItem-Objekt einzeln abgerufen wird.",
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
    resolutionFile: File | None = Field(
        None, description="Datei, die den Beschluss enthält, falls in diesem Tagesordnungspunkt ein Beschluss gefasst wurde."
    )
    auxiliaryFile: list[File] | None = Field(None, description="Weitere Datei-Anhänge zum Tagesordnungspunkt.")
    start: datetime | None = Field(None, description="Datum und Uhrzeit des Anfangszeitpunkts des Tagesordnungspunktes.")
    end: datetime | None = Field(None, description="Endzeitpunkt des Tagesordnungspunktes als Datum/Uhrzeit.")
    license: str | None = Field(None, description="Lizenz für die veröffentlichten Daten.")
    keyword: list[str] | None = Field(None, description="Stichwörter zur Person.")
    created: datetime | None = Field(None, description="Erstellungszeitpunkt.")
    modified: datetime | None = Field(None, description="Letzte Änderung.")
    web: HttpUrl | None = Field(None, description="HTML-Ansicht der Person.")
    deleted: bool | None = Field(False, description="Markiert dieses Objekt als gelöscht (true).")


class Paper(BaseModel):
    id: HttpUrl = Field(description="Eindeutige URL der Drucksache.")
    type: str | None = Field(None, description="Typ der Drucksache")
    body: HttpUrl | None = Field(None, description="Körperschaft, zu der die Drucksache gehört.")
    name: str | None = Field(None, description="Titel der Drucksache.")
    reference: str | None = Field(
        None,
        description="Kennung bzw. Aktenzeichen der Drucksache, mit der sie in der parlamentarischen Arbeit eindeutig referenziert werden kann.",
    )
    date: datetime | None = Field(None, description="Datum, welches als Ausgangspunkt für Fristen usw. verwendet wird.")
    paperType: str | None = Field(None, description="Art der Drucksache, z. B. Beantwortung einer Anfrage.")
    relatedPaper: list[HttpUrl] | None = Field(None, description="Inhaltlich verwandte Drucksachen.")
    superordinatedPaper: list[HttpUrl] | None = Field(None, description="Übergeordnete Drucksachen.")
    subordinatedPaper: list[HttpUrl] | None = Field(None, description="Untergeordnete Drucksachen.")
    mainFile: File | None = Field(
        None,
        description="Die Hauptdatei zu dieser Drucksache. Beispiel: Die Drucksache repräsentiert eine Beschlussvorlage und die Hauptdatei enthält den Text der Beschlussvorlage. Sollte keine eindeutige Hauptdatei vorhanden sein, wird diese Eigenschaft nicht ausgegeben.",
    )
    auxiliaryFile: list[File] | None = Field(
        None, description="Alle weiteren Dateien zur Drucksache, ausgenommen der gegebenenfalls in mainFile angegebenen."
    )
    location: list[Location] | None = Field(
        None,
        description="Sofern die Drucksache einen inhaltlichen Ortsbezug hat, beschreibt diese Eigenschaft den Ort in Textform und/oder in Form von Geodaten.",
    )
    originatorPerson: list[HttpUrl] | None = Field(
        None, description="Urheber der Drucksache, falls der Urheber eine Person ist. Es können auch mehrere Personen angegeben werden."
    )
    underDirectionOf: list[HttpUrl] | None = Field(
        None, description="Federführung. Amt oder Abteilung, für die Inhalte oder Beantwortung der Drucksache verantwortlich."
    )
    originatorOrganization: list[HttpUrl] | None = Field(
        None,
        description="Urheber der Drucksache, falls der Urheber eine Gruppierung ist. Es können auch mehrere Gruppierungen angegeben werden.",
    )
    license: str | None = Field(None, description="Lizenz für die veröffentlichten Daten.")
    keyword: list[str] | None = Field(None, description="Stichwörter zur Person.")
    created: datetime | None = Field(None, description="Erstellungszeitpunkt.")
    modified: datetime | None = Field(None, description="Letzte Änderung.")
    web: HttpUrl | None = Field(None, description="HTML-Ansicht der Person.")
    deleted: bool | None = Field(False, description="Markiert dieses Objekt als gelöscht (true).")


class Body(BaseModel):
    id: HttpUrl = Field(description="Eindeutige URL der Körperschaft.")
    type: str | None = Field(None, description="Typangabe: 'https://schema.oparl.org/1.1/Body'.")
    name: str = Field(description="Name der Körperschaft.")
    shortName: str | None = Field(None, description="Abkürzung der Körperschaft.")
    system: HttpUrl | None = Field(None, description="Verweis auf das zugehörige System-Objekt.")
    website: HttpUrl | None = Field(None, description="Offizielle Website der Körperschaft.")
    license: HttpUrl | None = Field(None, description="Standardlizenz für Daten dieser Körperschaft.")
    licenseValidSince: datetime | None = Field(None, description="Zeitpunkt, seit dem die Lizenz gilt.")
    oparlSince: datetime | None = Field(None, description="Zeitpunkt, ab dem die API für diese Körperschaft bereitsteht.")
    ags: str | None = Field(None, description="Amtlicher Gemeindeschlüssel.")
    rgs: str | None = Field(None, description="Regionalschlüssel.")
    equivalent: list[HttpUrl] | None = Field(None, description="Weitere Körperschaften mit ähnlicher Bedeutung oder Funktion.")
    contactEmail: str | None = Field(None, description="E-Mail-Adresse der Körperschaft.")
    contactName: str | None = Field(None, description="Name des Ansprechpartners.")
    organization: HttpUrl = Field(description="Liste der Organisationen der Körperschaft.")
    person: HttpUrl = Field(description="Liste der Personen der Körperschaft.")
    meeting: HttpUrl = Field(description="Liste der Sitzungen der Körperschaft.")
    paper: HttpUrl = Field(description="Liste der Vorlagen dieser Körperschaft.")
    legislativeTerm: HttpUrl = Field(description="Liste der Wahlperioden der Körperschaft.")
    agendaItem: HttpUrl = Field(description="Liste aller Tagesordnungspunkte der Körperschaft.")
    file: HttpUrl = Field(description="Liste aller Dateien der Körperschaft.")
    locationList: HttpUrl | None = Field(None, description="Liste der Orte, die mit dieser Körperschaft verknüpft sind.")
    legislativeTermList: HttpUrl = Field(description="Alternative URL zur Liste der Wahlperioden.")
    membership: HttpUrl = Field(description="Liste der Mitgliedschaften in der Körperschaft.")
    classification: str | None = Field(None, description="Art der Körperschaft, z. B. 'Stadt' oder 'Kreis'.")
    location: HttpUrl | None = Field(None, description="Ort der Verwaltung dieser Körperschaft.")
    keyword: list[str] | None = Field(None, description="Stichworte zur Körperschaft.")
    created: datetime | None = Field(None, description="Erstellungszeitpunkt.")
    modified: datetime | None = Field(None, description="Letzte Änderung.")
    web: HttpUrl | None = Field(None, description="HTML-Ansicht der Körperschaft.")
    deleted: bool | None = Field(False, description="Kennzeichnung als gelöscht.")


class Meeting(BaseModel):
    id: HttpUrl | None = Field(description="Eindeutige URL der Sitzung.")
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
    location: Location | None = Field(None, description="Sitzungsort.")
    organization: list[HttpUrl] | None = Field(
        None,
        description="Gruppierungen, denen die Sitzung zugeordnet ist. Im Regelfall wird hier eine Gruppierung verknüpft sein, es kann jedoch auch gemeinsame Sitzungen mehrerer Gruppierungen geben. Das erste Element sollte dann das federführende Gremium sein.",
    )
    participant: list[HttpUrl] | None = Field(
        None,
        description="Personen, die an der Sitzung teilgenommen haben (d.h. nicht nur die eingeladenen Personen, sondern die tatsächlich Anwesenden). Diese Eigenschaft kann selbstverständlich erst nach dem Stattfinden der Sitzung vorkommen.",
    )
    invitation: File | None = Field(None, description="Einladungsdokument zur Sitzung.")
    resultsProtocol: File | None = Field(
        None,
        description="Ergebnisprotokoll zur Sitzung. Diese Eigenschaft kann selbstverständlich erst nach dem Stattfinden der Sitzung vorkommen.",
    )
    verbatimProtocol: File | None = Field(
        None,
        description="Wortprotokoll zur Sitzung. Diese Eigenschaft kann selbstverständlich erst nach dem Stattfinden der Sitzung vorkommen.",
    )
    auxiliaryFile: list[File] | None = Field(
        None,
        description="Dateianhang zur Sitzung. Hiermit sind Dateien gemeint, die üblicherweise mit der Einladung zu einer Sitzung verteilt werden, und die nicht bereits über einzelne Tagesordnungspunkte referenziert sind.",
    )
    agendaItem: list[AgendaItem] | None = Field(
        None, description="Tagesordnungspunkte der Sitzung. Die Reihenfolge ist relevant. Es kann Sitzungen ohne TOPs geben."
    )
    license: str | None = Field(None, description="Lizenz für die veröffentlichten Daten.")
    keyword: list[str] | None = Field(None, description="Stichwörter zur Sitzung.")
    created: datetime | None = Field(None, description="Erstellungszeitpunkt.")
    modified: datetime | None = Field(None, description="Letzte Änderung.")
    web: HttpUrl | None = Field(None, description="HTML-Ansicht der Sitzung.")
    deleted: bool | None = Field(False, description="Markiert dieses Objekt als gelöscht (true).")


class ExtractArtifact(BaseModel):
    meetings: list[Meeting]


# Forward references for Membership and AgendaItem
Person.model_rebuild()
Meeting.model_rebuild()
AgendaItem.model_rebuild()
