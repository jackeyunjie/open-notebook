"""
API Key Provider - Database-first with environment fallback.

This module provides a unified interface for retrieving API keys and provider
configuration. It reads from Credential records (individual per-provider
credentials) and falls back to environment variables for backward compatibility.

Usage:
    from open_notebook.ai.key_provider import provision_provider_keys

    # Call before model provisioning to set env vars from DB
    await provision_provider_keys("openai")
"""

import os
from typing import Optional

from loguru import logger

from open_notebook.domain.credential import Credential


# =============================================================================
# Provider Configuration Mapping
# =============================================================================
# Maps provider names to their environment variable names.
# This is the single source of truth for provider-to-env-var mapping.

PROVIDER_CONFIG = {
    # Simple providers (just API key)
    "openai": {
        "env_var": "OPENAI_API_KEY",
    },
    "anthropic": {
        "env_var": "ANTHROPIC_API_KEY",
    },
    "google": {
        "env_var": "GOOGLE_API_KEY",
    },
    "groq": {
        "env_var": "GROQ_API_KEY",
    },
    "mistral": {
        "env_var": "MISTRAL_API_KEY",
    },
    "deepseek": {
        "env_var": "DEEPSEEK_API_KEY",
    },
    "xai": {
        "env_var": "XAI_API_KEY",
    },
    "openrouter": {
        "env_var": "OPENROUTER_API_KEY",
    },
    "voyage": {
        "env_var": "VOYAGE_API_KEY",
    },
    "elevenlabs": {
        "env_var": "ELEVENLABS_API_KEY",
    },
    # URL-based providers
    "ollama": {
        "env_var": "OLLAMA_API_BASE",
    },
}


async def _get_default_credential(provider: str) -> Optional[Credential]:
    """Get the first credential for a provider from the database."""
    try:
        credentials = await Credential.get_by_provider(provider)
        if credentials:
            return credentials[0]
    except Exception as e:
        logger.debug(f"Could not load credential from database for {provider}: {e}")
    return None


async def get_api_key(provider: str) -> Optional[str]:
    """
    Get API key for a provider. Checks database first, then env var.

    Args:
        provider: Provider name (openai, anthropic, etc.)

    Returns:
        API key string or None if not configured
    """
    cred = await _get_default_credential(provider)
    if cred and cred.api_key:
        logger.debug(f"Using {provider} API key from Credential")
        return cred.api_key.get_secret_value()

    # Fall back to environment variable
    config_info = PROVIDER_CONFIG.get(provider.lower())
    if config_info:
        env_value = os.environ.get(config_info["env_var"])
        if env_value:
            logger.debug(f"Using {provider} API key from environment variable")
        return env_value

    return None


async def _provision_simple_provider(provider: str) -> bool:
    """
    Set environment variable for a simple provider from DB config.

    Returns:
        True if key was set from database, False otherwise
    """
    provider_lower = provider.lower()
    config_info = PROVIDER_CONFIG.get(provider_lower)
    if not config_info:
        return False

    env_var = config_info["env_var"]

    cred = await _get_default_credential(provider_lower)
    if not cred:
        return False

    # Set API key / primary env var
    if cred.api_key:
        os.environ[env_var] = cred.api_key.get_secret_value()
        logger.debug(f"Set {env_var} from Credential")

    # Set base URL if present
    if cred.base_url:
        provider_upper = provider_lower.upper()
        os.environ[f"{provider_upper}_API_BASE"] = cred.base_url
        logger.debug(f"Set {provider_upper}_API_BASE from Credential")

    return True


async def _provision_vertex() -> bool:
    """
    Set environment variables for Google Vertex AI from DB config.

    Returns:
        True if any keys were set from database
    """
    any_set = False

    cred = await _get_default_credential("vertex")
    if not cred:
        return False

    if cred.project:
        os.environ["VERTEX_PROJECT"] = cred.project
        logger.debug("Set VERTEX_PROJECT from Credential")
        any_set = True
    if cred.location:
        os.environ["VERTEX_LOCATION"] = cred.location
        logger.debug("Set VERTEX_LOCATION from Credential")
        any_set = True
    if cred.credentials_path:
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = cred.credentials_path
        logger.debug("Set GOOGLE_APPLICATION_CREDENTIALS from Credential")
        any_set = True

    return any_set


