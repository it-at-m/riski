import os
import sys
from logging import Logger

from config.config import Config, get_config
from src.data_models import ExtractArtifact
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
    logger.info([obj.name for obj in extracted_meeting_list])

    logger.info("Extracting Heads of Departments")
    head_of_department_extractor = HeadOfDepartmentExtractor()
    extracted_head_of_department_list = head_of_department_extractor.run()
    logger.info(f"Extracted {len(extracted_head_of_department_list)} Heads of Departments")
    logger.info([obj.familyName for obj in extracted_head_of_department_list])

    if config.json_export:
        logger.info("Dumping extraction artifact to 'artifacts/extract.json'")
        extraction_artifact = ExtractArtifact(meetings=extracted_meeting_list, heads_of_departments=extracted_head_of_department_list)
        os.makedirs("artifacts", exist_ok=True)
        with open("artifacts/extract.json", "w", encoding="utf-8") as file:
            file.write(extraction_artifact.model_dump_json(indent=4))

    logger.info("Extraction process finished")
    logger.info("RIS Indexer completed successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())
