import os
import logging
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

# Initialize logger
logger = logging.getLogger(__name__)
load_dotenv()

def get_secret_env_first(env_key: str) -> str:
    """
    Retrieve a secret from environment variables first.
    If not found, fallback to Azure Key Vault.
    Includes detailed logging for debugging purposes.
    """
    value = os.getenv(env_key)
    if value:
        logger.debug(f"🔍 Loaded environment variable '{env_key}' from .env or system environment.")
        return value

    logger.debug(f"🌐 Environment variable '{env_key}' not found locally – checking Azure Key Vault...")

    vault_url = os.getenv("AZURE_KEYVAULT_URL")
    if not vault_url:
        logger.error("❌ AZURE_KEYVAULT_URL is missing – cannot connect to Azure Key Vault.")
        raise ValueError("AZURE_KEYVAULT_URL must be set in your environment.")

    try:
        credential = DefaultAzureCredential()
        client = SecretClient(vault_url=vault_url, credential=credential)
        secret_name = env_key.replace("_", "-").lower()
        secret = client.get_secret(secret_name).value
        logger.info(f"🔐 Secret '{secret_name}' retrieved successfully from Azure Key Vault.")
        return secret
    except Exception as e:
        logger.error(f"❌ Failed to retrieve secret '{env_key}' from Azure Key Vault: {e}")
        raise

if __name__ == "__main__":
    try:
        secret = get_secret_env_first("AZURE_OPENAI_API_KEY")
        print("✅ Secret retrieved:", secret[:5], "..." if secret else "")
    except Exception as e:
        print("❌ Error:", e)
