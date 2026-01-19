"""OpenAI GPT LLM provider - fallback option."""

import httpx
from typing import Dict, Optional
from .llm_provider import LLMProvider, LLMResponse


class OpenAIProvider(LLMProvider):
    """
    OpenAI GPT LLM provider.

    Fallback option with good all-around performance:
    - GPT-4o-mini: $0.15/$0.60 per 1M tokens (cost-effective)
    - GPT-4o: $2.50/$10 per 1M tokens (high quality)
    - GPT-4-turbo: $10/$30 per 1M tokens

    Default: gpt-4o-mini (best cost/quality balance)
    """

    BASE_URL = "https://api.openai.com/v1"

    # Cost per 1M tokens (USD) - varies by model
    MODEL_COSTS = {
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
        "gpt-4o": {"input": 2.50, "output": 10.0},
        "gpt-4-turbo": {"input": 10.0, "output": 30.0},
        "gpt-4": {"input": 30.0, "output": 60.0},
        "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
    }

    # Context lengths
    MODEL_CONTEXTS = {
        "gpt-4o-mini": 128_000,
        "gpt-4o": 128_000,
        "gpt-4-turbo": 128_000,
        "gpt-4": 8_192,
        "gpt-3.5-turbo": 16_385,
    }

    def __init__(self, api_key: str, model: str = "gpt-4o-mini", **kwargs):
        super().__init__(api_key, model, **kwargs)
        self.timeout = kwargs.get('timeout', 120.0)

    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.3
    ) -> LLMResponse:
        """Generate completion using OpenAI API."""
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature
                }
            )

            if response.status_code != 200:
                error_text = response.text
                raise Exception(f"OpenAI API error {response.status_code}: {error_text}")

            data = response.json()

            # Extract response data
            choice = data.get("choices", [{}])[0]
            content = choice.get("message", {}).get("content", "")
            usage = data.get("usage", {})
            input_tokens = usage.get("prompt_tokens", 0)
            output_tokens = usage.get("completion_tokens", 0)

            return LLMResponse(
                content=content,
                model=self.model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=self.calculate_cost(input_tokens, output_tokens)
            )

    def get_name(self) -> str:
        return "openai"

    def get_cost_per_1m_tokens(self) -> Dict[str, float]:
        return self.MODEL_COSTS.get(
            self.model,
            {"input": 0.15, "output": 0.60}
        )

    def get_max_context_length(self) -> int:
        return self.MODEL_CONTEXTS.get(self.model, 128_000)
