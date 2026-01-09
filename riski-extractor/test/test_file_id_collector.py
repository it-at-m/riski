from unittest.mock import MagicMock

from src.data_models import File
from src.filehandler.file_id_collector import clear_ids, collect_file_id, get_all_found_file_ids
from src.logtools import getLogger

# Mock Logger
logger = getLogger()
logger.debug = MagicMock()


# Decorated Test function
@collect_file_id
def sample_function(obj: File):
    return obj.id


def test_collect_file_id():
    clear_ids()
    file = File(id="123")
    assert get_all_found_file_ids() == []

    result = sample_function(file)

    assert result == file.id
    assert get_all_found_file_ids() == ["123"]


def test_collect_file_id_multiple_calls():
    clear_ids()

    file1 = File(id="123")
    file2 = File(id="456")

    sample_function(file1)
    sample_function(file2)

    assert get_all_found_file_ids() == ["123", "456"]
