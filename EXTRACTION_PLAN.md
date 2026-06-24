# Plan: Vollständiges Datenmodell füllen

## Status Übersicht

### ✅ Bereits befüllt (6 Extraktoren aktiv)
1. **Person** → PersonParser (StR-Mitglieder, BA-Mitglieder, Referenten)
2. **Organization** → CityCouncilFactionExtractor + GremiumOrganizationParser (Fraktionen, Ausschüsse, Bezirksausschüsse)
3. **Paper** → CityCouncilMotionExtractor, CityCouncilMeetingTemplateExtractor, BAMotionExtractor, BVRecommendationExtractor, BVRequestExtractor
4. **Meeting** → CityCouncilMeetingExtractor
5. **File** → während Paper-Extraktion (via downloadlinks)
6. **Keyword** → ad-hoc während allen Extraktion (Stadtbezirke, etc.)
7. **LegislativeTerm** → ad-hoc beim Parsen (via get_or_create_legislative_term)

### ⚠️ Noch nicht befüllt (direkt)
- **Body** — OParl-Konzept, nicht im RIS einzeln abrufbar
- **System** — OParl-Konzept, nicht im RIS einzeln abrufbar
- **Location** — nicht standalone abrufbar, nur via Meetings/Papers als Verweise
- **AgendaItem** — nur via Meeting-Detail-Seiten abrufbar
- **Membership** — Relationen zwischen Person und Organization
- **Consultation** — Relationen zwischen Paper und AgendaItem/Meeting
- **Post** — Positionen in Organizationen (z.B. "Vorsitzender")

### 🔗 Link-Tabellen (automatisch befüllt via relationships)
- FileDerivativeLink, FileAgendaItemLink, FileMeetingLink, FileKeywordLink, PaperFileLink
- PaperRelatedPaper, PaperSuperordinatedLink, PaperSubordinatedLink
- PaperLocationLink, PaperOriginatorPersonLink, PaperOriginatorOrgLink, PaperDirectionLink, PaperKeywordLink
- LocationBodies, LocationOrganizations, LocationPersons, LocationMeetings, LocationPapers, LocationKeyword
- MeetingOrganizationLink, MeetingParticipantLink, MeetingAgendaItemLink, MeetingKeywordLink
- PersonMembershipLink, MembershipKeyword, OrganizationMembership, OrganizationSubOrganization, OrganizationKeyword
- BodyKeywordLink, BodyEquivalentLink
- PersonKeywordLink, AgendaItemKeywordLink, LegislativeTermKeyword, ConsultationKeywordLink

---

## Implementierungs-Roadmap

### Phase 1: Meeting Details & AgendaItems (HIGH PRIORITY)
**Ziel:** Meetings mit ihren AgendaItems und damit verbundene Locations und Consultations füllen

#### 1.1 Meeting Detail Parser Enhancement
- **Was:** Meeting-Detail-Seiten parsen für erweiterte Informationen
  - Gremium (Organization) → MeetingOrganizationLink
  - Teilnehmer (Person) → MeetingParticipantLink
  - Tagesordnungspunkte (AgendaItems) → MeetingAgendaItemLink
  - Ort (Location) → LocationMeetings
- **Wie:** CityCouncilMeetingParser erweitern (aktuell nur Meeting-Basis)
- **Effort:** 2-4h

#### 1.2 AgendaItem Parser
- **Was:** Aus Meeting-Details AgendaItems extrahieren
  - AgendaItem Basis (name, number, order, public)
  - Verknüpfung zu Meeting
  - Verknüpfung zu Papers/Documents
- **Wie:** Neue Klasse `MeetingAgendaItemExtractor`
- **Effort:** 3-5h

#### 1.3 Location Extraction (via Meetings)
- **Was:** Ortsangaben aus Meeting-Details extrahieren/erstellen
  - Venue/Ort der Sitzung
  - Verknüpfung zu Meeting, Organization
- **Wie:** Helper-Funktion in db_access.py für Location creation; Meeting-Parser nutzen
- **Effort:** 2-3h

#### 1.4 Consultation Relations
- **Was:** Verknüpfung Paper → AgendaItem (Consultation)
  - Aus Meeting-Details: welche Papers wurden auf welcher Agenda behandelt
- **Wie:** Während AgendaItem-Extraktion erstellen
- **Effort:** 1-2h

---

### Phase 2: Membership & Organization Relations
**Ziel:** Beziehungen zwischen Personen und Organisationen füllen

#### 2.1 Membership Parser (via Gremium Details)
- **Was:** Person-Organization Zugehörigkeiten extrahieren
  - Startdatum, Enddatum, Rolle (Member, Vorsitzender, etc.)
  - Person → Organization Links
  - Wahlperiode
- **Wie:** GremiumOrganizationParser erweitern (Gremium-Detail-Seiten haben Mitgliederlisten)
- **Effort:** 3-4h

#### 2.2 Gremium Hierarchie (SubOrganizations)
- **Was:** Ausschuss-Struktur (Unterausschüsse, etc.)
  - Organization → subOrganizations
  - Aus Gremium-Übersicht/Details
- **Wie:** Beim GremiumOrganizationParser extraktion
- **Effort:** 1-2h

#### 2.3 Post Extraction (Positionen)
- **Was:** Rollen in Organizationen (Vorsitzender, Stellvertreter, etc.)
  - Post (name, organization)
  - Aus Gremium-Details/Mitgliederlisten
