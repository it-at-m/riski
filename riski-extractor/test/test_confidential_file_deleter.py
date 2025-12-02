import datetime
from unittest.mock import call, patch

import pytest
from src.data_models import File
from src.filehandler.confidential_file_deleter import ConfidentialFileDeleter


@pytest.fixture
def deleter():
    deleter = ConfidentialFileDeleter()
    return deleter


@patch("src.filehandler.confidential_file_deleter.get_all_found_file_ids")
@patch("src.filehandler.confidential_file_deleter.request_all")
@patch("src.filehandler.confidential_file_deleter.remove_object_by_id")
def test_delete_confidential_files(mock_remove_object_by_id, mock_request_all, mock_get_all_found_file_ids, deleter):
    mock_get_all_found_file_ids.return_value = ["file1", "file2"]
    mock_remove_object_by_id.return_value = None

    mock_request_all.return_value = [
        File(id="file1", modified=datetime.datetime(2023, 10, 1)),
        File(id="file2", modified=datetime.datetime(2023, 10, 2)),
        File(id="file3", modified=datetime.datetime(2023, 10, 3)),
        File(id="file4", modified=datetime.datetime(2023, 10, 30)),
    ]

    deleter.config.start_date = "2023-10-01"

    deleter.delete_confidential_files()

    calls = [call("file3", File), call("file4", File)]
    mock_remove_object_by_id.assert_has_calls(calls, any_order=False)
    assert mock_remove_object_by_id.call_count == 2


@patch("src.filehandler.confidential_file_deleter.get_all_found_file_ids")
@patch("src.filehandler.confidential_file_deleter.request_all")
@patch("src.filehandler.confidential_file_deleter.remove_object_by_id")
def test_no_files_deleted(mock_remove_object_by_id, mock_request_all, mock_get_all_found_file_ids, deleter):
    mock_get_all_found_file_ids.return_value = ["file1", "file2"]

    mock_request_all.return_value = [
        File(id="file1", modified=datetime.datetime(2023, 10, 1)),
        File(id="file2", modified=datetime.datetime(2023, 10, 2)),
    ]

    mock_remove_object_by_id.return_value = None

    deleter.config.start_date = "2023-10-01"

    deleter.delete_confidential_files()

    mock_remove_object_by_id.assert_not_called()


@patch("src.filehandler.confidential_file_deleter.get_all_found_file_ids")
@patch("src.filehandler.confidential_file_deleter.request_all")
@patch("src.filehandler.confidential_file_deleter.remove_object_by_id")
def test_files_not_modified_after_start_date(mock_remove_object_by_id, mock_request_all, mock_get_all_found_file_ids, deleter):
    mock_get_all_found_file_ids.return_value = []

    mock_request_all.return_value = [
        File(id="file1", modified=datetime.datetime(2023, 9, 30)),
        File(id="file2", modified=datetime.datetime(2023, 9, 29)),
    ]

    deleter.config.start_date = "2023-10-01"

    deleter.delete_confidential_files()

    mock_remove_object_by_id.assert_not_called()
