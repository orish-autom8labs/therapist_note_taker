"""Synthesis strategies for Stage 2 summarization and Stage 3 verification."""

from .base_synthesizer import BaseSynthesizer, SynthesisResult, ChunkSummary
from .key_topics import KeyTopicsSynthesizer
from .detailed_notes import DetailedNotesSynthesizer
from .verification import FaithfulnessVerifier

__all__ = [
    'BaseSynthesizer',
    'SynthesisResult',
    'ChunkSummary',
    'KeyTopicsSynthesizer',
    'DetailedNotesSynthesizer',
    'FaithfulnessVerifier',
]
