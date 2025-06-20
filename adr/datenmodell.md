# Datenmodell für die Abbildung von RIS

## Status
Vorgeschlagen

## Kontext
Das RIS (Rat-Informations-System) verwaltet verschiedene gesetzgeberische Prozesse, einschließlich Sitzungen, Tagesordnungspunkte, Anträge und Dokumente. Das Ziel dieses ADR ist es, zu definieren, wie die Datenstrukturen innerhalb des RIS für uns am besten dargestellt werden können. Eine Möglichkeit ist OParl. OParl ist eine standardisierte API für öffentliche Daten parlamentarischer Prozesse, die die Zugänglichkeit und Interoperabilität von Regierungsdaten verbessert.

## Mapping RIS auf Oparl

| **RIS Entität**              | **OParl Entität**    | 
|------------------------------|----------------------|
| STR_SITZUNG                  | MEETING              |
| TAGESORDNUNGSPUNKT           | AGENDA_ITEM          | 
| VORGANG                      | PAPER                |
| DOKUMENT                     | FILE                 | 
| ANTRAG                       | PAPER                | 
| BV_Empfehlung                | PAPER                | 
| SITZUNGSVORLAGE              | PAPER                | 
| AUSSCHUSS                    | ORGANIZATION         |
| MITGLIEDER                   | PERSON               |
| Wahlperiode                  | LEGISLATIVE_TERM     |
| indirekt über Vorsitz, Fraktionszugehörigkeit, etc... |MEMBERSHIP |
| jegliche Ortsangaben         | LOCATION             |
|                              | CONSULTATION         |
| (nur bei Oparl Schnittstelle)|BODY                  |
| (nur bei Oparl Schnittstelle)| SYSTEM               |

