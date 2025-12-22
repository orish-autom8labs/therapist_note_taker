# Troubleshooting: "Session not active" Error

## The Problem

You're seeing `[ERROR] Session not active` which means:
- Audio chunks are arriving ✅
- But transcription session was never created ❌

## Root Cause

The `start_session` message is either:
1. Not being sent from frontend
2. Not being received by backend
3. Failing to create the session

## Debugging Steps

### Step 1: Check Browser Console

Look for these messages in order:
1. `[DEBUG] Starting session...`
2. `[DEBUG] Requesting microphone access...`
3. `[DEBUG] Microphone access granted...`
4. `[DEBUG] Connecting to WebSocket: ws://localhost:3001/ws`
5. `[DEBUG] WebSocket connected, sending start_session`
6. `[DEBUG] Received WebSocket message: {"type":"session_started"...}`
7. `[DEBUG] Session started, resolving promise`
8. `[DEBUG] Transcription session created...`

**If you don't see #5 or #6:**
- WebSocket connection failed
- `start_session` message wasn't sent

**If you see #6 but not #7:**
- Backend received message but didn't respond
- Check server logs for errors

### Step 2: Check Server Logs

Look for these messages in order:
1. `[DEBUG] New WebSocket connection established`
2. `[DEBUG] Received WebSocket message: {"type":"start_session"...}`
3. `[DEBUG] Processing start_session message`
4. `[DEBUG] Starting transcription session with provider: Mock Provider (Testing)`
5. `[MOCK] start_streaming_session called`
6. `[DEBUG] Transcription session started: ...`
7. `[DEBUG] Received transcript chunk: ...`

**If you don't see #2:**
- `start_session` message never arrived
- WebSocket connection issue

**If you see #2 but not #4:**
- Session creation failed
- Check for error messages

### Step 3: Common Issues

#### Issue: WebSocket Connects But No Messages
**Check:**
- CORS settings in `main.py`
- WebSocket URL: Should be `ws://localhost:3001/ws`
- Browser console for WebSocket errors

#### Issue: start_session Sent But No Response
**Check:**
- Server logs for errors during session creation
- Check if provider is correctly loaded
- Check if OAuth tokens are valid

#### Issue: Connection Closes Immediately
**Check:**
- Server logs for `connection closed` messages
- Browser console for close events
- Network tab for WebSocket status

## Quick Test

Run this in browser console to test WebSocket:
```javascript
const ws = new WebSocket('ws://localhost:3001/ws');
ws.onopen = () => {
  console.log('✅ Connected');
  ws.send(JSON.stringify({
    type: 'start_session',
    sessionId: 'test123',
    patientName: 'Test Patient',
    accessToken: 'test_token',
    refreshToken: 'test_refresh'
  }));
};
ws.onmessage = (e) => console.log('📨 Received:', e.data);
ws.onerror = (e) => console.error('❌ Error:', e);
```

You should see a response with `session_started` or an error message.

## Next Steps

1. **Check browser console** - Look for the debug messages above
2. **Check server logs** - Look for the debug messages above  
3. **Share both outputs** - This will help identify exactly where it's failing




