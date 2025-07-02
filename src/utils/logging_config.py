"""Defines the logging configuration for the application."""
import logging
import os
import re
import uuid
from typing import Optional

from azure.storage.blob import BlobServiceClient
from opencensus.ext.azure.log_exporter import AzureLogHandler


def get_blob_service_client() -> BlobServiceClient:
    connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
    if not connection_string:
        raise ValueError('Brak AZURE_STORAGE_CONNECTION_STRING')
    return BlobServiceClient.from_connection_string(connection_string)


class RequestIdContext:
    request_id = 'no-request-id'


class RequestIdFilter(logging.Filter):
    def filter(self, record):
        record._request_id = RequestIdContext.request_id
        return True


def set_request_id(new_id: Optional[str] = None) -> str:
    """Ustawia nowe request_id (UUID) lub własne, i zwraca je."""
    RequestIdContext.request_id = new_id or str(uuid.uuid4())
    return RequestIdContext.request_id


def get_request_id() -> str:
    """Zwraca aktualne request_id (lub 'no-request-id')."""
    return RequestIdContext.request_id


def setup_logger(log_file_path: str) -> logging.Logger:
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    for handler in list(logger.handlers):
        logger.removeHandler(handler)

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] - [request_id=%(_request_id)s] - %(message)s',
    )
    request_filter = RequestIdFilter()

    file_handler = logging.FileHandler(
        log_file_path,
        mode='w',
        encoding='utf-8',
    )
    file_handler.setFormatter(formatter)
    file_handler.addFilter(request_filter)
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    stream_handler.addFilter(request_filter)
    logger.addHandler(stream_handler)

    def is_valid_instrumentation_key(key):
        return bool(
            re.match(
                r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$',
                key or '',
            ),
        )

    connection_string = os.getenv('APPINSIGHTS_CONNECTION_STRING')
    if connection_string:
        match = re.search(
            r'InstrumentationKey=([0-9a-fA-F-]+)',
            connection_string,
        )
        key = match.group(1) if match else None
        if key and is_valid_instrumentation_key(key):
            azure_handler = AzureLogHandler(
                connection_string=connection_string,
            )
            azure_handler.setFormatter(formatter)
            azure_handler.addFilter(request_filter)
            logger.addHandler(azure_handler)
            logger.info(
                'AzureLogHandler podłączony – logi będą wysyłane do Application Insights',
            )
        else:
            logger.warning(
                'APPINSIGHTS_CONNECTION_STRING ustawiony, ale InstrumentationKey jest nieprawidłowy – pomijam AzureLogHandler',
            )
    else:
        logger.warning(
            'Brak APPINSIGHTS_CONNECTION_STRING – logi nie będą wysyłane do Application Insights',
        )

    logger.info(
        f'Logger initialized. Log file: {log_file_path}, '
        f'Level: {logging.getLevelName(logger.level)}',
    )

    return logger
