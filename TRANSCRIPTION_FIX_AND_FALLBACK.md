# Transcription Fix: Fallback Mechanism & Window Width

## Issues Fixed

### 1. Window Width - 75% of Screen ✅
**Changed**: `max-width: 600px` → `max-width: 75vw` (75% of viewport width)
**File**: `client/src/App.css`

Now the app takes 75% of the screen width, giving more room for transcript display.

### 2. Final Tokens Explanation ✅

**What are Final Tokens?**
- Soniox's AI decides when text is "final" (complete and won't change)
- Based on:
  - **Endpoint Detection**: Speech pauses (0.5-2 seconds of silence)
  - **Natural Boundaries**: End of sentences, periods, question marks
  - **Model Confidence**: When Soniox is highly confident

**The Problem**:
- If you speak continuously without pausing, Soniox won't finalize tokens
- This means the UI waits for pauses before showing text
- Result: Delayed display, only showing after pauses

### 3. Fallback Mechanism ✅

**Solution**: Send accumulated text every 5 seconds even if not finalized

**How it works**:
1. **Final tokens** (when Soniox finalizes): Sent immediately ✅
2. **Fallback** (every 5 seconds): Send all accumulated text (final + non-final) ✅

**Benefits**:
- ✅ Users see progress every 5 seconds (even during continuous speech)
- ✅ Final tokens still sent when available (for accuracy)
- ✅ No letter-by-letter build-up (only every 5 seconds)
- ✅ Visual distinction: Fallback text in gray/italic with "(updating...)" label

### 4. Frontend Debugging ✅

Added extensive console logging to track:
- When chunks are received
- Chunk details (text, speaker, is_final, fallback)
- Whether chunks are appended or updated in place

## Changes Made

### Backend (`soniox_provider.py`):
1. Added fallback timer (5 seconds)
2. Track all accumulated tokens (final + non-final)
3. Send accumulated text every 5 seconds if no final tokens
4. Mark fallback chunks with `fallback: True` flag

### Frontend (`ActiveSession.js`):
1. Handle fallback chunks (update in place if same speaker)
2. Visual distinction: Gray/italic for fallback, normal for final
3. Show "(updating...)" label for fallback text
4. Extensive debug logging

### CSS (`App.css`):
1. Window width: 75% of viewport
2. Better word wrapping for long text

## Expected Behavior

**Before**:
- Text only appears after speech pauses (when Soniox finalizes)
- Long delays during continuous speech
- Only first words showing

**After**:
- Text appears every 5 seconds (fallback)
- Final tokens still sent immediately when available
- Full sentences visible
- Visual feedback: Gray text = updating, Black text = finalized

## Testing

1. **Restart server**:
   ```bash
   cd server
   python run.py
   ```

2. **Test continuous speech**:
   - Speak continuously for 10+ seconds
   - Should see text appear every 5 seconds (gray, italic)
   - When you pause, should see final text (black, normal)

3. **Check browser console**:
   - Look for `[DEBUG] Received transcript chunk:` messages
   - Verify chunks are being received and processed

4. **Check server logs**:
   - Look for `[SONIOX] FALLBACK: Sending accumulated text` every 5 seconds
   - Look for `[SONIOX] Sending FINAL transcript` when pauses occur

## Debugging

If text still doesn't appear:

1. **Check browser console**:
   - Are chunks being received? (`[DEBUG] Received transcript chunk`)
   - Are chunks being appended? (`[DEBUG] Appending new chunk`)

2. **Check server logs**:
   - Are final tokens being sent? (`[SONIOX] Sending FINAL transcript`)
   - Are fallback chunks being sent? (`[SONIOX] FALLBACK: Sending accumulated text`)

3. **Check WebSocket connection**:
   - Is WebSocket connected? (check browser Network tab)
   - Are messages being sent? (check server logs)




