"""
Main FastAPI server with WebSocket support for real-time transcription.
"""
import asyncio
import json
import os
import time
import traceback
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
import httpx
from src.config import config
from src.services.transcription_service import TranscriptionService
from src.services.drive_service import DriveService
from src.services.email_service import EmailService
from src.services.summarization import SummarizationService, SummaryStyle
from src.services.firestore_service import FirestoreService

app = FastAPI(title="Note Taker API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "https://note-taker-frontend-1049928242674.us-central1.run.app",
        "https://staging---note-taker-frontend-1049928242674.us-central1.run.app",
        "https://staging---note-taker-frontend-gj63k7jruq-uc.a.run.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Services
transcription_service = TranscriptionService()
email_service = EmailService()

# Initialize summarization service (only if enabled)
summarization_service = None
if config.summarization.enabled:
    try:
        summarization_service = SummarizationService(config.summarization)
        print(f'[SUMMARIZATION] Service initialized - Stage1: {config.summarization.stage1_provider}, Stage2: {config.summarization.stage2_provider}')
    except Exception as e:
        print(f'[SUMMARIZATION] Failed to initialize service: {e}')
        summarization_service = None

# Initialize Firestore service (only if enabled)
firestore_service: Optional[FirestoreService] = None
if config.firestore.enabled:
    try:
        firestore_service = FirestoreService()
        print(f'[FIRESTORE] Service initialized - collection prefix: {config.firestore.collection_prefix}')
    except Exception as e:
        print(f'[FIRESTORE] Failed to initialize service: {e}')
        firestore_service = None

# Helper function to create DriveService with user tokens
def create_drive_service_with_tokens(access_token: str, refresh_token: str) -> DriveService:
    """
    Create a new DriveService instance with user tokens.
    This ensures each user has their own isolated service instance.
    """
    service = DriveService()
    service.set_user_tokens({
        'access_token': access_token,
        'refresh_token': refresh_token,
    })
    return service

# Store active sessions
active_sessions: Dict[str, Dict[str, Any]] = {}

# Pydantic models for REST API
class TemporaryKeyResponse(BaseModel):
    apiKey: str

class ErrorResponse(BaseModel):
    error: str

class TranscriptChunk(BaseModel):
    text: str
    speaker: Optional[str] = None
    is_final: bool = False
    timestamp: Optional[float] = None

class TranscriptUpdate(BaseModel):
    sessionId: str
    chunks: list[TranscriptChunk]
    is_final: bool = False


@app.post(
    "/v1/auth/temporary-api-key",
    response_model=TemporaryKeyResponse,
    responses={400: {"model": ErrorResponse}},
)
async def generate_temporary_api_key():
    """
    Generate a temporary API key for Soniox WebSocket transcription.
    
    This endpoint uses the main Soniox API key (stored on server) to generate
    a temporary key that can be safely used by the client. Temporary keys
    expire in 60 seconds and can only be used for transcription.
    """
    # Get main Soniox API key from config
    soniox_api_key = config.transcription.providers.get('soniox', {}).get('api_key')
    if not soniox_api_key:
        raise HTTPException(
            status_code=400,
            detail="SONIOX_API_KEY is not set in environment variables"
        )
    
    # Get Soniox API host (default to production)
    soniox_api_host = os.getenv("SONIOX_API_HOST", "https://api.soniox.com")
    
    try:
        async with httpx.AsyncClient() as client:
            # Call Soniox API to generate temporary key
            response = await client.post(
                f"{soniox_api_host}/v1/auth/temporary-api-key",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {soniox_api_key}",
                },
                json={
                    "usage_type": "transcribe_websocket",
                    "expires_in_seconds": 60,  # Expires in 60 seconds
                },
                timeout=10.0,
            )
            
            # Check if the request was successful
            response.raise_for_status()
            
            # Parse the response
            data = response.json()
            
            return TemporaryKeyResponse(apiKey=data["api_key"])
    
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Soniox API error: {e.response.text}",
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Request error: {str(e)}"
        )
    except KeyError:
        raise HTTPException(
            status_code=500,
            detail="Invalid response format from Soniox API"
        )


class TranscriptUpdateWithTokens(BaseModel):
    sessionId: str
    chunks: list[TranscriptChunk]
    is_final: bool = False
    accessToken: Optional[str] = None
    refreshToken: Optional[str] = None
    patientName: Optional[str] = None
    includeTimestamps: Optional[bool] = False
    diagnosticInfo: Optional[dict] = None  # Stall events and other diagnostic data


