import argparse
import sys

from src import extract
from src.logtools import getLogger
from src.version import get_version

DEFAULT_START_URL = "https://risi.muenchen.de/risi/sitzung/uebersicht"


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="RIS Indexer - Collect, Extract, Transform, and Load data from Rathausinformationssystem website"
    )
    parser.add_argument("--starturl", default=DEFAULT_START_URL, help=f"URL to the sitemap (default: {DEFAULT_START_URL})")
    return parser.parse_args()


def main():
    args = parse_arguments()
    logger = getLogger()
    version = get_version()
    logger.info(f"RIS Extractor v{version} starting up")
    extractor = extract.RISExtractor()
    extract_artifacts = extractor.run(args.starturl)
    print(extract_artifacts)
    logger.info("Extraction process finished")
    # TODO: Transform
    logger.info("RIS Indexer completed successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())
