# Soniox 408 Timeout Issue - Analysis

## Problem
Soniox is timing out after 20 seconds with `Error 408: Request timeout`. Audio is being sent successfully, but Soniox isn't processing it and returning tokens.

## What's Happening
1. ✅ Connection established
2. ✅ Config sent successfully  
3. ✅ Audio chunks being sent (16KB chunks every ~1 second)
4. ❌ Soniox only returns empty token arrays
5. ❌ After 20 seconds: `Error 408: Request timeout`
6. ❌ No transcription tokens received

## Possible Causes

### 1. Audio Format Detection Issue
- Browser sends WebM/Opus chunks
- We're using `"audio_format": "auto"` 
- Soniox might not be detecting WebM/Opus correctly
- **Solution**: Try specifying format explicitly or check if WebM is supported

### 2. Chunk Size Too Large
- Official example uses 3840 byte chunks
- We're sending ~16KB chunks
- **Solution**: Might need to split chunks or send smaller pieces

### 3. Missing Configuration
- Official example uses `enable_endpoint_detection: True`
- We might be missing this
- **Solution**: Added endpoint detection

### 4. Audio Format Not Supported
- WebM/Opus might not work with `stt-rt-v3` model
- **Solution**: Check Soniox docs for supported formats

## What I Added

1. **Endpoint Detection**: Added `enable_endpoint_detection: True` (as per official example)
2. **Better Logging**: Track message count and timing

## Next Steps to Try

### Option 1: Test with Mock Provider
Switch to mock provider to verify the rest of the system works:
```bash
# In server/.env:
TRANSCRIPTION_PROVIDER=mock
```

### Option 2: Try Different Audio Format
The browser might need to send audio in a different format. Check if we can:
- Use PCM format instead of WebM
- Or specify WebM format explicitly in config

### Option 3: Check Soniox Account
- Verify account has balance
- Check if `stt-rt-v3` model supports Hebrew
- Check if WebM/Opus is supported for real-time

### Option 4: Contact Soniox Support
The 408 timeout suggests Soniox is rejecting the audio format or there's a configuration issue. Their support might have insights.

## Current Status

After restarting with endpoint detection, if you still get the timeout, the issue is likely:
- Audio format incompatibility
- Model/account limitations
- Configuration issue

The timeout happens after exactly 20 seconds, which suggests Soniox has a timeout for when no valid audio is detected.




