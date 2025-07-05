"""Defines the logging configuration for the application with per-session isolation."""
from __future__ import annotations

import logging
import os
import re
import uuid
from typing import Optional, Dict
import threading

from azure.storage.blob import BlobServiceClient
from opencensus.ext.azure.log_exporter import AzureLogHandler

from src.common.constants import LOGS_DIR
from src.utils.key_vault import get_secret_env_first


def get_blob_service_client() -> BlobServiceClient:
    connection_string = get_secret_env_first("AZURE_STORAGE_CONNECTION_STRING")
    if not connection_string:
        raise ValueError('Brak AZURE_STORAGE_CONNECTION_STRING')
    return BlobServiceClient.from_connection_string(connection_string)


class RequestIdContext:
    # Użyj thread-local storage dla izolacji między sesjami
    _local = threading.local()
    
    @classmethod
    def get_request_id(cls) -> str:
        if not hasattr(cls._local, 'request_id'):
            cls._local.request_id = 'no-request-id'
        return cls._local.request_id
    
    @classmethod
    def set_request_id(cls, request_id: str):
        cls._local.request_id = request_id


class RequestIdFilter(logging.Filter):
    def filter(self, record):
        record._request_id = RequestIdContext.get_request_id()
        return True


def set_request_id(new_id: Optional[str] = None) -> str:
    """Ustawia nowe request_id (UUID) lub własne, i zwraca je."""
    request_id = new_id or str(uuid.uuid4())
    RequestIdContext.set_request_id(request_id)
    return request_id


def get_request_id() -> str:
    """Zwraca aktualne request_id (lub 'no-request-id')."""
    return RequestIdContext.get_request_id()


# Słownik do przechowywania loggerów per request_id
_loggers: Dict[str, logging.Logger] = {}
_loggers_lock = threading.Lock()
_max_loggers = 50  # Maksymalna liczba aktywnych loggerów


def get_session_logger(request_id: str) -> logging.Logger:
    """Zwraca logger specyficzny dla danej sesji/request_id."""
    with _loggers_lock:
        # Sprawdź czy nie ma za dużo loggerów
        if len(_loggers) >= _max_loggers and request_id not in _loggers:
            # Usuń najstarszy logger (pierwszy w słowniku)
            oldest_id = next(iter(_loggers))
            _cleanup_logger(oldest_id)
            del _loggers[oldest_id]
        
        if request_id not in _loggers:
            _loggers[request_id] = _create_session_logger(request_id)
        return _loggers[request_id]


def _cleanup_logger(request_id: str):
    """Wewnętrzna funkcja do czyszczenia loggera."""
    if request_id in _loggers:
        logger = _loggers[request_id]
        for handler in logger.handlers[:]:
            handler.close()
            logger.removeHandler(handler)


def _create_session_logger(request_id: str) -> logging.Logger:
    """Tworzy nowy logger dla konkretnej sesji."""
    logger_name = f"session_{request_id}"
    logger = logging.getLogger(logger_name)
    
    # Jeśli logger już istnieje, zwróć go
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.INFO)
    logger.propagate = False  # Ważne! Nie propaguj do root loggera
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] - [request_id=%(request_id)s] - %(message)s',
    )
    
    # File handler dla tej konkretnej sesji
    log_file_path = os.path.join(LOGS_DIR, f"{request_id}.log")
    file_handler = logging.FileHandler(
        log_file_path,
        mode='w',
        encoding='utf-8',
    )
    file_handler.setFormatter(formatter)
    
    # Dodaj request_id do każdego rekordu
    class SessionFilter(logging.Filter):
        def __init__(self, req_id):
            super().__init__()
            self.req_id = req_id
            
        def filter(self, record):
            record.request_id = self.req_id
            return True
    
    session_filter = SessionFilter(request_id)
    file_handler.addFilter(session_filter)
    logger.addHandler(file_handler)
    
    # Stream handler (opcjonalnie, dla debugowania)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    stream_handler.addFilter(session_filter)
    logger.addHandler(stream_handler)
    
    # Azure handler
    def is_valid_instrumentation_key(key):
        return bool(
            re.match(
                r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$',
                key or '',
            ),
        )

    connection_string = get_secret_env_first("APPINSIGHTS_CONNECTION_STRING")
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
            azure_handler.addFilter(session_filter)
            logger.addHandler(azure_handler)
            logger.info(
                'AzureLogHandler podłączony – logi będą wysyłane do Application Insights',
            )
    
    logger.info(
        f'Session logger initialized for request_id: {request_id}. '
        f'Log file: {log_file_path}, Level: {logging.getLevelName(logger.level)}',
    )
    
    return logger


def setup_logger(log_file_path: str) -> logging.Logger:
    """Zachowana dla kompatybilności wstecznej, ale zalecane jest użycie get_session_logger."""
    request_id = get_request_id()
    return get_session_logger(request_id)


def cleanup_session_logger(request_id: str):
    """Czyści logger dla danej sesji (opcjonalne, do wywołania na końcu sesji)."""
    with _loggers_lock:
        if request_id in _loggers:
            _cleanup_logger(request_id)
            del _loggers[request_id]


def cleanup_all_loggers():
    """Czyści wszystkie loggery - użyj ostrożnie!"""
    with _loggers_lock:
        for request_id in list(_loggers.keys()):
            _cleanup_logger(request_id)
        _loggers.clear()