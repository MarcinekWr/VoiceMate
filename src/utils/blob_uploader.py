import os
from typing import Optional

from azure.storage.blob import BlobServiceClient

from src.utils.key_vault import get_secret_env_first
from src.utils.logging_config import get_request_id, get_session_logger


def upload_to_blob(
    container_name: str, file_path: str, blob_name: Optional[str] = None
):
    """
    Upload a file to Azure Blob Storage using a secure connection string.

    The function retrieves the Azure Blob Storage connection string using
    environment variables or Azure Key Vault, and uploads the given file
    to the specified container. Optionally, a custom blob name can be provided.

    Args:
        container_name (str): Name of the destination blob container in Azure.
        file_path (str): Local path to the file to be uploaded.
        blob_name (Optional[str], optional): Name to use for the blob in Azure.
            If not provided, the basename of the file will be used.

    Returns:
        None

    Raises:
        ValueError: If the Azure connection string is not found.
        Exception: If there is an error during the upload process.
    """
    request_id = get_request_id()
    logger = get_session_logger(request_id)

    connection_string = get_secret_env_first("AZURE_STORAGE_CONNECTION_STRING")
    if not connection_string:
        logger.error("❌ Brak AZURE_STORAGE_CONNECTION_STRING w .env")
        return

    try:
        blob_service_client = BlobServiceClient.from_connection_string(
            connection_string,
        )
        container_client = blob_service_client.get_container_client(
            container_name,
        )

        if not blob_name:
            blob_name = os.path.basename(file_path)

        with open(file_path, "rb") as data:
            container_client.upload_blob(
                name=blob_name,
                data=data,
                overwrite=True,
            )

        logger.info(
            f"✅ Plik '{file_path}' wysłany do kontenera '{container_name}' jako '{blob_name}'",
        )

    except Exception as e:
        logger.exception(f"❌ Błąd przy wysyłaniu do Azure Blob Storage: {e}")
