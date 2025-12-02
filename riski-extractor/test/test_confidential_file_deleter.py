import datetime
from unittest.mock import patch

import pytest
from src.data_models import File
from src.filehandler.confidential_file_deleter import ConfidentialFileDeleter  # Replace `your_module` with the actual module name


@pytest.fixture
def deleter():
    deleter = ConfidentialFileDeleter()
    return deleter


@patch("src.filehandler.confidential_file_deleter.get_all_found_file_ids")
@patch("src.filehandler.confidential_file_deleter.request_all")
@patch("src.filehandler.confidential_file_deleter.remove_object_by_id")
def test_delete_confidential_files(mock_remove_object_by_id, mock_request_all, mock_get_all_found_file_ids, deleter):
    # Arrange
    mock_get_all_found_file_ids.return_value = ["file1", "file2"]
    mock_remove_object_by_id.return_value = None

    # Simulate the request_all return value
    mock_request_all.return_value = [
        File(id="file1", modified=datetime.datetime(2023, 10, 1)),
        File(id="file2", modified=datetime.datetime(2023, 10, 2)),
        File(id="file3", modified=datetime.datetime(2023, 10, 3)),  # This one should be deleted
        File(id="file4", modified=datetime.datetime(2023, 9, 30)),  # This one should not be deleted
    ]

    # Mock config to have a start_date
    deleter.config.start_date = "2023-10-01"

    # Act
    deleter.delete_confidential_files()

    # Assert
    mock_remove_object_by_id.assert_called_once_with("file3", File)


@patch("src.filehandler.confidential_file_deleter.get_all_found_file_ids")
@patch("src.filehandler.confidential_file_deleter.request_all")
@patch("src.filehandler.confidential_file_deleter.remove_object_by_id")
def test_no_files_deleted(mock_remove_object_by_id, mock_request_all, mock_get_all_found_file_ids, deleter):
    # Arrange
    mock_get_all_found_file_ids.return_value = ["file1", "file2"]

    # Simulate the request_all return value
    mock_request_all.return_value = [
        File(id="file1", modified=datetime.datetime(2023, 10, 1)),
        File(id="file2", modified=datetime.datetime(2023, 10, 2)),
    ]

    mock_remove_object_by_id.return_value = None

    # Mock config to have a start_date
    deleter.config.start_date = "2023-10-01"

    # Act
    deleter.delete_confidential_files()

    # Assert
    mock_remove_object_by_id.assert_not_called()  # No files should be deleted


@patch("src.filehandler.confidential_file_deleter.get_all_found_file_ids")
@patch("src.filehandler.confidential_file_deleter.request_all")
@patch("src.filehandler.confidential_file_deleter.remove_object_by_id")
def test_files_not_modified_after_start_date(mock_remove_object_by_id, mock_request_all, mock_get_all_found_file_ids, deleter):
    # Arrange
    mock_get_all_found_file_ids.return_value = []

    # Simulate the request_all return value
    mock_request_all.return_value = [
        File(id="file1", modified=datetime.datetime(2023, 9, 30)),  # This should not be deleted
        File(id="file2", modified=datetime.datetime(2023, 9, 29)),  # This should not be deleted
    ]

    # Mock config to have a start_date
    deleter.config.start_date = "2023-10-01"

    # Act
    deleter.delete_confidential_files()

    # Assert
    mock_remove_object_by_id.assert_not_called()
