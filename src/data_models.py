from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, HttpUrl


class System(BaseModel):
    id: HttpUrl = Field(..., description="Die eindeutige URL dieses Objekts.")
    type: Optional[str] = Field(None, description="Der feste Typ des Objekts: 'https://schema.oparl.org/1.1/System'.")
    oparlVersion: str = Field(..., description="Die vom System unterstützte OParl-Version (z. B. 'https://schema.oparl.org/1.1/').")
    otherOparlVersions: Optional[List[HttpUrl]] = Field(
        None, description="Dient der Angabe von System-Objek­ten mit ande­ren OParl-Versio­nen."
    )
    license: Optional[HttpUrl] = Field(
        None, description="Lizenz, unter der durch diese API abruf­ba­ren Daten stehen, sofern nicht am einzel­nen Objekt anders ange­ge­ben."
    )
    body: HttpUrl = Field(..., description="Link zur Objektliste mit allen Körperschaf­ten, die auf dem System exis­tie­ren.")
    name: Optional[str] = Field(
        None,
        description="Nutzer­freund­li­cher Name für das System, mit dessen Hilfe Nutze­rin­nen und Nutzer das System erken­nen und von ande­ren unter­schei­den können.",
    )
    contactEmail: Optional[EmailStr] = Field(
        None,
        description="E-Mail-Adresse für Anfra­gen zur OParl-API. Die Angabe einer E-Mail-Adresse dient sowohl NutzerIn­nen wie auch Entwick­le­rin­nen von Clients zur Kontakt­auf­nahme mit dem Betrei­ber.",
    )
    contactName: Optional[str] = Field(
        None,
        description="Name der Ansprech­part­ne­rin bzw. des Ansprech­part­ners oder der Abtei­lung, die über die in contactEmail ange­ge­bene Adresse erreicht werden kann.",
    )
    website: Optional[HttpUrl] = Field(None, description="URL der Website des parla­men­ta­ri­schen Infor­ma­ti­ons­sys­tems")
    vendor: Optional[HttpUrl] = Field(None, description="URL der Website des Soft­wa­rean­bie­ters, von dem die OParl-Server-Soft­ware stammt.")
    product: Optional[HttpUrl] = Field(None, description="URL zu Infor­ma­tio­nen über die auf dem System genutzte OParl-Server-Soft­ware")
    created: Optional[datetime] = Field(None, description="Zeitpunkt der Erstellung dieses Objekts.")
    modified: Optional[datetime] = Field(None, description="Zeitpunkt der letzten Änderung dieses Objekts.")
    web: Optional[HttpUrl] = Field(None, description="URL zur HTML-Ansicht dieses Objekts.")
    deleted: Optional[bool] = Field(False, description="Markiert dieses Objekt als gelöscht (true).")


class Location(BaseModel):
    id: HttpUrl = Field(..., description="Die eindeutige URL des Orts.")
    type: Optional[str] = Field(None, description="Typ des Orts")
    description: Optional[str] = Field(None, description="Textuelle Beschreibung eines Orts, z. B. in Form einer Adresse.")
    geojson: Optional[dict] = Field(
        None,
        description="Geodaten-Repräsentation des Orts. Muss der GeoJSON-Spezifikation entsprechen, d.h. es muss ein vollständiges Feature-Objekt ausgegeben werden.",
    )
    streetAddress: Optional[str] = Field(None, description="Straße und Hausnummer der Anschrift.")
    room: Optional[str] = Field(None, description="Raumangabe der Anschrift.")
    postalCode: Optional[str] = Field(None, description="Postleitzahl der Anschrift.")
    subLocality: Optional[str] = Field(None, description="Untergeordnete Ortsangabe der Anschrift, z.B. Stadtbezirk, Ortsteil oder Dorf.")
    locality: Optional[str] = Field(None, description="Ortsangabe der Anschrift.")
    bodies: Optional[List[HttpUrl]] = Field(
        None,
        description="Rückverweise auf Body-Objekte. Wird nur ausgegeben, wenn das Location-Objekt nicht als eingebettetes Objekt aufgerufen wird.",
    )
    organizations: Optional[List[HttpUrl]] = Field(
        None,
        description="Rückverweise auf Organisation-Objekte. Wird nur ausgegeben, wenn das Location-Objekt nicht als eingebettetes Objekt aufgerufen wird.",
    )
    persons: Optional[List[HttpUrl]] = Field(
        None,
        description="Rückverweise auf Person-Objekte. Wird nur ausgegeben, wenn das Location-Objekt nicht als eingebettetes Objekt aufgerufen wird.",
    )
    meetings: Optional[List[HttpUrl]] = Field(
        None,
        description="Rückverweise auf Meeting-Objekte. Wird nur ausgegeben, wenn das Location-Objekt nicht als eingebettetes Objekt aufgerufen wird.",
    )
    papers: Optional[List[HttpUrl]] = Field(
        None,
        description="Rückverweise auf Paper-Objekte. Wird nur ausgegeben, wenn das Location-Objekt nicht als eingebettetes Objekt aufgerufen wird.",
    )
    license: Optional[str] = Field(None, description="Lizenz für die bereitgestellten Informationen.")
    keyword: Optional[List[str]] = Field(None, description="Stichwörter zur Wahlperiode.")
    created: Optional[datetime] = Field(None, description="Erstellungszeitpunkt.")
    modified: Optional[datetime] = Field(None, description="Letzte Änderung.")
    web: Optional[HttpUrl] = Field(None, description="HTML-Ansicht des Objekts.")
    deleted: Optional[bool] = Field(False, description="Markiert dieses Objekt als gelöscht (true).")


