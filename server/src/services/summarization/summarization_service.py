"""Main summarization service orchestrator."""

import asyncio
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional

from .language_detector import LanguageDetector
from .prompt_loader import PromptLoader
from .chunking import SpeakerSegmentChunker, FixedTimeChunker, BaseChunker
from .synthesis import (
    KeyTopicsSynthesizer,
    DetailedNotesSynthesizer,
    BaseSynthesizer,
    ChunkSummary,
    SynthesisResult
)
from ...providers.llm import LLMProviderFactory, LLMProvider


class SummaryStyle(Enum):
    """Available summary styles."""
    KEY_TOPICS = "key_topics"
    DETAILED_NOTES = "detailed_notes"


@dataclass
class SummaryResult:
    """Result of summarization operation."""
    success: bool
    content: Optional[str] = None
    key_topics: Optional[str] = None
    detailed_notes: Optional[str] = None
    language: str = 'en'
    total_duration_minutes: int = 0
    chunk_count: int = 0
    total_cost_usd: float = 0.0
    error_report: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class SummarizationService:
    """
    Orchestrates hierarchical transcript summarization.

    Two-stage pipeline:
    1. STAGE 1 (Chunking): Segment transcript and summarize chunks with cheap model
    2. STAGE 2 (Synthesis): Combine chunk summaries with quality model

    Key features:
    - Multi-provider LLM support (configurable per stage)
    - Multiple chunking strategies (speaker_segments, fixed_time)
    - Multiple synthesis styles (key_topics, detailed_notes)
    - Automatic language detection (Hebrew/English)
    - Complete error isolation (never fails transcript save)
    """

    def __init__(self, config: 'SummarizationConfig'):
        """
        Initialize summarization service.

        Args:
            config: SummarizationConfig with provider and strategy settings
        """
        self.config = config
        self.language_detector = LanguageDetector()
        self.prompt_loader = PromptLoader()

        # Initialize chunker based on config
        self.chunker = self._create_chunker(config.stage1_approach)

        # LLM providers are created lazily to allow config changes

    def _create_chunker(self, approach: str) -> BaseChunker:
        """Create chunker based on configured approach."""
        if approach == 'fixed_time':
            return FixedTimeChunker(
                chunk_duration_minutes=self.config.stage1_chunk_minutes_max
            )
        else:
            # Default: speaker_segments
            return SpeakerSegmentChunker(
                min_duration_minutes=self.config.stage1_chunk_minutes_min,
                max_duration_minutes=self.config.stage1_chunk_minutes_max
            )

    def _get_stage1_provider(self) -> LLMProvider:
        """Get LLM provider for Stage 1 (chunking)."""
        return LLMProviderFactory.create(
            provider_name=self.config.stage1_provider,
            api_key=self._get_api_key(self.config.stage1_provider),
            model=self.config.stage1_model
        )

    def _get_stage2_provider(self) -> LLMProvider:
        """Get LLM provider for Stage 2 (synthesis)."""
        return LLMProviderFactory.create(
            provider_name=self.config.stage2_provider,
            api_key=self._get_api_key(self.config.stage2_provider),
            model=self.config.stage2_model
        )

    def _get_api_key(self, provider: str) -> str:
        """Get API key for provider from config."""
        provider_lower = provider.lower()
        if provider_lower == 'deepseek':
            return self.config.deepseek_api_key
        elif provider_lower in ['claude', 'anthropic']:
            return self.config.anthropic_api_key
        elif provider_lower in ['openai', 'gpt']:
            return self.config.openai_api_key
        else:
            raise ValueError(f"Unknown provider: {provider}")

    async def summarize(
        self,
        transcript_buffer: List[Dict[str, Any]],
        session_start_ms: int,
        patient_name: str = "Unknown",
        styles: Optional[List[SummaryStyle]] = None
    ) -> SummaryResult:
        """
        Main entry point for summarization.

        This method NEVER raises exceptions - all errors are captured
        and returned in the SummaryResult.

        Args:
            transcript_buffer: List of transcript tokens with text, speaker, timestamp
            session_start_ms: Session start time in milliseconds
            patient_name: Patient name for error reporting
            styles: Summary styles to generate (defaults to config)

        Returns:
            SummaryResult with content or error_report
        """
        try:
            return await self._summarize_internal(
                transcript_buffer,
                session_start_ms,
                patient_name,
                styles
            )
        except Exception as e:
            # Capture ALL errors - never propagate
            error_report = self._format_error_report(
                e,
                transcript_buffer,
                patient_name,
                session_start_ms
            )
            return SummaryResult(
                success=False,
                error_report=error_report
            )

    async def _summarize_internal(
        self,
        transcript_buffer: List[Dict[str, Any]],
        session_start_ms: int,
        patient_name: str,
        styles: Optional[List[SummaryStyle]]
    ) -> SummaryResult:
        """Internal summarization logic."""
        if not transcript_buffer:
            return SummaryResult(
                success=True,
                content="No transcript content to summarize.",
                language='en'
            )

        # Use configured styles if not specified
        if styles is None:
            styles = [SummaryStyle(s) for s in self.config.stage2_styles]

        total_cost = 0.0

        # Step 1: Detect language
        language = self.language_detector.detect(transcript_buffer)

        # Step 2: Segment transcript into chunks
        segments = self.chunker.chunk(transcript_buffer, session_start_ms)

        if not segments:
            return SummaryResult(
                success=True,
                content="Transcript too short to summarize.",
                language=language
            )

        # Calculate duration
        total_duration_ms = (
            segments[-1].end_time_ms - segments[0].start_time_ms
        )
        total_duration_minutes = max(1, int(total_duration_ms / 60_000))

        # Step 3: Summarize each chunk (Stage 1)
        stage1_provider = self._get_stage1_provider()
        chunk_summaries, stage1_cost = await self._summarize_chunks(
            segments,
            stage1_provider,
            language
        )
        total_cost += stage1_cost

        # Step 4: Synthesize final summaries (Stage 2)
        stage2_provider = self._get_stage2_provider()
        synthesis_results = {}

        for style in styles:
            synthesizer = self._create_synthesizer(
                style,
                stage2_provider,
                language
            )
            result = await synthesizer.synthesize(
                chunk_summaries,
                total_duration_minutes
            )
            synthesis_results[style] = result
            total_cost += result.total_cost_usd

        # Build result
        key_topics = None
        detailed_notes = None

        if SummaryStyle.KEY_TOPICS in synthesis_results:
            key_topics = synthesis_results[SummaryStyle.KEY_TOPICS].content
        if SummaryStyle.DETAILED_NOTES in synthesis_results:
            detailed_notes = synthesis_results[SummaryStyle.DETAILED_NOTES].content

        # Combine into single content (use Hebrew headers if Hebrew detected)
        content_parts = []
        if language == 'he':
            key_topics_header = "סיכום נושאים מרכזיים"
            detailed_notes_header = "הערות מפורטות של הפגישה"
        else:
            key_topics_header = "KEY TOPICS SUMMARY"
            detailed_notes_header = "DETAILED SESSION NOTES"

        if key_topics:
            content_parts.append(f"{'='*50}\n{key_topics_header}\n{'='*50}\n\n{key_topics}")
        if detailed_notes:
            content_parts.append(f"{'='*50}\n{detailed_notes_header}\n{'='*50}\n\n{detailed_notes}")

        content = "\n\n".join(content_parts) if content_parts else "No summaries generated."

        return SummaryResult(
            success=True,
            content=content,
            key_topics=key_topics,
            detailed_notes=detailed_notes,
            language=language,
            total_duration_minutes=total_duration_minutes,
            chunk_count=len(segments),
            total_cost_usd=total_cost,
            metadata={
                'stage1_provider': self.config.stage1_provider,
                'stage1_model': self.config.stage1_model,
                'stage2_provider': self.config.stage2_provider,
                'stage2_model': self.config.stage2_model,
                'chunking_approach': self.config.stage1_approach,
            }
        )

    async def _summarize_chunks(
        self,
        segments: list,
        provider: LLMProvider,
        language: str
    ) -> tuple:
        """
        Summarize chunks in parallel using Stage 1 provider.

        Returns:
            Tuple of (chunk_summaries, total_cost)
        """
        # Load chunk summary prompt
        chunk_prompt = self.prompt_loader.load('chunk_summary', language)

        # Create summarization tasks
        tasks = []
        for segment in segments:
            prompt = chunk_prompt.format(
                transcript=segment.text,
                start_time=segment.start_timestamp,
                end_time=segment.end_timestamp,
                duration_minutes=f"{segment.duration_minutes:.1f}"
            )
            tasks.append(provider.complete_with_retry(prompt, max_tokens=1024, temperature=0.3))

        # Execute in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        chunk_summaries = []
        total_cost = 0.0

        for i, result in enumerate(results):
            segment = segments[i]

            if isinstance(result, Exception):
                # Handle individual chunk failure gracefully
                chunk_summaries.append(ChunkSummary(
                    summary=f"[Error summarizing chunk: {str(result)}]",
                    key_points=[],
                    start_timestamp=segment.start_timestamp,
                    end_timestamp=segment.end_timestamp,
                    speakers=list(segment.speakers)
                ))
            else:
                key_points, summary = self._parse_chunk_response(result.content)
                chunk_summaries.append(ChunkSummary(
                    summary=summary,
                    key_points=key_points,
                    start_timestamp=segment.start_timestamp,
                    end_timestamp=segment.end_timestamp,
                    speakers=list(segment.speakers)
                ))
                total_cost += result.cost_usd

        return chunk_summaries, total_cost

    def _parse_chunk_response(self, content: str) -> tuple:
        """Parse chunk summary response into key points and summary."""
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

    def _create_synthesizer(
        self,
        style: SummaryStyle,
        provider: LLMProvider,
        language: str
    ) -> BaseSynthesizer:
        """Create synthesizer for the given style."""
        if style == SummaryStyle.KEY_TOPICS:
            return KeyTopicsSynthesizer(
                llm_provider=provider,
                prompt_loader=self.prompt_loader,
                language=language
            )
        elif style == SummaryStyle.DETAILED_NOTES:
            return DetailedNotesSynthesizer(
                llm_provider=provider,
                prompt_loader=self.prompt_loader,
                language=language
            )
        else:
            raise ValueError(f"Unknown summary style: {style}")

    def _format_error_report(
        self,
        error: Exception,
        transcript_buffer: List[Dict[str, Any]],
        patient_name: str,
        session_start_ms: int
    ) -> str:
        """Format detailed error report for debugging."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        buffer_size = len(transcript_buffer)
        first_text = transcript_buffer[0].get('text', '')[:100] if transcript_buffer else 'N/A'

        return f"""
{'='*60}
SUMMARIZATION ERROR REPORT
{'='*60}

Timestamp: {timestamp}
Patient: {patient_name}
Session Start (ms): {session_start_ms}

Error Type: {type(error).__name__}
Error Message: {str(error)}

Transcript Info:
- Buffer size: {buffer_size} tokens
- First text: {first_text}...

Configuration:
- Stage 1 Provider: {self.config.stage1_provider}
- Stage 1 Model: {self.config.stage1_model}
- Stage 2 Provider: {self.config.stage2_provider}
- Stage 2 Model: {self.config.stage2_model}
- Chunking Approach: {self.config.stage1_approach}

Full Traceback:
{traceback.format_exc()}

{'='*60}
The transcript was saved successfully.
Please check API keys and configuration.
{'='*60}
"""
