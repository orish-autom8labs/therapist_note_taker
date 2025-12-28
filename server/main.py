"""
Main FastAPI server with WebSocket support for real-time transcription.
"""
import asyncio
import json
import os
import time
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

app = FastAPI(title="Note Taker API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "https://note-taker-frontend-1049928242674.us-central1.run.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Services
transcription_service = TranscriptionService()
email_service = EmailService()

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
        
        # Format transcript
        transcript_text = format_transcript(session['transcript_buffer'])
        
        # Generate file name
        from datetime import datetime
        now = datetime.now()
        date_str = now.strftime('%Y-%m-%d')
        time_str = now.strftime('%H-%M-%S')
        patient_name = session.get('patient_name', 'Unknown')
        
        if transcript_update.is_final:
            # Final save
            try:
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
                        'Clinic/Transcripts'
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
                        'Clinic/Transcripts'
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

                # Clean up session
                del active_sessions[session_id]

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
                        'Clinic/Transcripts'
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


def format_transcript(buffer: list) -> str:
    """Format transcript buffer into readable text."""
    output = ''
    current_speaker = None

    for chunk in buffer:
        if chunk.get('speaker') and chunk['speaker'] != current_speaker:
            if current_speaker is not None:
                output += '\n\n'
            output += f"{chunk.get('speaker', 'Unknown')}:\n"
            current_speaker = chunk['speaker']
        # Don't add extra space - tokens already include proper spacing
        output += chunk.get('text', '')

    return output.strip()


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
                                content = format_transcript(transcript_buffer)
                                temp_file_name = f"{config.autosave.temp_file_prefix}{file_name}"

                                if drive_file_id:
                                    await user_drive_service.update_file(drive_file_id, content)
                                else:
                                    file_info = await user_drive_service.save_transcript(
                                        content,
                                        temp_file_name,
                                        'Clinic/Transcripts'
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
                    'start_time': datetime.now(),
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
                    content = format_transcript(transcript_buffer)
                    session = active_sessions.get(session_id)
                    final_file_name = session['file_name'] if session else f"session_{session_id}.txt"

                    # Get user's drive service from session
                    session_drive_service = session.get('drive_service') if session else None
                    if not session_drive_service:
                        raise ValueError("No drive service found for session")

                    if drive_file_id:
                        # Create new file with final name
                        file_info = await session_drive_service.save_transcript(
                            content,
                            final_file_name,
                            'Clinic/Transcripts'
                        )
                        # Delete temp file
                        await session_drive_service.delete_file(drive_file_id)
                    else:
                        file_info = await session_drive_service.save_transcript(
                            content,
                            final_file_name,
                            'Clinic/Transcripts'
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

