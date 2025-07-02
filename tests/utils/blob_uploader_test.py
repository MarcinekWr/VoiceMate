import os
from unittest import mock

import pytest

from src.utils.blob_uploader import upload_to_blob


@mock.patch('src.utils.blob_uploader.get_secret_env_first', return_value=None)
def test_upload_to_blob_missing_connection_string(mock_get_secret, caplog):
    caplog.set_level("ERROR")
    upload_to_blob('container', 'file.txt')
    
    assert any("Brak AZURE_STORAGE_CONNECTION_STRING" in r.message for r in caplog.records)




@mock.patch('builtins.open', new_callable=mock.mock_open, read_data=b'fake data')
@mock.patch('src.utils.blob_uploader.BlobServiceClient')
@mock.patch.dict(os.environ, {'AZURE_STORAGE_CONNECTION_STRING': 'fake_connection_string'})
def test_upload_to_blob_success(mock_blob_service, mock_open_file, caplog):
    caplog.set_level('INFO')

    mock_container_client = mock.Mock()
    mock_blob_service.from_connection_string.return_value.get_container_client.return_value = mock_container_client

    upload_to_blob('audio', 'path/to/file.mp3', 'uploaded.mp3')

    mock_container_client.upload_blob.assert_called_once_with(
        name='uploaded.mp3', data=mock.ANY, overwrite=True
    )
    assert any(
        "Plik 'path/to/file.mp3' wysłany do kontenera 'audio'" in r.message for r in caplog.records)


@mock.patch('builtins.open', new_callable=mock.mock_open, read_data=b'data')
@mock.patch('src.utils.blob_uploader.BlobServiceClient')
@mock.patch.dict(os.environ, {'AZURE_STORAGE_CONNECTION_STRING': 'test_connection'})
def test_upload_to_blob_default_blob_name(mock_blob_service, mock_open_file):
    mock_container = mock.Mock()
    mock_blob_service.from_connection_string.return_value.get_container_client.return_value = mock_container

    upload_to_blob('logs', 'dir/logfile.log', blob_name=None)

    mock_container.upload_blob.assert_called_once_with(
        name='logfile.log', data=mock.ANY, overwrite=True
    )


@mock.patch('builtins.open', new_callable=mock.mock_open, read_data=b'data')
@mock.patch('src.utils.blob_uploader.BlobServiceClient')
@mock.patch.dict(os.environ, {'AZURE_STORAGE_CONNECTION_STRING': 'test_connection'})
def test_upload_to_blob_exception_handling(mock_blob_service, mock_open_file, caplog):
    caplog.set_level('ERROR')
    mock_blob_service.from_connection_string.side_effect = Exception(
        'Some Azure error')

    upload_to_blob('logs', 'fake.txt', 'blob.txt')

    assert any(
        '❌ Błąd przy wysyłaniu do Azure Blob Storage' in r.message for r in caplog.records)
