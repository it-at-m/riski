import argparse
import datetime
import sys
from logging import Logger

from config.config import Config, get_config
from src.extractor.city_council_member_extractor import CityCouncilMemberExtractor
from src.extractor.head_of_department_extractor import HeadOfDepartmentExtractor
from src.extractor.stadtratssitzungen_extractor import StadtratssitzungenExtractor
from src.logtools import getLogger
from src.version import get_version

DEFAULT_START_DATE = datetime.date.today().isoformat()
config: Config
logger: Logger


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="RIS Indexer - Collect, Extract, Transform, and Load data from Rathausinformationssystem website"
    )
    parser.add_argument(
        "--startdate", default=DEFAULT_START_DATE, help="Start date for filtering (YYYY-MM-DD). Default: {DEFAULT_START_DATE}"
    )

    return parser.parse_args()


def main():
    config = get_config()
    config.print_config()
    logger = getLogger()
    version = get_version()

    logger.info(f"RIS Indexer v{version} starting up")

    try:
        startdate = datetime.date.fromisoformat(config.start_date)
    except ValueError as e:
        logger.error(f"Invalid date format: {config.start_date}. Expected ISO format (YYYY-MM-DD): {e}")
        return 1

    logger.info(f"RIS Extractor v{version} starting up")

    logger.info(f"Extracting meetings starting from {startdate}")
    sitzungen_extractor = StadtratssitzungenExtractor()
    extracted_meeting_list = sitzungen_extractor.run(startdate)
    logger.info(f"Extracted {len(extracted_meeting_list)} meetings")
    logger.info([obj.name for obj in extracted_meeting_list])

    logger.info("Extracting Heads of Departments")
    head_of_department_extractor = HeadOfDepartmentExtractor()
    extracted_head_of_department_list = head_of_department_extractor.run(startdate)
    logger.info(f"Extracted {len(extracted_head_of_department_list)} Heads of Departments")

    logger.info("Extracting City Council Member")
    city_council_member_extractor = CityCouncilMemberExtractor()
    extracted_city_council_member_list = city_council_member_extractor.run(startdate)
    logger.info(f"Extracted {len(extracted_city_council_member_list)} Citiy Council Member")

    logger.info("Extraction process finished")
    # TODO: Transform
    logger.info("RIS Indexer completed successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())
