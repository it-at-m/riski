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
        <h1>{title}</h1>
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


def test_parse_basic_organization(parser):
    """Test basic organization parsing without members."""
    url = "https://risi.muenchen.de/gremium/detail/123"
    html = _create_gremium_html(title="Sportausschuss", short_name="SpA")

    with patch("src.parser.gremium_organization_parser.create_membership"):
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

    org = parser.parse(url, html)

    # Verify create_membership was called for each member
    assert mock_create_membership.call_count == 3

    # Check first call (Vorsitz)
    first_call = mock_create_membership.call_args_list[0]
    assert "101" in first_call[1]["person_id"]
    assert first_call[1]["role"] == "Vorsitz"
    assert first_call[1]["start_date"] == "2026-01-01"
    assert first_call[1]["end_date"] == "2032-12-31"

    # Check second call (Stellvertreter)
    second_call = mock_create_membership.call_args_list[1]
    assert "102" in second_call[1]["person_id"]
    assert second_call[1]["role"] == "Stellvertreter"

    # Check third call (regular member with different dates)
    third_call = mock_create_membership.call_args_list[2]
    assert "103" in third_call[1]["person_id"]
    assert third_call[1]["role"] == "Mitglied"
    assert third_call[1]["start_date"] == "2026-03-15"
    assert third_call[1]["end_date"] == "2030-09-30"


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

    org = parser.parse(url, html)

    # Both members should be created without dates
    assert mock_create_membership.call_count == 2
    for call in mock_create_membership.call_args_list:
        assert call[1]["start_date"] is None
        assert call[1]["end_date"] is None
        assert call[1]["role"] == "Mitglied"


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

    org = parser.parse(url, html)

    # Should only create 2 memberships, not 3 (deduped)
    assert mock_create_membership.call_count == 2
