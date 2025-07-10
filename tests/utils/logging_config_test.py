from __future__ import annotations

import logging
import os
import uuid
from unittest import mock

import pytest

from src.utils import logging_config


def test_get_blob_service_client_success(monkeypatch):
    monkeypatch.setenv(
        'AZURE_STORAGE_CONNECTION_STRING',
        'UseDevelopmentStorage=true',
    )

    with mock.patch(
        'src.utils.logging_config.BlobServiceClient.from_connection_string',
    ) as mock_client:
        mock_client.return_value = mock.Mock()
        client = logging_config.get_blob_service_client()
        assert client is mock_client.return_value


@mock.patch('src.utils.logging_config.get_secret_env_first', return_value=None)
def test_get_blob_service_client_missing_env(mock_get_secret):
    with pytest.raises(ValueError, match='Brak AZURE_STORAGE_CONNECTION_STRING'):
        logging_config.get_blob_service_client()


def test_request_id_set_and_get():
    new_id = str(uuid.uuid4())
    set_id = logging_config.set_request_id(new_id)
    assert set_id == new_id
    assert logging_config.get_request_id() == new_id

    auto_id = logging_config.set_request_id()
    assert isinstance(auto_id, str)
    assert len(auto_id) > 0
    assert logging_config.get_request_id() == auto_id


def test_request_id_filter():
    record = logging.LogRecord(
        name='test',
        level=logging.INFO,
        pathname='file',
        lineno=10,
        msg='Hello',
        args=(),
        exc_info=None,
    )
    logging_config.set_request_id('abc-123')
    filter_ = logging_config.RequestIdFilter()
    assert filter_.filter(record)
    assert record._request_id == 'abc-123'


@mock.patch('src.utils.logging_config.get_secret_env_first')
def test_setup_logger_creates_handlers(mock_get_secret, tmp_path, monkeypatch):
    def mock_get_secret_side_effect(key):
        if key == 'APPINSIGHTS_CONNECTION_STRING':
            return None
        return None
    mock_get_secret.side_effect = mock_get_secret_side_effect

    log_file = tmp_path / 'test.log'
    monkeypatch.delenv('APPINSIGHTS_CONNECTION_STRING', raising=False)

    request_id = 'test-request-123'
    logging_config.set_request_id(request_id)
    logging_config.cleanup_all_loggers()

    logger = logging_config.setup_logger(str(log_file))

    file_handler = None
    for handler in logger.handlers:
        if isinstance(handler, logging.FileHandler):
            file_handler = handler
            break

    for handler in logger.handlers:
        handler.flush()
        handler.close()

    expected_log_file = file_handler.baseFilename if file_handler else os.path.abspath(
        os.path.join('log_folder', 'logs', f'{request_id}.log'))

    assert os.path.exists(
        expected_log_file), f'Oczekiwany plik logu {expected_log_file} nie został utworzony'


@mock.patch('src.utils.logging_config.get_secret_env_first')
def test_logger_creates_log_file_reliably(mock_get_secret, tmp_path, monkeypatch):
    def mock_get_secret_side_effect(key):
        if key == 'APPINSIGHTS_CONNECTION_STRING':
            return None
        return None
    mock_get_secret.side_effect = mock_get_secret_side_effect
    import glob
    import os
    import time
    import uuid

    log_dir = 'log_folder/logs'
    if os.path.exists(log_dir):
        for old_log_file in glob.glob(os.path.join(log_dir, '*.log')):
            try:
                os.remove(old_log_file)
            except OSError:
                pass

    request_id = f'test-{uuid.uuid4()}'
    logging_config.set_request_id(request_id)
    logging_config.cleanup_all_loggers()

    logger = logging_config.setup_logger('should_be_ignored.log')

    file_handler = None
    for handler in logger.handlers:
        if isinstance(handler, logging.FileHandler):
            file_handler = handler
            break

    for handler in logger.handlers:
        handler.flush()
        handler.close()

    expected_log_file = file_handler.baseFilename if file_handler else os.path.abspath(
        os.path.join(log_dir, f'{request_id}.log'))

    assert os.path.exists(
        expected_log_file), f'Log file {expected_log_file} not found.'