async def run_summarization_background(
    drive_service: DriveService,
    buffer: list,
    patient_name: str,
    date_str: str,
    time_str: str,
    session_id: str
):
    """
    Run summarization in the background after transcript save completes.
    This function NEVER raises exceptions - all errors are logged and saved to Drive.
    Updates Firestore status through the lifecycle.
    """
    try:
        print(f'[SUMMARIZATION] Starting background summarization for session {session_id}...')

        # Update Firestore: status = "summarizing"
        if firestore_service:
            try:
                await firestore_service.set_summarizing(session_id)
            except Exception as fs_err:
                print(f'[FIRESTORE] Failed to set summarizing status: {fs_err}')

        # Get session start time from first token
        timestamps = [c.get('timestamp') for c in buffer if c.get('timestamp')]
        session_start_ms = int(min(timestamps)) if timestamps else 0

        # Run multi-level summarization
        summary_result = await summarization_service.summarize_all_levels(
            buffer,
            session_start_ms,
            patient_name
        )

        # Save summary to Drive (separate file)
        if summary_result.success and summary_result.content:
            summary_file_name = f"{patient_name}_{date_str}_{time_str}_Summary.txt"
            folder_path = f'Clinic/Transcripts/{patient_name}'

            # Check for duplicate summary before creating
            existing_summaries = await drive_service.find_files_by_name(
                summary_file_name, folder_path
            )
            if existing_summaries:
                print(f'[SUMMARIZATION] Summary already exists, skipping duplicate: {summary_file_name}')
                summary_file_info = existing_summaries[0]
            else:
                # RTL-friendly formatting (no decorative lines)
                summary_content = f"""סיכום פגישה טיפולית

מטופל/ת: {patient_name}
תאריך: {datetime.now().strftime('%d/%m/%Y')}

{summary_result.content}

נוצר באמצעות AI
"""
                summary_file_info = await drive_service.save_transcript(
                    summary_content,
                    summary_file_name,
                    folder_path
                )
            print(f'[SUMMARIZATION] Summary saved: {summary_file_name} (cost: ${summary_result.total_cost_usd:.4f})')

            # Update Firestore: status = "completed" with summary links
            if firestore_service and summary_file_info:
                try:
                    await firestore_service.set_completed(
                        session_id,
                        summary_info=summary_file_info,
                        cost_usd=summary_result.total_cost_usd,
                    )
                    print(f'[FIRESTORE] Session {session_id} marked as completed')
                except Exception as fs_err:
                    print(f'[FIRESTORE] Failed to set completed status: {fs_err}')

        elif not summary_result.success and summary_result.error_report:
            # Save error report to Drive for debugging (max 1 per session: overwrite existing)
            error_file_name = f"{patient_name}_{date_str}_{time_str}_Summary_ERROR.txt"
            folder_path = f'Clinic/Transcripts/{patient_name}'
            try:
                existing_errors = await drive_service.find_files_by_name(
                    error_file_name, folder_path
                )
                if existing_errors:
                    # Overwrite the existing error file
                    await drive_service.update_file(
                        existing_errors[0]['file_id'],
                        summary_result.error_report
                    )
                    print(f'[SUMMARIZATION] Error report updated (overwritten): {error_file_name}')
                else:
                    await drive_service.save_transcript(
                        summary_result.error_report,
                        error_file_name,
                        folder_path
                    )
                    print(f'[SUMMARIZATION] Error report saved: {error_file_name}')
            except Exception as save_error:
                print(f'[SUMMARIZATION] Failed to save error report: {save_error}')

            # Update Firestore: status = "summarization_failed"
            if firestore_service:
                try:
                    error_msg = summary_result.error_report[:500] if summary_result.error_report else "Unknown error"
                    await firestore_service.set_failed(session_id, error_msg)
                except Exception as fs_err:
                    print(f'[FIRESTORE] Failed to set failed status: {fs_err}')

    except Exception as summary_error:
        # Log error but NEVER propagate
        print(f'[SUMMARIZATION] Error during background summarization: {summary_error}')
        print(f'[SUMMARIZATION] Traceback: {traceback.format_exc()}')

        # Update Firestore: status = "summarization_failed"
        if firestore_service:
            try:
                await firestore_service.set_failed(
                    session_id,
                    f"{type(summary_error).__name__}: {str(summary_error)[:300]}"
                )
            except Exception as fs_err:
                print(f'[FIRESTORE] Failed to set failed status: {fs_err}')

        # Try to save error report
        try:
            error_report = f"""
{'='*60}
SUMMARIZATION ERROR REPORT
{'='*60}

Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Patient: {patient_name}
Session ID: {session_id}

Error Type: {type(summary_error).__name__}
Error Message: {str(summary_error)}

Traceback:
{traceback.format_exc()}

{'='*60}
The transcript was saved successfully.
Please check API keys and configuration.
{'='*60}
"""
            error_file_name = f"{patient_name}_{date_str}_{time_str}_Summary_ERROR.txt"
            await drive_service.save_transcript(
                error_report,
                error_file_name,
                f'Clinic/Transcripts/{patient_name}'
            )
            print(f'[SUMMARIZATION] Error report saved to Drive')
        except:
            print(f'[SUMMARIZATION] Failed to save error report to Drive')