class LegislativeTerm(BaseModel):
    id: HttpUrl = Field(..., description="Eindeutige URL der Wahlperiode.")
    type: Optional[str] = Field(None, description="Typ des Objekts: 'https://schema.oparl.org/1.1/LegislativeTerm'.")
    body: Optional[HttpUrl] = Field(None, description="Verweis auf die Körperschaft, zu der die Wahlperiode gehört.")
    name: Optional[str] = Field(None, description="Bezeichnung der Wahlperiode.")
    startDate: Optional[datetime] = Field(None, description="Beginn der Wahlperiode.")
    endDate: Optional[datetime] = Field(None, description="Ende der Wahlperiode.")
    license: Optional[str] = Field(None, description="Lizenz für die bereitgestellten Informationen.")
    keyword: Optional[List[str]] = Field(None, description="Stichwörter zur Wahlperiode.")
    created: Optional[datetime] = Field(None, description="Erstellungszeitpunkt.")
    modified: Optional[datetime] = Field(None, description="Letzte Änderung.")
    web: Optional[HttpUrl] = Field(None, description="HTML-Ansicht des Objekts.")
    deleted: Optional[bool] = Field(False, description="Markiert dieses Objekt als gelöscht (true).")


class Organization(BaseModel):
    id: HttpUrl = Field(..., description="Eindeutige URL der Organisation.")
    type: Optional[str] = Field(None, description="Typ des Objekts: 'https://schema.oparl.org/1.1/Organization'.")
    body: Optional[HttpUrl] = Field(None, description="Verweis auf die Körperschaft, zu der die Organisation gehört.")
    name: Optional[str] = Field(None, description="Bezeichnung der Organisation.")
    membership: Optional[List[HttpUrl]] = Field(None, description="Liste der zugehörigen Mitgliedschaften.")
    meeting: Optional[HttpUrl] = Field(None, description="Liste der Sitzungen dieser Organisation.")
    shortName: Optional[str] = Field(None, description="Abkürzung der Organisation.")
    post: Optional[List[str]] = Field(None, description="Posten oder Ämter, die in der Organisation existieren.")
    subOrganizationOf: Optional[HttpUrl] = Field(None, description="Verweis auf die übergeordnete Organisation.")
    organizationType: Optional[str] = Field(None, description="Typ der Organisation, z. B. Ausschuss, Fraktion.")
    classification: Optional[str] = Field(None, description="Klassifizierung, z. B. gesetzlich, freiwillig.")
    startDate: Optional[datetime] = Field(None, description="Beginn der Organisation.")
    endDate: Optional[datetime] = Field(None, description="Beendigung der Organisation.")
    website: Optional[HttpUrl] = Field(None, description="Website der Organisation.")
    location: Optional[HttpUrl] = Field(None, description="Ort, an dem die Organisation ansässig ist.")
    externalBody: Optional[HttpUrl] = Field(None, description="Verweis auf eine externe Körperschaft (nur bei Importen).")
    license: Optional[str] = Field(None, description="Lizenz für die veröffentlichten Daten.")
    keyword: Optional[List[str]] = Field(None, description="Stichwörter zur Organisation.")
    created: Optional[datetime] = Field(None, description="Erstellungszeitpunkt.")
    modified: Optional[datetime] = Field(None, description="Letzte Änderung.")
    web: Optional[HttpUrl] = Field(None, description="HTML-Ansicht der Organisation.")
    deleted: Optional[bool] = Field(False, description="Markiert dieses Objekt als gelöscht (true).")


