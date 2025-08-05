import argparse
import datetime
import sys

from src.extractor.city_council_member_extractor import CityCouncilMemberExtractor
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

    startdate = datetime.date.fromisoformat(args.startdate)

    logger.info(f"RIS Extractor v{version} starting up")

    # logger.info(f"Extracting meetings starting from {startdate}")
    # sitzungen_extractor = StadtratssitzungenExtractor()
    # ext_meeting_list = sitzungen_extractor.run(startdate)
    # print(ext_meeting_list)

    # logger.info("Extracting refernten")
    # ref_extractor = ReferentenExtractor()
    # ext_referenten_list = ref_extractor.run()
    # print(ext_referenten_list)

    logger.info("Extracting city council member")
    city_council_member_extractor = CityCouncilMemberExtractor()
    extracted_city_council_member_list = city_council_member_extractor.run(startdate)
    print(len(extracted_city_council_member_list))

    logger.info("Extraction process finished")
    # TODO: Transform
    logger.info("RIS Indexer completed successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())
