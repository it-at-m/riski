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
    instance.client = AsyncMock()
    instance.logger = MagicMock()
    return instance


@pytest.mark.asyncio
async def test_download_and_persist_file_updates_filename(filehandler_instance, mock_file):
    mock_response = AsyncMock()
    mock_response.content = b"test content"
    mock_response.headers = {"content-disposition": 'inline; filename="test_file.txt"'}

    filehandler_instance.client.get = AsyncMock(return_value=mock_response)

    with patch("src.filehandler.filehandler.update_file_content") as mock_update:
        await filehandler_instance.download_and_persist_file(mock_file)

        mock_update.assert_called_once_with(ANY, b"test content", "test_file.txt")


@pytest.mark.asyncio
async def test_download_and_persist_file_updates_filename_urlencoding(filehandler_instance, mock_file):
    mock_response = AsyncMock()
    mock_response.content = b"test content"
    mock_response.headers = {"content-disposition": 'inline; filename="test%20file.txt"'}

    filehandler_instance.client.get = AsyncMock(return_value=mock_response)
    with patch("src.filehandler.filehandler.update_file_content") as mock_update:
        await filehandler_instance.download_and_persist_file(mock_file)

        mock_update.assert_called_once_with(ANY, b"test content", "test file.txt")


@pytest.mark.asyncio
async def test_download_and_persist_file_not_updates_filename_when_unchanged_file(filehandler_instance, mock_file):
    mock_response = AsyncMock()
    mock_response.content = b"test"
    mock_response.headers = {"content-disposition": 'inline; filename="test_file.txt"'}

    filehandler_instance.client.get = AsyncMock(return_value=mock_response)
    mock_file.content = b"test"
    mock_file.size = len(b"test")

    with patch("src.filehandler.filehandler.update_file_content") as mock_update:
        await filehandler_instance.download_and_persist_file(mock_file)
        mock_update.assert_not_called()