class Person(BaseModel):
    id: HttpUrl = Field(..., description="Eindeutige URL der Person.")
    type: Optional[str] = Field(None, description="Typ des Objekts: 'https://schema.oparl.org/1.1/Person'.")
    body: Optional[HttpUrl] = Field(None, description="Verweis auf die Körperschaft, in der die Person aktiv ist.")
    name: Optional[str] = Field(None, description="Vollständiger Name der Person.")
    familyName: Optional[str] = Field(None, description="Nachname der Person.")
    givenName: Optional[str] = Field(None, description="Vorname der Person.")
    formOfAddress: Optional[str] = Field(None, description="Anrede der Person (z. B. Frau, Herr).")
    affix: Optional[str] = Field(None, description="Namenszusatz (z. B. von, zu, Freiherr).")
    title: Optional[List[str]] = Field(None, description="Titel der Person (z. B. Dr., Prof.).")
    gender: Optional[str] = Field(None, description="Geschlecht der Person.")
    phone: Optional[List[str]] = Field(None, description="Telefonnummer(n) der Person.")
    email: Optional[List[str]] = Field(None, description="E-Mail-Adresse(n) der Person.")
    location: Optional[HttpUrl] = Field(None, description="Verweis auf einen Ort, der mit der Person verknüpft ist.")
    status: Optional[List[str]] = Field(None, description="Statusinformationen zur Person (z. B. Mandat ruhend).")
    membership: Optional[List[HttpUrl]] = Field(None, description="Verweise auf Mitgliedschaften.")
    life: Optional[str] = Field(None, description="Lebensdaten der Person (z. B. Geburtsdatum).")
    lifeSource: Optional[str] = Field(None, description="Quelle der Lebensdaten.")
    license: Optional[str] = Field(None, description="Lizenz für die veröffentlichten Daten.")
    keyword: Optional[List[str]] = Field(None, description="Stichwörter zur Person.")
    created: Optional[datetime] = Field(None, description="Erstellungszeitpunkt.")
    modified: Optional[datetime] = Field(None, description="Letzte Änderung.")
    web: Optional[HttpUrl] = Field(None, description="HTML-Ansicht der Person.")
    deleted: Optional[bool] = Field(False, description="Markiert dieses Objekt als gelöscht (true).")


class Membership(BaseModel):
    id: HttpUrl = Field(..., description="Eindeutige URL der Mitgliedschaft.")
    type: Optional[str] = Field(None, description="Typ der Mitgliedschaft")
    person: Optional[HttpUrl] = Field(
        None,
        description="Rückverweis auf die Person, die Mitglied ist. Wird nur ausgegeben, wenn das Membership-Objekt einzeln abgerufen wird.",
    )
    organization: Optional[HttpUrl] = Field(None, description="Die Gruppierung, in der die Person Mitglied ist oder war.")
    role: Optional[str] = Field(
        None,
        description="Rolle der Person für die Gruppierung. Kann genutzt werden, um verschiedene Arten von Mitgliedschaften, z.B. in Gremien, zu unterscheiden.",
    )
    votingRight: Optional[bool] = Field(None, description="Gibt an, ob die Person in der Gruppierung stimmberechtigtes Mitglied ist.")
    startDate: Optional[datetime] = Field(None, description="Datum, an dem die Mitgliedschaft beginnt.")
    endDate: Optional[datetime] = Field(None, description="Datum, an dem die Mitgliedschaft endet.")
    onBehalfOf: Optional[HttpUrl] = Field(
        None,
        description="Die Gruppierung, für die die Person in der unter organization angegebenen Organisation sitzt. Beispiel: Mitgliedschaft als Vertreter einer Ratsfraktion, einer Gruppierung oder einer externen Organisation.",
    )
    license: Optional[str] = Field(None, description="Lizenz für die veröffentlichten Daten.")
    keyword: Optional[List[str]] = Field(None, description="Stichwörter zur Person.")
    created: Optional[datetime] = Field(None, description="Erstellungszeitpunkt.")
    modified: Optional[datetime] = Field(None, description="Letzte Änderung.")
    web: Optional[HttpUrl] = Field(None, description="HTML-Ansicht der Person.")
    deleted: Optional[bool] = Field(False, description="Markiert dieses Objekt als gelöscht (true).")


