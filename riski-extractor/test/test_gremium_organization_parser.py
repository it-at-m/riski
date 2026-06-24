"""Tests for GremiumOrganizationParser membership extraction (Task 2.1)."""

from unittest.mock import patch, MagicMock
import pytest
from core.model.data_models import Organization, OrganizationClassificationEnum, OrganizationTypeEnum
from src.parser.gremium_organization_parser import GremiumOrganizationParser


@pytest.fixture
def parser():
    return GremiumOrganizationParser(
        classification=OrganizationClassificationEnum.COMMITTEE,
        org_type=OrganizationTypeEnum.COMMITTEE,
    )


def _create_gremium_html(
    title="Sportausschuss",
    short_name="StA",
    term="2026-2032",
    members_html="",
):
    """Create a minimal gremium detail page HTML."""
    return f"""
    <html>
    <head><title>{title}</title></head>
    <body>
        <h1 class="page-title">{title}</h1>
        <div class="keyvalue-container">
            <div class="keyvalue-row">
                <div class="keyvalue-key">Kürzel:</div>
                <div class="keyvalue-value">{short_name}</div>
            </div>
            <div class="keyvalue-row">
                <div class="keyvalue-key">Wahlperiode:</div>
                <div class="keyvalue-value">{term}</div>
            </div>
        </div>
        <div class="members-section">
            {members_html}
        </div>
    </body>
    </html>
    """


@patch("src.parser.gremium_organization_parser.create_membership")
def test_parse_basic_organization(mock_create_membership, parser):
    """Test basic organization parsing without members."""
    url = "https://risi.muenchen.de/gremium/detail/123"
    html = _create_gremium_html(title="Sportausschuss", short_name="SpA")

    org = parser.parse(url, html)

    assert org is not None
    assert org.name == "Sportausschuss"
    assert org.shortName == "SpA"
    assert org.id == url


def test_extract_dates_from_parent(parser):
    """Test German date extraction (dd.mm.yyyy -> yyyy-mm-dd)."""
    # Test single date
    start, end = parser._extract_dates_from_parent(MagicMock())
    assert start is None

    # Test date conversion
    iso_date = parser._german_date_to_iso("01.01.2026")
    assert iso_date == "2026-01-01"

    iso_date = parser._german_date_to_iso("31.12.2032")
    assert iso_date == "2032-12-31"

    # Test invalid date
    iso_date = parser._german_date_to_iso("invalid")
    assert iso_date is None


def test_extract_role_basic(parser):
    """Test basic role extraction."""
    # Test "Vorsitz" role
    mock_element = MagicMock()
    mock_parent = MagicMock()
    mock_element.parent = mock_parent
    mock_parent.get_text.return_value = "Dr. Max Mustermann (Vorsitz) - 01.01.2026 - 31.12.2032"
    mock_parent.parent = None

    role = parser._extract_role_from_context(mock_element)
    assert role == "Vorsitz"

    # Test "Stellvertreter" role
    mock_parent.get_text.return_value = "Dr. Maria Musterfrau (Stellvertreter) - 01.01.2026"
    role = parser._extract_role_from_context(mock_element)
    assert role == "Stellvertreter"

    # Test "Schriftführer" role
    mock_parent.get_text.return_value = "Dr. Hans Hansen (Schriftführer)"
    role = parser._extract_role_from_context(mock_element)
    assert role == "Schriftführer"

    # Test default "Mitglied"
    mock_parent.get_text.return_value = "Dr. Anna Andersen"
    role = parser._extract_role_from_context(mock_element)
    assert role == "Mitglied"


