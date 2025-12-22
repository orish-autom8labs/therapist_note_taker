# How to Run the Official Soniox Live Demo

## Overview

The official Soniox example uses a **completely different architecture** than our code:

- **Official Example**: Uses `@soniox/speech-to-text-web` SDK (handles everything internally)
- **Our Code**: Manual WebSocket connection + manual audio handling

## Architecture Differences

### Official Example:
1. **Server**: Only generates temporary API keys (doesn't handle WebSocket)
2. **Client**: Uses Soniox SDK which:
   - Handles WebSocket connection directly to Soniox
   - Converts audio format automatically
   - Manages audio streaming
   - Processes tokens

### Our Code:
1. **Server**: Handles WebSocket connection, audio forwarding, token processing
2. **Client**: Sends audio to our server, receives transcripts

## Setup Instructions

### Step 1: Start the Server (Temporary API Key Service)

```bash
cd /Users/orish/code/soniox_examples/speech_to_text/apps/soniox-live-demo/server

# Create virtual environment (if not exists)
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set API key
export SONIOX_API_KEY="your_soniox_api_key_here"
# OR create .env file:
# echo "SONIOX_API_KEY=your_soniox_api_key_here" > .env

# Start server
./start.sh
# OR: uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Server will run on: `http://localhost:8000`

### Step 2: Start the React Frontend

Open a **new terminal**:

```bash
cd /Users/orish/code/soniox_examples/speech_to_text/apps/soniox-live-demo/react

# Install dependencies
npm install

# Start dev server
npm run dev
```

Frontend will run on: `http://localhost:5173` (or similar Vite port)

### Step 3: Test the Application

1. Open browser to `http://localhost:5173`
2. Grant microphone permissions
3. Click "Start Recording"
4. Speak into microphone
5. Watch real-time transcription appear

## Key Differences to Investigate

### 1. Audio Format Handling

**Official Example**:
- Uses Soniox SDK (`@soniox/speech-to-text-web`)
- SDK handles audio format conversion internally
- We don't see the WebSocket messages or audio format

**Our Code**:
- Manual WebSocket connection
- Sends WebM/Opus from browser
- Server forwards to Soniox (might be wrong format)

**Question**: How does the SDK convert WebM/Opus to what Soniox expects?

### 2. WebSocket Connection

**Official Example**:
- SDK connects directly to Soniox: `wss://stt-rt.soniox.com/transcribe-websocket`
- Client → Soniox (direct connection)

**Our Code**:
- Client → Our Server → Soniox (proxy connection)
- Our server handles WebSocket forwarding

### 3. Configuration

**Official Example**:
```typescript
sonioxClient.current?.start({
  model: "stt-rt-v3",
  enableLanguageIdentification: true,
  enableSpeakerDiarization: true,
  enableEndpointDetection: true,
  // ...
});
```

**Our Code**:
```python
config_message = {
    'api_key': self.api_key,
    'model': 'stt-rt-v3',
    'audio_format': 'auto',  # ← This might be the problem!
    'enable_endpoint_detection': True,
    # ...
}
```

### 4. Audio Chunking

**Official Example**:
- SDK handles chunking internally
- We don't see the implementation

**Our Code**:
- Manual chunking: 3840 bytes, 120ms delay
- Based on official Python example

## What to Check When Running

1. **Does it work?** (If yes, SDK handles format correctly)
2. **Browser console**: Check for any errors
3. **Network tab**: See WebSocket connection to Soniox
4. **Server logs**: See temporary API key generation

## Next Steps After Testing

1. **If it works**: Compare SDK behavior with our manual implementation
2. **Check SDK source**: See how it handles audio format
3. **Consider**: Should we use the SDK instead of manual WebSocket?

## Alternative: Use SDK in Our Code

If the SDK works, we could:
1. Replace our manual WebSocket with Soniox SDK
2. Keep our server architecture (Google Drive, etc.)
3. Use SDK on client side for transcription

This would be a significant refactor but might solve the audio format issue.

