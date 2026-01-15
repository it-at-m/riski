import asyncio
import os
import sys
from logging import Logger

from config.config import Config, get_config
from core.db.db import create_db_and_tables, init_db
from core.db.db_access import update_or_insert_objects_to_database
from core.model.data_models import ExtractArtifact
from faststream.kafka import KafkaBroker
from src.extractor.city_council_faction_extractor import CityCouncilFactionExtractor
from src.extractor.city_council_meeting_extractor import CityCouncilMeetingExtractor
from src.extractor.city_council_meeting_template_extractor import CityCouncilMeetingTemplateExtractor
from src.extractor.city_council_member_extractor import CityCouncilMemberExtractor
from src.extractor.city_council_motion_extractor import CityCouncilMotionExtractor
from src.extractor.head_of_department_extractor import HeadOfDepartmentExtractor
from src.filehandler.confidential_file_deleter import ConfidentialFileDeleter
from src.filehandler.filehandler import Filehandler
from src.kafka.security import setup_security
from src.version import get_version

from src.logtools import getLogger

config: Config
logger: Logger


async def main():
    config = get_config()
    config.print_config()
    logger = getLogger(__name__)
    version = get_version()

    init_db(config.core.db.database_url)
    create_db_and_tables()

    logger.info(f"RIS Indexer v{version} starting up")

    logger.info(f"Extract data from {config.start_date}{f' until {config.end_date}' if config.end_date else ''}")

    logger.info("Extracting City Council Factions")
    faction_extractor = CityCouncilFactionExtractor()
    extracted_faction_list = faction_extractor.run()
    logger.info(f"Extracted {len(extracted_faction_list)} factions")
    logger.debug([obj.name for obj in extracted_faction_list])
    update_or_insert_objects_to_database(extracted_faction_list)

    logger.info("Extracting meetings")
    meeting_extractor = CityCouncilMeetingExtractor()
    extracted_meeting_list = meeting_extractor.run()
    logger.info(f"Extracted {len(extracted_meeting_list)} meetings")
    logger.debug([obj.name for obj in extracted_meeting_list])
    update_or_insert_objects_to_database(extracted_meeting_list)

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

    logger.info("Extracting City Council Motions")
    city_council_motion_extractor = CityCouncilMotionExtractor()
    extracted_city_council_motion_list = city_council_motion_extractor.run()
    logger.info(f"Extracted {len(extracted_city_council_motion_list)} City Council Motions")
    logger.debug([obj.name for obj in extracted_city_council_motion_list])
    update_or_insert_objects_to_database(extracted_city_council_motion_list)

    broker = await createKafkaBroker(config, logger)
    try:
        async with Filehandler(broker) as filehandler:
            await filehandler.download_and_persist_files(batch_size=config.core.db.batch_size)
    finally:
        await broker.stop()
        logger.info("Broker closed.")

    confidential_file_deleter = ConfidentialFileDeleter()
    confidential_file_deleter.delete_confidential_files()

    if config.json_export:
        logger.info("Dumping extraction artifact to 'artifacts/extract.json'")
        extraction_artifact = ExtractArtifact(
            meetings=extracted_meeting_list,
            heads_of_departments=extracted_head_of_department_list,
            city_council_members=extracted_city_council_member_list,
            city_council_meeting_template=extracted_city_council_meeting_template_list,
            factions=extracted_faction_list,
            city_council_motions=extracted_city_council_motion_list,
        )
        os.makedirs("artifacts", exist_ok=True)
        with open("artifacts/extract.json", "w", encoding="utf-8") as file:
            file.write(extraction_artifact.model_dump_json(indent=4))

    logger.info("Extraction process finished")
    # TODO: Transform
    logger.info("RIS Indexer completed successfully")
    return 0


async def createKafkaBroker(config: Config, logger: Logger) -> KafkaBroker:
    security = setup_security()
    # Kafka Broker and FastStream app setup
    broker = KafkaBroker(bootstrap_servers=config.kafka_server, security=security)
    logger.debug("Connecting to Broker...")
    try:
        await broker.connect()
        logger.info("Broker connected.")
        return broker
    except Exception as e:
        logger.exception(f"Failed to connect to broker. - {e}")
        raise


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