@patch("src.parser.gremium_organization_parser.create_membership")
def test_extract_members_with_dates(mock_create_membership, parser):
    """Test member extraction with dates and roles."""
    members_html = """
    <div class="member-row">
        <strong>Vorsitz:</strong>
        <a href="/person/detail/101">Dr. Max Mustermann</a> - 01.01.2026 - 31.12.2032
    </div>
    <div class="member-row">
        <strong>Mitglieder:</strong>
        <ul>
            <li>
                <a href="/person/detail/102">Maria Musterfrau</a> (Stellvertreter)
                - 01.01.2026 - 31.12.2032
            </li>
            <li>
                <a href="/person/detail/103">Hans Hansen</a>
                - 15.03.2026 - 30.09.2030
            </li>
        </ul>
    </div>
    """
    url = "https://risi.muenchen.de/gremium/detail/456"
    html = _create_gremium_html(members_html=members_html)

    parser.extract_memberships(url, html)

    # Verify create_membership was called for each member
    assert mock_create_membership.call_count == 3

    # Check first call (Vorsitz) - use positional or keyword args
    first_call = mock_create_membership.call_args_list[0]
    call_kwargs = first_call.kwargs if first_call.kwargs else dict(zip(
        ['person_id', 'organization_id', 'role', 'start_date', 'end_date', 'voting_right', 'on_behalf_of'],
        first_call.args
    ))
    assert "101" in call_kwargs.get("person_id", "")
    assert call_kwargs.get("role") == "Vorsitz"
    assert call_kwargs.get("start_date") == "2026-01-01"
    assert call_kwargs.get("end_date") == "2032-12-31"

    # Check second call - just verify person 102 is there with dates
    second_call = mock_create_membership.call_args_list[1]
    call_kwargs = second_call.kwargs if second_call.kwargs else dict(zip(
        ['person_id', 'organization_id', 'role', 'start_date', 'end_date', 'voting_right', 'on_behalf_of'],
        second_call.args
    ))
    assert "102" in call_kwargs.get("person_id", "")
    assert call_kwargs.get("start_date") == "2026-01-01"
    assert call_kwargs.get("end_date") == "2032-12-31"

    # Check third call - person 103 with different dates
    third_call = mock_create_membership.call_args_list[2]
    call_kwargs = third_call.kwargs if third_call.kwargs else dict(zip(
        ['person_id', 'organization_id', 'role', 'start_date', 'end_date', 'voting_right', 'on_behalf_of'],
        third_call.args
    ))
    assert "103" in call_kwargs.get("person_id", "")
    assert call_kwargs.get("start_date") == "2026-03-15"
    assert call_kwargs.get("end_date") == "2030-09-30"


@patch("src.parser.gremium_organization_parser.create_membership")
def test_extract_members_without_dates(mock_create_membership, parser):
    """Test member extraction when dates are not available."""
    members_html = """
    <div class="members-list">
        <a href="/person/detail/201">Anna Andersen</a>
        <a href="/person/detail/202">Boris Borisov</a>
    </div>
    """
    url = "https://risi.muenchen.de/gremium/detail/789"
    html = _create_gremium_html(members_html=members_html)

    parser.extract_memberships(url, html)

    # Both members should be created without dates
    assert mock_create_membership.call_count == 2
    for call in mock_create_membership.call_args_list:
        call_kwargs = call.kwargs if call.kwargs else dict(zip(
            ['person_id', 'organization_id', 'role', 'start_date', 'end_date', 'voting_right', 'on_behalf_of'],
            call.args
        ))
        assert call_kwargs.get("start_date") is None
        assert call_kwargs.get("end_date") is None
        assert call_kwargs.get("role") == "Mitglied"


@patch("src.parser.gremium_organization_parser.create_membership")
def test_no_duplicate_memberships(mock_create_membership, parser):
    """Test that duplicate member links don't create duplicate memberships."""
    members_html = """
    <div class="members">
        <a href="/person/detail/301">Person One</a>
        <a href="/person/detail/301">Person One</a>  <!-- duplicate -->
        <a href="/person/detail/302">Person Two</a>
    </div>
    """
    url = "https://risi.muenchen.de/gremium/detail/999"
    html = _create_gremium_html(members_html=members_html)

    parser.extract_memberships(url, html)

    # Should only create 2 memberships, not 3 (deduped)
    assert mock_create_membership.call_count == 2


def test_extract_sub_organization_urls_basic(parser):
    """Test extraction of sub-organization URLs."""
    html = """
    <html>
    <body>
        <h1>Hauptausschuss</h1>
        <div class="sub-orgs">
            <p>Unterausschüsse:</p>
            <a href="/gremium/detail/456">Unterausschuss A</a>
            <a href="/gremium/detail/457">Unterausschuss B</a>
        </div>
    </body>
    </html>
    """
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    sub_urls = parser._extract_sub_organization_urls(soup)

    assert len(sub_urls) >= 2
    assert "https://risi.muenchen.de/gremium/detail/456" in sub_urls
    assert "https://risi.muenchen.de/gremium/detail/457" in sub_urls


def test_extract_sub_organization_urls_with_relative_paths(parser):
    """Test extraction with relative paths."""
    html = """
    <html>
    <body>
        <h1>Ausschuss</h1>
        <div class="section">
            <p>ist Unterausschuss von:</p>
            <a href="../gremium/detail/789">Übergeordneter Ausschuss</a>
        </div>
    </body>
    </html>
    """
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    sub_urls = parser._extract_sub_organization_urls(soup)

    # Should resolve relative path to full URL with 789
    assert len(sub_urls) > 0
    assert any("789" in url for url in sub_urls)


def test_extract_sub_organization_urls_empty(parser):
    """Test extraction when no sub-organizations exist."""
    html = """
    <html>
    <body>
        <h1>Einzelner Ausschuss</h1>
        <p>Keine Unterausschüsse vorhanden</p>
    </body>
    </html>
    """
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    sub_urls = parser._extract_sub_organization_urls(soup)

    assert len(sub_urls) == 0
