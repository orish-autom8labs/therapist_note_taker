"""Factory for creating LLM provider instances."""

from typing import Dict, Any, Optional
from .llm_provider import LLMProvider


class LLMProviderFactory:
    """
    Factory for creating LLM provider instances.

    Supports: deepseek, claude, openai
    """

    _providers: Dict[str, type] = {}

    @classmethod
    def register(cls, name: str, provider_class: type):
        """Register a provider class."""
        cls._providers[name.lower()] = provider_class

    @classmethod
    def create(
        cls,
        provider_name: str,
        api_key: str,
        model: Optional[str] = None,
        **kwargs
    ) -> LLMProvider:
        """
        Create an LLM provider instance.

        Args:
            provider_name: Provider identifier ('deepseek', 'claude', 'openai')
            api_key: API key for the provider
            model: Optional model override (uses default if not specified)
            **kwargs: Additional provider-specific configuration

        Returns:
            Configured LLMProvider instance

        Raises:
            ValueError: If provider is not registered
        """
        normalized = provider_name.lower()

        if normalized not in cls._providers:
            available = ', '.join(cls._providers.keys())
            raise ValueError(
                f"Unknown LLM provider: {provider_name}. "
                f"Available: {available}"
            )

        provider_class = cls._providers[normalized]

        # Use default model if not specified
        if model is None:
            model = cls._get_default_model(normalized)

        return provider_class(api_key=api_key, model=model, **kwargs)

    @classmethod
    def _get_default_model(cls, provider_name: str) -> str:
        """Get default model for a provider."""
        defaults = {
            'deepseek': 'deepseek-chat',
            'claude': 'claude-3-haiku-20240307',
            'openai': 'gpt-4o-mini',
        }
        return defaults.get(provider_name, '')

    @classmethod
    def get_available_providers(cls) -> list:
        """Get list of registered provider names."""
        return list(cls._providers.keys())


# Import and register providers (done at module load)
def _register_providers():
    """Register all available providers."""
    try:
        from .deepseek_provider import DeepSeekProvider
        LLMProviderFactory.register('deepseek', DeepSeekProvider)
    except ImportError:
        pass

    try:
        from .claude_provider import ClaudeProvider
        LLMProviderFactory.register('claude', ClaudeProvider)
    except ImportError:
        pass

    try:
        from .openai_provider import OpenAIProvider
        LLMProviderFactory.register('openai', OpenAIProvider)
    except ImportError:
        pass


_register_providers()
