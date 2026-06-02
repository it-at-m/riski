from logging import Logger

from config.config import get_config
from core.db.db_access import remove_object_by_id
from core.db.file_id_collector import get_all_ids_to_delete
from core.model.data_models import File

from src.logtools import context_log_url, getLogger


class ConfidentialFileDeleter:
    logger: Logger

    def __init__(self) -> None:
        self.logger = getLogger()
        self.config = get_config()

    def delete_confidential_files(self):
        file_ids_to_delete = get_all_ids_to_delete()

        if len(file_ids_to_delete) > self.config.max_files_to_delete_at_once:
            self.logger.warning(
                f"[Plausibility Issue] {len(file_ids_to_delete)} files are marked for deletion. Maximum allowed are {self.config.max_files_to_delete_at_once}. Skipping Deletion step."
            )
            return

        for id in file_ids_to_delete:
            with context_log_url(id):
                remove_object_by_id(id, File)
                self.logger.info("Deleted file")
