import argparse
import datetime
import sys

from src.extractor.referenten_extractor import ReferentenExtractor
from src.extractor.stadtratssitzungen_extractor import StadtratssitzungenExtractor
from src.logtools import getLogger
from src.version import get_version

DEFAULT_START_URL = "https://risi.muenchen.de/risi/sitzung/uebersicht"
DEFAULT_START_DATE = datetime.date.today().isoformat()


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="RIS Indexer - Collect, Extract, Transform, and Load data from Rathausinformationssystem website"
    )
    parser.add_argument("--starturl", default=DEFAULT_START_URL, help=f"URL to the sitemap (default: {DEFAULT_START_URL})")
    parser.add_argument("--startdate", default=DEFAULT_START_DATE, help="Startdate for filtering STR-Meetings (default: Empty String)")

    return parser.parse_args()


def main():
    args = parse_arguments()
    logger = getLogger()
    version = get_version()
    logger.info(f"RIS Extractor v{version} starting up")
    extractor = StadtratssitzungenExtractor()
    startdate = datetime.date.fromisoformat(args.startdate)
    logger.info(f"Extracting meetings starting from {startdate}")
    extract_artifacts = extractor.run(args.starturl, startdate)
    print(extract_artifacts)

    logger.info("Extracting refernten")
    ref_extractor = ReferentenExtractor()
    ref_extract_artifacts = ref_extractor.run()
    print(ref_extract_artifacts)

    logger.info("Extraction process finished")
    # TODO: Transform
    logger.info("RIS Indexer completed successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())
