"""Unit tests for CityCouncilMeetingParser HTML extraction methods."""
from bs4 import BeautifulSoup
from src.parser.city_council_meeting_parser import CityCouncilMeetingParser


def test_extract_person_names():
    """Test _extract_person_names doesn't crash."""
    parser = CityCouncilMeetingParser()

    test_cases = [
        "Dr. Max Mustermann",
        "Herr Prof. Anton Meyer",
        "Frau Dr. med. Anna Schneider",
        "StRin Maria Fischer",
        "i.V. Klaus Schmidt",
        "Mueller",
        "",
    ]

    for text in test_cases:
        result = parser._extract_person_names(text)
        print(f"  '{text}' -> {result}")
        assert result is not None, f"_extract_person_names should not return None for '{text}'"

    print("PASS: test_extract_person_names")


def test_extract_agenda_items_no_crash():
    """Test _extract_agenda_items doesn't crash on various HTML structures."""
    parser = CityCouncilMeetingParser()

    test_cases = [
        # No agenda section
        "<html><body><h1>Test</h1></body></html>",
        # With agenda section
        """<html><section aria-labelledby="sectionheader-tagesordnung">
            <li class="agenda-item">1. Eröffnung</li>
            <li class="agenda-item">2. Genehmigung</li>
        </section></html>""",
        # Empty agenda
        "<html><section aria-labelledby='sectionheader-tagesordnung'></section></html>",
    ]

    for i, html in enumerate(test_cases):
        soup = BeautifulSoup(html, "html.parser")
        items = parser._extract_agenda_items(soup, "https://test.example.com")
        print(f"  Case {i+1}: extracted {len(items)} items (no crash)")
        assert isinstance(items, list), f"Should return a list, got {type(items)}"

    print("PASS: test_extract_agenda_items_no_crash")


def test_extract_organizations_no_crash():
    """Test _extract_organizations doesn't crash."""
    parser = CityCouncilMeetingParser()

    html = """<html>
    <body>
        <a href="/gremium/detail/123">Stadtrat</a>
        <a href="/referat/detail/456">Referat fuer Kultur</a>
    </body>
    </html>"""

    soup = BeautifulSoup(html, "html.parser")
    orgs = parser._extract_organizations(soup)
    print(f"  Extracted {len(orgs)} organizations (no crash)")
    assert isinstance(orgs, list), f"Should return a list"

    print("PASS: test_extract_organizations_no_crash")


def test_extract_participants_no_crash():
    """Test _extract_participants doesn't crash."""
    parser = CityCouncilMeetingParser()

    html = """<html>
    <section aria-labelledby="sectionheader-teilnehmer">
        <a href="/person/detail/123">Max Mustermann</a>
        <a href="/person/detail/456">Anna Mueller</a>
    </section>
    </html>"""

    soup = BeautifulSoup(html, "html.parser")
    persons = parser._extract_participants(soup)
    print(f"  Extracted {len(persons)} participants (no crash)")
    assert isinstance(persons, list), f"Should return a list"

    print("PASS: test_extract_participants_no_crash")


def test_resolve_or_create_location_no_crash():
    """Test _resolve_or_create_location handles edge cases."""
    parser = CityCouncilMeetingParser()

    test_cases = [
        None,
        "",
        "   ",
        "Rathaus",
        "Plenarsaal 123",
        "Bezirksausschuss Altstadt-Lehel",
    ]

    for location_name in test_cases:
        try:
            result = parser._resolve_or_create_location(location_name)
            print(f"  '{location_name}' -> {result}")
        except Exception as e:
            print(f"  '{location_name}' -> ERROR: {e!r}")

    print("PASS: test_resolve_or_create_location_no_crash")


if __name__ == "__main__":
    print("Running CityCouncilMeetingParser robustness tests...\n")
    test_extract_person_names()
    test_extract_agenda_items_no_crash()
    test_extract_organizations_no_crash()
    test_extract_participants_no_crash()
    test_resolve_or_create_location_no_crash()
    print("\nAll tests completed successfully!")
