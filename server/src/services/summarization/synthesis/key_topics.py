"""Key Topics synthesis strategy - percentage-based topic breakdown."""

from typing import List
from .base_synthesizer import BaseSynthesizer, ChunkSummary, SynthesisResult


class KeyTopicsSynthesizer(BaseSynthesizer):
    """
    Synthesizes chunk summaries into a percentage-based topic breakdown.

    Output format example:
    ## Key Topics

    ### Initial Demo and Verifying File Access - 15%
    - Ori guided Shira to test the transcription
    - Shira successfully located the saved transcript file
    - The file was found under 'clinic/transcript' folder

    ### Defining Critical Features - 50%
    - Speaker identification identified as major shortcoming
    - Need for automatic titles with patient name
    ...
    """

    def get_style_name(self) -> str:
        return "key_topics"

    async def synthesize(
        self,
        chunk_summaries: List[ChunkSummary],
        total_duration_minutes: int
    ) -> SynthesisResult:
        """Synthesize into key topics format."""
        # Load synthesis prompt template
        prompt_template = self.prompt_loader.load('key_topics', self.language)

        # Format chunk summaries for prompt
        formatted_chunks = self._format_chunk_summaries_for_synthesis(chunk_summaries)

        # Build synthesis prompt
        prompt = prompt_template.format(
            chunk_summaries=formatted_chunks,
            total_chunks=len(chunk_summaries),
            total_duration_minutes=total_duration_minutes,
            patient_name=self.patient_name
        )

        # Generate synthesis (with retry on transient errors)
        response = await self.llm.complete_with_retry(
            prompt,
            max_tokens=4096,
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
