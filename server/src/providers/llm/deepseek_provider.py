"""DeepSeek LLM provider - cost-effective for chunk summarization."""

import httpx
from typing import Dict, Optional
from .llm_provider import LLMProvider, LLMResponse


class DeepSeekProvider(LLMProvider):
    """
    DeepSeek LLM provider.

    Cost-effective option for Stage 1 chunking:
    - Input: $0.14 per 1M tokens
    - Output: $0.28 per 1M tokens
    - Context: 128K tokens

    Uses OpenAI-compatible API.
    """

    BASE_URL = "https://api.deepseek.com/v1"

    # Cost per 1M tokens (USD)
    COST_INPUT = 0.14
    COST_OUTPUT = 0.28

    def __init__(self, api_key: str, model: str = "deepseek-chat", **kwargs):
        super().__init__(api_key, model, **kwargs)
        self.timeout = kwargs.get('timeout', 60.0)

    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.3
    ) -> LLMResponse:
        """Generate completion using DeepSeek API."""
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
                # Provide helpful error messages for common issues
                if response.status_code == 401:
                    raise Exception(f"DeepSeek API authentication failed (401). Check your DEEPSEEK_API_KEY. Response: {error_text}")
                elif response.status_code == 402:
                    raise Exception(f"DeepSeek API billing error (402). Check your account balance/billing. Response: {error_text}")
                elif response.status_code == 429:
                    raise Exception(f"DeepSeek API rate limit exceeded (429). Try again later. Response: {error_text}")
                else:
                    raise Exception(f"DeepSeek API error {response.status_code}: {error_text}")

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
        return "deepseek"

    def get_cost_per_1m_tokens(self) -> Dict[str, float]:
        return {
            "input": self.COST_INPUT,
            "output": self.COST_OUTPUT
        }

    def get_max_context_length(self) -> int:
        return 128_000
