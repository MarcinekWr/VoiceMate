import logging
import os

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient


def get_secret_env_first(env_key: str) -> str:
    """
    Retrieve a secret value by first checking local environment variables.
    If not found, fallback to Azure Key Vault using DefaultAzureCredential.

    The secret name used in Azure Key Vault is derived by replacing underscores
    in the env_key with hyphens and converting it to lowercase.

    Args:
        env_key (str): The name of the environment variable or secret.

    Returns:
        str: The value of the environment variable or secret.

    Raises:
        ValueError: If AZURE_KEYVAULT_URL is not set when fallback is needed.
        Exception: If retrieving the secret from Azure Key Vault fails.
    """
    logger = logging.getLogger("fallback")
    value = os.getenv(env_key)
    if value:
        logger.debug(
            f"🔍 Loaded environment variable '{env_key}' from .env or system environment."
        )
        return value

    logger.debug(
        f"🌐 Environment variable '{env_key}' not found locally – checking Azure Key Vault..."
    )

    vault_url = os.getenv("AZURE_KEYVAULT_URL")
    if not vault_url:
        logger.error(
            "❌ AZURE_KEYVAULT_URL is missing – cannot connect to Azure Key Vault."
        )
        raise ValueError("AZURE_KEYVAULT_URL must be set in your environment.")

    try:
        credential = DefaultAzureCredential()
        client = SecretClient(vault_url=vault_url, credential=credential)
        secret_name = env_key.replace("_", "-").lower()
        secret = client.get_secret(secret_name).value
        logger.info(
            f"🔐 Secret '{secret_name}' retrieved successfully from Azure Key Vault."
        )
        return secret
    except Exception as e:
        logger.error(
            f"❌ Failed to retrieve secret '{env_key}' from Azure Key Vault: {e}"
        )
        raise
