import sys
from logging import Logger

from config.config import Config, get_config
from src.extractor.city_council_member_extractor import CityCouncilMemberExtractor
from src.extractor.head_of_department_extractor import HeadOfDepartmentExtractor
from src.extractor.stadtratssitzungen_extractor import StadtratssitzungenExtractor
from src.logtools import getLogger
from src.version import get_version

config: Config
logger: Logger


def main():
    config = get_config()
    config.print_config()
    logger = getLogger()
    version = get_version()

    logger.info(f"RIS Indexer v{version} starting up")

    logger.info(f"Extracting meetings starting from {config.start_date}")
    sitzungen_extractor = StadtratssitzungenExtractor()
    extracted_meeting_list = sitzungen_extractor.run()
    logger.info(f"Extracted {len(extracted_meeting_list)} meetings")
    logger.debug([obj.name for obj in extracted_meeting_list])

    logger.info("Extracting Heads of Departments")
    head_of_department_extractor = HeadOfDepartmentExtractor()
    extracted_head_of_department_list = head_of_department_extractor.run()
    logger.info(f"Extracted {len(extracted_head_of_department_list)} Heads of Departments")
    logger.debug([hod.name for hod in extracted_head_of_department_list])

    logger.info(f"Extracting City Council Member starting from {config.start_date}")
    city_council_member_extractor = CityCouncilMemberExtractor()
    extracted_city_council_member_list = city_council_member_extractor.run()
    logger.info(f"Extracted {len(extracted_city_council_member_list)} City Council Member")
    logger.debug([ccm.name for ccm in extracted_city_council_member_list])

    logger.info("Extraction process finished")
    # TODO: Transform
    logger.info("RIS Indexer completed successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())
