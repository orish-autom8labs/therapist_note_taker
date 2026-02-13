"""Main summarization service orchestrator."""

import asyncio
import logging
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

from .language_detector import LanguageDetector
from .prompt_loader import PromptLoader
from .chunking import SpeakerSegmentChunker, FixedTimeChunker, BaseChunker
from .preprocessing import SpeakerMerger
from .synthesis import (
    KeyTopicsSynthesizer,
    DetailedNotesSynthesizer,
    FaithfulnessVerifier,
    BaseSynthesizer,
    ChunkSummary,
    SynthesisResult
)
from ...providers.llm import LLMProviderFactory, LLMProvider
from ...config import SummaryLevelConfig, SUMMARY_LEVELS


class SummaryStyle(Enum):
    """Available summary styles."""
    KEY_TOPICS = "key_topics"
    DETAILED_NOTES = "detailed_notes"


@dataclass
class LevelResult:
    """Result of a single summary level."""
    level_name: str
    level_label_he: str
    content: str
    key_topics: Optional[str] = None
    detailed_notes: Optional[str] = None
    cost_usd: float = 0.0
    chunk_count: int = 0


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
    level_results: List[LevelResult] = field(default_factory=list)


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

    def _create_provider(self, provider_name: str, model: str) -> LLMProvider:
        """Create an LLM provider from name and model."""
        return LLMProviderFactory.create(
            provider_name=provider_name,
            api_key=self._get_api_key(provider_name),
            model=model
        )

    async def summarize_all_levels(
        self,
        transcript_buffer: List[Dict[str, Any]],
        session_start_ms: int,
        patient_name: str = "Unknown",
        level_names: Optional[List[str]] = None,
    ) -> SummaryResult:
        """
        Run multiple summary levels and combine results.

        This is the main entry point for multi-level summarization.
        Each level runs independently with its own configuration.

        Args:
            transcript_buffer: List of transcript tokens
            session_start_ms: Session start time in milliseconds
            patient_name: Patient name for summaries
            level_names: Which levels to run (defaults to config.summary_levels)

        Returns:
            SummaryResult with all level results combined
        """
        try:
            return await self._summarize_all_levels_internal(
                transcript_buffer, session_start_ms, patient_name, level_names
            )
        except Exception as e:
            error_report = self._format_error_report(
                e, transcript_buffer, patient_name, session_start_ms
            )
            return SummaryResult(success=False, error_report=error_report)

    async def _summarize_all_levels_internal(
        self,
        transcript_buffer: List[Dict[str, Any]],
        session_start_ms: int,
        patient_name: str,
        level_names: Optional[List[str]],
    ) -> SummaryResult:
        """Internal multi-level summarization logic."""
        if not transcript_buffer:
            return SummaryResult(
                success=True,
                content="אין תוכן תמלול לסכם.",
                language='he'
            )

        if level_names is None:
            level_names = self.config.summary_levels

        language = self.language_detector.detect(transcript_buffer)
        total_cost = 0.0
        level_results: List[LevelResult] = []

        # Pre-compute shared resources: chunking (with and without overlap)
        segments_with_overlap = None
        segments_no_overlap = None

        for level_name in level_names:
            level_config = SUMMARY_LEVELS.get(level_name.strip())
            if not level_config:
                continue

            level_result = await self._run_single_level(
                transcript_buffer=transcript_buffer,
                session_start_ms=session_start_ms,
                patient_name=patient_name,
                language=language,
                level_config=level_config,
            )
            level_results.append(level_result)
            total_cost += level_result.cost_usd

        # Combine all level results into one document
        content = self._format_multi_level_document(
            level_results, patient_name, language
        )

        # Use the best available level for top-level fields
        best_result = level_results[-1] if level_results else None

        return SummaryResult(
            success=True,
            content=content,
            key_topics=best_result.key_topics if best_result else None,
            detailed_notes=best_result.detailed_notes if best_result else None,
            language=language,
            total_duration_minutes=0,  # Set by caller
            chunk_count=best_result.chunk_count if best_result else 0,
            total_cost_usd=total_cost,
            level_results=level_results,
            metadata={
                'levels_generated': [r.level_name for r in level_results],
                'stage1_provider': self.config.stage1_provider,
                'stage1_model': self.config.stage1_model,
            }
        )

    async def _run_single_level(
        self,
        transcript_buffer: List[Dict[str, Any]],
        session_start_ms: int,
        patient_name: str,
        language: str,
        level_config: SummaryLevelConfig,
    ) -> LevelResult:
        """Run a single summary level."""
        total_cost = 0.0
        chunk_summaries: List[ChunkSummary] = []

        # Pre-processing: merge ghost speakers (3→2)
        if level_config.use_speaker_merge:
            merger = SpeakerMerger()
            merge_result = merger.merge(transcript_buffer)
            if merge_result.was_merged:
                transcript_buffer = merge_result.buffer
                logger.info(
                    "[SPEAKER-MERGE] Level %s: merged speakers %s",
                    level_config.name, merge_result.merge_map,
                )

        if level_config.use_chunking:
            # Create chunker with or without overlap
            if level_config.use_overlap:
                chunker = SpeakerSegmentChunker(
                    min_duration_minutes=self.config.stage1_chunk_minutes_min,
                    max_duration_minutes=self.config.stage1_chunk_minutes_max,
                    overlap_turns=3
                )
            else:
                chunker = SpeakerSegmentChunker(
                    min_duration_minutes=self.config.stage1_chunk_minutes_min,
                    max_duration_minutes=self.config.stage1_chunk_minutes_max,
                    overlap_turns=0
                )

            segments = chunker.chunk(transcript_buffer, session_start_ms)

            if segments:
                # Stage 1: Extract/summarize chunks
                stage1_provider = self._get_stage1_provider()
                chunk_summaries, stage1_cost = await self._summarize_chunks(
                    segments, stage1_provider, language,
                    use_structured_extraction=level_config.use_structured_extraction
                )
                total_cost += stage1_cost

        # Stage 2: Synthesis
        stage2_provider = self._create_provider(
            level_config.stage2_provider, level_config.stage2_model
        )
        synthesis_results: Dict[str, str] = {}

        if level_config.use_chunking and chunk_summaries:
            # Normal multi-chunk synthesis
            total_duration_ms = (
                segments[-1].end_time_ms - segments[0].start_time_ms
            ) if segments else 0
            total_duration_minutes = max(1, int(total_duration_ms / 60_000))

            for style_name in level_config.stage2_styles:
                style = SummaryStyle(style_name)
                synthesizer = self._create_synthesizer(
                    style, stage2_provider, language, patient_name=patient_name
                )
                result = await synthesizer.synthesize(
                    chunk_summaries, total_duration_minutes
                )
                synthesis_results[style_name] = result.content
                total_cost += result.total_cost_usd
        else:
            # Quick mode: single pass on full transcript
            total_duration_minutes = self._estimate_duration_minutes(
                transcript_buffer, session_start_ms
            )
            for style_name in level_config.stage2_styles:
                style = SummaryStyle(style_name)
                synthesizer = self._create_synthesizer(
                    style, stage2_provider, language, patient_name=patient_name
                )
                # Create a single pseudo-chunk from the full transcript
                full_text = self._format_full_transcript_for_quick(
                    transcript_buffer, session_start_ms
                )
                pseudo_chunk = ChunkSummary(
                    summary=full_text,
                    key_points=[],
                    start_timestamp="00:00",
                    end_timestamp=self.chunker.ms_to_timestamp(
                        total_duration_minutes * 60_000
                    ),
                    speakers=[],
                    raw_extraction=""
                )
                result = await synthesizer.synthesize(
                    [pseudo_chunk], total_duration_minutes
                )
                synthesis_results[style_name] = result.content
                total_cost += result.total_cost_usd

        # Stage 3: Verification (if configured)
        if level_config.use_verification and chunk_summaries:
            verification_provider = self._create_provider(
                level_config.verification_provider,
                level_config.verification_model
            )
            verifier = FaithfulnessVerifier(
                llm_provider=verification_provider,
                prompt_loader=self.prompt_loader,
                language=language,
                patient_name=patient_name
            )

            # Verify each synthesis result
            for style_name, draft_content in list(synthesis_results.items()):
                verified = await verifier.verify(
                    chunk_summaries, draft_content, patient_name
                )
                synthesis_results[style_name] = verified.content
                total_cost += verified.total_cost_usd

        # Build combined content for this level
        content_parts = []
        key_topics = synthesis_results.get('key_topics')
        detailed_notes = synthesis_results.get('detailed_notes')

        if key_topics:
            content_parts.append(key_topics)
        if detailed_notes:
            content_parts.append(detailed_notes)

        return LevelResult(
            level_name=level_config.name,
            level_label_he=level_config.label_he,
            content='\n\n'.join(content_parts) if content_parts else "לא נוצר סיכום.",
            key_topics=key_topics,
            detailed_notes=detailed_notes,
            cost_usd=total_cost,
            chunk_count=len(chunk_summaries),
        )

    def _estimate_duration_minutes(
        self,
        transcript_buffer: List[Dict[str, Any]],
        session_start_ms: int
    ) -> int:
        """Estimate total duration from transcript buffer."""
        if not transcript_buffer:
            return 0
        first_ts = transcript_buffer[0].get('timestamp', 0)
        last_ts = transcript_buffer[-1].get('timestamp', 0)
        duration_ms = last_ts - first_ts
        return max(1, int(duration_ms / 60_000))

    def _format_full_transcript_for_quick(
        self,
        transcript_buffer: List[Dict[str, Any]],
        session_start_ms: int
    ) -> str:
        """Format full transcript for quick single-pass mode."""
        lines = []
        current_speaker = None
        for token in transcript_buffer:
            speaker = token.get('speaker', 'Unknown')
            text = token.get('text', '')
            if not text.strip():
                continue
            if speaker != current_speaker:
                lines.append(f"\nדובר {speaker}: {text}")
                current_speaker = speaker
            else:
                lines.append(text)
        return ' '.join(lines)

    def _format_multi_level_document(
        self,
        level_results: List[LevelResult],
        patient_name: str,
        language: str,
    ) -> str:
        """Format all level results into one combined document."""
        parts = []

        for level_result in level_results:
            header = f"**{level_result.level_label_he}**"
            parts.append(f"{header}\n\n{level_result.content}")

        return '\n\n---\n\n'.join(parts)

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
                language,
                patient_name=patient_name
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
        language: str,
        use_structured_extraction: bool = True
    ) -> tuple:
        """
        Summarize/extract from chunks in parallel using Stage 1 provider.

        Args:
            segments: Transcript segments to process
            provider: LLM provider for Stage 1
            language: Language code
            use_structured_extraction: If True, use new structured extraction prompt.
                If False, use legacy chunk_summary prompt (for Level 1 quick mode).

        Returns:
            Tuple of (chunk_summaries, total_cost)
        """
        # Load appropriate prompt
        if use_structured_extraction:
            chunk_prompt = self.prompt_loader.load('chunk_extraction', language)
            max_tokens = 2048
            temperature = 0.1
        else:
            chunk_prompt = self.prompt_loader.load('chunk_summary', language)
            max_tokens = 1024
            temperature = 0.3

        # Create extraction/summarization tasks
        tasks = []
        for segment in segments:
            prompt = chunk_prompt.format(
                transcript=segment.text,
                start_time=segment.start_timestamp,
                end_time=segment.end_timestamp,
                duration_minutes=f"{segment.duration_minutes:.1f}"
            )
            tasks.append(provider.complete_with_retry(
                prompt, max_tokens=max_tokens, temperature=temperature
            ))

        # Execute in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        chunk_summaries: list[ChunkSummary] = []
        total_cost = 0.0

        for i, result in enumerate(results):
            segment = segments[i]

            if isinstance(result, Exception):
                # Handle individual chunk failure gracefully
                chunk_summaries.append(ChunkSummary(
                    summary=f"[שגיאה בחילוץ קטע: {str(result)}]",
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
                    speakers=list(segment.speakers),
                    raw_extraction=result.content if use_structured_extraction else ""
                ))
                total_cost += result.cost_usd

        return chunk_summaries, total_cost

    def _parse_chunk_response(self, content: str) -> tuple:
        """Parse chunk summary response into key points and summary.

        Handles both legacy (KEY_POINTS + SUMMARY) and new structured
        extraction format (SPEAKERS, TOPICS, EMOTIONS_EXPRESSED, etc.).
        """
        key_points: list[str] = []
        summary = ""

        lines = content.strip().split('\n')
        section = None

        # Check if this is the new structured extraction format
        is_structured = any(
            s in content.upper()
            for s in ['SPEAKERS:', 'TOPICS:', 'EMOTIONS_EXPRESSED:']
        )

        if is_structured:
            return self._parse_structured_extraction(content)

        # Legacy format parsing
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

    def _parse_structured_extraction(self, content: str) -> tuple:
        """Parse new structured extraction format into key points and summary.

        Returns (key_points, summary) for backward compatibility,
        plus stores full extraction in the ChunkSummary.raw_extraction field.
        """
        sections: dict[str, list[str]] = {}
        current_section = None
        summary = ""

        for line in content.strip().split('\n'):
            line_stripped = line.strip()
            line_upper = line_stripped.upper()

            # Detect section headers
            if line_upper.startswith('SPEAKERS:'):
                current_section = 'speakers'
                continue
            elif line_upper.startswith('TOPICS:'):
                current_section = 'topics'
                continue
            elif line_upper.startswith('EMOTIONS_EXPRESSED:') or line_upper.startswith('EMOTIONS:'):
                current_section = 'emotions'
                continue
            elif line_upper.startswith('THERAPEUTIC_MOMENTS:') or line_upper.startswith('THERAPEUTIC MOMENTS:'):
                current_section = 'therapeutic_moments'
                continue
            elif line_upper.startswith('SIGNIFICANT_QUOTES:') or line_upper.startswith('SIGNIFICANT QUOTES:'):
                current_section = 'significant_quotes'
                continue
            elif line_upper.startswith('FACTUAL_DETAILS:') or line_upper.startswith('FACTUAL DETAILS:'):
                current_section = 'factual_details'
                continue
            elif line_upper.startswith('ACTION_ITEMS:') or line_upper.startswith('ACTION ITEMS:'):
                current_section = 'action_items'
                continue
            elif line_upper.startswith('SUMMARY:'):
                current_section = 'summary'
                continue

            if current_section == 'summary' and line_stripped:
                summary += line_stripped + ' '
            elif current_section and line_stripped.startswith('-'):
                point = line_stripped.lstrip('-').strip()
                if point:
                    sections.setdefault(current_section, []).append(point)

        # Build key_points from topics + emotions for backward compatibility
        key_points = sections.get('topics', []) + sections.get('emotions', [])

        if not summary:
            summary = content.strip()

        return key_points, summary.strip()

    def _create_synthesizer(
        self,
        style: SummaryStyle,
        provider: LLMProvider,
        language: str,
        patient_name: str = 'Unknown'
    ) -> BaseSynthesizer:
        """Create synthesizer for the given style."""
        if style == SummaryStyle.KEY_TOPICS:
            return KeyTopicsSynthesizer(
                llm_provider=provider,
                prompt_loader=self.prompt_loader,
                language=language,
                patient_name=patient_name
            )
        elif style == SummaryStyle.DETAILED_NOTES:
            return DetailedNotesSynthesizer(
                llm_provider=provider,
                prompt_loader=self.prompt_loader,
                language=language,
                patient_name=patient_name
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
