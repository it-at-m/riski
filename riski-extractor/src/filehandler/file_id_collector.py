from logging import Logger

from src.data_models import File
from src.logtools import getLogger

file_ids: list[str] = []
logger: Logger = getLogger()


def collect_file_id(f):
    def wrap(*args, **kwargs):
        if isinstance(*args, File):
            logger.debug(f"Found id: {args[0].id}")
            file_ids.append(args[0].id)
        res = f(*args, **kwargs)
        return res

    return wrap


def get_all_found_file_ids() -> list[str]:
    return file_ids
