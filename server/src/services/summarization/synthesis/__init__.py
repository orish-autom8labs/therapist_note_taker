"""Synthesis strategies for Stage 2 summarization."""

from .base_synthesizer import BaseSynthesizer, SynthesisResult, ChunkSummary
from .key_topics import KeyTopicsSynthesizer
from .detailed_notes import DetailedNotesSynthesizer

__all__ = [
    'BaseSynthesizer',
    'SynthesisResult',
    'ChunkSummary',
    'KeyTopicsSynthesizer',
    'DetailedNotesSynthesizer',
]