- **Wie:** Helper für Post creation; GremiumOrganizationParser nutzen
- **Effort:** 2-3h

---

### Phase 3: System & Body (OParl Standard)
**Ziel:** OParl-Basis-Entitäten befüllen

#### 3.1 System & Body Seed
- **Was:** Manuelle Initialisierung (nicht via RIS abrufbar)
  - System: https://schema.oparl.org/1.1/System für München RIS
  - Body: Landeshauptstadt München als übergeordnete Body
  - Optionale weitere Bodies: Bezirksausschüsse als Sub-Bodies
- **Wie:** Migration-Script oder Init-SQL
- **Effort:** 1-2h

#### 3.2 Body-Verknüpfungen
- **Was:** Body zu existierenden Entities verknüpfen (optional)
  - Body → Organizations, Persons, Papers, etc.
- **Wie:** Nach Body-Seed via Migration oder ad-hoc in Parsern
- **Effort:** 1h (optional)

---

### Phase 4: Paper Relations & Advanced
**Ziel:** Papierhierarchie und erweiterte Relationen füllen

#### 4.1 Paper Relations (via Paper-Details)
- **Was:** Zwischen Papers:
  - Related Papers (verwandte Anträge)
  - Subordinated Papers (ist Bestandteil von)
  - Superordinated Papers (enthält)
- **Wie:** Aus Paper-Detail-Seiten (Links zu verwandten Papers)
- **Effort:** 2-3h

#### 4.2 Paper Locations (via Paper Details)
- **Was:** Ortsangaben aus Papers (Stadtbezirke, Straßen, etc.)
  - Paper → Location (welche Orte betroffen)
  - Location → Paper (welche Papers betreffen diesen Ort)
- **Wie:** Paper-Parser erweitern
- **Effort:** 1-2h

#### 4.3 Paper → Originator Relations
- **Was:** Bereits teilweise done (via Parsern)
  - Verifizieren und vollständig machen
  - Paper → Person (Initiator)
  - Paper → Organization (Initiator)
  - Paper → Organization (Richtung/verantwortlich)
- **Wie:** Review+Enhancement der Motion/BV Parsers
- **Effort:** 1-2h

---

### Phase 5: Keywords & Advanced Relations
**Ziel:** Keywords und weitere Verknüpfungen vollständig

#### 5.1 Enhanced Keyword Extraction
- **Was:** Keywords aus Paper/Meeting/Person/Organization Details
  - Themen, Bezirke, Deput-Zuständigkeiten, etc.
- **Wie:** Erweiterte Parser-Logik
- **Effort:** 2-3h

#### 5.2 Verify Link Tables
- **Was:** Sicherstellen dass alle Relationships automatisch befüllt sind
  - via SQLModel Relationships (bei update_or_insert)
  - Besonders: MeetingParticipant, OrganizationMembership, etc.
- **Wie:** Smoke-Tests nach Phase 1-4
- **Effort:** 1-2h

---

## Priorisierung & Schätzung

### High Priority (kritisch für RIS Daten)
- **Phase 1:** Meeting Details & AgendaItems → 8-14h (Kern des RIS)
- **Phase 2:** Membership & Gremium Hierarchie → 6-9h (Wer sitzt wo)

### Medium Priority (inhaltlich wichtig)
- **Phase 4.1-4.2:** Paper Relations & Locations → 3-5h (Papierkontext)

### Low Priority (OParl Standard, optional)
- **Phase 3:** System & Body → 2-3h (optional, nur für OParl Vollständigkeit)
- **Phase 4.3:** Paper Originator Review → 1-2h (mostly done)
- **Phase 5:** Enhanced Keywords → 3-5h (nice-to-have)

---

## Geschätzter Gesamtaufwand

| Phase | Effort | Kritikalität |
|-------|--------|--------------|
| 1. Meeting & AgendaItem | 8-14h | 🔴 CRITICAL |
| 2. Membership & Org Relations | 6-9h | 🔴 CRITICAL |
| 3. System & Body | 2-3h | 🟡 OPTIONAL |
| 4. Paper Relations | 3-5h | 🟢 MEDIUM |
| 5. Keywords & Advanced | 3-5h | 🟢 MEDIUM |
| **Testing & Verification** | **3-5h** | **🔴 CRITICAL** |
| **Total** | **25-41h** | |

---

## Nächste Schritte

1. **Sofort (Phase 1.1-1.2):** Meeting & AgendaItem Parser implementieren
   - Höchste Priorität: ohne Meetings & AgendaItems ist RIS unvollständig
   
2. **Dann (Phase 2):** Membership & Gremium Hierarchie
   - Zeigt "Wer sitzt wo" — essentiell für Analyse
   
3. **Später:** Paper Relations & Advanced (nice-to-have Verbesserungen)

4. **Optional:** System/Body (nur wenn OParl 100% Compliance nötig)

---

## Notes

- **Bestehende Extractors können parallel erweitert werden** — kein Konflikt
- **Link-Tabellen werden automatisch befüllt** via SQLModel Relationships
- **Location ist Bottle-Neck** — nicht standalone abrufbar, muss ad-hoc erstellt werden
- **Tests nötig für jede Phase** — Smoke-Tests dass Daten in DB landen
