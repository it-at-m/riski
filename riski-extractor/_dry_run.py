"""Dry-run test: instantiate all extractors without running extraction."""

import sys

try:
    print("[1/9] Importing extractors...")
    from src.extractor.ba_member_extractor import BAMemberExtractor
    from src.extractor.bezirksausschuss_paper_extractor import (
        BAMotionExtractor,
        BVRecommendationExtractor,
        BVRequestExtractor,
    )
    from src.extractor.city_council_faction_extractor import CityCouncilFactionExtractor
    from src.extractor.city_council_meeting_extractor import CityCouncilMeetingExtractor
    from src.extractor.city_council_meeting_template_extractor import CityCouncilMeetingTemplateExtractor
    from src.extractor.city_council_member_extractor import CityCouncilMemberExtractor
    from src.extractor.city_council_motion_extractor import CityCouncilMotionExtractor
    from src.extractor.gremium_organization_extractor import (
        BACommitteeExtractor,
        StRCommitteeExtractor,
    )
    from src.extractor.head_of_department_extractor import HeadOfDepartmentExtractor
    from src.extractor.legislative_term_extractor import LegislativeTermExtractor
    from src.extractor.location_extractor import LocationExtractor

    print("[2/9] Instantiating all extractors...")
    extractors = [
        ("CityCouncilFactionExtractor", CityCouncilFactionExtractor()),
        ("CityCouncilMemberExtractor", CityCouncilMemberExtractor()),
        ("HeadOfDepartmentExtractor", HeadOfDepartmentExtractor()),
        ("CityCouncilMeetingExtractor", CityCouncilMeetingExtractor()),
        ("CityCouncilMeetingTemplateExtractor", CityCouncilMeetingTemplateExtractor()),
        ("CityCouncilMotionExtractor", CityCouncilMotionExtractor()),
        ("BAMemberExtractor", BAMemberExtractor()),
        ("BAMotionExtractor", BAMotionExtractor()),
        ("BVRecommendationExtractor", BVRecommendationExtractor()),
        ("BVRequestExtractor", BVRequestExtractor()),
        ("StRCommitteeExtractor", StRCommitteeExtractor()),
        ("BACommitteeExtractor", BACommitteeExtractor()),
        ("LegislativeTermExtractor", LegislativeTermExtractor()),
        ("LocationExtractor", LocationExtractor()),
    ]

    print(f"[3/14] {len(extractors)} extractors instantiated:")
    for name, ext in extractors:
        print(f"  - {name}: {ext.__class__.__name__}")

    print("[14/14] Dry-run complete. All extractors ready.")
    sys.exit(0)
except Exception as e:
    print(f"[FAIL] {e!r}")
    import traceback

    traceback.print_exc()
    sys.exit(1)