async def _provision_azure() -> bool:
    """
    Set environment variables for Azure OpenAI from DB config.

    Returns:
        True if any keys were set from database
    """
    any_set = False

    cred = await _get_default_credential("azure")
    if not cred:
        return False

    if cred.api_key:
        os.environ["AZURE_OPENAI_API_KEY"] = cred.api_key.get_secret_value()
        logger.debug("Set AZURE_OPENAI_API_KEY from Credential")
        any_set = True
    if cred.api_version:
        os.environ["AZURE_OPENAI_API_VERSION"] = cred.api_version
        logger.debug("Set AZURE_OPENAI_API_VERSION from Credential")
        any_set = True
    if cred.endpoint:
        os.environ["AZURE_OPENAI_ENDPOINT"] = cred.endpoint
        logger.debug("Set AZURE_OPENAI_ENDPOINT from Credential")
        any_set = True
    if cred.endpoint_llm:
        os.environ["AZURE_OPENAI_ENDPOINT_LLM"] = cred.endpoint_llm
        logger.debug("Set AZURE_OPENAI_ENDPOINT_LLM from Credential")
        any_set = True
    if cred.endpoint_embedding:
        os.environ["AZURE_OPENAI_ENDPOINT_EMBEDDING"] = cred.endpoint_embedding
        logger.debug("Set AZURE_OPENAI_ENDPOINT_EMBEDDING from Credential")
        any_set = True
    if cred.endpoint_stt:
        os.environ["AZURE_OPENAI_ENDPOINT_STT"] = cred.endpoint_stt
        logger.debug("Set AZURE_OPENAI_ENDPOINT_STT from Credential")
        any_set = True
    if cred.endpoint_tts:
        os.environ["AZURE_OPENAI_ENDPOINT_TTS"] = cred.endpoint_tts
        logger.debug("Set AZURE_OPENAI_ENDPOINT_TTS from Credential")
        any_set = True

    return any_set


async def _provision_openai_compatible() -> bool:
    """
    Set environment variables for OpenAI-Compatible providers from DB config.

    Returns:
        True if any keys were set from database
    """
    any_set = False

    cred = await _get_default_credential("openai_compatible")
    if not cred:
        return False

    if cred.api_key:
        os.environ["OPENAI_COMPATIBLE_API_KEY"] = cred.api_key.get_secret_value()
        logger.debug("Set OPENAI_COMPATIBLE_API_KEY from Credential")
        any_set = True
    if cred.base_url:
        os.environ["OPENAI_COMPATIBLE_BASE_URL"] = cred.base_url
        logger.debug("Set OPENAI_COMPATIBLE_BASE_URL from Credential")
        any_set = True

    return any_set


async def provision_provider_keys(provider: str) -> bool:
    """
    Provision environment variables from database for a specific provider.

    This function checks if the provider has a Credential record stored in the
    database and sets the corresponding environment variables. If the database
    doesn't have the configuration, existing environment variables remain unchanged.

    This is the main entry point for the DB->Env fallback mechanism.

    Args:
        provider: Provider name (openai, anthropic, azure, vertex,
                  openai-compatible, etc.)

    Returns:
        True if any keys were set from database, False otherwise

    Example:
        # Before provisioning a model, ensure DB keys are in env vars
        await provision_provider_keys("openai")
        model = AIFactory.create_language(model_name="gpt-4", provider="openai")
    """
    # Normalize provider name
    provider_lower = provider.lower()

    # Handle complex providers with multiple config fields
    if provider_lower == "vertex":
        return await _provision_vertex()
    elif provider_lower == "azure":
        return await _provision_azure()
    elif provider_lower in ("openai-compatible", "openai_compatible"):
        return await _provision_openai_compatible()

    # Handle simple providers
    return await _provision_simple_provider(provider_lower)


async def provision_all_keys() -> dict[str, bool]:
    """
    Provision environment variables from database for all providers.

    NOTE: This function is deprecated for request-time use because it can leave
    stale env vars after key deletion. Keys should only be provisioned at startup
    or via provision_provider_keys() for specific providers.

    Useful at application startup to load all DB-stored keys into environment.

    Returns:
        Dict mapping provider names to whether keys were set from DB
    """
    results: dict[str, bool] = {}

    # Simple providers
    for provider in PROVIDER_CONFIG.keys():
        results[provider] = await provision_provider_keys(provider)

    # Complex providers
    results["vertex"] = await provision_provider_keys("vertex")
    results["azure"] = await provision_provider_keys("azure")
    results["openai_compatible"] = await provision_provider_keys("openai_compatible")

    return results


# =============================================================================
# Environment Variable to Database Initialization
# =============================================================================
# Auto-create ProviderConfig and Credential from environment variables
# This enables code-based configuration without UI setup

