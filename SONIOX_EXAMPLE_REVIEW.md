# Soniox Official Example Review & How to Run

## Summary

I've reviewed the official Soniox Live Demo example. Here's what I found and how to run it.

## Key Discovery: Architecture Difference

The official example uses a **completely different approach** than our code:

### Official Example:
- ✅ Uses **Soniox SDK** (`@soniox/speech-to-text-web`) on the client
- ✅ SDK handles **everything**: WebSocket, audio format conversion, token processing
- ✅ Client connects **directly to Soniox** (not through our server)
- ✅ Server only generates **temporary API keys** (doesn't handle WebSocket)

### Our Code:
- ❌ Manual WebSocket connection
- ❌ Manual audio forwarding (WebM/Opus → Soniox)
- ❌ Server proxies WebSocket connection
- ❌ **Problem**: WebM/Opus format not processed by Soniox → 408 timeout

## Why Our Code Times Out

1. **Browser sends**: WebM/Opus (compressed audio)
2. **We forward**: Raw WebM/Opus bytes to Soniox
3. **Soniox expects**: PCM raw audio (or properly formatted stream)
4. **Soniox can't process**: WebM/Opus with `audio_format: 'auto'`
5. **Result**: 408 timeout after 20 seconds

**The SDK likely converts WebM/Opus to PCM internally**, but we're sending raw WebM/Opus.

## How to Run the Official Example

### Quick Start (Automated)

```bash
cd /Users/orish/code/note_taker
./run_soniox_example.sh
```

### Manual Steps

#### Step 1: Start the Server

```bash
cd /Users/orish/code/soniox_examples/speech_to_text/apps/soniox-live-demo/server

# Create virtual environment
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

Server runs on: **http://localhost:8000**

#### Step 2: Start the React Frontend

Open a **new terminal**:

```bash
cd /Users/orish/code/soniox_examples/speech_to_text/apps/soniox-live-demo/react

# Install dependencies
npm install

# Start dev server
npm run dev
```

Frontend runs on: **http://localhost:5173** (or similar Vite port)

#### Step 3: Test

1. Open browser to `http://localhost:5173`
2. Grant microphone permissions
3. Click "Start Recording"
4. Speak into microphone
5. Watch real-time transcription appear

## What to Check When Testing

1. **Does it work?** (If yes, SDK handles format correctly)
2. **Browser console**: Check for any errors
3. **Network tab**: See WebSocket connection to Soniox
4. **Server logs**: See temporary API key generation

## Files Created

1. **`HOW_TO_RUN_SONIOX_EXAMPLE.md`**: Detailed setup instructions
2. **`COMPARISON_OFFICIAL_VS_OUR_CODE.md`**: Side-by-side comparison
3. **`run_soniox_example.sh`**: Automated setup script

## Next Steps After Testing

### If the Example Works:

1. **Compare behavior**: See how SDK handles audio vs our code
2. **Check SDK source**: Investigate how SDK converts audio format
3. **Decide**: Should we use SDK or convert audio to PCM?

### Options:

**Option 1: Use Soniox SDK** (Like Official Example) ⭐
- ✅ SDK handles audio format conversion
- ✅ Proven to work
- ❌ Requires refactoring our architecture
- ❌ Client connects directly to Soniox

**Option 2: Convert Audio to PCM** (Keep Our Architecture)
- ✅ Keeps our current architecture
- ✅ Server handles everything
- ❌ Need audio conversion library (`pydub` + `ffmpeg`)
- ❌ More complex

**Option 3: Check SDK Source Code**
- Investigate how SDK converts audio
- Replicate in our code

## Recommendation

1. **First**: Run the official example to confirm it works
2. **Then**: Decide whether to:
   - Use SDK (Option 1) - easier, but requires refactoring
   - Convert to PCM (Option 2) - keeps our architecture, but more work

## Questions to Answer

1. Does the official example work with your API key?
2. Does it transcribe in real-time without timeouts?
3. What audio format does the SDK send to Soniox? (Check Network tab)
4. Should we refactor to use SDK or convert audio to PCM?

