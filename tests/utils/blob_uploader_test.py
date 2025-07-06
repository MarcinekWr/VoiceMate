from __future__ import annotations

import os
from unittest import mock

import pytest

from src.utils.blob_uploader import upload_to_blob


def test_upload_to_blob_default_blob_name(monkeypatch):
    """Testuje, czy domyślna nazwa blob to nazwa pliku, jeśli nie podano blob_name."""
    mock_blob_service = mock.Mock()
    mock_container = mock.Mock()
    monkeypatch.setattr(
        'src.utils.blob_uploader.BlobServiceClient', mock_blob_service)
    mock_blob_service.from_connection_string.return_value.get_container_client.return_value = mock_container

    with mock.patch.dict(os.environ, {'AZURE_STORAGE_CONNECTION_STRING': 'test_connection'}):
        with mock.patch('builtins.open', mock.mock_open(read_data=b'data')):
            upload_to_blob('test-container',
                           'dir/testfile.txt', blob_name=None)
            mock_container.upload_blob.assert_called_once_with(
                name='testfile.txt',
                data=mock.ANY,
                overwrite=True,
            )


def test_upload_to_blob_logs_info_on_success(monkeypatch):
    """Testuje, czy upload_blob został wywołany z odpowiednimi argumentami."""
    mock_blob_service = mock.Mock()
    mock_container = mock.Mock()
    monkeypatch.setattr(
        'src.utils.blob_uploader.BlobServiceClient', mock_blob_service)
    mock_blob_service.from_connection_string.return_value.get_container_client.return_value = mock_container

    with mock.patch.dict(os.environ, {'AZURE_STORAGE_CONNECTION_STRING': 'test_connection'}):
        with mock.patch('builtins.open', mock.mock_open(read_data=b'data')):
            upload_to_blob('test-container', 'dir/testfile.txt',
                           blob_name='blob.txt')
            mock_container.upload_blob.assert_called_once_with(
                name='blob.txt',
                data=mock.ANY,
                overwrite=True,
            )
