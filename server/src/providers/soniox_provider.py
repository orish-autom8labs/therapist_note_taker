"""
Soniox transcription provider implementation.
High accuracy Hebrew transcription with speaker diarization.
Uses Soniox WebSocket API for real-time streaming.
"""
import os
import asyncio
import json
import time
import websockets
from typing import Dict, Any, Callable, List, Optional
from .transcription_provider import TranscriptionProvider


class SonioxProvider(TranscriptionProvider):
    """Soniox transcription provider with real-time streaming via WebSocket."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get('api_key') or os.getenv('SONIOX_API_KEY')
        if not self.api_key:
            raise ValueError("Soniox API key is required")
        self.websocket = None
        # Correct Soniox WebSocket endpoint
        self.websocket_uri = "wss://stt-rt.soniox.com/transcribe-websocket"
        self.is_streaming = False
        self.response_task = None
    
    def get_name(self) -> str:
        return 'Soniox'
    
    def supports_language(self, language_code: str) -> bool:
        """Soniox supports Hebrew and many other languages."""
        normalized = self._normalize_language_code(language_code)
        return normalized is not None
    
    def _normalize_language_code(self, language_code: str) -> Optional[str]:
        """
        Convert locale codes to ISO 639-1 codes for Soniox.
        Soniox uses 2-letter ISO codes (e.g., 'he', 'en'), not locale codes (e.g., 'he-IL', 'en-US').
        """
        # Map common locale codes to ISO 639-1
        locale_to_iso = {
            'he-IL': 'he',
            'he': 'he',
            'en-US': 'en',
            'en-GB': 'en',
            'en': 'en',
            'es-ES': 'es',
            'es-MX': 'es',
            'es': 'es',
            'fr-FR': 'fr',
            'fr': 'fr',
            'de-DE': 'de',
            'de': 'de',
            'ar-SA': 'ar',
            'ar': 'ar',
            'ru-RU': 'ru',
            'ru': 'ru',
            'ja-JP': 'ja',
            'ja': 'ja',
            'zh-CN': 'zh',
            'zh-TW': 'zh',
            'zh': 'zh',
        }
        
        # Check if it's already a 2-letter code
        if len(language_code) == 2 and language_code.isalpha():
            return language_code.lower()
        
        # Check locale mapping
        if language_code in locale_to_iso:
            return locale_to_iso[language_code]
        
        # Try extracting 2-letter code from locale (e.g., "he-IL" -> "he")
        parts = language_code.split('-')
        if len(parts) > 0 and len(parts[0]) == 2:
            return parts[0].lower()
        
        return None
    
    def supports_speaker_diarization(self) -> bool:
        return True
    
    async def start_streaming_session(
        self,
        options: Dict[str, Any],
        on_transcript: Callable[[Dict[str, Any]], None],
        on_error: Callable[[Exception], None]
    ) -> Dict[str, Any]:
        """Start streaming transcription session with Soniox WebSocket API."""
        language = options.get('language', 'he-IL')
        enable_speaker_diarization = options.get('enable_speaker_diarization', True)
        
        print(f'[SONIOX] Starting streaming session - language: {language}, diarization: {enable_speaker_diarization}')
        
        self.is_streaming = True
        
        try:
            # Connect to Soniox WebSocket API
            # No authentication in headers - API key goes in config message
            print(f'[SONIOX] Connecting to {self.websocket_uri}')
            self.websocket = await websockets.connect(self.websocket_uri)
            print('[SONIOX] WebSocket connected')
            
            # Send initial configuration message (required by Soniox)
            # API key must be in the config message, not headers
            config_message = {
                'api_key': self.api_key,  # Required: API key in config message
                'model': 'stt-rt-v3',  # Required: transcription model (using v3 as per official examples)
                'audio_format': 'auto',  # Auto-detect format (webm/opus from browser)
                # For raw audio, you'd use:
                # 'audio_format': 'pcm_s16le',
                # 'sample_rate': 16000,
                # 'num_channels': 1,
            }
            
            # Add language hint if supported
            # Soniox uses ISO 639-1 codes (2-letter), not locale codes (e.g., "he" not "he-IL")
            if language:
                # Convert locale codes to ISO 639-1 codes
                language_code = self._normalize_language_code(language)
                if language_code:
                    config_message['language_hints'] = [language_code]
                    print(f'[SONIOX] Using language hint: {language_code} (from {language})')
                else:
                    print(f'[SONIOX WARNING] Unsupported language code: {language}, skipping language hint')
            
            # Add speaker diarization if enabled
            if enable_speaker_diarization:
                config_message['enable_speaker_diarization'] = True
            
            # Enable endpoint detection (as per official example) - helps with latency
            config_message['enable_endpoint_detection'] = True
            
            await self.websocket.send(json.dumps(config_message))
            print(f'[SONIOX] Sent config: {json.dumps(config_message, indent=2)}')
            
            # Track final tokens (accumulated) - matching official example approach
            final_tokens: List[dict] = []

            # Track all tokens (final + non-final) for fallback mechanism
            all_accumulated_tokens: List[dict] = []
            last_sent_time = time.time()
            FALLBACK_INTERVAL = 5.0  # Send accumulated text every 5 seconds

            # DIAGNOSTIC: Track response numbers and speaker state
            response_number = 0
            total_tokens_received = 0
            total_chunks_sent = 0

            # Start background task to process responses
            async def process_responses():
                """Process streaming responses from Soniox (matching official example approach)."""
                nonlocal final_tokens, all_accumulated_tokens, last_sent_time, response_number, total_tokens_received, total_chunks_sent
                try:
                    print('[SONIOX] Starting response processing loop')
                    first_message = True
                    
                    message_count = 0
                    last_response_time = time.time()
                    
                    async for message in self.websocket:
                        message_count += 1
                        current_time = time.time()
                        time_since_last = current_time - last_response_time
                        last_response_time = current_time
                        
                        print(f'[SONIOX] Message #{message_count} received (after {time_since_last:.2f}s, type: {type(message).__name__}, len: {len(str(message))})')
                        
                        if not self.is_streaming:
                            print('[SONIOX] Streaming stopped, exiting response loop')
                            break
                        
                        # Handle first message (could be error or acknowledgment)
                        if first_message:
                            first_message = False
                            print(f'[SONIOX] First response received: {str(message)[:500]}')
                            print(f'[SONIOX] First response type: {type(message)}')
                            
                            # Check if it's an error
                            try:
                                # Handle both string and bytes messages
                                if isinstance(message, bytes):
                                    message_str = message.decode('utf-8', errors='ignore')
                                else:
                                    message_str = str(message)
                                
                                error_data = json.loads(message_str)
                                print(f'[SONIOX] First response parsed: {json.dumps(error_data, indent=2)}')
                                
                                # Check for Soniox error responses (they use error_code and error_message)
                                if 'error_code' in error_data or 'error_message' in error_data:
                                    error_code = error_data.get('error_code', 'Unknown')
                                    error_msg = error_data.get('error_message', 'Unknown error')
                                    print(f'[SONIOX ERROR] Error {error_code}: {error_msg}')
                                    self.is_streaming = False
                                    raise Exception(f"Soniox error {error_code}: {error_msg}")
                                elif 'error' in error_data:
                                    error_msg = error_data.get('error', 'Unknown error')
                                    print(f'[SONIOX ERROR] Configuration error: {error_msg}')
                                    self.is_streaming = False
                                    raise Exception(f"Soniox configuration error: {error_msg}")
                                elif 'status' in error_data and error_data.get('status') != 'ok':
                                    error_msg = error_data.get('message', 'Configuration failed')
                                    print(f'[SONIOX ERROR] Status error: {error_msg}')
                                    self.is_streaming = False
                                    raise Exception(f"Soniox error: {error_msg}")
                                else:
                                    print('[SONIOX] Configuration accepted, continuing...')
                                    # Continue processing - this might be a status message or first transcription
                            except json.JSONDecodeError as e:
                                # Not JSON, might be binary data or something else
                                print(f'[SONIOX] First response is not JSON: {e}')
                                print(f'[SONIOX] Message content: {str(message)[:200]}')
                            except Exception as e:
                                print(f'[SONIOX ERROR] Error processing first response: {e}')
                                self.is_streaming = False
                                raise
                        
                        try:
                            # Parse JSON response
                            data = json.loads(message)
                            
                            # Check for errors first (as per official example)
                            if data.get("error_code") is not None:
                                error_code = data.get('error_code')
                                error_msg = data.get('error_message', 'Unknown error')
                                print(f'[SONIOX ERROR] Error {error_code}: {error_msg}')
                                
                                # Handle 408 timeout more gracefully - don't kill session immediately
                                # Soniox might still process audio, just slowly
                                if error_code == 408:
                                    print(f'[SONIOX WARNING] Timeout error (408) - continuing to process audio, but Soniox may be slow')
                                    # Don't set is_streaming = False for timeout - let it continue
                                    # The session might recover if we keep sending audio
                                    # Only log the error, don't raise exception
                                    await on_error(Exception(f"Soniox timeout (408): {error_msg}. Continuing to send audio..."))
                                else:
                                    # For other errors, mark as inactive
                                    self.is_streaming = False
                                    raise Exception(f"Soniox error {error_code}: {error_msg}")
                            
                            # Log tokens if present
                            if 'tokens' in data and data['tokens']:
                                tokens_info = []
                                for token in data['tokens'][:5]:  # Show first 5 tokens
                                    tokens_info.append({
                                        'text': token.get('text', ''),
                                        'is_final': token.get('is_final', False),
                                        'speaker': token.get('speaker', 'N/A')
                                    })
                                print(f'[SONIOX] Received {len(data["tokens"])} tokens (showing first 5): {tokens_info}')
                            else:
                                # Empty tokens might be normal - just progress updates
                                if data.get('final_audio_proc_ms', 0) > 0 or data.get('total_audio_proc_ms', 0) > 0:
                                    print(f'[SONIOX] Progress update: final={data.get("final_audio_proc_ms", 0)}ms, total={data.get("total_audio_proc_ms", 0)}ms')
                                else:
                                    print(f'[SONIOX] Received response (no tokens, no progress): {json.dumps(data, indent=2)[:200]}...')
                            
                            # Process tokens (matching official example approach)
                            if 'tokens' in data and data['tokens']:
                                response_number += 1
                                print(f'\n{"="*80}')
                                print(f'[DIAGNOSTIC] RESPONSE #{response_number} - Processing {len(data["tokens"])} tokens')
                                print(f'{"="*80}')

                                # Parse tokens from current response (as per official example)
                                non_final_tokens: List[dict] = []
                                new_final_tokens: List[dict] = []

                                token_num_in_response = 0
                                for token in data.get("tokens", []):
                                    token_num_in_response += 1
                                    token_text = token.get('text', '')
                                    token_speaker = token.get('speaker')
                                    token_is_final = token.get('is_final', False)

                                    # DIAGNOSTIC: Log every token with full details
                                    print(f'[DIAGNOSTIC] Response #{response_number}, Token #{token_num_in_response}:')
                                    print(f'  - text: "{token_text}"')
                                    print(f'  - speaker: {token_speaker} (type: {type(token_speaker).__name__})')
                                    print(f'  - is_final: {token_is_final}')
                                    print(f'  - will_filter: {token_text.strip() in ["<end>", "</s>", "<s>", "<unk>", ""]}')

                                    # Only process tokens with text (as per official example)
                                    if token_text:
                                        total_tokens_received += 1
                                        if token.get('is_final', False):
                                            # Final tokens are returned once and should be appended to final_tokens
                                            final_tokens.append(token)
                                            new_final_tokens.append(token)
                                            print(f'  → Added to final_tokens (total final tokens now: {len(final_tokens)})')
                                        else:
                                            # Non-final tokens update as more audio arrives; reset them on every response
                                            non_final_tokens.append(token)
                                            print(f'  → Added to non_final_tokens (count in this response: {len(non_final_tokens)})')

                                print(f'\n[DIAGNOSTIC] Response #{response_number} Summary:')
                                print(f'  - New final tokens: {len(new_final_tokens)}')
                                print(f'  - Non-final tokens: {len(non_final_tokens)}')
                                print(f'  - Total accumulated final tokens: {len(final_tokens)}')
                                print(f'  - Total tokens received so far: {total_tokens_received}')
                                
                                # Render and send transcript
                                # Strategy: 
                                # 1. Send final tokens immediately (when Soniox finalizes)
                                # 2. Fallback: Send accumulated text every 5 seconds (for continuous speech)
                                
                                # Update accumulated tokens (for fallback)
                                all_accumulated_tokens = final_tokens + non_final_tokens
                                
                                # Send new final tokens as finalized chunks (priority)
                                if new_final_tokens:
                                    print(f'\n[DIAGNOSTIC] Processing {len(new_final_tokens)} NEW final tokens for speaker detection...')

                                    # Process tokens in order, detecting speaker changes (like Soniox example)
                                    current_speaker = None
                                    current_texts: List[str] = []
                                    current_segment_start_ms = None  # Track first token timestamp for segment
                                    token_idx = 0

                                    for token in new_final_tokens:
                                        token_idx += 1
                                        speaker = token.get('speaker', 'Unknown')
                                        text = token.get('text', '')
                                        # Capture Soniox token timestamp (start_ms) if available
                                        token_start_ms = token.get('start_ms')

                                        print(f'[DIAGNOSTIC] Token {token_idx}/{len(new_final_tokens)}: speaker={speaker}, text="{text[:30]}...", start_ms={token_start_ms}')

                                        # Filter out special tokens at token level
                                        if text.strip() in ['<end>', '</s>', '<s>', '<unk>', '']:
                                            print(f'  → FILTERED (special token)')
                                            continue

                                        # Speaker changed - send accumulated text from previous speaker
                                        if speaker != current_speaker and current_speaker is not None:
                                            print(f'  → SPEAKER CHANGE detected! From {current_speaker} to {speaker}')
                                            # Send the accumulated text
                                            transcript_text = ''.join(current_texts).strip()
                                            if transcript_text:
                                                # Format speaker ID consistently - convert to string
                                                speaker_str = str(current_speaker) if current_speaker != 'Unknown' else 'Unknown'
                                                # Use Soniox token timestamp if available, fallback to current time
                                                timestamp = current_segment_start_ms if current_segment_start_ms else int(asyncio.get_event_loop().time() * 1000)
                                                transcript_data = {
                                                    'text': transcript_text,
                                                    'speaker': speaker_str,
                                                    'is_final': True,
                                                    'timestamp': timestamp,
                                                }
                                                total_chunks_sent += 1
                                                print(f'  → SENDING CHUNK #{total_chunks_sent}: Speaker {speaker_str}, timestamp={timestamp}ms, text="{transcript_text[:50]}..." ({len(transcript_text)} chars)')
                                                await on_transcript(transcript_data)
                                            # Reset for new speaker - use current token's timestamp as new segment start
                                            current_texts = []
                                            current_segment_start_ms = token_start_ms
                                        elif speaker == current_speaker:
                                            print(f'  → Same speaker ({speaker}), accumulating...')
                                        else:
                                            print(f'  → First token (current_speaker is None), starting with speaker {speaker}')
                                            # First token of first segment - capture its timestamp
                                            current_segment_start_ms = token_start_ms

                                        # Update current speaker and accumulate text
                                        current_speaker = speaker
                                        current_texts.append(text)

                                    # Send remaining accumulated text from last speaker
                                    if current_texts:
                                        transcript_text = ''.join(current_texts).strip()
                                        if transcript_text:
                                            # Format speaker ID consistently - convert to string
                                            speaker_str = str(current_speaker) if current_speaker != 'Unknown' else 'Unknown'
                                            # Use Soniox token timestamp if available, fallback to current time
                                            timestamp = current_segment_start_ms if current_segment_start_ms else int(asyncio.get_event_loop().time() * 1000)
                                            transcript_data = {
                                                'text': transcript_text,
                                                'speaker': speaker_str,
                                                'is_final': True,
                                                'timestamp': timestamp,
                                            }
                                            total_chunks_sent += 1
                                            print(f'  → SENDING FINAL CHUNK #{total_chunks_sent}: Speaker {speaker_str}, timestamp={timestamp}ms, text="{transcript_text[:50]}..." ({len(transcript_text)} chars)')
                                            await on_transcript(transcript_data)

                                    print(f'[DIAGNOSTIC] Finished processing response #{response_number}. Total chunks sent so far: {total_chunks_sent}')

                                    last_sent_time = time.time()  # Reset fallback timer
                                
                                # Fallback: Send accumulated text every 5 seconds if no final tokens
                                # This ensures users see progress during continuous speech
                                current_time = time.time()
                                time_since_last_send = current_time - last_sent_time

                                # Always check fallback timer, even if no tokens yet (helps debug slow Soniox)
                                if time_since_last_send >= FALLBACK_INTERVAL:
                                    if all_accumulated_tokens:
                                        # Process tokens in order, detecting speaker changes (like Soniox example)
                                        fallback_speaker = None
                                        fallback_texts: List[str] = []
                                        fallback_segment_start_ms = None  # Track first token timestamp

                                        for token in all_accumulated_tokens:
                                            speaker = token.get('speaker', 'Unknown')
                                            text = token.get('text', '')
                                            token_start_ms = token.get('start_ms')

                                            # Filter out special tokens
                                            if text.strip() in ['<end>', '</s>', '<s>', '<unk>', '']:
                                                continue

                                            # Speaker changed - send accumulated text from previous speaker
                                            if speaker != fallback_speaker and fallback_speaker is not None:
                                                # Send the accumulated text
                                                transcript_text = ''.join(fallback_texts).strip()
                                                if transcript_text:
                                                    speaker_str = str(fallback_speaker) if fallback_speaker != 'Unknown' else 'Unknown'
                                                    timestamp = fallback_segment_start_ms if fallback_segment_start_ms else int(asyncio.get_event_loop().time() * 1000)
                                                    transcript_data = {
                                                        'text': transcript_text,
                                                        'speaker': speaker_str,
                                                        'is_final': False,  # Mark as non-final (fallback)
                                                        'fallback': True,  # Flag to indicate this is a fallback
                                                        'timestamp': timestamp,
                                                    }
                                                    print(f'[SONIOX] FALLBACK: Sending accumulated text ({time_since_last_send:.1f}s): "{transcript_text}" from Speaker {speaker_str}')
                                                    await on_transcript(transcript_data)
                                                # Reset for new speaker
                                                fallback_texts = []
                                                fallback_segment_start_ms = token_start_ms
                                            elif fallback_segment_start_ms is None:
                                                # First token - capture timestamp
                                                fallback_segment_start_ms = token_start_ms

                                            # Update current speaker and accumulate text
                                            fallback_speaker = speaker
                                            fallback_texts.append(text)

                                        # Send remaining accumulated text from last speaker
                                        if fallback_texts:
                                            transcript_text = ''.join(fallback_texts).strip()
                                            if transcript_text:
                                                speaker_str = str(fallback_speaker) if fallback_speaker != 'Unknown' else 'Unknown'
                                                timestamp = fallback_segment_start_ms if fallback_segment_start_ms else int(asyncio.get_event_loop().time() * 1000)
                                                transcript_data = {
                                                    'text': transcript_text,
                                                    'speaker': speaker_str,
                                                    'is_final': False,  # Mark as non-final (fallback)
                                                    'fallback': True,  # Flag to indicate this is a fallback
                                                    'timestamp': timestamp,
                                                }
                                                print(f'[SONIOX] FALLBACK: Sending accumulated text ({time_since_last_send:.1f}s): "{transcript_text}" from Speaker {speaker_str}')
                                                await on_transcript(transcript_data)

                                        last_sent_time = current_time
                                    else:
                                        # No tokens yet, but 5 seconds passed - log status for debugging
                                        print(f'[SONIOX] FALLBACK: No tokens received yet after {time_since_last_send:.1f}s - Soniox may be processing slowly or timing out')
                                        # Reset timer to check again in 5 seconds
                                        last_sent_time = current_time
                                
                                # Check if session finished
                                if data.get("finished"):
                                    print('[SONIOX] Session finished.')
                                    self.is_streaming = False
                            
                        except json.JSONDecodeError:
                            print(f'[SONIOX WARNING] Received non-JSON message: {message[:100]}')
                        except Exception as e:
                            print(f'[SONIOX ERROR] Error processing response: {e}')
                            if self.is_streaming:
                                await on_error(e)
                            
                except websockets.exceptions.ConnectionClosedOK as e:
                    print(f'[SONIOX] Connection closed gracefully: code={e.code}, reason={e.reason}')
                    self.is_streaming = False  # Mark as inactive
                    if self.is_streaming:  # This won't execute, but keeping for consistency
                        # Connection closed unexpectedly
                        await on_error(Exception(f"Soniox connection closed: {e.reason or 'Unknown reason'}"))
                except websockets.exceptions.ConnectionClosedError as e:
                    print(f'[SONIOX ERROR] Connection closed with error: code={e.code}, reason={e.reason}')
                    self.is_streaming = False  # Mark as inactive
                    if self.is_streaming:  # This won't execute, but keeping for consistency
                        await on_error(e)
                except Exception as e:
                    print(f'[SONIOX ERROR] Response processing failed: {e}')
                    import traceback
                    traceback.print_exc()
                    if self.is_streaming:
                        await on_error(e)
            
            # Start response processing task
            self.response_task = asyncio.create_task(process_responses())
            print('[SONIOX] Response processing task started')
            
            async def send_audio(audio_chunk: bytes):
                """Send audio chunk to Soniox, splitting into 3840-byte pieces (matching official example)."""
                # Allow sending audio even if streaming is marked False (might recover)
                if not self.websocket:
                    print(f'[SONIOX] Cannot send audio: websocket={self.websocket is not None}')
                    return
                
                # Check if connection is still open
                if self.websocket.closed:
                    print('[SONIOX ERROR] WebSocket is closed, cannot send audio')
                    self.is_streaming = False
                    return
                
                # Warn if streaming is False but still try to send (for recovery)
                if not self.is_streaming:
                    print(f'[SONIOX WARNING] Streaming marked False, but attempting to send audio anyway (recovery attempt)')
                
                try:
                    
                    # Split large chunks into 3840-byte pieces (matching official example)
                    CHUNK_SIZE = 3840  # Official example uses 3840 bytes
                    total_sent = 0
                    
                    for i in range(0, len(audio_chunk), CHUNK_SIZE):
                        chunk = audio_chunk[i:i+CHUNK_SIZE]
                        if len(chunk) == 0:
                            break
                        
                        # Send binary audio data
                        print(f'[SONIOX] Sending {len(chunk)} bytes of audio (chunk {i//CHUNK_SIZE + 1} of {(len(audio_chunk) + CHUNK_SIZE - 1)//CHUNK_SIZE})')
                        await self.websocket.send(chunk)
                        total_sent += len(chunk)
                        
                        # Sleep for 120ms between chunks (matching official example timing)
                        if i + CHUNK_SIZE < len(audio_chunk):  # Don't sleep after last chunk
                            await asyncio.sleep(0.120)
                    
                    print(f'[SONIOX] Audio chunk sent successfully ({total_sent} total bytes)')
                except websockets.exceptions.ConnectionClosed:
                    print('[SONIOX ERROR] Connection closed while sending audio')
                    self.is_streaming = False
                    if self.is_streaming:  # Check again after setting flag
                        await on_error(Exception("Soniox connection closed"))
                except Exception as e:
                    print(f'[SONIOX ERROR] Failed to send audio: {e}')
                    import traceback
                    traceback.print_exc()
                    if self.is_streaming:
                        await on_error(e)
            
            async def stop():
                """Stop the streaming session."""
                nonlocal self
                print('[SONIOX] Stopping stream')
                self.is_streaming = False
                
                if self.websocket:
                    try:
                        # Send empty string to signal end-of-audio (as per official example)
                        await self.websocket.send("")
                        await asyncio.sleep(0.5)  # Wait for final responses
                        await self.websocket.close()
                    except Exception as e:
                        print(f'[SONIOX ERROR] Error closing WebSocket: {e}')
                    finally:
                        self.websocket = None
                
                # Cancel response task
                if self.response_task:
                    self.response_task.cancel()
                    try:
                        await self.response_task
                    except asyncio.CancelledError:
                        pass
            
            def is_active_check() -> bool:
                is_active = self.is_streaming and self.websocket is not None and not self.websocket.closed
                if not is_active:
                    print(f'[SONIOX DEBUG] is_active_check: streaming={self.is_streaming}, websocket={self.websocket is not None}, closed={self.websocket.closed if self.websocket else "N/A"}')
                return is_active
            
            return {
                'send_audio': send_audio,
                'stop': stop,
                'is_active': is_active_check
            }
            
        except Exception as e:
            print(f'[SONIOX ERROR] Failed to start streaming session: {e}')
            import traceback
            traceback.print_exc()
            self.is_streaming = False
            await on_error(e)
            raise
    
    async def process_batch(
        self,
        audio_buffer: bytes,
        options: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Process batch audio file using Soniox REST API."""
        language = options.get('language', 'he-IL')
        enable_speaker_diarization = options.get('enable_speaker_diarization', True)
        
        try:
            import aiohttp
            
            # Use Soniox REST API for batch processing
            url = "https://api.soniox.com/v1/transcribe_file"
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/octet-stream'
            }
            
            params = {
                'language': language,
            }
            if enable_speaker_diarization:
                params['enable_speaker_diarization'] = 'true'
                params['num_speakers'] = '2'
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, data=audio_buffer, params=params) as response:
                    if response.status == 200:
                        result = await response.json()
                        return self._parse_soniox_batch_response(result)
                    else:
                        error_text = await response.text()
                        raise Exception(f"Soniox API error {response.status}: {error_text}")
        except Exception as e:
            raise Exception(f"Soniox batch processing failed: {str(e)}")
    
    def _parse_soniox_batch_response(self, result: Any) -> List[Dict[str, Any]]:
        """Parse Soniox batch response."""
        segments = []
        
        try:
            # Soniox batch response format
            words = result.get('words', [])
            
            if words:
                current_segment = {
                    'text': '',
                    'speaker': None,
                    'start_time': None,
                    'end_time': None,
                }
                
                for word in words:
                    word_text = word.get('text', '')
                    word_speaker = word.get('speaker')
                    word_start = word.get('start_ms')
                    word_end = word.get('end_ms')
                    
                    if current_segment['speaker'] != word_speaker:
                        if current_segment['text']:
                            segments.append({
                                **current_segment,
                                'speaker': f"Speaker {current_segment['speaker']}" if current_segment['speaker'] is not None else None,
                            })
                        current_segment = {
                            'text': word_text,
                            'speaker': word_speaker,
                            'start_time': word_start / 1000.0 if word_start else None,
                            'end_time': word_end / 1000.0 if word_end else None,
                        }
                    else:
                        current_segment['text'] += ' ' + word_text
                        if word_end:
                            current_segment['end_time'] = word_end / 1000.0
                
                if current_segment['text']:
                    segments.append({
                        **current_segment,
                        'speaker': f"Speaker {current_segment['speaker']}" if current_segment['speaker'] is not None else None,
                    })
        
        except Exception as e:
            print(f'[SONIOX ERROR] Failed to parse batch response: {e}')
            import traceback
            traceback.print_exc()
        
        return segments
