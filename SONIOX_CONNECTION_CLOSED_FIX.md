# Soniox Connection Closed Immediately - Troubleshooting

## Problem
The Soniox WebSocket connection is established but immediately closed with code 1000 (normal closure) when trying to send audio. This suggests Soniox is rejecting the connection after receiving the configuration.

## What I Fixed

1. **Added initial response handling**: Now we check the first message from Soniox to see if it's an error
2. **Better error detection**: Check for error messages in the response
3. **Improved connection state checking**: Verify connection is open before sending audio
4. **Better logging**: More detailed error messages to help diagnose

## Common Causes

### 1. Invalid API Key
**Check**: Verify your `SONIOX_API_KEY` in `server/.env` is correct
- Go to [Soniox Console](https://soniox.com/console)
- Verify the API key matches exactly
- Check if the key has expired or been revoked

### 2. Wrong Model Name
**Check**: The model `stt-rt-preview` might not be available for your account
- Try: `stt-rt` or check Soniox docs for available models
- Some accounts might have different model names

### 3. Configuration Format Issues
**Check**: The config message might be missing required fields or have wrong format
- Current config includes: `api_key`, `model`, `audio_format`, `language_hints`, `enable_speaker_diarization`
- Soniox might require additional fields or different format

### 4. Account/Plan Limitations
**Check**: Your Soniox account might not have access to real-time transcription
- Verify your plan includes WebSocket/real-time transcription
- Check for usage limits or restrictions

## Debugging Steps

1. **Check Server Logs**:
   After restarting, look for:
   ```
   [SONIOX] Connecting to wss://stt-rt.soniox.com/transcribe-websocket
   [SONIOX] WebSocket connected
   [SONIOX] Sent config: {...}
   [SONIOX] First response: ...
   ```

2. **Look for Error Messages**:
   - If you see `[SONIOX] Configuration error: ...`, that's the problem
   - The first response will show what Soniox is complaining about

3. **Test API Key**:
   ```bash
   # Verify the key is set
   cd server
   cat .env | grep SONIOX_API_KEY
   ```

4. **Try Different Model**:
   Edit `server/src/providers/soniox_provider.py` line 63:
   ```python
   'model': 'stt-rt',  # Try this instead of 'stt-rt-preview'
   ```

## Next Steps

1. **Restart the server** to pick up the changes:
   ```bash
   cd server
   # Stop server (Ctrl+C)
   source venv/bin/activate
   python run.py
   ```

2. **Start a session** and check the logs for:
   - `[SONIOX] First response: ...` - This will show what Soniox is saying
   - Any error messages about configuration

3. **If you see an error in the first response**, share it and I can help fix the config

## Alternative: Use Mock Provider for Testing

If Soniox continues to have issues, you can test with the mock provider:
```bash
# In server/.env:
TRANSCRIPTION_PROVIDER=mock
```

This will let you test the rest of the system while we debug Soniox.

## Reference
- Soniox WebSocket API: https://soniox.com/docs/stt/api-reference/websocket-api
- Soniox Console: https://soniox.com/console




