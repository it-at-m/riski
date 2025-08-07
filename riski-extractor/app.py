import argparse
import datetime
import sys

from src.extractor.referenten_extractor import ReferentenExtractor
from src.extractor.stadtratssitzungen_extractor import StadtratssitzungenExtractor
from src.logtools import getLogger
from src.version import get_version

DEFAULT_START_DATE = datetime.date.today().isoformat()


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="RIS Indexer - Collect, Extract, Transform, and Load data from Rathausinformationssystem website"
    )
    parser.add_argument(
        "--startdate", default=DEFAULT_START_DATE, help="Startdate for filtering STR-Meetings in ISO format (default: today's date)"
    )

    return parser.parse_args()


def main():
    args = parse_arguments()
    logger = getLogger()
    version = get_version()

    logger.info(f"RIS Indexer v{version} starting up")

    try:
        startdate = datetime.date.fromisoformat(args.startdate)
    except ValueError as e:
        logger.error(f"Invalid date format: {args.startdate}. Expected ISO format (YYYY-MM-DD): {e}")
        return 1

    logger.info(f"Extracting meetings starting from {startdate}")
    sitzungen_extractor = StadtratssitzungenExtractor()
    ext_meeting_list = sitzungen_extractor.run(startdate)
    print(ext_meeting_list)

    logger.info("Extracting refernten")
    ref_extractor = ReferentenExtractor()
    ext_referenten_list = ref_extractor.run()
    print(ext_referenten_list)

    logger.info("Extraction process finished")
    logger.info("RIS Indexer completed successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())
