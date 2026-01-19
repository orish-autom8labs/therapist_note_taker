"""Speaker-based chunking strategy - breaks at speaker changes within time bounds."""

from typing import List, Dict, Any, Set
from .base_chunker import BaseChunker, TranscriptSegment


class SpeakerSegmentChunker(BaseChunker):
    """
    Chunks transcript by speaker changes within time boundaries.

    Strategy:
    1. Accumulate tokens until reaching min_duration
    2. After min_duration, look for natural break points (speaker changes)
    3. Force break at max_duration regardless of speaker

    This preserves conversational context while limiting chunk sizes.
    Best for: Therapy sessions, interviews, meetings with natural turn-taking.
    """

    def chunk(
        self,
        transcript_buffer: List[Dict[str, Any]],
        session_start_ms: int
    ) -> List[TranscriptSegment]:
        """Segment transcript by speaker changes within time bounds."""
        if not transcript_buffer:
            return []

        segments: List[TranscriptSegment] = []
        current_tokens: List[Dict[str, Any]] = []
        current_start_ms: int = None
        current_speakers: Set[str] = set()

        for token in transcript_buffer:
            token_time = token.get('timestamp', 0)
            speaker = token.get('speaker', 'Unknown')

            # Initialize start time for first token
            if current_start_ms is None:
                current_start_ms = token_time

            current_duration = token_time - current_start_ms

            # Check if we should start a new segment
            should_break = False

            if current_duration >= self.max_duration_ms:
                # Force break at max duration
                should_break = True
            elif current_duration >= self.min_duration_ms and current_tokens:
                # Check for speaker change as natural break point
                last_speaker = current_tokens[-1].get('speaker', 'Unknown')
                if speaker != last_speaker:
                    should_break = True

            if should_break and current_tokens:
                # Create segment from accumulated tokens
                segment = self._create_segment(
                    current_tokens,
                    current_start_ms,
                    current_speakers,
                    session_start_ms
                )
                segments.append(segment)

                # Reset for next segment
                current_tokens = []
                current_start_ms = token_time
                current_speakers = set()

            # Add token to current segment
            current_tokens.append(token)
            if speaker != 'Unknown':
                current_speakers.add(speaker)

        # Don't forget the last segment
        if current_tokens:
            segment = self._create_segment(
                current_tokens,
                current_start_ms,
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

        # Get end time from last token
        end_ms = int(tokens[-1].get('timestamp', start_ms)) if tokens else start_ms

        # Format text with timestamps and speaker labels
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
