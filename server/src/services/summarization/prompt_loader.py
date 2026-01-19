"""Prompt template loader for summarization."""

import os
from pathlib import Path
from functools import lru_cache
from typing import Optional


class PromptLoader:
    """
    Loads prompt templates from markdown files.

    Enables single-location changes for prompt engineering.
    Templates are cached for performance.

    Directory structure:
        prompts/summarization/
            chunk_summary_en.md
            chunk_summary_he.md
            key_topics_en.md
            key_topics_he.md
            detailed_notes_en.md
            detailed_notes_he.md
    """

    def __init__(self, prompts_dir: Optional[str] = None):
        """
        Initialize prompt loader.

        Args:
            prompts_dir: Optional custom prompts directory.
                        Defaults to server/src/prompts/summarization/
        """
        if prompts_dir is None:
            # Default: relative to this file's location
            self.prompts_dir = (
                Path(__file__).parent.parent.parent / 'prompts' / 'summarization'
            )
        else:
            self.prompts_dir = Path(prompts_dir)

    @lru_cache(maxsize=32)
    def load(self, prompt_name: str, language: str = 'en') -> str:
        """
        Load a prompt template.

        Args:
            prompt_name: Name of the prompt (e.g., 'chunk_summary', 'key_topics')
            language: Language code ('en' or 'he')

        Returns:
            Prompt template string with {placeholders}

        Raises:
            FileNotFoundError: If prompt template doesn't exist
        """
        filename = f"{prompt_name}_{language}.md"
        filepath = self.prompts_dir / filename

        if not filepath.exists():
            # Fall back to English if language-specific doesn't exist
            fallback_path = self.prompts_dir / f"{prompt_name}_en.md"
            if fallback_path.exists():
                filepath = fallback_path
            else:
                raise FileNotFoundError(
                    f"Prompt template not found: {filename} "
                    f"(looked in {self.prompts_dir})"
                )

        return filepath.read_text(encoding='utf-8')

    def reload(self):
        """Clear cache to reload prompts (useful in development)."""
        self.load.cache_clear()

    def get_available_prompts(self) -> list:
        """Get list of available prompt templates."""
        if not self.prompts_dir.exists():
            return []

        prompts = []
        for file in self.prompts_dir.glob('*.md'):
            prompts.append(file.stem)
        return sorted(prompts)
