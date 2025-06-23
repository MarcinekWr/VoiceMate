"""Defines the logging configuration for the application."""
import logging


def setup_logger(log_file_path):
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        filename=log_file_path,
        filemode="w",
    )
    return logging.getLogger("AppLogger")
