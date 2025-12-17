# Data model for mapping RIS

## Status

Accepted

## Context

The RIS (Rat-Informations-System = Council Information System) manages various legislative processes, including meetings, agenda items, motions, and documents. The goal of this ADR is to define how the data structures within the RIS can best be represented for us. One possibility is OParl. OParl is a standardized API for public data from parliamentary processes that improves the accessibility and interoperability of government data.

## Mapping RIS to Oparl

| **RIS Entity**                                        | **OParl Entity** |
| ----------------------------------------------------- | ---------------- |
| STR_SITZUNG                                           | MEETING          |
| TAGESORDNUNGSPUNKT                                    | AGENDA_ITEM      |
| VORGANG                                               | PAPER            |
| DOKUMENT                                              | FILE             |
| ANTRAG                                                | PAPER            |
| BV_Empfehlung                                         | PAPER            |
| SITZUNGSVORLAGE                                       | PAPER            |
| AUSSCHUSS                                             | ORGANIZATION     |
| MITGLIEDER                                            | PERSON           |
| Wahlperiode                                           | LEGISLATIVE_TERM |
| indirekt über Vorsitz, Fraktionszugehörigkeit, etc... | MEMBERSHIP       |
| jegliche Ortsangaben                                  | LOCATION         |
|                                                       | CONSULTATION     |
| (nur bei Oparl Schnittstelle)                         | BODY             |
| (nur bei Oparl Schnittstelle)                         | SYSTEM           |

A city council MEETING (StR_Sitzung) has multiple AGENDA_ITEMs of which each can have a "Sitzungsvorlage" or "Beschlussvorlage" (PAPER with accompanying FILE). This relates to one or multiple StR_Antrag or BV_Empfehlung (different type of PAPER). So these will for now be modeled via the relationship relatedPaper. The consultation about those will result in the AGENDA_ITEM's result str, resolutionText, and resolutionFile. A StR_Antrag that wasn't consulted about yet (i.e. when being created) will only exist in its relation to its initiating originatorPersons and/or originatorOrganizations.
An AGENDA_ITEM can probably consult about only parts of a StR_Antrag and the decision about it (result) can be delayed, so multiple AGENDA_ITEMs can relate to the same StR_Antrag/BV_Empfehlung. That fact is modeled by the list of CONSULTATIONs that the PAPER (= StR_Antrag in that case) contains.

![Entity relationship diagram to show the relationships between city council applications](Stadtratsantrag_relations_dark.png)

## Paper Types

| **Type Identification** |
| ----------------------- |
| Str-Antrag              |
| BA-Antrag               |
| Sitzungsvorlage         |
| BV-Empfehlung           |
| BV-Anfrage              |

### Subtypes

#### Str-Antrag

| **Type Identification** |
| ----------------------- |
| Dringlichkeitsantrag    |
| Antrag                  |
| Anfrage                 |
| Änderungsantrag         |
| Ergänzungsantrag        |

#### BA-Antrag

| **Type Identification** |
| ----------------------- |
| BA-Antrag               |

#### BV-Empfehlung

| **Type Identification** |
| ----------------------- |
| BV-Empfehlung           |

#### BV-Anfrage

| **Type Identification** |
| ----------------------- |
| BV-Anfrage              |

#### Sitzungsvorlage

| **Type Identification** |
| ----------------------- |
| Beschlussvorlage VB     |
| Beschlussvorlage SB     |
| Beschlussvorlage SB+VB  |
| Bekanntgabe             |
| Direkt                  |
| Sitzungsvorlage zur DA  |