@app.post("/api/sessions/{session_id}/transcript")
async def save_transcript(
    session_id: str,
    transcript_update: TranscriptUpdateWithTokens = Body(...)
):
    """
    Save transcript chunks from client.
    Called periodically (every 1 minute) for auto-save and on session end for final save.
    """
    try:
        # Create user-specific DriveService instance if tokens provided
        drive_service = None
        refreshed_tokens = None
        if transcript_update.accessToken and transcript_update.refreshToken:
            drive_service = create_drive_service_with_tokens(
                transcript_update.accessToken,
                transcript_update.refreshToken
            )

            # Check if token needs refresh (and refresh if needed)
            refreshed_tokens = drive_service._refresh_token_if_needed()
            if refreshed_tokens:
                print('[SERVER] Tokens refreshed, will return new tokens to client')

        # Get session info
        if session_id not in active_sessions:
            # Create new session entry
            # Get patient name from request or use default
            patient_name = transcript_update.patientName or 'Unknown'
            active_sessions[session_id] = {
                'patient_name': patient_name,
                'start_time': time.time() * 1000,
                'transcript_buffer': [],
                'drive_file_id': None,
                'frequent_timestamps': bool(transcript_update.includeTimestamps),
            }
        
        session = active_sessions[session_id]
        
        # Add chunks to buffer
        for chunk in transcript_update.chunks:
            session['transcript_buffer'].append({
                'text': chunk.text,
                'speaker': chunk.speaker,
                'is_final': chunk.is_final,
                'timestamp': chunk.timestamp or time.time() * 1000,
            })
        
        # Generate file name
        from datetime import datetime
        now = datetime.now()
        date_str = now.strftime('%Y-%m-%d')
        time_str = now.strftime('%H-%M-%S')
        patient_name = session.get('patient_name', 'Unknown')
        start_time = session.get('start_time', now.timestamp() * 1000)
        frequent_timestamps = session.get('frequent_timestamps', False)

        # Format transcript with header
        transcript_text = format_transcript_with_header(
            session['transcript_buffer'],
            patient_name,
            start_time,
            now.timestamp() * 1000,
            frequent_timestamps=frequent_timestamps,
        )
        
        if transcript_update.is_final:
            # Final save
            try:
                # ═══════════════════════════════════════════════════════════
                # IDEMPOTENCY CHECK: If session already exists in Firestore, return existing data
                # ═══════════════════════════════════════════════════════════
                if firestore_service:
                    try:
                        existing = await firestore_service.get_session(session_id)
                        if existing:
                            print(f'[IDEMPOTENCY] Session {session_id} already exists in Firestore, returning existing data')
                            transcript_info = existing.get("transcript", {})
                            response = {
                                "status": "success",
                                "sessionId": session_id,
                                "fileInfo": {
                                    "id": transcript_info.get("drive_file_id"),
                                    "name": transcript_info.get("drive_file_name"),
                                    "web_view_link": transcript_info.get("web_view_link"),
                                },
                            }
                            if refreshed_tokens:
                                response["refreshedTokens"] = refreshed_tokens
                            return response
                    except Exception as fs_err:
                        print(f'[FIRESTORE] Idempotency check failed (non-blocking): {fs_err}')

                file_name = f"{patient_name}_{date_str}_{time_str}.txt"

                # If we have a temp file, update it; otherwise create new
                if session.get('drive_file_id'):
                    # Update existing temp file
                    file_info = await drive_service.update_file(
                        session['drive_file_id'],
                        transcript_text
                    )
                    # Note: We can't rename via update, so we create new and delete old
                    file_info = await drive_service.save_transcript(
                        transcript_text,
                        file_name,
                        f'Clinic/Transcripts/{patient_name}'
                    )
                    # Delete old temp file
                    try:
                        await drive_service.delete_file(session['drive_file_id'])
                    except:
                        pass  # Ignore delete errors
                else:
                    # Create new file
                    file_info = await drive_service.save_transcript(
                        transcript_text,
                        file_name,
                        f'Clinic/Transcripts/{patient_name}'
                    )
                
                # Send email notification (optional - don't fail if email fails)
                if file_info.get('web_view_link'):
                    try:
                        await email_service.send_session_complete_email(
                            patient_name,
                            file_info['web_view_link'],
                        )
                        print(f'[EMAIL] Notification sent for session {session_id}')
                    except Exception as email_error:
                        print(f'[EMAIL] Failed to send notification: {email_error}')
                        # Don't fail the save operation if email fails

                # ═══════════════════════════════════════════════════════════════════
                # FIRESTORE: Create session document after transcript saved
                # ═══════════════════════════════════════════════════════════════════
                if firestore_service:
                    try:
                        # Calculate metadata from transcript buffer
                        token_count = len(session['transcript_buffer'])
                        timestamps = [c.get('timestamp') for c in session['transcript_buffer'] if c.get('timestamp')]
                        duration_minutes = 0
                        if len(timestamps) >= 2:
                            duration_minutes = int((max(timestamps) - min(timestamps)) / 60_000)

                        await firestore_service.create_session(
                            session_id=session_id,
                            user_email="",  # We don't have email from tokens; could add later
                            patient_name=patient_name,
                            transcript_info=file_info,
                            refresh_token=transcript_update.refreshToken,
                            metadata={
                                "duration_minutes": duration_minutes,
                                "token_count": token_count,
                                "language": "he",  # Default; detected during summarization
                            },
                        )
                        print(f'[FIRESTORE] Session {session_id} created with status=transcript_saved')
                    except Exception as fs_err:
                        print(f'[FIRESTORE] Failed to create session doc (non-blocking): {fs_err}')

                # ═══════════════════════════════════════════════════════════════════
                # DIAGNOSTIC INFO (Save if stall events detected)
                # ═══════════════════════════════════════════════════════════════════
                if transcript_update.diagnosticInfo:
                    try:
                        diag = transcript_update.diagnosticInfo
                        stall_count = diag.get('totalStallCount', 0)
                        if stall_count > 0:
                            print(f'[DIAGNOSTIC] ⚠️ Session had {stall_count} stall events - saving diagnostic file')
                            diag_file_name = f"{patient_name}_{date_str}_{time_str}_DIAGNOSTIC.txt"
                            diag_content = f"""{'═' * 60}
TRANSCRIPTION DIAGNOSTIC REPORT
{'═' * 60}

Session: {patient_name}
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Session ID: {session_id}

{'═' * 60}
SUMMARY
{'═' * 60}
- Total Stall Events: {stall_count}
- Recovery Count: {diag.get('recoveryCount', 0)}
- Session Duration: {diag.get('sessionDurationSeconds', 0)} seconds
- Final Token Count: {diag.get('finalTokenCount', 0)}

{'═' * 60}
STALL EVENTS (Detailed)
{'═' * 60}
"""
                            for i, event in enumerate(diag.get('stallEvents', []), 1):
                                diag_content += f"""
Event #{i}:
  Type: {event.get('type')}
  Timestamp: {event.get('timestamp')}
  Seconds Since Last Token: {event.get('secondsSinceLastToken', 'N/A')}
  Token Count at Event: {event.get('tokenCountAtStall', event.get('tokenCountAtRecovery', 'N/A'))}
  Session Elapsed: {event.get('sessionElapsedSeconds', 'N/A')} seconds
  SDK State: {event.get('state', 'N/A')}
  Was In Background: {event.get('wasInBackground', 'N/A')}
  User Agent: {event.get('userAgent', 'N/A')[:100]}...
"""
                            diag_content += f"""
{'═' * 60}
Please share this file when reporting transcription issues.
{'═' * 60}
"""
                            await drive_service.save_transcript(
                                diag_content,
                                diag_file_name,
                                f'Clinic/Transcripts/{patient_name}'
                            )
                            print(f'[DIAGNOSTIC] Diagnostic file saved: {diag_file_name}')
                    except Exception as diag_error:
                        print(f'[DIAGNOSTIC] Failed to save diagnostic file: {diag_error}')
                        # Don't fail the save operation if diagnostic fails

                # ═══════════════════════════════════════════════════════════════════
                # SUMMARIZATION (Runs in BACKGROUND - never blocks transcript response)
                # ═══════════════════════════════════════════════════════════════════
                # Copy data needed for background task before cleanup
                if summarization_service and session.get('transcript_buffer'):
                    buffer_copy = list(session['transcript_buffer'])  # Copy buffer
                    asyncio.create_task(
                        run_summarization_background(
                            drive_service,
                            buffer_copy,
                            patient_name,
                            date_str,
                            time_str,
                            session_id
                        )
                    )
                    print(f'[SUMMARIZATION] Background task started for session {session_id}')

                # Clean up session
                del active_sessions[session_id]

                response = {
                    "status": "success",
                    "sessionId": session_id,
                    "fileInfo": {
                        "id": file_info.get('file_id'),
                        "name": file_info.get('file_name'),
                        "web_view_link": file_info.get('web_view_link'),
                    },
                }

                # Include refreshed tokens if they were updated (either proactively or during retry)
                if refreshed_tokens:
                    response["refreshedTokens"] = refreshed_tokens
                else:
                    # Check if tokens were refreshed during the Drive operation
                    retry_refreshed_tokens = drive_service.get_and_clear_refreshed_tokens()
                    if retry_refreshed_tokens:
                        print('[SERVER] Tokens were refreshed during Drive operation, returning to client')
                        response["refreshedTokens"] = retry_refreshed_tokens

                return response
            except Exception as e:
                print(f"[ERROR] Failed to save transcript: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        else:
            # Auto-save (temporary file)
            try:
                temp_file_name = f".temp_{patient_name}_{date_str}_{time_str}.txt"
                
                if session.get('drive_file_id'):
                    # Update existing temp file
                    file_info = await drive_service.update_file(
                        session['drive_file_id'],
                        transcript_text
                    )
                else:
                    # Create new temp file
                    file_info = await drive_service.save_transcript(
                        transcript_text,
                        temp_file_name,
                        f'Clinic/Transcripts/{patient_name}'
                    )
                    session['drive_file_id'] = file_info.get('file_id')

                response = {
                    "status": "success",
                    "fileInfo": {
                        "id": file_info.get('file_id'),
                        "name": file_info.get('file_name'),
                        "web_view_link": file_info.get('web_view_link'),
                    },
                }

                # Include refreshed tokens if they were updated (either proactively or during retry)
                if refreshed_tokens:
                    response["refreshedTokens"] = refreshed_tokens
                else:
                    # Check if tokens were refreshed during the Drive operation
                    retry_refreshed_tokens = drive_service.get_and_clear_refreshed_tokens()
                    if retry_refreshed_tokens:
                        print('[SERVER] Tokens were refreshed during Drive operation (auto-save), returning to client')
                        response["refreshedTokens"] = retry_refreshed_tokens

                return response
            except Exception as e:
                print(f"[ERROR] Failed to auto-save transcript: {e}")
                # Don't fail the request, just log the error
                return {
                    "status": "error",
                    "message": str(e),
                }
    
    except Exception as e:
        print(f"[ERROR] Error in save_transcript: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sessions/{session_id}/status")
async def get_session_status(session_id: str):
    """
    Get session status for frontend polling.
    Returns status, transcript link, summary links (if available).
    """
    if not firestore_service:
        raise HTTPException(status_code=503, detail="Firestore not enabled")

    try:
        session = await firestore_service.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        transcript = session.get("transcript", {})
        summaries = session.get("summaries", {})
        summarization = session.get("summarization", {})

        response: Dict[str, Any] = {
            "sessionId": session_id,
            "status": session.get("status", "unknown"),
            "transcript": {
                "webViewLink": transcript.get("web_view_link"),
                "fileName": transcript.get("drive_file_name"),
            },
        }

        # Include summary info if available
        detailed_notes = summaries.get("detailed_notes")
        if detailed_notes:
            response["summary"] = {
                "webViewLink": detailed_notes.get("web_view_link"),
                "fileName": detailed_notes.get("drive_file_name"),
            }

        # Include error info if failed
        if session.get("status") == "summarization_failed":
            response["error"] = summarization.get("last_error", "Unknown error")
            response["attempts"] = summarization.get("attempts", 0)

        return response
    except HTTPException:
        raise
    except Exception as e:
        print(f'[ERROR] Failed to get session status: {e}')
        raise HTTPException(status_code=500, detail=str(e))


def ms_to_timestamp(ms, session_start_ms = 0) -> str:
    """Convert milliseconds to MM:SS format relative to session start."""
    if ms is None:
        ms = 0
    # Ensure we're working with integers (timestamps might be floats)
    ms = int(ms) if ms >= 0 else 0
    session_start_ms = int(session_start_ms) if session_start_ms else 0

    relative_ms = max(0, ms - session_start_ms)
    total_seconds = relative_ms // 1000
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    return f"{minutes:02d}:{seconds:02d}"


HEBREW_LETTERS = ['א׳', 'ב׳', 'ג׳', 'ד׳', 'ה׳', 'ו׳', 'ז׳', 'ח׳', 'ט׳', 'י׳']


def _get_speaker_label(index: int) -> str:
    """Get Hebrew speaker label for a given index (0-based)."""
    if index < len(HEBREW_LETTERS):
        return HEBREW_LETTERS[index]
    return str(index + 1)


def format_transcript(buffer: list) -> str:
    """Format transcript buffer into readable text (compact, Hebrew)."""
    output = ''
    current_speaker = None

    # Map speaker numbers to Hebrew letters
    speaker_map = {}
    next_index = 0

    for chunk in buffer:
        speaker_id = chunk.get('speaker', 'Unknown')

        # Assign label to new speakers
        if speaker_id != 'Unknown' and speaker_id not in speaker_map:
            speaker_map[speaker_id] = _get_speaker_label(next_index)
            next_index += 1

        speaker_label = speaker_map.get(speaker_id, speaker_id)

        if speaker_label != current_speaker:
            if current_speaker is not None:
                output += '\n'  # Single newline between speakers
            output += f"דובר {speaker_label}: "
            current_speaker = speaker_label

        # Don't add extra space - tokens already include proper spacing
        output += chunk.get('text', '')

    return output.strip()


def format_transcript_with_timestamps(buffer: list, session_start_ms: int = None, timestamp_interval_ms: int = 300000) -> str:
    """
    Format transcript buffer with timestamps every ~5 minutes (compact, Hebrew).

    Output format:
    [00:00] דובר א׳: Text from speaker A...
    דובר ב׳: Text from speaker B...
    [05:12] דובר א׳: Text continues...

    Args:
        buffer: List of transcript chunks with text, speaker, timestamp
        session_start_ms: Session start time in ms (for relative timestamps)
        timestamp_interval_ms: Minimum interval between timestamps (default 5 minutes = 300000ms)

    Returns:
        Formatted transcript string with sparse inline timestamps
    """
    if not buffer:
        return ""

    # Determine session start from first timestamp if not provided
    if session_start_ms is None:
        timestamps = [chunk.get('timestamp') for chunk in buffer if chunk.get('timestamp')]
        session_start_ms = min(timestamps) if timestamps else 0

    output_lines = []
    current_speaker = None
    current_text = ""  # Accumulate text for current speaker
    current_line_prefix = ""  # Prefix for the current line (timestamp + speaker)
    last_timestamp_ms = None  # Track when we last output a timestamp

    # Map speaker numbers to Hebrew letters
    speaker_map = {}
    next_index = 0

    for chunk in buffer:
        speaker_id = chunk.get('speaker', 'Unknown')
        text = chunk.get('text', '')
        timestamp_ms = chunk.get('timestamp', 0)

        # Skip empty text
        if not text.strip():
            continue

        # Assign label to new speakers
        if speaker_id != 'Unknown' and speaker_id not in speaker_map:
            speaker_map[speaker_id] = _get_speaker_label(next_index)
            next_index += 1

        speaker_label = speaker_map.get(speaker_id, speaker_id)

        # New speaker turn - flush accumulated text and start new line
        if speaker_label != current_speaker:
            # Flush previous speaker's accumulated text
            if current_text:
                output_lines.append(f"{current_line_prefix}{current_text.strip()}")

            # Add timestamp only if: first entry OR enough time has passed since last timestamp
            should_add_timestamp = (
                last_timestamp_ms is None or
                (timestamp_ms - last_timestamp_ms) >= timestamp_interval_ms
            )

            if should_add_timestamp:
                timestamp_str = ms_to_timestamp(timestamp_ms, session_start_ms)
                current_line_prefix = f"[{timestamp_str}] דובר {speaker_label}: "
                last_timestamp_ms = timestamp_ms
            else:
                current_line_prefix = f"דובר {speaker_label}: "

            current_speaker = speaker_label
            current_text = ""  # Reset for new speaker

        # Accumulate text (don't add extra space - tokens already include proper spacing)
        current_text += text

    # Flush final speaker's text
    if current_text:
        output_lines.append(f"{current_line_prefix}{current_text.strip()}")

    return '\n'.join(output_lines)


def format_transcript_with_header(buffer: list, patient_name: str, start_time=None, end_time=None, frequent_timestamps: bool = False) -> str:
    """
    Format transcript with Hebrew header including patient name, date, and duration.

    Args:
        buffer: List of transcript chunks
        patient_name: Patient name for header
        start_time: Session start time (ms or datetime)
        end_time: Session end time (ms or datetime)
        frequent_timestamps: If True, timestamps every ~1.5 min; otherwise every ~5 min
    """
    from datetime import datetime

    # Calculate start/end from token timestamps (most accurate)
    session_start_ms = None
    if buffer:
        token_timestamps = [chunk.get('timestamp') for chunk in buffer if chunk.get('timestamp')]
        if token_timestamps:
            # Use token timestamps as source of truth for duration
            session_start_ms = min(token_timestamps)
            start_time = session_start_ms
            end_time = max(token_timestamps)

    # Fallback: if still no start_time, use current time (shouldn't happen)
    if start_time is None:
        start_time = datetime.now().timestamp() * 1000

    # Ensure start_time is datetime object for header formatting
    start_datetime = start_time
    if isinstance(start_datetime, (int, float)):
        start_datetime = datetime.fromtimestamp(start_datetime / 1000)  # Convert from milliseconds

    # Calculate end time and duration
    end_datetime = end_time
    if end_datetime is None:
        end_datetime = datetime.now()
    elif isinstance(end_datetime, (int, float)):
        end_datetime = datetime.fromtimestamp(end_datetime / 1000)

    duration_seconds = (end_datetime - start_datetime).total_seconds()
    duration_minutes = int(duration_seconds / 60)

    # Create Hebrew header
    header = f"""{'═' * 50}
        תמלול פגישה טיפולית
{'═' * 50}

מטופל/ת: {patient_name}
תאריך: {start_datetime.strftime('%d/%m/%Y')}
שעה: {start_datetime.strftime('%H:%M')} - {end_datetime.strftime('%H:%M')}
משך: {duration_minutes} דקות

{'═' * 50}

"""

    # Format transcript body — always with timestamps, frequency varies
    timestamp_interval = 90_000 if frequent_timestamps else 300_000  # 1.5 min or 5 min
    body = format_transcript_with_timestamps(buffer, session_start_ms, timestamp_interval)

    return header + body


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time transcription."""
    # Accept the WebSocket connection
    await websocket.accept()
    print('[DEBUG] New WebSocket connection established')
    print(f'[DEBUG] WebSocket client: {websocket.client}')
    print(f'[DEBUG] WebSocket headers: {dict(websocket.headers)}')
    
    session_id = None
    transcription_session = None
    transcript_buffer = []
    drive_file_id = None
    last_save_time = time.time() * 1000
    auto_save_task = None
    
    try:
        while True:
            data = await websocket.receive_text()
            print(f'[DEBUG] Received WebSocket message: {data[:100]}...')
            message = json.loads(data)
            print(f'[DEBUG] Message type: {message.get("type")}')
            
            if message['type'] == 'start_session':
                print('[DEBUG] Processing start_session message')
                # Start session
                session_data = message
                session_id = session_data.get('sessionId')
                patient_name = session_data.get('patientName')
                access_token = session_data.get('accessToken')
                refresh_token = session_data.get('refreshToken')
                
                if not session_id or not patient_name or not access_token:
                    await websocket.send_text(json.dumps({
                        'type': 'error',
                        'message': 'Missing required fields: sessionId, patientName, accessToken'
                    }))
                    continue
                
                # Create user-specific DriveService instance
                user_drive_service = create_drive_service_with_tokens(access_token, refresh_token)
                
                # Generate file name
                from datetime import datetime
                now = datetime.now()
                date_str = now.strftime('%Y-%m-%d')
                time_str = now.strftime('%H-%M')
                file_name = f"{patient_name}_{date_str}_{time_str}.txt"
                
                # Start transcription session
                async def on_transcript(chunk: Dict[str, Any]):
                    """Handle transcript chunk."""
                    text = chunk.get('text', '')
                    speaker = chunk.get('speaker', 'Unknown')
                    is_final = chunk.get('is_final', False)
                    
                    # Print transcript in a readable format
                    print(f'[TRANSCRIPT] {"[FINAL]" if is_final else "[PARTIAL]"} {speaker}: {text}')
                    print(f'[DEBUG] Full transcript chunk: {chunk}')
                    
                    transcript_buffer.append(chunk)
                    
                    # Send to frontend
                    message = json.dumps({
                        'type': 'transcript',
                        **chunk
                    })
                    print(f'[DEBUG] Sending transcript to frontend: {message[:200]}...')
                    await websocket.send_text(message)
                
                async def on_error(error: Exception):
                    """Handle transcription error."""
                    print(f'[ERROR] Transcription error: {error}')
                    import traceback
                    traceback.print_exc()
                    await websocket.send_text(json.dumps({
                        'type': 'error',
                        'message': f'Transcription error: {str(error)}'
                    }))
                
                print(f'[DEBUG] Starting transcription session with provider: {transcription_service.get_provider_info()["name"]}')
                try:
                    transcription_session = await transcription_service.start_session(
                        {},
                        on_transcript,
                        on_error
                    )
                    print(f'[DEBUG] Transcription session started: {transcription_session}')
                except Exception as e:
                    print(f'[ERROR] Failed to start transcription session: {e}')
                    import traceback
                    traceback.print_exc()
                    await websocket.send_text(json.dumps({
                        'type': 'error',
                        'message': f'Failed to start session: {str(e)}'
                    }))
                    continue
                
                # Start auto-save task
                async def auto_save_loop():
                    """Auto-save to Drive every 1 minute."""
                    nonlocal drive_file_id, last_save_time
                    while True:
                        await asyncio.sleep(60)  # 1 minute
                        if transcript_buffer:
                            try:
                                # Format with header for auto-save
                                content = format_transcript_with_header(
                                    transcript_buffer,
                                    patient_name,
                                    start_time
                                )
                                temp_file_name = f"{config.autosave.temp_file_prefix}{file_name}"

                                if drive_file_id:
                                    await user_drive_service.update_file(drive_file_id, content)
                                else:
                                    file_info = await user_drive_service.save_transcript(
                                        content,
                                        temp_file_name,
                                        f'Clinic/Transcripts/{patient_name}'
                                    )
                                    drive_file_id = file_info['file_id']
                            except Exception as e:
                                print(f'Auto-save error: {e}')
                
                auto_save_task = asyncio.create_task(auto_save_loop())
                
                # Store session with user's DriveService
                active_sessions[session_id] = {
                    'websocket': websocket,
                    'transcription_session': transcription_session,
                    'transcript_buffer': transcript_buffer,
                    'drive_file_id': drive_file_id,
                    'patient_name': patient_name,
                    'file_name': file_name,
                    'start_time': time.time() * 1000,  # Store as milliseconds timestamp for consistency
                    'drive_service': user_drive_service,  # Store user-specific drive service
                    'access_token': access_token,
                    'refresh_token': refresh_token,
                }
                
                await websocket.send_text(json.dumps({
                    'type': 'session_started',
                    'sessionId': session_id
                }))
            
            elif message['type'] == 'audio_chunk':
                # Handle audio chunk
                print(f'[DEBUG] Received audio chunk, size: {len(message.get("audio", ""))}')
                print(f'[DEBUG] transcription_session exists: {transcription_session is not None}')
                if not transcription_session:
                    print('[ERROR] No transcription session - start_session may not have been processed')
                    await websocket.send_text(json.dumps({
                        'type': 'error',
                        'message': 'Session not active - no transcription session. Did start_session complete?'
                    }))
                    continue
                
                is_active_check = transcription_session.get('is_active')
                print(f'[DEBUG] is_active function exists: {is_active_check is not None}')
                if is_active_check:
                    is_active = is_active_check()
                    print(f'[DEBUG] is_active() returned: {is_active}')
                else:
                    is_active = False
                    print('[ERROR] is_active function not found in session')
                
                if not is_active:
                    print('[WARNING] Session marked inactive, but continuing to accept audio chunks')
                    print('[WARNING] This may happen if Soniox timed out - audio will be buffered')
                    # Don't reject audio chunks - they might be processed later
                    # Just log a warning instead of sending error
                    # continue  # Commented out - allow audio to be sent even if session marked inactive
                
                # Convert base64 audio to bytes
                import base64
                try:
                    audio_bytes = base64.b64decode(message['audio'])
                    print(f'[DEBUG] Sending {len(audio_bytes)} bytes to transcription provider')
                    await transcription_session['send_audio'](audio_bytes)
                except Exception as e:
                    print(f'[ERROR] Error processing audio chunk: {e}')
                    import traceback
                    traceback.print_exc()
            
            elif message['type'] == 'stop_session':
                # Stop session
                if not transcription_session:
                    await websocket.send_text(json.dumps({
                        'type': 'error',
                        'message': 'No active session'
                    }))
                    continue
                
                # Stop transcription
                await transcription_session['stop']()
                
                # Cancel auto-save task
                if auto_save_task:
                    auto_save_task.cancel()
                
                # Final save to Drive
                try:
                    session = active_sessions.get(session_id)
                    final_file_name = session['file_name'] if session else f"session_{session_id}.txt"

                    # Get user's drive service from session
                    session_drive_service = session.get('drive_service') if session else None
                    if not session_drive_service:
                        raise ValueError("No drive service found for session")

                    # Format transcript with header
                    patient_name = session.get('patient_name', 'Unknown') if session else 'Unknown'
                    start_time = session.get('start_time') if session else None
                    content = format_transcript_with_header(
                        transcript_buffer,
                        patient_name,
                        start_time
                    )

                    if drive_file_id:
                        # Create new file with final name
                        file_info = await session_drive_service.save_transcript(
                            content,
                            final_file_name,
                            f'Clinic/Transcripts/{patient_name}'
                        )
                        # Delete temp file
                        await session_drive_service.delete_file(drive_file_id)
                    else:
                        file_info = await session_drive_service.save_transcript(
                            content,
                            final_file_name,
                            f'Clinic/Transcripts/{patient_name}'
                        )
                    
                    # Send email notification
                    if session:
                        from datetime import datetime
                        now = datetime.now()
                        await email_service.send_transcript_notification(
                            'user@example.com',  # Get from session or token
                            {
                                'patient_name': session['patient_name'],
                                'date': now.strftime('%Y-%m-%d'),
                                'time': now.strftime('%H:%M'),
                            },
                            file_info['web_view_link']
                        )
                    
                    # Map Python snake_case to JavaScript camelCase for frontend
                    file_info_frontend = {
                        'fileId': file_info.get('file_id'),
                        'fileName': file_info.get('file_name'),
                        'webViewLink': file_info.get('web_view_link'),  # Map web_view_link to webViewLink
                        'webContentLink': file_info.get('web_content_link'),
                    }
                    
                    await websocket.send_text(json.dumps({
                        'type': 'session_complete',
                        'fileInfo': file_info_frontend
                    }))
                except Exception as e:
                    print(f'Final save error: {e}')
                    await websocket.send_text(json.dumps({
                        'type': 'error',
                        'message': f'Failed to save transcript: {str(e)}'
                    }))
                
                # Clean up
                if session_id:
                    active_sessions.pop(session_id, None)
                transcript_buffer = []
                drive_file_id = None
                break
    
    except WebSocketDisconnect:
        print('[DEBUG] WebSocket connection closed/disconnected')
        if session_id:
            active_sessions.pop(session_id, None)
        if transcription_session:
            try:
                await transcription_session['stop']()
            except:
                pass
        if auto_save_task:
            auto_save_task.cancel()
    except Exception as e:
        print(f'[ERROR] WebSocket error: {e}')
        import traceback
        traceback.print_exc()
        if session_id:
            active_sessions.pop(session_id, None)


# REST API Routes

@app.get("/api/auth/google/url")
async def get_google_auth_url():
    """Get Google OAuth URL."""
    service = DriveService()  # Temporary instance just for OAuth flow
    auth_url = service.get_auth_url()
    return {"authUrl": auth_url}


@app.get("/auth/google/callback")
async def google_oauth_callback(code: str):
    """OAuth callback endpoint."""
    import os
    try:
        service = DriveService()  # Temporary instance just for OAuth flow
        tokens = await service.get_tokens(code)

        # Redirect to frontend with tokens
        frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')
        redirect_url = (
            f"{frontend_url}/auth/callback?"
            f"access_token={tokens['access_token']}&"
            f"refresh_token={tokens.get('refresh_token', '')}"
        )

        print(f'[OAuth] FRONTEND_URL env var: {os.getenv("FRONTEND_URL")}')
        print(f'[OAuth] frontend_url variable: {frontend_url}')
        print(f'[OAuth] Full redirect_url: {redirect_url}')
        print(f'[OAuth] redirect_url starts with http: {redirect_url.startswith("http")}')

        # Use 302 status code for better browser compatibility with absolute URLs
        response = RedirectResponse(url=redirect_url, status_code=302)
        print(f'[OAuth] Response headers: {response.headers}')
        return response
    except Exception as e:
        print(f'OAuth callback error: {e}')
        raise HTTPException(status_code=500, detail="Authentication failed")


@app.post("/api/auth/google/tokens")
async def exchange_tokens(request: Request):
    """Exchange code for tokens (alternative API endpoint)."""
    try:
        body = await request.json()
        code = body.get('code')
        if not code:
            raise HTTPException(status_code=400, detail="Authorization code required")
        
        tokens = await drive_service.get_tokens(code)
        return {"tokens": tokens}
    except Exception as e:
        print(f'Token exchange error: {e}')
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/transcription/provider")
async def get_provider_info():
    """Get provider information."""
    info = transcription_service.get_provider_info()
    return info


@app.post("/api/admin/cleanup-temp-files")
async def cleanup_temp_files(access_token: str, refresh_token: str):
    """
    Cleanup temp files (requires admin user tokens).
    TODO: Implement proper admin authentication.
    """
    try:
        # Create drive service with provided admin tokens
        admin_drive_service = create_drive_service_with_tokens(access_token, refresh_token)
        count = await admin_drive_service.cleanup_temp_files(
            'Clinic/Transcripts',
            config.autosave.temp_file_retention_hours
        )
        return {"deleted": count}
    except Exception as e:
        print(f'Cleanup error: {e}')
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "provider": transcription_service.get_provider_info()["name"]
    }


if __name__ == "__main__":
    import uvicorn
    import os
    
    port = config.server.port
    print(f"Server running on port {port}")
    print(f"Transcription provider: {transcription_service.get_provider_info()['name']}")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=config.server.node_env == "development"
    )

