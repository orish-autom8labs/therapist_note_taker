"""Fixed time interval chunking strategy - consistent chunk sizes."""

from typing import List, Dict, Any, Set
from .base_chunker import BaseChunker, TranscriptSegment


class FixedTimeChunker(BaseChunker):
    """
    Chunks transcript by fixed time intervals.

    Strategy:
    1. Split transcript every N minutes (configurable via max_duration)
    2. No consideration of speaker changes
    3. Consistent, predictable chunk sizes

    Best for: Long monologues, lectures, or when consistent chunk sizes
    are more important than conversational context.

    Note: This may cut through mid-sentence. For better results with
    multi-speaker content, use SpeakerSegmentChunker instead.
    """

    def __init__(
        self,
        chunk_duration_minutes: int = 5,
        **kwargs
    ):
        """
        Initialize with fixed chunk duration.

        Args:
            chunk_duration_minutes: Duration for each chunk
        """
        # For fixed time, min and max are the same
        super().__init__(
            min_duration_minutes=chunk_duration_minutes,
            max_duration_minutes=chunk_duration_minutes
        )
        self.chunk_duration_ms = chunk_duration_minutes * 60 * 1000

    def chunk(
        self,
        transcript_buffer: List[Dict[str, Any]],
        session_start_ms: int
    ) -> List[TranscriptSegment]:
        """Segment transcript by fixed time intervals."""
        if not transcript_buffer:
            return []

        segments: List[TranscriptSegment] = []
        current_tokens: List[Dict[str, Any]] = []
        chunk_start_ms: int = session_start_ms
        current_speakers: Set[str] = set()

        for token in transcript_buffer:
            token_time = token.get('timestamp', 0)
            speaker = token.get('speaker', 'Unknown')

            # Check if we've exceeded the chunk duration
            if token_time - chunk_start_ms >= self.chunk_duration_ms and current_tokens:
                # Create segment
                segment = self._create_segment(
                    current_tokens,
                    chunk_start_ms,
                    current_speakers,
                    session_start_ms
                )
                segments.append(segment)

                # Reset for next chunk
                current_tokens = []
                chunk_start_ms = token_time
                current_speakers = set()

            # Add token to current chunk
            current_tokens.append(token)
            if speaker != 'Unknown':
                current_speakers.add(speaker)

        # Don't forget the last segment
        if current_tokens:
            segment = self._create_segment(
                current_tokens,
                chunk_start_ms,
                current_speakers,
                session_start_ms
            )
            segments.append(segment)

        return segments

    def _create_segment(
        self,
        tokens: List[Dict[str, Any]],
        start_ms,
        speakers: Set[str],
        session_start_ms
    ) -> TranscriptSegment:
        """Create a TranscriptSegment from accumulated tokens."""
        # Ensure integers (timestamps might be floats)
        start_ms = int(start_ms or 0)
        session_start_ms = int(session_start_ms or 0)
        end_ms = int(tokens[-1].get('timestamp', start_ms)) if tokens else start_ms

        text = self._format_segment_text(tokens, session_start_ms)

        return TranscriptSegment(
            text=text,
            start_time_ms=start_ms,
            end_time_ms=end_ms,
            start_timestamp=self.ms_to_timestamp(max(0, start_ms - session_start_ms)),
            end_timestamp=self.ms_to_timestamp(max(0, end_ms - session_start_ms)),
            speakers=speakers,
            token_count=self.estimate_tokens(text)
        )
