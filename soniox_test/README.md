# Soniox Official Example - Quick Start

This is the official Soniox real-time transcription example. Use it to verify your API key and connection work.

## Quick Setup

1. **Set your API key**:
   ```bash
   export SONIOX_API_KEY=your_soniox_api_key_here
   ```
   
   Get your API key from: https://soniox.com/console

2. **Run the setup script**:
   ```bash
   cd soniox_test
   ./setup_and_run.sh
   ```

   Or manually:
   ```bash
   cd soniox_test
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   export SONIOX_API_KEY=your_api_key_here
   python soniox_realtime.py --audio_path assets/coffee_shop.mp3
   ```

## What to Expect

**If it works:**
- You'll see "Connecting to Soniox..."
- Then "Session started."
- Transcription tokens will appear in real-time
- Final transcript will be displayed

**If it fails:**
- Check the error message
- Common issues:
  - Missing or invalid API key
  - Account balance exhausted (error 402)
  - Network/connection issues

## Testing with Your Own Audio

```bash
python soniox_realtime.py --audio_path /path/to/your/audio.mp3
```

Supported formats: MP3, WAV, FLAC, etc. (see Soniox docs for full list)

## Next Steps

Once this works, we can:
1. Compare our implementation with this working example
2. See what's different
3. Fix our implementation