class File(BaseModel):
    id: HttpUrl = Field(..., description="Eindeutige URL des Dokuments.")
    type: Optional[str] = Field(None, description="Typ der Datei")
    name: Optional[str] = Field(
        None, description="Benutzerfreundlicher Name für das Objekt. Sollte keine Dateiendungen wie '.pdf' enthalten."
    )
    fileName: Optional[str] = Field(
        None,
        description="Dateiname, unter dem die Datei in einem Dateisystem gespeichert werden kann (z.B. 'eineDatei.pdf'). Clients sollten sicherstellen, dass dieser Name den lokalen Anforderungen an Dateisysteme entspricht.",
    )
    mimeType: Optional[str] = Field(None, description="MIME-Typ der Datei")
    date: Optional[datetime] = Field(None, description="Datum, das als Ausgangspunkt für Fristen usw. verwendet wird.")
    size: Optional[int] = Field(None, description="Größe der Datei in Bytes")
    sha1Checksum: Optional[str] = Field(
        None,
        description="[Veraltet] SHA1-Prüfziffer des Dateiinhalt in hexadezimaler Schreibweise. Sollte nicht mehr verwendet werden, da SHA1 als unsicher gilt. Stattdessen sollte sha512Checksum verwendet werden.",
    )
    sha512Checksum: Optional[str] = Field(None, description="SHA512-Prüfziffer des Dateiinhalt in hexadezimaler Schreibweise.")
    text: Optional[str] = Field(
        None, description="Reine Textwiedergabe des Dateiinhalts, sofern dieser in Textform wiedergegeben werden kann."
    )
    accessUrl: HttpUrl = Field(None, description="Zwingend erforderliche URL für den allgemeinen Zugriff auf die Datei.")
    downloadUrl: Optional[HttpUrl] = Field(None, description="URL zum Herunterladen der Datei.")
    externalServiceUrl: Optional[HttpUrl] = Field(
        None, description="Externe URL, die zusätzliche Zugriffsoptionen bietet (z.B. ein YouTube-Video)."
    )
    masterFile: Optional[HttpUrl] = Field(None, description="Datei, von der das aktuelle Objekt abgeleitet wurde.")
    derivativeFile: Optional[List[HttpUrl]] = Field(None, description="Dateien, die von dem aktuellen Objekt abgeleitet wurden.")
    fileLicense: Optional[HttpUrl] = Field(
        None,
        description="Lizenz, unter der die Datei angeboten wird. Wenn diese Eigenschaft nicht verwendet wird, ist der Wert von license oder die Lizenz eines übergeordneten Objektes maßgeblich.",
    )
    meeting: Optional[List[HttpUrl]] = Field(
        None,
        description="Rückverweise auf Meeting-Objekte. Wird nur ausgegeben, wenn das File-Objekt nicht als eingebettetes Objekt aufgerufen wird.",
    )
    agendaItem: Optional[List[HttpUrl]] = Field(
        None,
        description="Rückverweise auf AgendaItem-Objekte. Wird nur ausgegeben, wenn das File-Objekt nicht als eingebettetes Objekt aufgerufen wird.",
    )
    paper: Optional[List[HttpUrl]] = Field(
        None,
        description="Rückverweise auf Paper-Objekte. Wird nur ausgegeben, wenn das File-Objekt nicht als eingebettetes Objekt aufgerufen wird.",
    )
    license: Optional[str] = Field(None, description="Lizenz für die veröffentlichten Daten.")
    keyword: Optional[List[str]] = Field(None, description="Stichwörter zur Person.")
    created: Optional[datetime] = Field(None, description="Erstellungszeitpunkt.")
    modified: Optional[datetime] = Field(None, description="Letzte Änderung.")
    web: Optional[HttpUrl] = Field(None, description="HTML-Ansicht der Person.")
    deleted: Optional[bool] = Field(False, description="Markiert dieses Objekt als gelöscht (true).")


