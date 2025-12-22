"""
Transcription service that uses the configured provider.
This is the main interface for transcription operations.
"""
from typing import Dict, Any, Callable
from ..providers.provider_factory import ProviderFactory
from ..config import config


class TranscriptionService:
    """Transcription service that uses the configured provider."""
    
    def __init__(self):
        """Initialize with provider from config."""
        provider_name = config.transcription.provider
        provider_config = config.transcription.providers.get(provider_name, {})
        
        # Create provider instance
        self.provider = ProviderFactory.create_provider(provider_name, provider_config)
    
    def get_provider(self):
        """Get the current provider instance."""
        return self.provider
    
    async def start_session(
        self,
        options: Dict[str, Any] = None,
        on_transcript: Callable[[Dict[str, Any]], None] = None,
        on_error: Callable[[Exception], None] = None
    ) -> Dict[str, Any]:
        """
        Start a streaming transcription session.
        
        Args:
            options: Session options (language, enable_speaker_diarization, etc.)
            on_transcript: Callback for transcript chunks
            on_error: Error callback
        
        Returns:
            Session control object
        """
        if options is None:
            options = {}
        
        session_options = {
            'language': options.get('language') or config.transcription.defaults.language,
            'enable_speaker_diarization': options.get(
                'enable_speaker_diarization',
                config.transcription.defaults.enable_speaker_diarization
            ),
            **options,
        }
        
        return await self.provider.start_streaming_session(
            session_options,
            on_transcript,
            on_error
        )
    
    async def process_batch(
        self,
        audio_buffer: bytes,
        options: Dict[str, Any] = None
    ) -> list:
        """
        Process a batch audio file.
        
        Args:
            audio_buffer: Audio file buffer
            options: Processing options
        
        Returns:
            Array of transcript segments
        """
        if options is None:
            options = {}
        
        process_options = {
            'language': options.get('language') or config.transcription.defaults.language,
            'enable_speaker_diarization': options.get(
                'enable_speaker_diarization',
                config.transcription.defaults.enable_speaker_diarization
            ),
            **options,
        }
        
        return await self.provider.process_batch(audio_buffer, process_options)
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get provider information."""
        return {
            'name': self.provider.get_name(),
            'supports_hebrew': self.provider.supports_language('he-IL'),
            'supports_speaker_diarization': self.provider.supports_speaker_diarization(),
        }
    
    def switch_provider(self, provider_name: str, provider_config: Dict[str, Any] = None):
        """
        Switch to a different provider (for testing).
        
        Args:
            provider_name: Name of the provider
            provider_config: Provider configuration
        """
        if provider_config is None:
            provider_config = {}
        
        full_config = {
            **config.transcription.providers.get(provider_name, {}),
            **provider_config,
        }
        self.provider = ProviderFactory.create_provider(provider_name, full_config)




