import os
from unittest.mock import patch

import pytest
from core.model.data_models import Person
from src.parser.person_parser import PersonParser


def load_html(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()


def _create_html(name="Frau Dr. Laura Dornheim", status="Referent*in", life="IT-Referentin seit 2022"):
    html_template = load_html(os.path.join(os.path.dirname(__file__), "test_person_template.html"))
    print(name)
    html_template = html_template.replace(">>name<<", name)
    html_template = html_template.replace(">>status<<", status)
    html_template = html_template.replace(">>life<<", life)
    return html_template


@pytest.fixture
def parser():
    return PersonParser()


@patch("src.parser.person_parser.request_person_by_full_name")
def test_new_person(mock_request_person_by_full_name, parser):
    mock_request_person_by_full_name.return_value = None

    url = "http://example.com/person/3"
    html = _create_html()
    person = parser.parse(url, html)
    print(person)
    assert person.familyName == "Dornheim"
    assert person.givenName == "Laura"
    assert person.name == "Frau Dr. Laura Dornheim"
    assert person.formOfAddress == "Frau"
    assert person.life == "IT-Referentin seit 2022"
    assert person.lifeSource == url
    assert person.status == ["Referent*in"]
    assert person.title == "Dr."
    assert person.web == url
    assert not person.deleted


@patch("src.parser.person_parser.request_person_by_full_name")
def test_existing_person_with_no_name(mock_request_person_by_full_name, parser):
    existing_person = Person(
        id="http://example.com/person/2",
        familyName="Dornheim",
        givenName="Laura",
        name=None,
        formOfAddress=None,
        life=None,
        lifeSource=None,
        status=["Referent*in"],
        title="Dr.",
        web="http://example.com/person/2",
        deleted=False,
    )
    mock_request_person_by_full_name.return_value = existing_person

    url = "http://example.com/person/3"
    html = _create_html()
    person = parser.parse(url, html)

    assert person.name == "Frau Dr. Laura Dornheim"
    assert person.life == "IT-Referentin seit 2022"
    assert person.lifeSource == url
    assert person.status == ["Referent*in"]


@patch("src.parser.person_parser.request_person_by_full_name")
def test_existing_person_with_no_form_of_address(mock_request_person_by_full_name, parser):
    existing_person = Person(
        id="http://example.com/person/2",
        familyName="Dornheim",
        givenName="Laura",
        name="Frau Dr. Laura Dornheim",
        formOfAddress=None,
        life="IT-Referentin seit 2022",
        lifeSource="http://example.com/person/2",
        status=["Referent*in"],
        title="Dr.",
        web="http://example.com/person/2",
        deleted=False,
    )
    mock_request_person_by_full_name.return_value = existing_person

    url = "http://example.com/person/3"
    html = _create_html()
    person = parser.parse(url, html)

    assert person.formOfAddress == "Frau"


@patch("src.parser.person_parser.request_person_by_full_name")
def test_existing_person_with_shorter_life(mock_request_person_by_full_name, parser):
    existing_person = Person(
        id="http://example.com/person/2",
        familyName="Dornheim",
        givenName="Laura",
        name="Frau Dr. Laura Dornheim",
        formOfAddress="Frau",
        life="IT-Referentin seit 2022",
        lifeSource="http://example.com/person/2",
        status=["Professor"],
        title="Dr.",
        web="http://example.com/person/2",
        deleted=False,
    )
    mock_request_person_by_full_name.return_value = existing_person

    url = "http://example.com/person/3"
    html = _create_html(life="IT-Referentin seit September 2022")
    person = parser.parse(url, html)

    assert person.life == "IT-Referentin seit September 2022"


@patch("src.parser.person_parser.request_person_by_full_name")
def test_existing_person_with_different_status(mock_request_person_by_full_name, parser):
    existing_person = Person(
        id="http://example.com/person/2",
        familyName="Dornheim",
        givenName="Laura",
        name="Frau Dr. Laura Dornheim",
        formOfAddress="Frau",
        life="IT-Referentin seit 2022",
        lifeSource="http://example.com/person/2",
        status=["Referent*in"],
        title="Dr.",
        web="http://example.com/person/2",
        deleted=False,
    )
    mock_request_person_by_full_name.return_value = existing_person

    url = "http://example.com/person/3"
    html = _create_html(status="Stadtratsmitglied")
    person = parser.parse(url, html)

    assert "Referent*in" in person.status
    assert "Stadtratsmitglied" in person.status
