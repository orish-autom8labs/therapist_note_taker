# Debugging Steps

I've added extensive debugging to help identify the issue. Follow these steps:

## Step 1: Check Server Logs

Look at the terminal where you're running `python run.py`. You should see:
- `[DEBUG] New WebSocket connection established`
- `[DEBUG] Received WebSocket message: ...`
- `[DEBUG] Processing start_session message`
- `[DEBUG] Starting transcription session with provider: Mock Provider (Testing)`
- `[DEBUG] Transcription session started: ...`

**If you don't see these messages:**
- WebSocket connection isn't working
- Check if server is running on port 3001
- Check browser console for WebSocket errors

## Step 2: Check Browser Console

1. Open browser DevTools (F12 or Cmd+Option+I)
2. Go to "Console" tab
3. Look for messages starting with `[DEBUG]`:
   - `[DEBUG] Starting session...`
   - `[DEBUG] Requesting microphone access...`
   - `[DEBUG] Microphone access granted...`
   - `[DEBUG] Connecting to WebSocket: ws://localhost:3001/ws`
   - `[DEBUG] WebSocket connected...`
   - `[DEBUG] Received transcript chunk: ...`

**If you see errors (red text):**
- Copy the error message
- Check what it says

## Step 3: Check Network Tab

1. In DevTools, go to "Network" tab
2. Filter by "WS" (WebSocket)
3. You should see a connection to `ws://localhost:3001/ws`
4. Click on it to see messages

## Step 4: Common Issues

### Issue: No WebSocket connection
**Symptoms:** No `[DEBUG] WebSocket connected` message
**Fix:** 
- Check server is running: `lsof -ti:3001`
- Check CORS settings in `main.py`
- Check firewall/antivirus blocking WebSocket

### Issue: WebSocket connects but no messages
**Symptoms:** Connection established but no transcript
**Fix:**
- Check server logs for errors
- Check if `start_session` message is received
- Check if transcription session is created

### Issue: Audio chunks not being sent
**Symptoms:** No `[DEBUG] Audio chunk available` messages
**Fix:**
- Check microphone permissions
- Check MediaRecorder is working
- Check browser console for errors

## What to Share

If it's still not working, share:
1. **Server logs** - Copy the last 20-30 lines from terminal
2. **Browser console** - Copy all `[DEBUG]` and error messages
3. **Network tab** - Screenshot of WebSocket connection

This will help identify exactly where it's failing.




