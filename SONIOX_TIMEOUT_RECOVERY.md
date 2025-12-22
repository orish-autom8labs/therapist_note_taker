# Soniox 408 Timeout Recovery Fix

## Problem

From your logs:
- **Line 413**: `[SONIOX] Message #2 received (after 20.17s)` - Only 2 messages in 20 seconds!
- **Line 414**: `[SONIOX ERROR] Error 408: Request timeout.`
- **Line 421**: `streaming=False` - Session marked inactive
- **Lines 423+**: `[ERROR] Session not active` - All audio chunks rejected

**Root Cause**: Soniox times out after 20 seconds if it doesn't receive tokens, which marks the session inactive and blocks all further audio.

## Fixes Applied

### 1. Graceful 408 Timeout Handling ✅
**File**: `server/src/providers/soniox_provider.py`

**Before**: 408 timeout immediately killed the session
**After**: 408 timeout is logged as warning, session continues

```python
if error_code == 408:
    print(f'[SONIOX WARNING] Timeout error (408) - continuing to process audio')
    # Don't set is_streaming = False - let it continue
    # Session might recover if we keep sending audio
```

### 2. Allow Audio Even When Session Marked Inactive ✅
**File**: `server/main.py`

**Before**: Audio chunks rejected if `is_active() == False`
**After**: Audio chunks accepted even if inactive (for recovery)

```python
if not is_active:
    print('[WARNING] Session marked inactive, but continuing to accept audio')
    # Don't reject - allow audio to be sent
```

### 3. Improved Fallback Mechanism ✅
**File**: `server/src/providers/soniox_provider.py`

**Before**: Fallback only worked if tokens existed
**After**: Fallback logs status even when no tokens (helps debug)

```python
if time_since_last_send >= FALLBACK_INTERVAL:
    if all_accumulated_tokens:
        # Send accumulated text
    else:
        # Log that no tokens received yet
        print('[SONIOX] FALLBACK: No tokens received yet - Soniox may be processing slowly')
```

### 4. Audio Sending Recovery ✅
**File**: `server/src/providers/soniox_provider.py`

**Before**: Audio rejected if `is_streaming == False`
**After**: Audio sent even if streaming marked False (recovery attempt)

```python
if not self.is_streaming:
    print('[SONIOX WARNING] Streaming marked False, but attempting to send audio anyway')
# Continue to send audio
```

## Why This Happens

**Soniox 408 Timeout** occurs when:
1. Soniox receives audio but doesn't process it quickly enough
2. No tokens are returned within 20 seconds
3. Soniox assumes the connection is dead and times out

**Possible Causes**:
- Audio format detection issues (WebM/Opus)
- Network latency
- Soniox server load
- Audio quality issues

## Expected Behavior After Fix

1. **408 Timeout**: Logged as warning, session continues
2. **Audio Chunks**: Still accepted and sent to Soniox
3. **Recovery**: Session might recover if Soniox starts processing
4. **Fallback**: Status messages every 5 seconds even if no tokens

## Testing

1. **Restart server**:
   ```bash
   cd server
   python run.py
   ```

2. **Test with continuous speech**:
   - Speak for 30+ seconds
   - Watch for 408 timeout warning (should not kill session)
   - Audio should continue to be sent
   - Check if transcription eventually appears

3. **Check logs for**:
   - `[SONIOX WARNING] Timeout error (408) - continuing to process audio`
   - `[WARNING] Session marked inactive, but continuing to accept audio`
   - `[SONIOX] FALLBACK: No tokens received yet` (every 5 seconds)

## If It Still Doesn't Work

If Soniox continues to timeout and not process audio:

1. **Check audio format**: WebM/Opus might not be supported
2. **Try mock provider**: Switch to mock to verify rest of system works
3. **Contact Soniox support**: May be account/API issue
4. **Check Soniox dashboard**: Verify account status and balance




