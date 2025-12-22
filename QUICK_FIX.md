# Quick Fix: Use Mock Provider for Testing

## The Problem
Soniox provider is not implemented yet - it's just a template. That's why transcription isn't working.

## Quick Solution: Use Mock Provider

### Step 1: Change Provider in `.env`
Edit `server/.env` and change:
```bash
TRANSCRIPTION_PROVIDER=soniox
```
to:
```bash
TRANSCRIPTION_PROVIDER=mock
```

### Step 2: Restart Server
```bash
# Stop current server (Ctrl+C)
cd server
source venv/bin/activate
python run.py
```

### Step 3: Test Again
1. Start a session
2. You'll see **fake Hebrew transcripts** appearing automatically
3. This tests the full UI flow
4. "Stop & Save" will work

## What Mock Provider Does
- Generates fake Hebrew transcript text
- Simulates speaker diarization (Speaker 1, Speaker 2)
- Tests the complete flow without needing real API

## Next Steps
Once UI flow works, you can:
1. Implement Soniox API integration
2. Switch back to `TRANSCRIPTION_PROVIDER=soniox`
3. Or use Google provider (which is fully implemented)

## Debugging Real Provider

If you want to debug the real Soniox integration:

1. **Check browser console** (F12 → Console):
   - Look for WebSocket errors
   - Look for transcription errors

2. **Check server logs** (terminal running `python run.py`):
   - Look for errors when audio is sent
   - Look for Soniox API errors

3. **Check WebSocket connection**:
   - In browser console, run:
   ```javascript
   const ws = new WebSocket('ws://localhost:3001/ws');
   ws.onopen = () => console.log('Connected');
   ws.onerror = (e) => console.error('Error:', e);
   ```

4. **Implement Soniox API**:
   - Check Soniox documentation
   - Implement `send_audio()` in `soniox_provider.py`
   - Test with real API calls




