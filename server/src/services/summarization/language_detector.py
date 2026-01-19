"""Language detection for transcripts."""

from typing import List, Dict, Any


class LanguageDetector:
    """
    Detects language from transcript content.

    Supports:
    - Hebrew ('he')
    - English ('en')

    Detection is based on Unicode character analysis.
    """

    # Hebrew Unicode range
    HEBREW_START = 0x0590
    HEBREW_END = 0x05FF

    # Threshold for language detection
    HEBREW_THRESHOLD = 0.3  # 30% Hebrew characters = Hebrew text

    def detect(self, transcript_buffer: List[Dict[str, Any]]) -> str:
        """
        Detect primary language of transcript.

        Args:
            transcript_buffer: List of transcript tokens with 'text' field

        Returns:
            Language code: 'he' for Hebrew, 'en' for English
        """
        # Sample text from transcript (first 100 tokens for efficiency)
        text = ' '.join(
            token.get('text', '')
            for token in transcript_buffer[:100]
        )

        return self.detect_from_text(text)

    def detect_from_text(self, text: str) -> str:
        """
        Detect language from raw text.

        Args:
            text: Text string to analyze

        Returns:
            Language code: 'he' for Hebrew, 'en' for English
        """
        if not text:
            return 'en'  # Default to English

        # Count Hebrew and total alphabetic characters
        hebrew_chars = sum(
            1 for c in text
            if self.HEBREW_START <= ord(c) <= self.HEBREW_END
        )
        total_alpha = sum(1 for c in text if c.isalpha())

        if total_alpha == 0:
            return 'en'  # Default to English for non-alphabetic text

        hebrew_ratio = hebrew_chars / total_alpha

        return 'he' if hebrew_ratio > self.HEBREW_THRESHOLD else 'en'

    def get_supported_languages(self) -> List[str]:
        """Get list of supported language codes."""
        return ['en', 'he']
