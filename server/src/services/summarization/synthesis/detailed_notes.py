"""Detailed Notes synthesis strategy - comprehensive paragraphs with timestamps."""

from typing import List
from .base_synthesizer import BaseSynthesizer, ChunkSummary, SynthesisResult


class DetailedNotesSynthesizer(BaseSynthesizer):
    """
    Synthesizes chunk summaries into detailed clinical notes with timestamps.

    Output format example:
    ## Detailed Session Notes

    ### Roles and Commercial Responsibilities
    Nicolas Cassorla and Jaime are in charge of all commercial areas,
    including management of nine salespeople and meeting sales forecasts (00:01:46).
    Nicolas emphasized their dual role: team management and handling their own
    clients as part of that team (00:03:28).

    ### Forecasts and Sales Analysis
    The company uses software called Catrax with forecast and sales modules...
    """

    def get_style_name(self) -> str:
        return "detailed_notes"

    async def synthesize(
        self,
        chunk_summaries: List[ChunkSummary],
        total_duration_minutes: int
    ) -> SynthesisResult:
        """Synthesize into detailed notes format."""
        # Load synthesis prompt template
        prompt_template = self.prompt_loader.load('detailed_notes', self.language)

        # Format chunk summaries for prompt
        formatted_chunks = self._format_chunk_summaries_for_synthesis(chunk_summaries)

        # Build synthesis prompt
        prompt = prompt_template.format(
            chunk_summaries=formatted_chunks,
            total_chunks=len(chunk_summaries),
            total_duration_minutes=total_duration_minutes
        )

        # Generate synthesis (with retry on transient errors)
        response = await self.llm.complete_with_retry(
            prompt,
            max_tokens=4096,  # Claude 3 Haiku max output limit
            temperature=0.3
        )

        return SynthesisResult(
            content=response.content,
            style=self.get_style_name(),
            chunk_count=len(chunk_summaries),
            total_input_tokens=response.input_tokens,
            total_output_tokens=response.output_tokens,
            total_cost_usd=response.cost_usd
        )
