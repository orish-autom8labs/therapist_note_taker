# Soniox API Integration Setup Guide

This guide explains how to set up and use the Soniox transcription provider in your note-taking app.

## Prerequisites

1. **Soniox Account**: Sign up at [https://soniox.com](https://soniox.com)
2. **API Key**: Obtain your API key from the Soniox Console

## Installation

1. **Install Dependencies**:
   ```bash
   cd server
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   pip install -r requirements.txt
   ```

   This will install:
   - `soniox` (if available) - Official Soniox Python SDK
   - `websockets` - For WebSocket connections
   - `aiohttp` - For REST API calls (batch processing)

## Configuration

1. **Set API Key in `.env`**:
   ```bash
   cd server
   # Edit .env file
   SONIOX_API_KEY=your_soniox_api_key_here
   TRANSCRIPTION_PROVIDER=soniox
   ```

2. **Restart the Server**:
   After changing `.env`, always restart the server:
   ```bash
   # Stop the current server (Ctrl+C)
   # Then restart:
   python run.py
   ```

## How It Works

The Soniox provider uses the **WebSocket API** for real-time streaming transcription:

1. **Connection**: Establishes a WebSocket connection to `wss://api.soniox.com/v1/realtime`
2. **Authentication**: Uses Bearer token authentication (API key in Authorization header)
3. **Configuration**: Sends initial config message with:
   - Audio format: `auto` (detects webm/opus from browser)
   - Language hints: Hebrew (`he-IL`) by default
   - Speaker diarization: Enabled (2 speakers)
4. **Streaming**: Sends binary audio chunks as they arrive from the browser
5. **Responses**: Receives JSON messages with transcription tokens
6. **Processing**: Groups tokens by speaker and sends to your app

## Features

- ✅ **Real-time Streaming**: Low-latency transcription as you speak
- ✅ **Hebrew Support**: Optimized for Hebrew (`he-IL`) language
- ✅ **Speaker Diarization**: Identifies Speaker 1 and Speaker 2
- ✅ **Auto-format Detection**: Automatically detects audio format from browser
- ✅ **Error Handling**: Robust error handling and reconnection logic

## Testing

1. **Start the Server**:
   ```bash
   cd server
   source venv/bin/activate
   python run.py
   ```

2. **Start the Frontend**:
   ```bash
   cd client
   npm start
   ```

3. **Test Transcription**:
   - Open `http://localhost:3000`
   - Sign in with Google
   - Start a session
   - Speak into your microphone
   - You should see transcripts appearing in real-time

## Troubleshooting

### "Soniox API key is required"
- **Solution**: Make sure `SONIOX_API_KEY` is set in `server/.env`
- **Check**: Run `cat server/.env | grep SONIOX_API_KEY` to verify

### "Connection failed" or "Authentication error"
- **Solution**: Verify your API key is correct in the Soniox Console
- **Check**: The API key should start with your project identifier
- **Note**: Some Soniox plans may have rate limits or require specific authentication

### "No transcription appearing"
- **Check Server Logs**: Look for `[SONIOX]` messages in the server console
- **Check Browser Console**: Look for WebSocket connection errors
- **Verify Provider**: Ensure `TRANSCRIPTION_PROVIDER=soniox` in `.env`
- **Restart Server**: Always restart after changing `.env`

### WebSocket Connection Issues
- **Firewall**: Ensure port 443 (HTTPS/WSS) is not blocked
- **Network**: Check your internet connection
- **API Status**: Verify Soniox API is operational

## Authentication Methods

The implementation tries two authentication methods:

1. **Bearer Token in Headers** (primary):
   ```python
   headers = {'Authorization': f'Bearer {api_key}'}
   ```

2. **Query Parameter** (fallback):
   ```
   wss://api.soniox.com/v1/realtime?api_key=your_key
   ```

If you encounter authentication errors, check the Soniox documentation for the latest authentication method.

## Response Format

Soniox sends responses in this format:
```json
{
  "tokens": [
    {"text": "Hello", "is_final": true, "speaker": 0},
    {"text": " ", "is_final": true, "speaker": 0},
    {"text": "world", "is_final": false, "speaker": 1}
  ],
  "audio_final_proc_ms": 1200,
  "audio_total_proc_ms": 1500
}
```

The provider processes these tokens and groups them by speaker for display in your app.

## Batch Processing

For batch transcription (not used in real-time mode), the provider uses the REST API:
- Endpoint: `https://api.soniox.com/v1/transcribe_file`
- Method: POST
- Headers: `Authorization: Bearer {api_key}`
- Body: Binary audio data

## Next Steps

1. **Test with Hebrew**: Try speaking Hebrew to verify accuracy
2. **Monitor Costs**: Check your Soniox usage dashboard
3. **Adjust Settings**: Modify language hints or speaker count in `soniox_provider.py` if needed
4. **Error Monitoring**: Watch server logs for any issues

## Support

- **Soniox Documentation**: [https://soniox.com/docs](https://soniox.com/docs)
- **Soniox Console**: [https://soniox.com/console](https://soniox.com/console)
- **API Reference**: [https://soniox.com/docs/stt/api-reference](https://soniox.com/docs/stt/api-reference)




