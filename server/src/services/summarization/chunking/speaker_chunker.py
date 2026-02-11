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
    4. Include overlap_turns from previous chunk as context prefix

    This preserves conversational context while limiting chunk sizes.
    Best for: Therapy sessions, interviews, meetings with natural turn-taking.
    """

    def __init__(
        self,
        min_duration_minutes: int = 3,
        max_duration_minutes: int = 8,
        overlap_turns: int = 3
    ):
        """
        Initialize chunker with duration bounds and overlap.

        Args:
            min_duration_minutes: Minimum chunk duration
            max_duration_minutes: Maximum chunk duration
            overlap_turns: Number of speaker turns from previous chunk
                to include as context prefix in next chunk (0 = no overlap)
        """
        super().__init__(min_duration_minutes, max_duration_minutes)
        self.overlap_turns = overlap_turns

    def chunk(
        self,
        transcript_buffer: List[Dict[str, Any]],
        session_start_ms: int
    ) -> List[TranscriptSegment]:
        """Segment transcript by speaker changes within time bounds."""
        if not transcript_buffer:
            return []

        # First pass: split into raw chunks (no overlap)
        raw_chunks = self._split_into_chunks(transcript_buffer)

        # Second pass: add overlap context from previous chunk
        segments: List[TranscriptSegment] = []
        for i, chunk_tokens in enumerate(raw_chunks):
            # Get overlap tokens from previous chunk
            overlap_tokens: List[Dict[str, Any]] = []
            if i > 0 and self.overlap_turns > 0:
                overlap_tokens = self._get_last_n_turns(
                    raw_chunks[i - 1], self.overlap_turns
                )

            start_ms = chunk_tokens[0].get('timestamp', 0) if chunk_tokens else 0
            speakers: Set[str] = set()
            for t in chunk_tokens:
                s = t.get('speaker', 'Unknown')
                if s != 'Unknown':
                    speakers.add(s)

            segment = self._create_segment_with_overlap(
                chunk_tokens,
                overlap_tokens,
                start_ms,
                speakers,
                session_start_ms
            )
            segments.append(segment)

        return segments

    def _split_into_chunks(
        self,
        transcript_buffer: List[Dict[str, Any]]
    ) -> List[List[Dict[str, Any]]]:
        """Split transcript into raw token lists (no overlap)."""
        chunks: List[List[Dict[str, Any]]] = []
        current_tokens: List[Dict[str, Any]] = []
        current_start_ms: int | None = None

        for token in transcript_buffer:
            token_time = token.get('timestamp', 0)

            if current_start_ms is None:
                current_start_ms = token_time

            current_duration = token_time - current_start_ms
            should_break = False

            if current_duration >= self.max_duration_ms:
                should_break = True
            elif current_duration >= self.min_duration_ms and current_tokens:
                last_speaker = current_tokens[-1].get('speaker', 'Unknown')
                speaker = token.get('speaker', 'Unknown')
                if speaker != last_speaker:
                    should_break = True

            if should_break and current_tokens:
                chunks.append(current_tokens)
                current_tokens = []
                current_start_ms = token_time

            current_tokens.append(token)

        if current_tokens:
            chunks.append(current_tokens)

        return chunks

    def _get_last_n_turns(
        self,
        tokens: List[Dict[str, Any]],
        n_turns: int
    ) -> List[Dict[str, Any]]:
        """Get the last N speaker turns from a token list."""
        if not tokens or n_turns <= 0:
            return []

        # Walk backwards through tokens, counting speaker changes
        turns_found = 0
        current_speaker = None
        start_idx = len(tokens)

        for i in range(len(tokens) - 1, -1, -1):
            speaker = tokens[i].get('speaker', 'Unknown')
            if speaker != current_speaker:
                if current_speaker is not None:
                    turns_found += 1
                if turns_found >= n_turns:
                    start_idx = i + 1
                    break
                current_speaker = speaker
            start_idx = i

        return tokens[start_idx:]

    def _create_segment_with_overlap(
        self,
        tokens: List[Dict[str, Any]],
        overlap_tokens: List[Dict[str, Any]],
        start_ms: int,
        speakers: Set[str],
        session_start_ms: int
    ) -> TranscriptSegment:
        """Create a TranscriptSegment with optional overlap context prefix."""
        start_ms = int(start_ms or 0)
        session_start_ms = int(session_start_ms or 0)
        end_ms = int(tokens[-1].get('timestamp', start_ms)) if tokens else start_ms

        # Format main text
        main_text = self._format_segment_text(tokens, session_start_ms)

        # Add overlap context prefix if available
        if overlap_tokens:
            overlap_text = self._format_segment_text(overlap_tokens, session_start_ms)
            text = f"[הקשר מהקטע הקודם]\n{overlap_text}\n\n[תחילת הקטע הנוכחי]\n{main_text}"
        else:
            text = main_text

        return TranscriptSegment(
            text=text,
            start_time_ms=start_ms,
            end_time_ms=end_ms,
            start_timestamp=self.ms_to_timestamp(max(0, start_ms - session_start_ms)),
            end_timestamp=self.ms_to_timestamp(max(0, end_ms - session_start_ms)),
            speakers=speakers,
            token_count=self.estimate_tokens(text)
        )

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
