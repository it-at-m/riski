import os
from unittest.mock import patch

from sqlalchemy import func
from sqlmodel import select
from src.data_models import Person
from src.db.db_access import get_or_insert_object_to_database, insert_and_return_object, request_person_by_familyName
from src.extractor.city_council_meeting_template_extractor import CityCouncilMeetingTemplateExtractor


def load_html(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()


def test_extractor_with_different_person(session):
    extractor = CityCouncilMeetingTemplateExtractor()

    html_data_1 = load_html(os.path.join(os.path.dirname(__file__), "test_council_meeting_template_extractor_html.html"))
    html_data_2 = load_html(os.path.join(os.path.dirname(__file__), "test_council_meeting_template_extractor_html_2.html"))

    url_1 = "http://example.com/template_1"
    url_2 = "http://example.com/template_2"

    # Patching the db-access methods used in the parser, to ensure usage of the correct db-session
    def insert_person_patched(object):
        return insert_and_return_object(object, session)

    def request_person_by_familyName_patched(familyName, logger):
        return request_person_by_familyName(familyName, logger, session)

    def get_or_insert_patched(object):
        return get_or_insert_object_to_database(object, session)

    with (
        patch("src.parser.city_council_meeting_template_parser.insert_and_return_object") as insert_person,
        patch("src.parser.city_council_meeting_template_parser.request_person_by_familyName") as request_person,
        patch("src.parser.city_council_meeting_template_parser.get_or_insert_object_to_database") as get_or_insert,
    ):
        insert_person.side_effect = insert_person_patched
        request_person.side_effect = request_person_by_familyName_patched
        get_or_insert.side_effect = get_or_insert_patched

        extractor.parser.parse(url_1, html_data_1)
        extractor.parser.parse(url_2, html_data_2)

    statement = select(func.count()).select_from(Person)
    person_count = session.exec(statement).one()
    assert person_count == 2, f"There should be exactly 2 people in the db. Found: {person_count}"
    statement = select(func.count()).select_from(Person).where(Person.familyName == "Doe")
    person_count = session.exec(statement).one()
    assert person_count == 1, f"Person Doe should be in DB exactly once. Found: {person_count}"
    statement = select(func.count()).select_from(Person).where(Person.familyName == "Joe")
    person_count = session.exec(statement).one()
    assert person_count == 1, f"Person Joe should be in DB exactly once. Found: {person_count}"


def test_extractor_with_same_person(session):
    extractor = CityCouncilMeetingTemplateExtractor()

    html_data_1 = load_html(os.path.join(os.path.dirname(__file__), "test_council_meeting_template_extractor_html.html"))

    url_1 = "http://example.com/template_1"
    url_2 = "http://example.com/template_2"

    # Patching the db-access methods used in the parser, to ensure usage of the correct db-session
    def insert_person_patched(object):
        return insert_and_return_object(object, session)

    def request_person_by_familyName_patched(familyName, logger):
        return request_person_by_familyName(familyName, logger, session)

    def get_or_insert_patched(object):
        return get_or_insert_object_to_database(object, session)

    with (
        patch("src.parser.city_council_meeting_template_parser.insert_and_return_object") as insert_person,
        patch("src.parser.city_council_meeting_template_parser.request_person_by_familyName") as request_person,
        patch("src.parser.city_council_meeting_template_parser.get_or_insert_object_to_database") as get_or_insert,
    ):
        insert_person.side_effect = insert_person_patched
        request_person.side_effect = request_person_by_familyName_patched
        get_or_insert.side_effect = get_or_insert_patched

        extractor.parser.parse(url_1, html_data_1)
        extractor.parser.parse(url_2, html_data_1)

    statement = select(func.count()).select_from(Person).where(Person.familyName == "Doe")
    person_count = session.exec(statement).one()
    assert person_count == 1, f"Person Doe should be in DB exactly once. Found: {person_count}"
