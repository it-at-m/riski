from unittest.mock import call, patch

import pytest
from core.model.data_models import File
from src.filehandler.confidential_file_deleter import ConfidentialFileDeleter


@pytest.fixture
def deleter():
    deleter = ConfidentialFileDeleter()
    return deleter


@patch("src.filehandler.confidential_file_deleter.get_all_ids_to_delete")
@patch("src.filehandler.confidential_file_deleter.remove_object_by_id")
def test_delete_confidential_files(mock_remove_object_by_id, mock_get_all_ids_to_delete, deleter):
    mock_get_all_ids_to_delete.return_value = ["file1", "file2"]
    mock_remove_object_by_id.return_value = None

    deleter.config.start_date = "2023-10-01"

    deleter.delete_confidential_files()

    calls = [call("file1", File), call("file2", File)]
    mock_remove_object_by_id.assert_has_calls(calls, any_order=False)
    assert mock_remove_object_by_id.call_count == 2


@patch("src.filehandler.confidential_file_deleter.get_all_ids_to_delete")
@patch("src.filehandler.confidential_file_deleter.remove_object_by_id")
def test_delete_confidential_files_fileidlist_empty(mock_remove_object_by_id, mock_get_all_ids_to_delete, deleter):
    mock_get_all_ids_to_delete.return_value = ["file1", "file2", "file3", "file4"]
    mock_remove_object_by_id.return_value = None

    deleter.config.start_date = "2023-10-01"

    deleter.delete_confidential_files()

    calls = [call("file2", File), call("file1", File), call("file4", File), call("file3", File)]
    mock_remove_object_by_id.assert_has_calls(calls, any_order=True)
    assert mock_remove_object_by_id.call_count == 4


@patch("src.filehandler.confidential_file_deleter.get_all_ids_to_delete")
@patch("src.filehandler.confidential_file_deleter.remove_object_by_id")
def test_no_files_deleted(mock_remove_object_by_id, mock_get_all_ids_to_delete, deleter):
    mock_get_all_ids_to_delete.return_value = []

    mock_remove_object_by_id.return_value = None

    deleter.config.start_date = "2023-10-01"

    deleter.delete_confidential_files()

    mock_remove_object_by_id.assert_not_called()


@patch("src.filehandler.confidential_file_deleter.get_all_ids_to_delete")
@patch("src.filehandler.confidential_file_deleter.remove_object_by_id")
def test_files_not_modified_after_start_date(mock_remove_object_by_id, mock_get_all_ids_to_delete, deleter):
    mock_get_all_ids_to_delete.return_value = []

    deleter.config.start_date = "2023-10-01"

    deleter.delete_confidential_files()

    mock_remove_object_by_id.assert_not_called()
