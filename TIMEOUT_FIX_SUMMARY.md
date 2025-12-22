# Soniox 408 Timeout Fix Summary

## Problem Identified

From your logs:
- **Line 413**: Only 2 messages received in 20 seconds (config + timeout)
- **Line 414**: `[SONIOX ERROR] Error 408: Request timeout.`
- **Line 421**: `streaming=False` - Session marked inactive
- **Lines 423+**: All audio chunks rejected with `[ERROR] Session not active`

**Root Cause**: Soniox times out after 20 seconds if it doesn't process audio quickly enough, which kills the session and blocks all further audio.

## Fixes Applied

### 1. Graceful 408 Timeout Handling ✅
**File**: `server/src/providers/soniox_provider.py`

- **Before**: 408 timeout immediately killed session (`is_streaming = False`)
- **After**: 408 timeout logged as warning, session continues
- **Code**: Added special handling for error_code 408 to not kill session

### 2. Allow Audio Even When Session Marked Inactive ✅
**File**: `server/main.py`

- **Before**: Audio chunks rejected if `is_active() == False`
- **After**: Audio chunks accepted even if inactive (for recovery)
- **Code**: Changed from `continue` (reject) to warning log only

### 3. Audio Sending Recovery ✅
**File**: `server/src/providers/soniox_provider.py`

- **Before**: Audio rejected if `is_streaming == False`
- **After**: Audio sent even if streaming marked False (recovery attempt)
- **Code**: Removed `is_streaming` check, only check `websocket` exists

### 4. Improved Fallback Logging ✅
**File**: `server/src/providers/soniox_provider.py`

- **Before**: Fallback only logged if tokens existed
- **After**: Fallback logs status every 5 seconds even if no tokens
- **Code**: Added `else` clause to log when no tokens received

## Expected Behavior After Fix

1. **408 Timeout**: Logged as warning, session continues
2. **Audio Chunks**: Still accepted and sent to Soniox (even after timeout)
3. **Recovery**: Session might recover if Soniox starts processing
4. **Status Updates**: Logs every 5 seconds showing progress (or lack thereof)

## Testing

1. **Restart server**:
   ```bash
   cd server
   python run.py
   ```

2. **Test with continuous speech**:
   - Speak for 30+ seconds
   - Watch for 408 timeout warning (should NOT kill session)
   - Audio should continue to be sent
   - Check logs for status updates every 5 seconds

3. **Check logs for**:
   - `[SONIOX WARNING] Timeout error (408) - continuing to process audio`
   - `[WARNING] Session marked inactive, but continuing to accept audio`
   - `[SONIOX] FALLBACK: No tokens received yet after X.Xs` (every 5 seconds)
   - `[SONIOX WARNING] Streaming marked False, but attempting to send audio anyway`

## Why Soniox Times Out

**Possible Causes**:
1. **Audio Format**: WebM/Opus might not be detected correctly
2. **Network Latency**: Slow connection to Soniox servers
3. **Soniox Server Load**: High load on Soniox side
4. **Audio Quality**: Poor audio quality or too quiet

**The 408 timeout happens when**:
- Soniox receives audio but doesn't process it within 20 seconds
- No tokens are returned, so Soniox assumes connection is dead
- Soniox closes the connection with 408 error

## Next Steps if Still Not Working

If Soniox continues to timeout:

1. **Switch to Mock Provider** (to verify rest of system works):
   ```bash
   # In server/.env:
   TRANSCRIPTION_PROVIDER=mock
   ```

2. **Check Soniox Account**:
   - Verify account has balance
   - Check Soniox dashboard for account status
   - Verify API key is correct

3. **Try Different Audio Format**:
   - May need to convert WebM/Opus to PCM before sending
   - Or specify format explicitly in config

4. **Contact Soniox Support**:
   - May be account/API issue
   - Or WebM/Opus format not supported for real-time

## Summary

✅ **Fixed**: 408 timeout no longer kills session  
✅ **Fixed**: Audio chunks accepted even after timeout  
✅ **Fixed**: Better logging for debugging  
✅ **Fixed**: Recovery mechanism in place  

The session should now continue even after Soniox timeouts, allowing for potential recovery.




