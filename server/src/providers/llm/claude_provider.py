"""Anthropic Claude LLM provider - high quality for synthesis."""

import httpx
from typing import Dict, Optional
from .llm_provider import LLMProvider, LLMResponse


class ClaudeProvider(LLMProvider):
    """
    Anthropic Claude LLM provider.

    High quality option for Stage 2 synthesis:
    - Claude 3 Haiku: $0.25/$1.25 per 1M tokens (cost-effective)
    - Claude 3 Sonnet: $3/$15 per 1M tokens (balanced)
    - Claude 3 Opus: $15/$75 per 1M tokens (highest quality)

    Default: claude-3-haiku-20240307 (best cost/quality for summaries)
    """

    BASE_URL = "https://api.anthropic.com/v1"
    API_VERSION = "2023-06-01"

    # Cost per 1M tokens (USD) - varies by model
    MODEL_COSTS = {
        "claude-3-haiku-20240307": {"input": 0.25, "output": 1.25},
        "claude-3-5-haiku-20241022": {"input": 1.0, "output": 5.0},
        "claude-3-sonnet-20240229": {"input": 3.0, "output": 15.0},
        "claude-3-5-sonnet-20241022": {"input": 3.0, "output": 15.0},
        "claude-3-opus-20240229": {"input": 15.0, "output": 75.0},
    }

    # Context lengths
    MODEL_CONTEXTS = {
        "claude-3-haiku-20240307": 200_000,
        "claude-3-5-haiku-20241022": 200_000,
        "claude-3-sonnet-20240229": 200_000,
        "claude-3-5-sonnet-20241022": 200_000,
        "claude-3-opus-20240229": 200_000,
    }

    def __init__(self, api_key: str, model: str = "claude-3-haiku-20240307", **kwargs):
        super().__init__(api_key, model, **kwargs)
        self.timeout = kwargs.get('timeout', 120.0)

    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.3
    ) -> LLMResponse:
        """Generate completion using Anthropic Claude API."""
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": self.API_VERSION,
            "Content-Type": "application/json"
        }

        body = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}]
        }

        if system_prompt:
            body["system"] = system_prompt

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.BASE_URL}/messages",
                headers=headers,
                json=body
            )

            if response.status_code != 200:
                error_text = response.text
                # Provide helpful error messages for common issues
                if response.status_code == 401:
                    raise Exception(f"Claude API authentication failed (401). Check your ANTHROPIC_API_KEY. Response: {error_text}")
                elif response.status_code == 402:
                    raise Exception(f"Claude API billing error (402). Check your Anthropic account balance/billing. Response: {error_text}")
                elif response.status_code == 429:
                    raise Exception(f"Claude API rate limit exceeded (429). Try again later. Response: {error_text}")
                elif response.status_code == 529:
                    raise Exception(f"Claude API overloaded (529). Anthropic servers are busy, try again later. Response: {error_text}")
                else:
                    raise Exception(f"Claude API error {response.status_code}: {error_text}")

            data = response.json()

            # Extract response data
            content_blocks = data.get("content", [])
            content = ""
            for block in content_blocks:
                if block.get("type") == "text":
                    content += block.get("text", "")

            usage = data.get("usage", {})
            input_tokens = usage.get("input_tokens", 0)
            output_tokens = usage.get("output_tokens", 0)

            return LLMResponse(
                content=content,
                model=self.model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=self.calculate_cost(input_tokens, output_tokens)
            )

    def get_name(self) -> str:
        return "claude"

    def get_cost_per_1m_tokens(self) -> Dict[str, float]:
        # Return costs for current model, default to haiku costs
        return self.MODEL_COSTS.get(
            self.model,
            {"input": 0.25, "output": 1.25}
        )

    def get_max_context_length(self) -> int:
        return self.MODEL_CONTEXTS.get(self.model, 200_000)
