import sys
from logging import Logger

from config.config import Config, get_config
from src.db.db import create_db_and_tables
from src.db.db_access import update_or_insert_objects_to_database
from src.extractor.city_council_meeting_extractor import CityCouncilMeetingExtractor
from src.extractor.city_council_meeting_template_extractor import CityCouncilMeetingTemplateExtractor
from src.extractor.city_council_member_extractor import CityCouncilMemberExtractor
from src.extractor.head_of_department_extractor import HeadOfDepartmentExtractor
from src.logtools import getLogger
from src.version import get_version

config: Config
logger: Logger


def main():
    config = get_config()
    config.print_config()
    logger = getLogger()
    version = get_version()

    create_db_and_tables()

    logger.info(f"RIS Indexer v{version} starting up")
    logger.info(f"Extract data from {config.start_date}{f' until {config.end_date}' if config.end_date else ''}")

    logger.info("Extracting meetings")
    sitzungen_extractor = CityCouncilMeetingExtractor()
    extracted_meeting_list = sitzungen_extractor.run()
    logger.info(f"Extracted {len(extracted_meeting_list)} meetings")
    logger.debug([obj.name for obj in extracted_meeting_list])

    logger.info("Extracting Heads of Departments")
    head_of_department_extractor = HeadOfDepartmentExtractor()
    extracted_head_of_department_list = head_of_department_extractor.run()
    logger.info(f"Extracted {len(extracted_head_of_department_list)} Heads of Departments")
    logger.debug([hod.name for hod in extracted_head_of_department_list])
    update_or_insert_objects_to_database(extracted_head_of_department_list)

    logger.info("Extracting City Council Members")
    city_council_member_extractor = CityCouncilMemberExtractor()
    extracted_city_council_member_list = city_council_member_extractor.run()
    logger.info(f"Extracted {len(extracted_city_council_member_list)} City Council Members")
    logger.debug([ccm.name for ccm in extracted_city_council_member_list])
    update_or_insert_objects_to_database(extracted_city_council_member_list)

    logger.info("Extracting City Council Meeting Templates")
    city_council_meeting_template_extractor = CityCouncilMeetingTemplateExtractor()
    extracted_city_council_meeting_template_list = city_council_meeting_template_extractor.run()
    logger.info(f"Extracted {len(extracted_city_council_meeting_template_list)} City Council Meeting Templates")
    logger.debug([template.name for template in extracted_city_council_meeting_template_list])
    update_or_insert_objects_to_database(extracted_city_council_meeting_template_list)

    logger.info("Extraction process finished")
    # TODO: Transform
    logger.info("RIS Indexer completed successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())
