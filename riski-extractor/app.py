import datetime
import sys
from logging import Logger

from config.config import Config, get_config
from src import extract
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

    extractor = extract.RISExtractor()
    try:
        startdate = datetime.date.fromisoformat(config.start_date)
    except ValueError as e:
        logger.error(f"Invalid date format: {config.start_date}. Expected ISO format (YYYY-MM-DD): {e}")
        return 1

    logger.info(f"Extracting meetings starting from {startdate}")
    extract_artifacts = extractor.run(startdate)
    print(extract_artifacts)
    logger.info("Extraction process finished")
    logger.info("RIS Indexer completed successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())
