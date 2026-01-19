"""Abstract base class for transcript chunking strategies."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Any, Set


@dataclass
class TranscriptSegment:
    """A segment of transcript for summarization."""
    text: str                    # Formatted text with speaker labels
    start_time_ms: int           # Start time in milliseconds
    end_time_ms: int             # End time in milliseconds
    start_timestamp: str         # "MM:SS" format
    end_timestamp: str           # "MM:SS" format
    speakers: Set[str]           # Set of speaker identifiers in segment
    token_count: int             # Approximate token count

    @property
    def duration_minutes(self) -> float:
        """Duration of segment in minutes."""
        return (self.end_time_ms - self.start_time_ms) / 60_000


class BaseChunker(ABC):
    """
    Abstract base class for transcript chunking strategies.

    Chunkers segment transcripts into manageable pieces for Stage 1 summarization.
    Different strategies optimize for different aspects:
    - SpeakerSegmentChunker: Preserves conversational flow
    - FixedTimeChunker: Consistent chunk sizes
    - ProgressiveChunker: Maximum compression (future)
    """

    def __init__(
        self,
        min_duration_minutes: int = 3,
        max_duration_minutes: int = 8
    ):
        """
        Initialize chunker with duration bounds.

        Args:
            min_duration_minutes: Minimum chunk duration
            max_duration_minutes: Maximum chunk duration
        """
        self.min_duration_ms = min_duration_minutes * 60 * 1000
        self.max_duration_ms = max_duration_minutes * 60 * 1000

    @abstractmethod
    def chunk(
        self,
        transcript_buffer: List[Dict[str, Any]],
        session_start_ms: int
    ) -> List[TranscriptSegment]:
        """
        Segment transcript into chunks.

        Args:
            transcript_buffer: List of transcript tokens with text, speaker, timestamp
            session_start_ms: Session start time in milliseconds (for relative timestamps)

        Returns:
            List of TranscriptSegment objects
        """
        pass

    @staticmethod
    def ms_to_timestamp(ms) -> str:
        """Convert milliseconds to MM:SS format."""
        # Ensure integer (timestamps might be floats)
        ms = int(ms) if ms and ms >= 0 else 0
        total_seconds = ms // 1000
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes:02d}:{seconds:02d}"

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """
        Estimate token count for text.

        Rough approximation: ~4 characters per token for English,
        ~2 characters per token for Hebrew/other scripts.
        """
        if not text:
            return 0

        # Check if text contains Hebrew characters
        hebrew_chars = sum(1 for c in text if '\u0590' <= c <= '\u05FF')
        total_chars = len(text)

        if hebrew_chars > total_chars * 0.3:
            # Hebrew-heavy text: ~2 chars per token
            return total_chars // 2
        else:
            # English/mixed: ~4 chars per token
            return total_chars // 4

    def _format_segment_text(
        self,
        tokens: List[Dict[str, Any]],
        session_start_ms: int,
        include_timestamps: bool = True
    ) -> str:
        """
        Format tokens into readable text with speaker labels and timestamps.

        Output format:
        MM:SS
        Speaker A
        Text text text...

        MM:SS
        Speaker B
        Different text...
        """
        if not tokens:
            return ""

        lines = []
        current_speaker = None
        speaker_map = {}
        next_letter = ord('A')

        for token in tokens:
            speaker_id = token.get('speaker', 'Unknown')
            text = token.get('text', '')
            timestamp_ms = token.get('timestamp', 0)

            # Skip empty text
            if not text.strip():
                continue

            # Map speaker IDs to letters
            if speaker_id not in speaker_map and speaker_id != 'Unknown':
                speaker_map[speaker_id] = chr(next_letter)
                next_letter += 1

            speaker_label = speaker_map.get(speaker_id, speaker_id)

            # New speaker block
            if speaker_label != current_speaker:
                if lines:
                    lines.append("")  # Blank line between speakers

                if include_timestamps:
                    relative_ms = int(timestamp_ms or 0) - int(session_start_ms or 0)
                    timestamp = self.ms_to_timestamp(max(0, relative_ms))
                    lines.append(timestamp)

                lines.append(f"Speaker {speaker_label}")
                current_speaker = speaker_label

            lines.append(text)

        return '\n'.join(lines)
