# Running Official Soniox Example

This guide will help you run the official Soniox real-time transcription example to verify your API key and connection work.

## Step 1: Copy Example to Your Project

The example is already cloned at `/tmp/soniox_examples`. Let's copy it to your project:

```bash
cd /Users/orish/code/note_taker
cp -r /tmp/soniox_examples/speech_to_text/python ./soniox_test
cp -r /tmp/soniox_examples/speech_to_text/assets ./soniox_test/assets
```

## Step 2: Set Up Environment

```bash
cd soniox_test
python3 -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

## Step 3: Set API Key

```bash
export SONIOX_API_KEY=your_soniox_api_key_here
# Or add it to a .env file in soniox_test/
```

## Step 4: Run the Example

```bash
# Test with the provided audio file
python soniox_realtime.py --audio_path assets/coffee_shop.mp3

# Or test with Hebrew (if you have a Hebrew audio file)
python soniox_realtime.py --audio_path assets/coffee_shop.mp3 --audio_format auto
```

## What to Expect

If it works, you should see:
- "Connecting to Soniox..."
- "Session started."
- Transcription tokens appearing in real-time
- Final transcript at the end

If it fails, you'll see:
- Error messages indicating what's wrong
- This will help us understand if it's an API key issue, account issue, or something else

## Next Steps

Once we confirm the official example works, we can:
1. Compare our implementation with the working example
2. Identify what's different
3. Fix our implementation to match




