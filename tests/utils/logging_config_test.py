import logging
import os
import uuid
from unittest import mock

import pytest

from src.utils import logging_config


def test_get_blob_service_client_success(monkeypatch):
    monkeypatch.setenv('AZURE_STORAGE_CONNECTION_STRING',
                       'UseDevelopmentStorage=true')

    with mock.patch('src.utils.logging_config.BlobServiceClient.from_connection_string') as mock_client:
        mock_client.return_value = mock.Mock()
        client = logging_config.get_blob_service_client()
        assert client is mock_client.return_value


def test_get_blob_service_client_missing_env(monkeypatch):
    monkeypatch.delenv('AZURE_STORAGE_CONNECTION_STRING', raising=False)
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
        name='test', level=logging.INFO, pathname='file', lineno=10,
        msg='Hello', args=(), exc_info=None
    )
    logging_config.set_request_id('abc-123')
    filter_ = logging_config.RequestIdFilter()
    assert filter_.filter(record)
    assert record._request_id == 'abc-123'


def test_setup_logger_creates_handlers(tmp_path, monkeypatch):
    log_file = tmp_path / 'test.log'
    monkeypatch.delenv('APPINSIGHTS_CONNECTION_STRING', raising=False)

    logger = logging_config.setup_logger(str(log_file))
    logger.info('Test log')

    with open(log_file, encoding='utf-8') as f:
        content = f.read()
    assert 'Test log' in content

    for handler in logger.handlers:
        assert any(isinstance(f, logging_config.RequestIdFilter)
                   for f in handler.filters)
