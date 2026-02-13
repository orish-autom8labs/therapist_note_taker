"""
Adjacency-based speaker merger for diarization cleanup.

Merges "ghost" speakers (3→2) before LLM processing. Soniox often
misidentifies a third speaker in 2-person therapy sessions, especially
during opening small talk when tone/volume differs from clinical portions.

Core insight: in a 2-person conversation the same person never talks to
themselves. If Speaker C is actually Speaker B, then C never appears
adjacent to B — but C does appear adjacent to A.

Algorithm:
1. Count unique speakers; skip if ≤ 2
2. Rank by token count; top 2 are "major", rest are "minor" (ghosts)
3. For each minor speaker, count turn-adjacencies with each major
4. Merge minor into the major it is LEAST adjacent to (= most likely same person)
"""

import logging
from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


@dataclass
class MergeResult:
    """Result of a speaker merge operation."""
    buffer: List[Dict[str, Any]]
    merge_map: Dict[str, str]  # e.g. {"Speaker C": "Speaker B"}
    was_merged: bool


class SpeakerMerger:
    """Merges ghost speakers in transcript buffers using turn-adjacency analysis."""

    def merge(self, transcript_buffer: List[Dict[str, Any]]) -> MergeResult:
        """
        Merge ghost speakers into major speakers.

        Args:
            transcript_buffer: List of token dicts with 'text', 'speaker', 'timestamp'.

        Returns:
            MergeResult with (possibly modified) buffer, merge map, and merge flag.
        """
        if not transcript_buffer:
            return MergeResult(buffer=transcript_buffer, merge_map={}, was_merged=False)

        speaker_tokens = self._count_speaker_tokens(transcript_buffer)
        unique_speakers = list(speaker_tokens.keys())

        if len(unique_speakers) <= 2:
            logger.info("[SPEAKER-MERGE] %d speakers found, no merge needed", len(unique_speakers))
            return MergeResult(buffer=transcript_buffer, merge_map={}, was_merged=False)

        logger.info(
            "[SPEAKER-MERGE] %d speakers found: %s",
            len(unique_speakers),
            {s: speaker_tokens[s] for s in unique_speakers},
        )

        # Rank by token count; top 2 are major
        ranked = sorted(unique_speakers, key=lambda s: speaker_tokens[s], reverse=True)
        major_speakers = ranked[:2]
        minor_speakers = ranked[2:]

        logger.info(
            "[SPEAKER-MERGE] Major: %s, Minor (ghosts): %s",
            major_speakers, minor_speakers,
        )

        # Compute turn adjacency
        turns = self._extract_turns(transcript_buffer)
        adjacency = self._compute_adjacencies(turns, major_speakers, minor_speakers)

        # Build merge map: iteratively merge smallest ghost first
        merge_map: Dict[str, str] = {}
        for minor in minor_speakers:
            target = self._find_merge_target(minor, major_speakers, adjacency, turns)
            merge_map[minor] = target
            logger.info("[SPEAKER-MERGE] Merging '%s' → '%s'", minor, target)

        # Apply merges
        merged_buffer = self._apply_merge(transcript_buffer, merge_map)

        return MergeResult(buffer=merged_buffer, merge_map=merge_map, was_merged=True)

    def _count_speaker_tokens(
        self, transcript_buffer: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """Count total token characters per speaker (proxy for speech volume)."""
        counts: Counter[str] = Counter()
        for token in transcript_buffer:
            speaker = token.get('speaker', 'Unknown')
            text = token.get('text', '')
            counts[speaker] += len(text)
        return dict(counts)

    def _extract_turns(
        self, transcript_buffer: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Extract the sequence of speaker turns (consecutive same-speaker
        tokens collapsed into one turn).
        """
        turns: List[str] = []
        prev_speaker: str | None = None
        for token in transcript_buffer:
            speaker = token.get('speaker', 'Unknown')
            if speaker != prev_speaker:
                turns.append(speaker)
                prev_speaker = speaker
        return turns

    def _compute_adjacencies(
        self,
        turns: List[str],
        major_speakers: List[str],
        minor_speakers: List[str],
    ) -> Dict[str, Dict[str, int]]:
        """
        Build adjacency matrix: for each minor speaker, count how many times
        it appears directly before or after each major speaker.
        """
        adj: Dict[str, Dict[str, int]] = {
            minor: {major: 0 for major in major_speakers}
            for minor in minor_speakers
        }

        for i, speaker in enumerate(turns):
            if speaker not in adj:
                continue
            # Check previous turn
            if i > 0 and turns[i - 1] in adj[speaker]:
                adj[speaker][turns[i - 1]] += 1
            # Check next turn
            if i < len(turns) - 1 and turns[i + 1] in adj[speaker]:
                adj[speaker][turns[i + 1]] += 1

        return adj

    def _find_merge_target(
        self,
        minor: str,
        major_speakers: List[str],
        adjacency: Dict[str, Dict[str, int]],
        turns: List[str],
    ) -> str:
        """
        Decide which major speaker the minor should be merged into.

        Primary: least adjacent major (= most likely same person).
        Tiebreaker: merge into the major with the closest average turn length.
        """
        adj_counts = adjacency[minor]

        # Find the minimum adjacency count
        min_adj = min(adj_counts.values())
        candidates = [m for m, count in adj_counts.items() if count == min_adj]

        if len(candidates) == 1:
            return candidates[0]

        # Tiebreaker: compare average turn length (characters per turn)
        turn_lengths = self._compute_turn_lengths(turns, minor, candidates)
        minor_avg = turn_lengths.get(minor, 0)

        best = candidates[0]
        best_diff = float('inf')
        for candidate in candidates:
            diff = abs(turn_lengths.get(candidate, 0) - minor_avg)
            if diff < best_diff:
                best_diff = diff
                best = candidate

        return best

    def _compute_turn_lengths(
        self,
        turns: List[str],
        minor: str,
        candidates: List[str],
    ) -> Dict[str, float]:
        """Compute average turn length (number of consecutive tokens) per speaker."""
        # Count consecutive runs
        run_counts: Counter[str] = Counter()
        run_totals: Counter[str] = Counter()
        relevant = {minor} | set(candidates)

        current_speaker: str | None = None
        current_run = 0
        for speaker in turns:
            if speaker == current_speaker:
                current_run += 1
            else:
                if current_speaker in relevant:
                    run_counts[current_speaker] += 1
                    run_totals[current_speaker] += current_run
                current_speaker = speaker
                current_run = 1
        # Final run
        if current_speaker in relevant:
            run_counts[current_speaker] += 1
            run_totals[current_speaker] += current_run

        return {
            s: (run_totals[s] / run_counts[s] if run_counts[s] > 0 else 0)
            for s in relevant
        }

    def _apply_merge(
        self,
        transcript_buffer: List[Dict[str, Any]],
        merge_map: Dict[str, str],
    ) -> List[Dict[str, Any]]:
        """
        Return a new buffer with speaker IDs remapped according to merge_map.
        Does NOT mutate the original buffer.
        """
        merged: List[Dict[str, Any]] = []
        for token in transcript_buffer:
            speaker = token.get('speaker', 'Unknown')
            new_speaker = merge_map.get(speaker, speaker)
            merged.append({**token, 'speaker': new_speaker})
        return merged
