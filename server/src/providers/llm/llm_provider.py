"""Abstract base class for LLM providers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Optional

from .retry import retry_with_backoff


@dataclass
class LLMResponse:
    """Standard response from LLM providers."""
    content: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float

    def __repr__(self) -> str:
        return (
            f"LLMResponse(model={self.model}, "
            f"tokens={self.input_tokens}+{self.output_tokens}, "
            f"cost=${self.cost_usd:.4f})"
        )


class LLMProvider(ABC):
    """
    Abstract base class for LLM providers.

    Implementations must provide:
    - complete(): Generate completion from prompt
    - get_name(): Provider identifier
    - get_cost_per_1m_tokens(): Cost structure for billing
    - get_max_context_length(): Context window size
    """

    def __init__(self, api_key: str, model: str, **kwargs):
        """
        Initialize LLM provider.

        Args:
            api_key: API key for the provider
            model: Model identifier (e.g., 'deepseek-chat', 'claude-3-haiku-20240307')
            **kwargs: Additional provider-specific configuration
        """
        self.api_key = api_key
        self.model = model
        self.config = kwargs

    @abstractmethod
    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.3
    ) -> LLMResponse:
        """
        Generate completion from the LLM.

        Args:
            prompt: User prompt/message
            system_prompt: Optional system instructions
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0-1)

        Returns:
            LLMResponse with content and metadata
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Get provider name (e.g., 'deepseek', 'claude', 'openai')."""
        pass

    @abstractmethod
    def get_cost_per_1m_tokens(self) -> Dict[str, float]:
        """
        Get cost per 1 million tokens.

        Returns:
            Dict with 'input' and 'output' costs in USD
        """
        pass

    @abstractmethod
    def get_max_context_length(self) -> int:
        """Get maximum context length in tokens."""
        pass

    async def complete_with_retry(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.3,
        max_retries: int = 3,
    ) -> 'LLMResponse':
        """
        Generate completion with automatic retry on transient errors.

        Uses exponential backoff: 2s -> 4s -> 8s.
        Non-retryable errors (401, 402) are raised immediately.
        """
        return await retry_with_backoff(
            self.complete,
            prompt,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            max_retries=max_retries,
            base_delay=2.0,
            max_delay=16.0,
        )

    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost for a completion."""
        costs = self.get_cost_per_1m_tokens()
        input_cost = (input_tokens / 1_000_000) * costs['input']
        output_cost = (output_tokens / 1_000_000) * costs['output']
        return input_cost + output_cost
