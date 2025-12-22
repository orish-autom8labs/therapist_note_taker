"""
Abstract base class for transcription providers.
All transcription providers must implement this interface.
"""
from abc import ABC, abstractmethod
from typing import Callable, Optional, List, Dict, Any


class TranscriptionProvider(ABC):
    """
    Abstract base class for transcription providers.
    All providers must inherit from this and implement the required methods.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the provider with configuration.
        
        Args:
            config: Provider-specific configuration dictionary
        """
        self.config = config
        if self.__class__ == TranscriptionProvider:
            raise TypeError("TranscriptionProvider is abstract and cannot be instantiated directly")
    
    @abstractmethod
    async def start_streaming_session(
        self,
        options: Dict[str, Any],
        on_transcript: Callable[[Dict[str, Any]], None],
        on_error: Callable[[Exception], None]
    ) -> Dict[str, Any]:
        """
        Start a real-time transcription session.
        
        Args:
            options: Session options (language, enable_speaker_diarization, etc.)
            on_transcript: Callback function called with transcript chunks
                Receives: {text: str, speaker: Optional[str], is_final: bool, timestamp: int}
            on_error: Error callback function
        
        Returns:
            Session object with methods:
            - send_audio(audio_chunk: bytes) -> None
            - stop() -> Coroutine[None, None, None]
            - is_active() -> bool
        """
        pass
    
    @abstractmethod
    async def process_batch(
        self,
        audio_buffer: bytes,
        options: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Process a batch audio file (for fallback/recovery).
        
        Args:
            audio_buffer: Audio file buffer
            options: Processing options (language, enable_speaker_diarization, etc.)
        
        Returns:
            List of transcript segments:
            [{text: str, speaker: Optional[str], start_time: Optional[float], end_time: Optional[float]}]
        """
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """
        Get provider name.
        
        Returns:
            Provider name string
        """
        pass
    
    @abstractmethod
    def supports_language(self, language_code: str) -> bool:
        """
        Check if provider supports a specific language.
        
        Args:
            language_code: Language code (e.g., 'he-IL' for Hebrew)
        
        Returns:
            True if language is supported
        """
        pass
    
    @abstractmethod
    def supports_speaker_diarization(self) -> bool:
        """
        Check if provider supports speaker diarization.
        
        Returns:
            True if speaker diarization is supported
        """
        pass