# Extended provider config with additional metadata for auto-initialization
PROVIDER_INIT_CONFIG = {
    "deepseek": {
        "env_var": "DEEPSEEK_API_KEY",
        "base_url_env": "DEEPSEEK_BASE_URL",
        "default_base_url": "https://api.deepseek.com",
        "display_name": "DeepSeek",
    },
    "qwen": {
        "env_var": "DASHSCOPE_API_KEY",
        "base_url_env": "DASHSCOPE_BASE_URL",
        "default_base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "display_name": "通义千问",
    },
    "moonshot": {
        "env_var": "MOONSHOT_API_KEY",
        "base_url_env": "MOONSHOT_BASE_URL",
        "default_base_url": "https://api.moonshot.cn/v1",
        "display_name": "Moonshot",
    },
    "openai": {
        "env_var": "OPENAI_API_KEY",
        "base_url_env": "OPENAI_BASE_URL",
        "default_base_url": None,
        "display_name": "OpenAI",
    },
    "anthropic": {
        "env_var": "ANTHROPIC_API_KEY",
        "base_url_env": "ANTHROPIC_BASE_URL",
        "default_base_url": None,
        "display_name": "Anthropic",
    },
}


async def init_provider_from_env(provider: str) -> bool:
    """
    Initialize a provider from environment variables.
    Creates Credential and ProviderConfig records if they don't exist.

    Args:
        provider: Provider name (deepseek, qwen, moonshot, etc.)

    Returns:
        True if provider was initialized, False otherwise
    """
    from open_notebook.domain.credential import Credential
    from open_notebook.domain.provider_config import ProviderConfig, ProviderCredential

    provider_lower = provider.lower()
    config = PROVIDER_INIT_CONFIG.get(provider_lower)
    if not config:
        logger.warning(f"No init config found for provider: {provider}")
        return False

    # Check if already configured in database (check both Credential and ProviderConfig)
    existing_creds = await Credential.get_by_provider(provider_lower)
    if existing_creds:
        logger.debug(f"Provider {provider} already has credentials in DB, skipping env init")
        return False

    # Also check ProviderConfig
    try:
        provider_config = await ProviderConfig.get_instance()
        if provider_config.get_default_config(provider_lower):
            logger.debug(f"Provider {provider} already has ProviderConfig, skipping env init")
            return False
    except Exception:
        # ProviderConfig might not exist yet, continue with initialization
        pass

    # Get API key from environment
    api_key = os.environ.get(config["env_var"])
    if not api_key:
        logger.debug(f"No API key found in env var {config['env_var']} for {provider}")
        return False

    try:
        # Determine base URL
        base_url = os.environ.get(config["base_url_env"]) or config["default_base_url"]

        # Create Credential record
        credential = Credential(
            name=f"{config['display_name']} Auto-Config",
            provider=provider_lower,
            api_key=api_key,
            base_url=base_url,
        )
        await credential.save()
        logger.info(f"Created Credential for {provider} from environment variable")

        # Create ProviderConfig entry
        try:
            from pydantic import SecretStr
            provider_config = await ProviderConfig.get_instance()

            # Create new ProviderCredential
            new_cred = ProviderCredential(
                id=f"{provider_lower}_auto_{os.urandom(4).hex()}",
                name=f"{config['display_name']} Auto-Config",
                provider=provider_lower,
                is_default=True,
                api_key=SecretStr(api_key),
                base_url=base_url,
            )
            provider_config.add_config(provider_lower, new_cred)
            await provider_config.save()
            logger.info(f"Created ProviderConfig for {provider}")
        except Exception as e:
            logger.warning(f"Could not create ProviderConfig for {provider}: {e}")
            # Non-critical error, Credential is already created

        return True

    except Exception as e:
        logger.error(f"Failed to initialize {provider} from environment: {e}")
        return False


async def init_all_providers_from_env() -> dict[str, bool]:
    """
    Initialize all supported providers from environment variables.
    Call this at application startup to auto-configure providers.

    Returns:
        Dict mapping provider names to initialization success status
    """
    results: dict[str, bool] = {}

    for provider in PROVIDER_INIT_CONFIG.keys():
        try:
            results[provider] = await init_provider_from_env(provider)
        except Exception as e:
            logger.error(f"Error initializing {provider}: {e}")
            results[provider] = False

    # Log summary
    initialized = [p for p, success in results.items() if success]
    if initialized:
        logger.info(f"Auto-initialized providers from environment: {', '.join(initialized)}")
    else:
        logger.debug("No providers were auto-initialized from environment variables")

    return results
