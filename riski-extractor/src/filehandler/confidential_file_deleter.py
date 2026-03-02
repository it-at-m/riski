import datetime
from logging import Logger

from config.config import get_config
from core.db.db_access import remove_object_by_id, request_batch
from core.db.file_id_collector import get_all_found_file_ids
from core.model.data_models import File

from src.logtools import getLogger


class ConfidentialFileDeleter:
    logger: Logger

    def __init__(self) -> None:
        self.logger = getLogger()
        self.config = get_config()

    def delete_confidential_files(self):
        doc_ids = get_all_found_file_ids()
        limit = self.config.core.db.batch_size
        offset = 0
        file_ids_to_delete = []
        while True:
            files: list[File] = request_batch(File, offset=offset, limit=limit)
            if not files:
                break

            for file in files:
                if not file.modified:
                    continue

                if file.id not in doc_ids and datetime.datetime.strptime(self.config.start_date, "%Y-%m-%d").date() <= file.modified.date():
                    file_ids_to_delete.append(file.id)
                    self.logger.info(f"Marked File {file.id} for deletion")

            offset += limit

        if len(file_ids_to_delete) > 100:
            self.logger.warning(f"[Plausibility Issue] {len(file_ids_to_delete)} files are marked for deletion. Skipping Deletion step.")
            return

        for id in file_ids_to_delete:
            remove_object_by_id(id, File)
