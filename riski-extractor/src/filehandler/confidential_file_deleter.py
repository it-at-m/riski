import datetime
from logging import Logger

from config.config import get_config
from src.data_models import File
from src.db.db_access import remove_object_by_id, request_all
from src.filehandler.file_id_collector import get_all_found_file_ids
from src.logtools import getLogger


class ConfidentialFileDeleter:
    logger: Logger

    def __init__(self) -> None:
        self.logger = getLogger()
        self.config = get_config()

    def delete_confidential_files(self):
        doc_ids = get_all_found_file_ids()

        for file in request_all(File):
            if not file.modified:
                continue

            if file.id not in doc_ids and datetime.datetime.strptime(self.config.start_date, "%Y-%m-%d") < file.modified:
                remove_object_by_id(file.id, File)
                self.logger.info(f"Deleted File: {file.id}")
