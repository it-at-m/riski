import argparse
import datetime
import sys

from src.extractor.head_of_department_extractor import HeadOfDepartmentExtractor
from src.extractor.stadtratssitzungen_extractor import StadtratssitzungenExtractor
from src.logtools import getLogger
from src.version import get_version

DEFAULT_START_DATE = datetime.date.today().isoformat()


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="RIS Indexer - Collect, Extract, Transform, and Load data from Rathausinformationssystem website"
    )
    parser.add_argument("--startdate", default=DEFAULT_START_DATE, help="Startdate for filtering STR-Meetings (default: Empty String)")

    return parser.parse_args()


def main():
    args = parse_arguments()
    logger = getLogger()
    version = get_version()

    logger.info(f"RIS Indexer v{version} starting up")

    startdate = datetime.date.fromisoformat(args.startdate)

    logger.info(f"RIS Extractor v{version} starting up")

    logger.info(f"Extracting meetings starting from {startdate}")
    sitzungen_extractor = StadtratssitzungenExtractor()

    extracted_meeting_list = sitzungen_extractor.run(startdate)
    logger.info(f"Extracted {len(extracted_meeting_list)} meetings")
    print([obj.name for obj in extracted_meeting_list])

    logger.info("Extracting Heads of Departments")
    head_of_department_extractor = HeadOfDepartmentExtractor()
    extracted_head_of_department_list = head_of_department_extractor.run(startdate)
    logger.info(f"Extracted {len(extracted_head_of_department_list)} Heads of Departments")
    print([obj.familyName for obj in extracted_head_of_department_list])

    logger.info("Extraction process finished")
    # TODO: Transform
    logger.info("RIS Indexer completed successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())
