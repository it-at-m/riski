from logging import Logger

from data_models import File
from src.logtools import getLogger

file_ids: list[str] = []
logger: Logger = getLogger()


def collect_file_id(f):
    def wrap(*args, **kwargs):
        if isinstance(*args, File):
            file_ids.append(args.id)
            logger.info(f"Found id: {args.id}")
        res = f(*args, **kwargs)
        return res

    return wrap


def get_all_found_file_ids() -> list[str]:
    return file_ids
