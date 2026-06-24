"""Throwaway end-to-end smoke test for a single extractor against live RIS + DB."""

import sys

from config.config import get_config
from core.db.db import create_db_and_tables, init_db
from core.db.db_access import request_all
from core.model.data_models import LegislativeTerm, Location, Organization, Paper, Person
from src.extractor.bezirksausschuss_paper_extractor import BAMotionExtractor


def main():
    config = get_config()
    init_db(config.core.db.database_url)
    create_db_and_tables()
    print(f"date range: {config.start_date} .. {config.end_date}")

    ext = BAMotionExtractor()
    # cap to the first overview page for a fast smoke test
    ext._get_next_page_path = lambda _html: None
    ext.run()

    papers = request_all(Paper)
    print(f"\nPaper rows in DB: {len(papers)}")
    for p in papers[:10]:
        print(f"  type={p.paper_type} ref={p.reference!r} name={(p.name or '')[:55]!r} date={p.date}")
    print(
        f"Person rows: {len(request_all(Person))}, Org rows: {len(request_all(Organization))}, "
        f"Terms: {len(request_all(LegislativeTerm))}, Locations: {len(request_all(Location))}"
    )


if __name__ == "__main__":
    sys.exit(main())
