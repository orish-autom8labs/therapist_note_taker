"""
Google Cloud Speech-to-Text provider implementation.
Alternative provider for Hebrew transcription.
"""
import os
import json
from typing import Dict, Any, Callable, List, Optional
from google.cloud import speech_v1
from google.oauth2 import service_account
from .transcription_provider import TranscriptionProvider


class GoogleProvider(TranscriptionProvider):
    """Google Cloud Speech-to-Text provider."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.project_id = config.get('project_id') or os.getenv('GOOGLE_PROJECT_ID')
        credentials_data = config.get('credentials')
        
        if credentials_data:
            if isinstance(credentials_data, str):
                credentials_data = json.loads(credentials_data)
            self.credentials = service_account.Credentials.from_service_account_info(
                credentials_data
            )
        else:
            # Try to load from environment or default credentials
            self.credentials = None
        
        self.client = None
    
    def get_name(self) -> str:
        return 'Google Cloud Speech-to-Text'
    
    def supports_language(self, language_code: str) -> bool:
        """Google supports Hebrew (he-IL)."""
        return language_code in ['he', 'he-IL', 'en', 'en-US']
    
    def supports_speaker_diarization(self) -> bool:
        return True
    
    async def initialize(self):
        """Initialize Google Speech client."""
        if not self.client:
            if self.credentials:
                self.client = speech_v1.SpeechClient(credentials=self.credentials)
            else:
                # Use default credentials (for local dev with gcloud auth)
                self.client = speech_v1.SpeechClient()
        return self.client
    
    async def start_streaming_session(
        self,
        options: Dict[str, Any],
        on_transcript: Callable[[Dict[str, Any]], None],
        on_error: Callable[[Exception], None]
    ) -> Dict[str, Any]:
        """Start streaming transcription session."""
        await self.initialize()
        
        language = options.get('language', 'he-IL')
        enable_speaker_diarization = options.get('enable_speaker_diarization', True)
        
        config = speech_v1.RecognitionConfig(
            encoding=speech_v1.RecognitionConfig.AudioEncoding.WEBM_OPUS,
            sample_rate_hertz=16000,
            language_code=language,
            enable_speaker_diarization=enable_speaker_diarization,
            diarization_speaker_count=2,
            model='latest_long',  # Better for longer sessions
        )
        
        streaming_config = speech_v1.StreamingRecognitionConfig(
            config=config,
            interim_results=True,  # Get partial results
        )
        
        is_active = True
        stream = None
        
        try:
            # Create streaming recognize request
            requests = []
            
            async def send_audio(audio_chunk: bytes):
                """Send audio chunk to Google."""
                nonlocal stream
                if not is_active:
                    return
                
                if stream is None:
                    # Initialize stream
                    stream = await self.client.streaming_recognize()
                    # Start background task to receive responses
                    import asyncio
                    asyncio.create_task(self._process_stream_responses(
                        stream, on_transcript, on_error
                    ))
                
                request = speech_v1.StreamingRecognizeRequest(audio_content=audio_chunk)
                await stream.write(request)
            
            async def stop():
                """Stop the streaming session."""
                nonlocal is_active, stream
                is_active = False
                if stream:
                    await stream.done_writing()
                    stream = None
            
            def is_active_check() -> bool:
                return is_active
            
            return {
                'send_audio': send_audio,
                'stop': stop,
                'is_active': is_active_check
            }
        except Exception as e:
            on_error(e)
            raise
    
    async def _process_stream_responses(
        self,
        stream,
        on_transcript: Callable[[Dict[str, Any]], None],
        on_error: Callable[[Exception], None]
    ):
        """Process streaming responses from Google."""
        try:
            async for response in stream:
                if response.results:
                    for result in response.results:
                        if result.alternatives:
                            alternative = result.alternatives[0]
                            transcript_chunk = self._parse_google_response(result)
                            if transcript_chunk and transcript_chunk.get('text'):
                                on_transcript({
                                    'text': transcript_chunk['text'],
                                    'speaker': transcript_chunk.get('speaker'),
                                    'is_final': transcript_chunk.get('is_final', False),
                                    'timestamp': int(__import__('time').time() * 1000),
                                })
        except Exception as e:
            on_error(e)
    
    async def process_batch(
        self,
        audio_buffer: bytes,
        options: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Process batch audio file."""
        await self.initialize()
        
        language = options.get('language', 'he-IL')
        enable_speaker_diarization = options.get('enable_speaker_diarization', True)
        
        config = speech_v1.RecognitionConfig(
            encoding=speech_v1.RecognitionConfig.AudioEncoding.WEBM_OPUS,
            sample_rate_hertz=16000,
            language_code=language,
            enable_speaker_diarization=enable_speaker_diarization,
            diarization_speaker_count=2,
        )
        
        audio = speech_v1.RecognitionAudio(content=audio_buffer)
        
        request = speech_v1.RecognizeRequest(config=config, audio=audio)
        
        try:
            response = await self.client.recognize(request=request)
            return self._parse_google_batch_response(response)
        except Exception as e:
            raise Exception(f"Google batch processing failed: {str(e)}")
    
    def _parse_google_response(self, result) -> Optional[Dict[str, Any]]:
        """Parse Google streaming response."""
        if result.results and len(result.results) > 0:
            alternative = result.results[0].alternatives[0] if result.results[0].alternatives else None
            if alternative:
                speaker = None
                if alternative.words and len(alternative.words) > 0:
                    speaker_tag = alternative.words[0].speaker_tag
                    if speaker_tag:
                        speaker = f'Speaker {speaker_tag}'
                
                return {
                    'text': alternative.transcript,
                    'speaker': speaker,
                    'is_final': result.is_final_alternative,
                }
        return None
    
    def _parse_google_batch_response(self, response) -> List[Dict[str, Any]]:
        """Parse Google batch response."""
        segments = []
        
        if response.results:
            for result in response.results:
                if result.alternatives:
                    alternative = result.alternatives[0]
                    if alternative.words:
                        current_segment = {
                            'text': '',
                            'speaker': None,
                            'start_time': None,
                            'end_time': None,
                        }
                        
                        for word in alternative.words:
                            speaker_tag = word.speaker_tag
                            
                            if current_segment['speaker'] != speaker_tag:
                                if current_segment['text']:
                                    segments.append({
                                        **current_segment,
                                        'speaker': f"Speaker {current_segment['speaker']}" if current_segment['speaker'] else None,
                                    })
                                current_segment = {
                                    'text': word.word,
                                    'speaker': speaker_tag,
                                    'start_time': word.start_time.total_seconds() if word.start_time else None,
                                    'end_time': word.end_time.total_seconds() if word.end_time else None,
                                }
                            else:
                                current_segment['text'] += ' ' + word.word
                                if word.end_time:
                                    current_segment['end_time'] = word.end_time.total_seconds()
                        
                        if current_segment['text']:
                            segments.append({
                                **current_segment,
                                'speaker': f"Speaker {current_segment['speaker']}" if current_segment['speaker'] else None,
                            })
        
        return segments




