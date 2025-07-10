"""Defines the logging configuration for the application with per-session isolation."""

from __future__ import annotations

import logging
import os
import re
import threading
import uuid

from azure.storage.blob import BlobServiceClient
from opencensus.ext.azure.log_exporter import AzureLogHandler

from src.common.constants import LOGS_DIR
from src.utils.key_vault import get_secret_env_first


def get_blob_service_client() -> BlobServiceClient:
    """
    Creates a BlobServiceClient using the Azure Storage connection string from environment or Key Vault.

    Returns:
        BlobServiceClient: Azure BlobServiceClient instance.

    Raises:
        ValueError: If the connection string is not set.
    """
    connection_string = get_secret_env_first("AZURE_STORAGE_CONNECTION_STRING")
    if not connection_string:
        raise ValueError("Brak AZURE_STORAGE_CONNECTION_STRING")
    return BlobServiceClient.from_connection_string(connection_string)


class RequestIdContext:
    """Manages per-thread request ID using thread-local storage."""

    _local = threading.local()

    @classmethod
    def get_request_id(cls) -> str:
        """
        Returns the current thread-local request ID.

        Returns:
            str: Current request ID, or 'no-request-id' if not set.
        """
        if not hasattr(cls._local, "request_id"):
            cls._local.request_id = "no-request-id"
        return cls._local.request_id

    @classmethod
    def set_request_id(cls, request_id: str):
        """
        Sets the request ID for the current thread.

        Args:
            request_id (str): Unique identifier for the request/session.
        """
        cls._local.request_id = request_id


class RequestIdFilter(logging.Filter):
    """Injects request ID into log records for formatting."""

    def filter(self, record):
        record._request_id = RequestIdContext.get_request_id()
        return True


def set_request_id(new_id: str | None = None) -> str:
    """
    Sets a new UUID as the request ID or uses the provided one.

    Args:
        new_id (str, optional): Custom request ID. If None, a new UUID is generated.

    Returns:
        str: The assigned request ID.
    """
    request_id = new_id or str(uuid.uuid4())
    RequestIdContext.set_request_id(request_id)
    return request_id


def get_request_id() -> str:
    """
    Returns the current request ID.

    Returns:
        str: The current request ID or 'no-request-id' if not set.
    """
    return RequestIdContext.get_request_id()


# Słownik do przechowywania loggerów per request_id
_loggers: dict[str, logging.Logger] = {}
_loggers_lock = threading.Lock()
_max_loggers = 50  # Maksymalna liczba aktywnych loggerów


def get_session_logger(request_id: str) -> logging.Logger:
    """
    Returns a logger specific to the given request/session.

    Creates a new logger if one does not already exist.

    Args:
        request_id (str): Unique session ID.

    Returns:
        logging.Logger: The logger instance.
    """
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
    """
    Internal function to clean up logger handlers for a given request ID.

    Args:
        request_id (str): Request ID whose logger should be cleaned up.
    """
    if request_id in _loggers:
        logger = _loggers[request_id]
        for handler in logger.handlers[:]:
            handler.close()
            logger.removeHandler(handler)


def _create_session_logger(request_id: str) -> logging.Logger:
    """
    Creates and configures a new logger for the given request ID.

    Includes:
    - File handler (per session)
    - Stream handler (optional)
    - Azure Application Insights handler (if configured)

    Args:
        request_id (str): Unique request/session identifier.

    Returns:
        logging.Logger: Configured logger instance.
    """
    logger_name = f"session_{request_id}"
    logger = logging.getLogger(logger_name)

    # Jeśli logger już istnieje, zwróć go
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    logger.propagate = False  # Ważne! Nie propaguj do root loggera

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] - [request_id=%(request_id)s] - %(message)s",
    )

    # File handler dla tej konkretnej sesji
    log_file_path = os.path.join(LOGS_DIR, f"{request_id}.log")
    file_handler = logging.FileHandler(
        log_file_path,
        mode="w",
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    # Dodaj request_id do każdego rekordu
    class SessionFilter(logging.Filter):
        def __init__(self, req_id):
            super().__init__()
            self.req_id = req_id

        def filter(self, record):
            """
            Adds request ID to the log record.

            Args:
                record (LogRecord): The log record being processed.

            Returns:
                bool: Always returns True.
            """
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
                r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$",
                key or "",
            ),
        )

    connection_string = get_secret_env_first("APPINSIGHTS_CONNECTION_STRING")
    if connection_string:
        match = re.search(
            r"InstrumentationKey=([0-9a-fA-F-]+)",
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
                "AzureLogHandler podłączony – logi będą wysyłane do Application Insights",
            )

    logger.info(
        f"Session logger initialized for request_id: {request_id}. "
        f"Log file: {log_file_path}, Level: {logging.getLevelName(logger.level)}",
    )

    return logger


def setup_logger(log_file_path: str) -> logging.Logger:
    """
    Legacy-compatible function for setting up a logger using the current request ID.

    Args:
        log_file_path (str): Path to the log file (unused in modern flow).

    Returns:
        logging.Logger: Logger for the current session.
    """
    request_id = get_request_id()
    return get_session_logger(request_id)


def cleanup_session_logger(request_id: str):
    """
    Removes and deletes all handlers for a session-specific logger.

    Args:
        request_id (str): The request ID of the logger to clean up.
    """
    with _loggers_lock:
        if request_id in _loggers:
            _cleanup_logger(request_id)
            del _loggers[request_id]


def cleanup_all_loggers():
    """
    Clears and removes all session loggers.

    This should be used with caution, as it forcefully closes and removes
    all active loggers from memory. Useful for application shutdown or reset scenarios.
    """
    with _loggers_lock:
        for request_id in list(_loggers.keys()):
            _cleanup_logger(request_id)
        _loggers.clear()
