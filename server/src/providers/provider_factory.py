"""
Factory for creating transcription provider instances.
Add new providers here to make them available.
"""
import os
from typing import Dict, Any
from .transcription_provider import TranscriptionProvider
from .soniox_provider import SonioxProvider
from .google_provider import GoogleProvider
from .mock_provider import MockProvider


class ProviderFactory:
    """Factory for creating transcription provider instances."""
    
    @staticmethod
    def create_provider(provider_name: str, config: Dict[str, Any] = None) -> TranscriptionProvider:
        """
        Create a transcription provider instance.
        
        Args:
            provider_name: Name of the provider ('soniox', 'google', etc.)
            config: Provider-specific configuration dictionary
        
        Returns:
            Provider instance
        
        Raises:
            ValueError: If provider name is unknown
        """
        if config is None:
            config = {}
        
        normalized_name = provider_name.lower()
        
        if normalized_name == 'soniox':
            return SonioxProvider({
                'api_key': config.get('api_key') or os.getenv('SONIOX_API_KEY'),
            })
        
        elif normalized_name in ['google', 'google-cloud', 'google-speech']:
            return GoogleProvider({
                'project_id': config.get('project_id') or os.getenv('GOOGLE_PROJECT_ID'),
                'credentials': config.get('credentials') or os.getenv('GOOGLE_CREDENTIALS'),
            })
        
        elif normalized_name == 'mock':
            return MockProvider(config)
        
        else:
            available = ', '.join(ProviderFactory.get_available_providers())
            raise ValueError(
                f"Unknown transcription provider: {provider_name}. "
                f"Available providers: {available}"
            )
    
    @staticmethod
    def get_available_providers() -> list:
        """
        Get list of available providers.
        
        Returns:
            List of provider names
        """
        return ['soniox', 'google', 'mock']
    
    @staticmethod
    def get_provider_info(provider_name: str) -> Dict[str, Any]:
        """
        Get provider information.
        
        Args:
            provider_name: Name of the provider
        
        Returns:
            Dictionary with provider information, or None if not found
        """
        normalized_name = provider_name.lower()
        
        providers = {
            'soniox': {
                'name': 'Soniox',
                'supports_hebrew': True,
                'supports_speaker_diarization': True,
                'supports_streaming': True,
                'description': 'High accuracy Hebrew transcription with speaker diarization',
            },
            'google': {
                'name': 'Google Cloud Speech-to-Text',
                'supports_hebrew': True,
                'supports_speaker_diarization': True,
                'supports_streaming': True,
                'description': 'Google Cloud Speech-to-Text with Hebrew support',
            },
        }
        
        return providers.get(normalized_name)

