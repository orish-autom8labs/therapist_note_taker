# Soniox WebSocket Endpoint Fix

## Problem
The Soniox provider was getting HTTP 404 when trying to connect to Soniox's WebSocket API.

## Root Cause
1. **Wrong endpoint URL**: Was using `wss://api.soniox.com/v1/realtime` (doesn't exist)
2. **Wrong authentication method**: Was trying to use Bearer token in headers or query parameter

## Solution
Updated the Soniox provider to use the correct endpoint and authentication:

### Correct Endpoint
```
wss://stt-rt.soniox.com/transcribe-websocket
```

### Correct Authentication
- **No headers or query parameters** for authentication
- **API key goes in the initial configuration JSON message** sent after connecting
- The config message must include:
  - `api_key` (required)
  - `model` (required) - e.g., `"stt-rt-preview"`
  - `audio_format` (required) - e.g., `"auto"`

## What Changed

1. **Updated WebSocket URI**:
   ```python
   # OLD (wrong):
   self.websocket_uri = "wss://api.soniox.com/v1/realtime"
   
   # NEW (correct):
   self.websocket_uri = "wss://stt-rt.soniox.com/transcribe-websocket"
   ```

2. **Updated Connection Method**:
   ```python
   # OLD (wrong):
   headers = {'Authorization': f'Bearer {self.api_key}'}
   self.websocket = await websockets.connect(uri, extra_headers=headers)
   
   # NEW (correct):
   self.websocket = await websockets.connect(self.websocket_uri)
   # Then send config message with API key
   ```

3. **Updated Configuration Message**:
   ```python
   config_message = {
       'api_key': self.api_key,  # Required: in message, not headers
       'model': 'stt-rt-preview',  # Required: model name
       'audio_format': 'auto',
       'language_hints': [language],
       'enable_speaker_diarization': True,
   }
   ```

## Next Steps

1. **Restart the server** to pick up the changes:
   ```bash
   cd server
   # Stop current server (Ctrl+C)
   source venv/bin/activate
   python run.py
   ```

2. **Test the connection**:
   - Start a session from the browser
   - Check server logs - you should see:
     ```
     [SONIOX] Connecting to wss://stt-rt.soniox.com/transcribe-websocket
     [SONIOX] WebSocket connected
     [SONIOX] Sent config: {...}
     ```

3. **If you still get errors**:
   - Verify your `SONIOX_API_KEY` is correct in `server/.env`
   - Check Soniox console to ensure your API key is valid
   - Check server logs for any error messages

## Reference
- Soniox WebSocket API Docs: https://soniox.com/docs/stt/api-reference/websocket-api
- Endpoint: `wss://stt-rt.soniox.com/transcribe-websocket`




