import sys
from logging import Logger

from config.config import Config, get_config
from core.db.db import create_db_and_tables, init_db
from src.extractor.city_council_faction_extractor import CityCouncilFactionExtractor
from src.extractor.city_council_meeting_extractor import CityCouncilMeetingExtractor
from src.extractor.city_council_meeting_template_extractor import CityCouncilMeetingTemplateExtractor
from src.extractor.city_council_member_extractor import CityCouncilMemberExtractor
from src.extractor.city_council_motion_extractor import CityCouncilMotionExtractor
from src.extractor.head_of_department_extractor import HeadOfDepartmentExtractor
from src.filehandler.confidential_file_deleter import ConfidentialFileDeleter
from src.filehandler.filehandler import Filehandler
from src.version import get_version

from src.logtools import getLogger

config: Config
logger: Logger


def main():
    config = get_config()
    config.print_config()
    logger = getLogger()
    version = get_version()

    init_db(config.core.db.database_url)
    create_db_and_tables()

    logger.info(f"RIS Indexer v{version} starting up")

    logger.info(f"Extract data from {config.start_date}{f' until {config.end_date}' if config.end_date else ''}")

    logger.info("Extracting City Council Factions")
    faction_extractor = CityCouncilFactionExtractor()
    faction_extractor.run()
    logger.info("Extracted factions")

    logger.info("Extracting meetings")
    meeting_extractor = CityCouncilMeetingExtractor()
    meeting_extractor.run()
    logger.info("Extracted meetings")

    logger.info("Extracting Heads of Departments")
    head_of_department_extractor = HeadOfDepartmentExtractor()
    head_of_department_extractor.run()
    logger.info("Extracted Heads of Departments")

    logger.info("Extracting City Council Members")
    city_council_member_extractor = CityCouncilMemberExtractor()
    city_council_member_extractor.run()
    logger.info("Extracted City Council Members")

    logger.info("Extracting City Council Meeting Templates")
    city_council_meeting_template_extractor = CityCouncilMeetingTemplateExtractor()
    city_council_meeting_template_extractor.run()
    logger.info("Extracted City Council Meeting Templates")

    logger.info("Extracting City Council Motions")
    city_council_motion_extractor = CityCouncilMotionExtractor()
    city_council_motion_extractor.run()
    logger.info("Extracted City Council Motions")

    filehandler = Filehandler()
    filehandler.download_and_persist_files(batch_size=config.core.db.batch_size)

    confidential_file_deleter = ConfidentialFileDeleter()
    confidential_file_deleter.delete_confidential_files()

    logger.info("Extraction process finished")

    logger.info("RIS Indexer completed successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())