class AgendaItem(BaseModel):
    id: HttpUrl = Field(..., description="Eindeutige URL des Tagesordnungspunkt.")
    type: Optional[str] = Field(None, description="Typ des Tagesordnungspunktes")
    meeting: Optional[HttpUrl] = Field(
        None,
        description="Rückverweis auf das Meeting, welches nur dann ausgegeben werden muss, wenn das AgendaItem-Objekt einzeln abgerufen wird.",
    )
    number: Optional[str] = Field(
        None,
        description="Gliederungs-Nummer des Tagesordnungspunktes. Eine beliebige Zeichenkette, wie z. B. '10.', '10.1', 'C', 'c)' o. ä.",
    )
    order: Optional[int] = Field(
        None,
        description="Die Position des Tagesordnungspunktes in der Sitzung, beginnend bei 0. Diese Nummer entspricht der Position in Meeting:agendaItem.",
    )
    name: Optional[str] = Field(None, description="Das Thema des Tagesordnungspunktes.")
    public: Optional[bool] = Field(
        None, description="Kennzeichnet, ob der Tagesordnungspunkt zur Behandlung in öffentlicher Sitzung vorgesehen ist/war."
    )
    result: Optional[str] = Field(
        None,
        description="Kategorische Information über das Ergebnis der Beratung des Tagesordnungspunktes, z. B. 'Unverändert beschlossen' oder 'Geändert beschlossen'.",
    )
    resolutionText: Optional[str] = Field(
        None, description="Text des Beschlusses, falls in diesem Tagesordnungspunkt ein Beschluss gefasst wurde."
    )
    resolutionFile: Optional[File] = Field(
        None, description="Datei, die den Beschluss enthält, falls in diesem Tagesordnungspunkt ein Beschluss gefasst wurde."
    )
    auxiliaryFile: Optional[List[File]] = Field(None, description="Weitere Datei-Anhänge zum Tagesordnungspunkt.")
    start: Optional[datetime] = Field(None, description="Datum und Uhrzeit des Anfangszeitpunkts des Tagesordnungspunktes.")
    end: Optional[datetime] = Field(None, description="Endzeitpunkt des Tagesordnungspunktes als Datum/Uhrzeit.")
    license: Optional[str] = Field(None, description="Lizenz für die veröffentlichten Daten.")
    keyword: Optional[List[str]] = Field(None, description="Stichwörter zur Person.")
    created: Optional[datetime] = Field(None, description="Erstellungszeitpunkt.")
    modified: Optional[datetime] = Field(None, description="Letzte Änderung.")
    web: Optional[HttpUrl] = Field(None, description="HTML-Ansicht der Person.")
    deleted: Optional[bool] = Field(False, description="Markiert dieses Objekt als gelöscht (true).")


class Paper(BaseModel):
    id: HttpUrl = Field(..., description="Eindeutige URL der Drucksache.")
    type: Optional[str] = Field(None, description="Typ der Drucksache")
    body: Optional[HttpUrl] = Field(None, description="Körperschaft, zu der die Drucksache gehört.")
    name: Optional[str] = Field(None, description="Titel der Drucksache.")
    reference: Optional[str] = Field(
        None,
        description="Kennung bzw. Aktenzeichen der Drucksache, mit der sie in der parlamentarischen Arbeit eindeutig referenziert werden kann.",
    )
    date: Optional[datetime] = Field(None, description="Datum, welches als Ausgangspunkt für Fristen usw. verwendet wird.")
    paperType: Optional[str] = Field(None, description="Art der Drucksache, z. B. Beantwortung einer Anfrage.")
    relatedPaper: Optional[List[HttpUrl]] = Field(None, description="Inhaltlich verwandte Drucksachen.")
    superordinatedPaper: Optional[List[HttpUrl]] = Field(None, description="Übergeordnete Drucksachen.")
    subordinatedPaper: Optional[List[HttpUrl]] = Field(None, description="Untergeordnete Drucksachen.")
    mainFile: Optional[File] = Field(
        None,
        description="Die Hauptdatei zu dieser Drucksache. Beispiel: Die Drucksache repräsentiert eine Beschlussvorlage und die Hauptdatei enthält den Text der Beschlussvorlage. Sollte keine eindeutige Hauptdatei vorhanden sein, wird diese Eigenschaft nicht ausgegeben.",
    )
    auxiliaryFile: Optional[List[File]] = Field(
        None, description="Alle weiteren Dateien zur Drucksache, ausgenommen der gegebenenfalls in mainFile angegebenen."
    )
    location: Optional[List[Location]] = Field(
        None,
        description="Sofern die Drucksache einen inhaltlichen Ortsbezug hat, beschreibt diese Eigenschaft den Ort in Textform und/oder in Form von Geodaten.",
    )
    originatorPerson: Optional[List[HttpUrl]] = Field(
        None, description="Urheber der Drucksache, falls der Urheber eine Person ist. Es können auch mehrere Personen angegeben werden."
    )
    underDirectionOf: Optional[List[HttpUrl]] = Field(
        None, description="Federführung. Amt oder Abteilung, für die Inhalte oder Beantwortung der Drucksache verantwortlich."
    )
    originatorOrganization: Optional[List[HttpUrl]] = Field(
        None,
        description="Urheber der Drucksache, falls der Urheber eine Gruppierung ist. Es können auch mehrere Gruppierungen angegeben werden.",
    )
    license: Optional[str] = Field(None, description="Lizenz für die veröffentlichten Daten.")
    keyword: Optional[List[str]] = Field(None, description="Stichwörter zur Person.")
    created: Optional[datetime] = Field(None, description="Erstellungszeitpunkt.")
    modified: Optional[datetime] = Field(None, description="Letzte Änderung.")
    web: Optional[HttpUrl] = Field(None, description="HTML-Ansicht der Person.")
    deleted: Optional[bool] = Field(False, description="Markiert dieses Objekt als gelöscht (true).")


