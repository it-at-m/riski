from logging import Logger

from src.data_models import File
from src.logtools import getLogger

file_ids: list[str] = []
logger: Logger = getLogger()


def collect_file_id(f):
    def wrap(*args, **kwargs):
        # Prefer first positional arg if present, otherwise fall back to common keyword names
        candidate = args[0] if args else kwargs.get("obj")
        if isinstance(candidate, File):
            logger.debug(f"Found id: {candidate.id}")
            file_ids.append(candidate.id)
        return f(*args, **kwargs)

    return wrap


def get_all_found_file_ids() -> list[str]:
    return file_ids


def clear_ids():
    file_ids.clear()
