# Audio Format Fix Options

## Quick Test: Try Explicit Format

Let's first try specifying the format explicitly to see if Soniox supports WebM/Opus:

### Test 1: Explicit WebM Format

**File**: `server/src/providers/soniox_provider.py`

Change:
```python
'audio_format': 'auto',  # Current
```

To:
```python
'audio_format': 'webm',  # Try explicit
```

**Test**: Restart server and try again. If it works, great! If not, continue to Test 2.

### Test 2: Explicit Opus Format

If Test 1 fails, try:
```python
'audio_format': 'opus',  # Try Opus codec
```

## Proper Fix: Convert to PCM

If explicit formats don't work, we need to convert WebM/Opus to PCM.

### Step 1: Install Audio Conversion Library

```bash
cd server
source venv/bin/activate
pip install pydub
```

**Note**: `pydub` requires `ffmpeg` to be installed on your system:
```bash
# macOS
brew install ffmpeg

# Or download from: https://ffmpeg.org/download.html
```

### Step 2: Add PCM Conversion

**File**: `server/main.py`

Add conversion before sending to Soniox:
```python
from pydub import AudioSegment
import io

# Convert WebM/Opus to PCM
audio_segment = AudioSegment.from_file(
    io.BytesIO(audio_bytes),
    format="webm"
)
# Convert to PCM: 16kHz, 16-bit, mono
pcm_audio = audio_segment.set_frame_rate(16000).set_channels(1).set_sample_width(2)
pcm_bytes = pcm_audio.raw_data

# Send PCM to Soniox
await transcription_session['send_audio'](pcm_bytes)
```

**File**: `server/src/providers/soniox_provider.py`

Update config:
```python
config_message = {
    'api_key': self.api_key,
    'model': 'stt-rt-v3',
    'audio_format': 'pcm_s16le',  # Explicit PCM format
    'sample_rate': 16000,
    'num_channels': 1,
}
```

## Which Option to Choose?

**For quick test**: Try explicit WebM/Opus format first (5 minutes)
**For reliable solution**: Convert to PCM (30 minutes, but guaranteed to work)