class Body(BaseModel):
    id: HttpUrl = Field(..., description="Eindeutige URL der Körperschaft.")
    type: Optional[str] = Field(None, description="Typangabe: 'https://schema.oparl.org/1.1/Body'.")
    name: str = Field(..., description="Name der Körperschaft.")
    shortName: Optional[str] = Field(None, description="Abkürzung der Körperschaft.")
    system: Optional[HttpUrl] = Field(None, description="Verweis auf das zugehörige System-Objekt.")
    website: Optional[HttpUrl] = Field(None, description="Offizielle Website der Körperschaft.")
    license: Optional[HttpUrl] = Field(None, description="Standardlizenz für Daten dieser Körperschaft.")
    licenseValidSince: Optional[datetime] = Field(None, description="Zeitpunkt, seit dem die Lizenz gilt.")
    oparlSince: Optional[datetime] = Field(None, description="Zeitpunkt, ab dem die API für diese Körperschaft bereitsteht.")
    ags: Optional[str] = Field(None, description="Amtlicher Gemeindeschlüssel.")
    rgs: Optional[str] = Field(None, description="Regionalschlüssel.")
    equivalent: Optional[List[HttpUrl]] = Field(None, description="Weitere Körperschaften mit ähnlicher Bedeutung oder Funktion.")
    contactEmail: Optional[str] = Field(None, description="E-Mail-Adresse der Körperschaft.")
    contactName: Optional[str] = Field(None, description="Name des Ansprechpartners.")
    organization: HttpUrl = Field(..., description="Liste der Organisationen der Körperschaft.")
    person: HttpUrl = Field(..., description="Liste der Personen der Körperschaft.")
    meeting: HttpUrl = Field(..., description="Liste der Sitzungen der Körperschaft.")
    paper: HttpUrl = Field(..., description="Liste der Vorlagen dieser Körperschaft.")
    legislativeTerm: HttpUrl = Field(..., description="Liste der Wahlperioden der Körperschaft.")
    agendaItem: HttpUrl = Field(..., description="Liste aller Tagesordnungspunkte der Körperschaft.")
    file: HttpUrl = Field(..., description="Liste aller Dateien der Körperschaft.")
    locationList: HttpUrl = Field(Nodescription="Liste der Orte, die mit dieser Körperschaft verknüpft sind.")
    legislativeTermList: HttpUrl = Field(..., description="Alternative URL zur Liste der Wahlperioden.")
    membership: HttpUrl = Field(..., description="Liste der Mitgliedschaften in der Körperschaft.")
    classification: Optional[str] = Field(None, description="Art der Körperschaft, z. B. 'Stadt' oder 'Kreis'.")
    location: Optional[HttpUrl] = Field(None, description="Ort der Verwaltung dieser Körperschaft.")
    keyword: Optional[List[str]] = Field(None, description="Stichworte zur Körperschaft.")
    created: Optional[datetime] = Field(None, description="Erstellungszeitpunkt.")
    modified: Optional[datetime] = Field(None, description="Letzte Änderung.")
    web: Optional[HttpUrl] = Field(None, description="HTML-Ansicht der Körperschaft.")
    deleted: Optional[bool] = Field(False, description="Kennzeichnung als gelöscht.")


