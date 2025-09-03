# Extraction process Structure

## Process

We decided that the extraction process should be split into two steps.
First the extraction of the entities and then afterwards the extraction of the relations.
The Entites should be written to the database without any relations and in the second step the
relations should be added for all the entities.

## Reasoning

We are extracting all the data out of the plain HTML of the RIS wihtout any access to the datastore.
Thererfore we also need to extract the relations out of the HTML. Sometimes those are represented as Hyperlinks
and sometimes it is only plain Text. If wewant to create all the relations in the first run, we would need to create very
large nested objects and would end up with very huge extractor classes.

So we decided to spliut the extraction into the steps mentioned above, to first retreive all the information for the entities
and then in a second run we gather all the information for the relations. With this design we can always lookup the entities we want to create a relation for 
in the database and if they exist create the relation, and if they do not exist log an ERROR and skip the relation.

With this approach we do need more time for the process as we basically iteerate over the entities/pages twice, but we can keep our code much more lean, readable
and understandable.

## Entities

### Entity Extractor

The entity extractor only care about the data which is part of this entity only. It does not care about any relations in any way.
It is only ressponssible for getting the HTML for this specifi entity.

### Entity Parser

The entity parser creates the object to write to the DB for the specific entity type. It does not care about relations and sets them to None.

## Relations

### Relations Extractor

The relations extractor should be responsible for creating the relations based on the results the relations parser delivers.
It should query the database for the corresponding entries and save the newly created relation to the database

### Relations Parser

The relations parser should only look up the relations for a entity in the HTML. It does not care about any other inforamtion regarding the entities.

## Problems

This apporach can lead to some problems e.g. we have entities that need relations in the Database but there is no way to get all the entites in the RIS on their own.
This applies to Locations, every City Council Meeting has a Location where it takes place but those Locations can only be reteived via the Meeting.
The Meetings often take place in the same Locations but it is not poossible to find them on other pages in the RIS to have a distinct list of those Locations.
Therefore we need to develop a mechanism for such entites to have an initial fill for our database so that we can link them with the realtions.

Another problem is, that not all relations are provided as hyperlinks in the RIS, sometimes it is just text, so we need to be aware of this and need to figure out
how we can still identify the correct database entries. This applies to the related people in City Council Motions. These are only reffered by their name and their role
e.g. "Herr STR Thomas Müller", this string cannot be found in the database as we do save name and role seperately, so we need to be aware of this.
