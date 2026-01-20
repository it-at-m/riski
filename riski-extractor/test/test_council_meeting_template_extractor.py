import os

from core.model.data_models import Person
from sqlalchemy import func
from sqlmodel import select
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

    extractor.parser.parse(url_1, html_data_1)
    extractor.parser.parse(url_2, html_data_1)

    statement = select(func.count()).select_from(Person).where(Person.familyName == "Doe")
    person_count = session.exec(statement).one()
    assert person_count == 1, f"Person Doe should be in DB exactly once. Found: {person_count}"
