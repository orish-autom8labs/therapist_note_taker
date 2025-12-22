"""
Mock transcription provider for testing.
Generates fake transcripts to test the UI flow.
"""
import asyncio
import random
from typing import Dict, Any, Callable, List
from .transcription_provider import TranscriptionProvider


class MockProvider(TranscriptionProvider):
    """Mock provider that simulates transcription for testing."""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config or {})
        self.is_streaming = False
        self.transcription_task = None
    
    def get_name(self) -> str:
        return 'Mock Provider (Testing)'
    
    def supports_language(self, language_code: str) -> bool:
        return True  # Supports all languages for testing
    
    def supports_speaker_diarization(self) -> bool:
        return True
    
    async def start_streaming_session(
        self,
        options: Dict[str, Any],
        on_transcript: Callable[[Dict[str, Any]], None],
        on_error: Callable[[Exception], None]
    ) -> Dict[str, Any]:
        """Start mock streaming session."""
        print('[MOCK] start_streaming_session called')
        language = options.get('language', 'he-IL')
        enable_speaker_diarization = options.get('enable_speaker_diarization', True)
        
        self.is_streaming = True
        print(f'[MOCK] Streaming set to True, language: {language}, diarization: {enable_speaker_diarization}')
        
        # Sample Hebrew phrases for testing
        sample_phrases = [
            "שלום, איך אתה מרגיש היום?",
            "אני מרגיש טוב, תודה.",
            "מה הביא אותך לכאן היום?",
            "רציתי לדבר על החרדה שלי.",
            "בוא נדבר על זה. מתי אתה מרגיש חרדה?",
            "בעיקר כשאני צריך לדבר בפני אנשים.",
            "איך זה משפיע עליך?",
            "אני מתחיל להזיע ויש לי קושי לנשום.",
        ]
        
        current_speaker = 1
        phrase_index = 0
        
        async def simulate_transcription():
            """Simulate receiving transcript chunks."""
            nonlocal current_speaker, phrase_index
            import time
            
            print('[MOCK] Starting transcription simulation')
            
            while self.is_streaming and phrase_index < len(sample_phrases):
                await asyncio.sleep(2)  # Simulate delay
                
                if not self.is_streaming:
                    print('[MOCK] Streaming stopped, ending simulation')
                    break
                
                phrase = sample_phrases[phrase_index]
                phrase_index += 1
                
                # Alternate speakers
                if enable_speaker_diarization:
                    speaker = f"Speaker {current_speaker}"
                    current_speaker = 2 if current_speaker == 1 else 1
                else:
                    speaker = None
                
                # Send transcript chunk
                chunk = {
                    'text': phrase,
                    'speaker': speaker,
                    'is_final': True,
                    'timestamp': int(time.time() * 1000),
                }
                print(f'[MOCK] Sending transcript chunk: {chunk}')
                try:
                    # Call the callback (it's async, so await it)
                    if asyncio.iscoroutinefunction(on_transcript):
                        await on_transcript(chunk)
                    else:
                        on_transcript(chunk)
                    print(f'[MOCK] Transcript chunk sent successfully')
                except Exception as e:
                    print(f'[MOCK ERROR] Failed to send transcript chunk: {e}')
                    import traceback
                    traceback.print_exc()
        
        # Start simulation task immediately
        print('[MOCK] Creating transcription simulation task')
        try:
            # Get the current event loop
            loop = asyncio.get_event_loop()
            self.transcription_task = loop.create_task(simulate_transcription())
            print('[MOCK] Simulation task created and started')
        except Exception as e:
            print(f'[MOCK ERROR] Failed to create simulation task: {e}')
            import traceback
            traceback.print_exc()
            on_error(e)
        
        async def send_audio(audio_chunk: bytes):
            """Mock send audio - just acknowledge receipt."""
            if not self.is_streaming:
                return
            # In real implementation, this would send to Soniox
            # For mock, we just simulate transcription above
            pass
        
        async def stop():
            """Stop the streaming session."""
            self.is_streaming = False
            if self.transcription_task:
                self.transcription_task.cancel()
                try:
                    await self.transcription_task
                except asyncio.CancelledError:
                    pass
        
        def is_active_check() -> bool:
            return self.is_streaming
        
        return {
            'send_audio': send_audio,
            'stop': stop,
            'is_active': is_active_check
        }
    
    async def process_batch(
        self,
        audio_buffer: bytes,
        options: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Process batch audio file (mock)."""
        return [
            {
                'text': 'Mock transcript segment 1',
                'speaker': 'Speaker 1',
                'start_time': 0.0,
                'end_time': 5.0,
            },
            {
                'text': 'Mock transcript segment 2',
                'speaker': 'Speaker 2',
                'start_time': 5.0,
                'end_time': 10.0,
            },
        ]

