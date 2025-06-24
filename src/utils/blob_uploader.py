import os
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv
import logging

load_dotenv()
logger = logging.getLogger(__name__)

AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")

def upload_to_blob(container_name: str, file_path: str, blob_name: str = None):
    if not AZURE_STORAGE_CONNECTION_STRING:
        logger.error("❌ Brak AZURE_STORAGE_CONNECTION_STRING w .env")
        return

    try:
        blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
        container_client = blob_service_client.get_container_client(container_name)

        if not blob_name:
            blob_name = os.path.basename(file_path)

        with open(file_path, "rb") as data:
            container_client.upload_blob(name=blob_name, data=data, overwrite=True)
        
        logger.info(f"✅ Plik '{file_path}' wysłany do kontenera '{container_name}' jako '{blob_name}'")

    except Exception as e:
        logger.exception(f"❌ Błąd przy wysyłaniu do Azure Blob Storage: {e}")
