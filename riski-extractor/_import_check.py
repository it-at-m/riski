"""Quick import check to validate all new extractors/parsers load without errors."""

import sys

try:
    from src.extractor.ba_member_extractor import BAMemberExtractor
    from src.extractor.bezirksausschuss_paper_extractor import (
        BAMotionExtractor,
        BVRecommendationExtractor,
        BVRequestExtractor,
    )
    from src.extractor.gremium_organization_extractor import (
        BACommitteeExtractor,
        StRCommitteeExtractor,
    )
    from src.extractor.legislative_term_extractor import LegislativeTermExtractor
    from src.extractor.location_extractor import LocationExtractor

    print("[OK] All new extractors and parsers imported successfully")
    print(f"  BAMemberExtractor: {BAMemberExtractor}")
    print(f"  BAMotionExtractor: {BAMotionExtractor}")
    print(f"  BVRecommendationExtractor: {BVRecommendationExtractor}")
    print(f"  BVRequestExtractor: {BVRequestExtractor}")
    print(f"  StRCommitteeExtractor: {StRCommitteeExtractor}")
    print(f"  BACommitteeExtractor: {BACommitteeExtractor}")
    print(f"  LegislativeTermExtractor: {LegislativeTermExtractor}")
    print(f"  LocationExtractor: {LocationExtractor}")
    sys.exit(0)
except Exception as e:
    print(f"[FAIL] Import failed: {e!r}")
    import traceback

    traceback.print_exc()
    sys.exit(1)
