from unittest.mock import MagicMock, patch

import pytest
from src.data_models import File
from src.filehandler.filehandler import Filehandler


@pytest.fixture
def mock_file():
    return File(id="123", content=None, fileName="initial_filename.pdf", accessUrl="")


@pytest.fixture
def filehandler_instance():
    instance = Filehandler()
    instance.client = MagicMock()
    instance.logger = MagicMock()
    return instance


def test_download_and_persist_file_updates_filename(filehandler_instance, mock_file):
    mock_response = MagicMock()
    mock_response.content = b"test content"
    mock_response.headers = {"content-disposition": 'inline; filename="test_file.txt"'}

    filehandler_instance.client.get = MagicMock(return_value=mock_response)

    with patch("src.filehandler.filehandler.update_or_insert_objects_to_database") as mock_update:
        filehandler_instance.download_and_persist_file(mock_file)

        assert mock_file.fileName == "test_file.txt"
        assert mock_file.content == b"test content"
        assert mock_file.size == len(b"test content")
        mock_update.assert_called_once()


def test_download_and_persist_file_updates_filename_urlencoding(filehandler_instance, mock_file):
    mock_response = MagicMock()
    mock_response.content = b"test content"
    mock_response.headers = {"content-disposition": 'inline; filename="test%20file.txt"'}

    filehandler_instance.client.get = MagicMock(return_value=mock_response)
    with patch("src.filehandler.filehandler.update_or_insert_objects_to_database") as mock_update:
        filehandler_instance.download_and_persist_file(mock_file)

        assert mock_file.fileName == "test file.txt"
        assert mock_file.content == b"test content"
        assert mock_file.size == len(b"test content")
        mock_update.assert_called_once()


def test_download_and_persist_file_not_updates_filename_when_unchanged_file(filehandler_instance, mock_file):
    mock_response = MagicMock()
    mock_response.content = b"test"
    mock_response.headers = {"content-disposition": 'inline; filename="test_file.txt"'}

    filehandler_instance.client.get = MagicMock(return_value=mock_response)
    mock_file.content = b"test"
    mock_file.size = len(b"test")

    with patch("src.filehandler.filehandler.update_or_insert_objects_to_database") as mock_update:
        filehandler_instance.download_and_persist_file(mock_file)

        assert mock_file.fileName == "initial_filename.pdf"
        assert mock_file.content == b"test"
        assert mock_file.size == len(b"test")
        mock_update.assert_not_called()
