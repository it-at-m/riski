from unittest.mock import ANY, AsyncMock, MagicMock, patch

import pytest
from core.model.data_models import File
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


@pytest.mark.asyncio
async def test_download_and_persist_file_updates_filename(filehandler_instance, mock_file):
    mock_response = MagicMock()
    mock_response.content = b"test content"
    mock_response.headers = {"content-disposition": 'inline; filename="test_file.txt"'}

    filehandler_instance.client.get = AsyncMock(return_value=mock_response)

    with (
        patch("src.filehandler.filehandler.update_or_insert_objects_to_database") as mock_update,
        patch("src.filehandler.filehandler.request_object_by_risid") as mock_request_object,
    ):
        mock_request_object.return_value = mock_file

        await filehandler_instance.download_and_persist_file(mock_file.id)

        mock_update.assert_called_once_with(ANY, b"test content", "test_file.txt")


@pytest.mark.asyncio
async def test_download_and_persist_file_updates_filename_urlencoding(filehandler_instance, mock_file):
    mock_response = MagicMock()
    mock_response.content = b"test content"
    mock_response.headers = {"content-disposition": 'inline; filename="test%20file.txt"'}

    filehandler_instance.client.get = AsyncMock(return_value=mock_response)

    with (
        patch("src.filehandler.filehandler.update_or_insert_objects_to_database") as mock_update,
        patch("src.filehandler.filehandler.request_object_by_risid") as mock_request_object,
    ):
        mock_request_object.return_value = mock_file

        await filehandler_instance.download_and_persist_file(mock_file.id)

        mock_update.assert_called_once_with(ANY, b"test content", "test file.txt")


@pytest.mark.asyncio
async def test_download_and_persist_file_not_updates_filename_when_unchanged_file(filehandler_instance, mock_file):
    mock_response = MagicMock()
    mock_response.content = b"test"
    mock_response.headers = {"content-disposition": 'inline; filename="test_file.txt"'}

    filehandler_instance.client.get = AsyncMock(return_value=mock_response)
    mock_file.content = b"test"
    mock_file.size = len(b"test")

    with (
        patch("src.filehandler.filehandler.update_or_insert_objects_to_database") as mock_update,
        patch("src.filehandler.filehandler.request_object_by_risid") as mock_request_object,
    ):
        mock_request_object.return_value = mock_file

        await filehandler_instance.download_and_persist_file(mock_file.id)

        mock_update.assert_not_called()
