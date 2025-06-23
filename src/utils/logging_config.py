"""Defines the logging configuration for the application."""
import logging
import os
from opencensus.ext.azure.log_exporter import AzureLogHandler
from common.constants import LOG_FILE_PATH  

def setup_logger(log_file_path: str = LOG_FILE_PATH) -> logging.Logger:
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

        file_handler = logging.FileHandler(log_file_path, mode="w", encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

        connection_string = os.getenv("APPINSIGHTS_CONNECTION_STRING")
        if connection_string:
            azure_handler = AzureLogHandler(connection_string=connection_string)
            azure_handler.setFormatter(formatter)
            logger.addHandler(azure_handler)
            logger.info("AzureLogHandler podłączony – logi będą wysyłane do Application Insights")
        else:
            logger.warning("Brak APPINSIGHTS_CONNECTION_STRING – logi nie będą wysyłane do Application Insights")

    return logger

