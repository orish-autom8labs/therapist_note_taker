"""Abstract base class for synthesis strategies."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional
from ..chunking.base_chunker import TranscriptSegment
from ....providers.llm import LLMProvider


@dataclass
class ChunkSummary:
    """Summary of a single transcript chunk."""
    summary: str
    key_points: List[str]
    start_timestamp: str
    end_timestamp: str
    speakers: List[str]


@dataclass
class SynthesisResult:
    """Result of synthesis operation."""
    content: str
    style: str
    chunk_count: int
    total_input_tokens: int
    total_output_tokens: int
    total_cost_usd: float


class BaseSynthesizer(ABC):
    """
    Abstract base class for synthesis strategies.

    Synthesizers combine chunk summaries into final output formats:
    - KeyTopicsSynthesizer: Percentage-based topic breakdown
    - DetailedNotesSynthesizer: Comprehensive paragraphs with timestamps
    """

    def __init__(
        self,
        llm_provider: LLMProvider,
        prompt_loader: 'PromptLoader',
        language: str = 'en'
    ):
        """
        Initialize synthesizer.

        Args:
            llm_provider: LLM provider for generating summaries
            prompt_loader: Loader for prompt templates
            language: Language code ('en' or 'he')
        """
        self.llm = llm_provider
        self.prompt_loader = prompt_loader
        self.language = language

    @abstractmethod
    def get_style_name(self) -> str:
        """Get the style identifier (e.g., 'key_topics', 'detailed_notes')."""
        pass

    @abstractmethod
    async def synthesize(
        self,
        chunk_summaries: List[ChunkSummary],
        total_duration_minutes: int
    ) -> SynthesisResult:
        """
        Synthesize chunk summaries into final output.

        Args:
            chunk_summaries: List of chunk summaries from Stage 1
            total_duration_minutes: Total session duration

        Returns:
            SynthesisResult with final content and metadata
        """
        pass

    async def summarize_chunk(
        self,
        segment: TranscriptSegment,
        chunk_prompt_template: str
    ) -> ChunkSummary:
        """
        Summarize a single transcript segment (Stage 1).

        Args:
            segment: Transcript segment to summarize
            chunk_prompt_template: Prompt template for chunk summarization

        Returns:
            ChunkSummary with summary and key points
        """
        prompt = chunk_prompt_template.format(
            transcript=segment.text,
            start_time=segment.start_timestamp,
            end_time=segment.end_timestamp,
            duration_minutes=f"{segment.duration_minutes:.1f}"
        )

        response = await self.llm.complete(prompt, temperature=0.3)

        # Parse response into key points and summary
        key_points, summary = self._parse_chunk_response(response.content)

        return ChunkSummary(
            summary=summary,
            key_points=key_points,
            start_timestamp=segment.start_timestamp,
            end_timestamp=segment.end_timestamp,
            speakers=list(segment.speakers)
        )

    def _parse_chunk_response(self, content: str) -> tuple:
        """
        Parse LLM response into key points and summary.

        Expected format:
        KEY_POINTS:
        - Point 1
        - Point 2

        SUMMARY:
        Summary text here.
        """
        key_points = []
        summary = ""

        lines = content.strip().split('\n')
        section = None

        for line in lines:
            line_stripped = line.strip()

            if 'KEY_POINTS:' in line_stripped.upper() or 'KEY POINTS:' in line_stripped.upper():
                section = 'key_points'
                continue
            elif 'SUMMARY:' in line_stripped.upper():
                section = 'summary'
                continue

            if section == 'key_points' and line_stripped.startswith('-'):
                point = line_stripped.lstrip('-').strip()
                if point:
                    key_points.append(point)
            elif section == 'summary' and line_stripped:
                summary += line_stripped + ' '

        # Fallback: if parsing fails, use entire content as summary
        if not summary:
            summary = content.strip()

        return key_points, summary.strip()

    def _format_chunk_summaries_for_synthesis(
        self,
        chunk_summaries: List[ChunkSummary]
    ) -> str:
        """Format chunk summaries for the synthesis prompt."""
        parts = []

        for i, chunk in enumerate(chunk_summaries, 1):
            speakers_str = ', '.join(chunk.speakers) if chunk.speakers else 'Unknown'
            points_str = '\n'.join(f'  - {p}' for p in chunk.key_points)

            part = f"""
## Chunk {i} ({chunk.start_timestamp} - {chunk.end_timestamp})
Speakers: {speakers_str}

Key Points:
{points_str}

Summary: {chunk.summary}
"""
            parts.append(part.strip())

        return '\n\n'.join(parts)
