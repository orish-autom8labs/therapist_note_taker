"""Faithfulness verification - Stage 3 of the summarization pipeline."""

from typing import List
from .base_synthesizer import BaseSynthesizer, ChunkSummary, SynthesisResult


class FaithfulnessVerifier(BaseSynthesizer):
    """
    Verifies and corrects a draft summary against structured extractions.

    Stage 3 of the pipeline:
    - Input: Stage 1 extractions + Stage 2 draft summary
    - Evaluates on rubric: completeness, faithfulness, conciseness
    - Output: Corrected summary with ungrounded claims removed
    """

    def get_style_name(self) -> str:
        return "verification"

    async def synthesize(
        self,
        chunk_summaries: List[ChunkSummary],
        total_duration_minutes: int
    ) -> SynthesisResult:
        """Not used directly - use verify() instead."""
        raise NotImplementedError("Use verify() for faithfulness verification")

    async def verify(
        self,
        chunk_summaries: List[ChunkSummary],
        draft_summary: str,
        patient_name: str,
    ) -> SynthesisResult:
        """
        Verify a draft summary against structured extractions.

        Args:
            chunk_summaries: Stage 1 structured extractions
            draft_summary: Stage 2 draft summary to verify
            patient_name: Patient name for the prompt

        Returns:
            SynthesisResult with corrected summary content
        """
        # Format extractions for verification prompt
        extractions = self._format_extractions(chunk_summaries)

        # Load verification prompt
        prompt_template = self.prompt_loader.load('verification', self.language)

        prompt = prompt_template.format(
            patient_name=patient_name,
            extractions=extractions,
            draft_summary=draft_summary,
        )

        response = await self.llm.complete_with_retry(
            prompt,
            max_tokens=4096,
            temperature=0.2
        )

        return SynthesisResult(
            content=response.content,
            style="verification",
            chunk_count=len(chunk_summaries),
            total_input_tokens=response.input_tokens,
            total_output_tokens=response.output_tokens,
            total_cost_usd=response.cost_usd
        )

    def _format_extractions(self, chunk_summaries: List[ChunkSummary]) -> str:
        """Format chunk extractions for the verification prompt."""
        parts = []
        for i, chunk in enumerate(chunk_summaries, 1):
            if chunk.raw_extraction:
                parts.append(
                    f"## קטע {i} ({chunk.start_timestamp} - {chunk.end_timestamp})\n\n"
                    f"{chunk.raw_extraction}"
                )
            else:
                # Fallback for legacy format
                points_str = '\n'.join(f'  - {p}' for p in chunk.key_points)
                parts.append(
                    f"## קטע {i} ({chunk.start_timestamp} - {chunk.end_timestamp})\n"
                    f"סיכום: {chunk.summary}\n"
                    f"נקודות מפתח:\n{points_str}"
                )
        return '\n\n'.join(parts)
