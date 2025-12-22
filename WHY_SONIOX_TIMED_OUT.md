# Why Soniox Timed Out - Detailed Explanation

## What Happened

From your logs:
- ✅ **Audio chunks sent successfully**: Lines 131-412 show many successful sends
- ✅ **Soniox received audio**: Connection was active, audio was transmitted
- ❌ **Soniox didn't process audio**: Only 2 messages in 20 seconds (config + timeout)
- ❌ **No tokens returned**: Soniox never sent any transcription tokens
- ❌ **408 timeout after 20 seconds**: Soniox gave up because it couldn't process the audio

## Root Cause Analysis

### The Problem: Audio Format Mismatch

**What we're sending**:
- Browser: `audio/webm;codecs=opus` (WebM container with Opus codec)
- Format: WebM/Opus (compressed, variable bitrate)
- Encoding: Base64 encoded, then decoded to bytes

**What Soniox expects**:
- Official example uses: **MP3 files** (pre-recorded)
- Or: **PCM raw audio** (uncompressed, fixed sample rate)
- Format: `pcm_s16le` (16-bit PCM, little-endian, 16kHz, mono)

**The Issue**:
- Soniox's `"audio_format": "auto"` might not correctly detect WebM/Opus
- WebM/Opus is a **container format** (not raw audio)
- Soniox might be waiting for raw PCM audio but receiving WebM/Opus
- After 20 seconds of receiving unprocessable audio, Soniox times out

## Why 20 Seconds?

Soniox has a **20-second timeout** for real-time transcription:
- If no tokens are returned within 20 seconds, Soniox assumes:
  - The audio format is wrong
  - The connection is dead
  - There's a configuration error
- Soniox closes the connection with **408 Request Timeout**

## Evidence from Your Logs

1. **Audio being sent**: ✅
   ```
   [SONIOX] Sending 1948 bytes of audio (chunk 1 of 1)
   [SONIOX] Audio chunk sent successfully (1948 total bytes)
   ```
   (Repeated many times)

2. **Soniox receiving but not processing**: ❌
   ```
   [SONIOX] Message #2 received (after 20.17s, type: str, len: 113)
   [SONIOX ERROR] Error 408: Request timeout.
   ```
   Only 2 messages in 20 seconds = Soniox received audio but couldn't process it

3. **No tokens**: ❌
   - No `[SONIOX] Received X tokens` messages
   - No `[SONIOX TOKEN]` messages
   - Soniox never processed the audio

## Why It Worked Once

You mentioned "one very successful try" - this could be:
1. **Different browser**: Different browser might send audio in a different format
2. **Different audio quality**: Browser might have used different codec settings
3. **Timing**: Soniox might have processed it before timeout
4. **Network**: Faster connection might have helped

## Solutions

### Option 1: Convert WebM/Opus to PCM (Recommended) ⭐

**Convert browser audio to PCM before sending to Soniox**

**Pros**:
- ✅ Soniox definitely supports PCM
- ✅ More reliable
- ✅ Matches official example format

**Cons**:
- ❌ Requires audio conversion library (e.g., `pydub`, `ffmpeg`)
- ❌ More complex implementation
- ❌ Higher bandwidth (uncompressed audio)

**Implementation**:
- Use `pydub` or `ffmpeg` to convert WebM/Opus → PCM
- Send PCM to Soniox with explicit format: `pcm_s16le`, `sample_rate: 16000`, `num_channels: 1`

### Option 2: Try Explicit WebM Format

**Specify WebM format explicitly in config**

**Pros**:
- ✅ Simple (just change config)
- ✅ No conversion needed

**Cons**:
- ❌ Might not work (WebM might not be supported)
- ❌ Unknown if Soniox supports WebM/Opus for real-time

**Implementation**:
```python
config_message = {
    'api_key': self.api_key,
    'model': 'stt-rt-v3',
    'audio_format': 'webm',  # Try explicit format
    # Or try:
    # 'audio_format': 'opus',
}
```

### Option 3: Use Different Browser Audio Format

**Configure browser to record in different format**

**Pros**:
- ✅ No server-side conversion
- ✅ Browser handles encoding

**Cons**:
- ❌ Limited browser support
- ❌ Might not be possible (browsers prefer WebM/Opus)

**Implementation**:
```javascript
// Try different mimeType
const mediaRecorder = new MediaRecorder(stream, {
  mimeType: 'audio/webm',  // Without codecs
  // Or try:
  // mimeType: 'audio/ogg;codecs=opus',
});
```

### Option 4: Switch to Mock Provider (For Testing)

**Use mock provider to verify rest of system works**

**Pros**:
- ✅ Verifies UI and flow work
- ✅ No Soniox issues

**Cons**:
- ❌ Not real transcription
- ❌ Only for testing

## Recommended Next Steps

1. **First**: Try Option 2 (explicit WebM format) - easiest to test
2. **If that fails**: Implement Option 1 (PCM conversion) - most reliable
3. **For testing**: Use Option 4 (mock provider) to verify UI works

## Why "Auto" Format Detection Fails

Soniox's `"audio_format": "auto"` works by:
1. Analyzing the first few bytes of audio
2. Detecting the format signature (magic bytes)
3. Determining codec and parameters

**Problem with WebM/Opus**:
- WebM is a container format (like MP4)
- Opus is the codec inside
- Soniox might detect "WebM" but not know how to extract/process Opus
- Or Soniox might not support Opus codec for real-time

**Solution**: Either:
- Convert to PCM (raw audio, no container)
- Or specify format explicitly if Soniox supports it

## Summary

**Why it timed out**:
- Soniox received audio (WebM/Opus) but couldn't process it
- After 20 seconds of unprocessable audio, Soniox timed out
- No tokens were ever returned

**Root cause**:
- Audio format mismatch: WebM/Opus vs. expected PCM/MP3
- Soniox's "auto" detection doesn't work for WebM/Opus

**Next steps**:
- Convert to PCM format (most reliable)
- Or try explicit WebM format (quick test)
- Or use mock provider (for testing)




