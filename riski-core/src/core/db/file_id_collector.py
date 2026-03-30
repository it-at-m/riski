from logging import Logger

from src.logtools import getLogger

file_ids: list[str] = []
logger: Logger = getLogger()


def mark_file_id_for_deletion(f):
    logger.debug(f"Did not find id: {f}")
    file_ids.append(f)


def get_all_ids_to_delete() -> list[str]:
    return file_ids


def clear_ids():
    file_ids.clear()