class Meeting(BaseModel):
    id: HttpUrl = Field(..., description="Eindeutige URL der Sitzung.")
    type: Optional[str] = Field(None, description="Typ der Sitzung")
    name: Optional[str] = Field(None, description="Name der Sitzung.")
    meetingState: Optional[str] = Field(
        None,
        description="Aktueller Status der Sitzung. Empfohlene Werte sind 'terminiert' (geplant), 'eingeladen' (vor der Sitzung bis zur Freigabe des Protokolls) und 'durchgeführt' (nach Freigabe des Protokolls).",
    )
    cancelled: Optional[bool] = Field(None, description="Wenn die Sitzung ausfällt, wird 'cancelled' auf true gesetzt.")
    start: Optional[datetime] = Field(
        None,
        description="Datum und Uhrzeit des Anfangszeitpunkts der Sitzung. Bei einer zukünftigen Sitzung ist dies der geplante Zeitpunkt, bei einer stattgefundenen kann es der tatsächliche Startzeitpunkt sein.",
    )
    end: Optional[datetime] = Field(
        None,
        description="Endzeitpunkt der Sitzung als Datum/Uhrzeit. Bei einer zukünftigen Sitzung ist dies der geplante Zeitpunkt, bei einer stattgefundenen kann es der tatsächliche Endzeitpunkt sein.",
    )
    location: Optional[Location] = Field(None, description="Sitzungsort.")
    organization: Optional[List[HttpUrl]] = Field(
        None,
        description="Gruppierungen, denen die Sitzung zugeordnet ist. Im Regelfall wird hier eine Gruppierung verknüpft sein, es kann jedoch auch gemeinsame Sitzungen mehrerer Gruppierungen geben. Das erste Element sollte dann das federführende Gremium sein.",
    )
    participant: Optional[List[HttpUrl]] = Field(
        None,
        description="Personen, die an der Sitzung teilgenommen haben (d.h. nicht nur die eingeladenen Personen, sondern die tatsächlich Anwesenden). Diese Eigenschaft kann selbstverständlich erst nach dem Stattfinden der Sitzung vorkommen.",
    )
    invitation: Optional[File] = Field(None, description="Einladungsdokument zur Sitzung.")
    resultsProtocol: Optional[File] = Field(
        None,
        description="Ergebnisprotokoll zur Sitzung. Diese Eigenschaft kann selbstverständlich erst nach dem Stattfinden der Sitzung vorkommen.",
    )
    verbatimProtocol: Optional[File] = Field(
        None,
        description="Wortprotokoll zur Sitzung. Diese Eigenschaft kann selbstverständlich erst nach dem Stattfinden der Sitzung vorkommen.",
    )
    auxiliaryFile: Optional[List[File]] = Field(
        None,
        description="Dateianhang zur Sitzung. Hiermit sind Dateien gemeint, die üblicherweise mit der Einladung zu einer Sitzung verteilt werden, und die nicht bereits über einzelne Tagesordnungspunkte referenziert sind.",
    )
    agendaItem: Optional[List[AgendaItem]] = Field(
        None, description="Tagesordnungspunkte der Sitzung. Die Reihenfolge ist relevant. Es kann Sitzungen ohne TOPs geben."
    )
    license: Optional[str] = Field(None, description="Lizenz für die veröffentlichten Daten.")
    keyword: Optional[List[str]] = Field(None, description="Stichwörter zur Person.")
    created: Optional[datetime] = Field(None, description="Erstellungszeitpunkt.")
    modified: Optional[datetime] = Field(None, description="Letzte Änderung.")
    web: Optional[HttpUrl] = Field(None, description="HTML-Ansicht der Person.")
    deleted: Optional[bool] = Field(False, description="Markiert dieses Objekt als gelöscht (true).")


# Forward references for Membership and AgendaItem
Person.model_rebuild()
Meeting.model_rebuild()
AgendaItem.model_rebuild()
