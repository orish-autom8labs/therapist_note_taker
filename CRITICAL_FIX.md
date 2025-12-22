# Critical: Restart Server After Changing Provider

## The Problem

You changed `.env` to use `mock` provider, but **the server needs to be restarted** for the change to take effect!

The server reads the `.env` file **only when it starts**, not while it's running.

## Fix Steps

1. **Stop the current server:**
   - Go to terminal where `python run.py` is running
   - Press `Ctrl+C` to stop it

2. **Restart the server:**
   ```bash
   cd server
   source venv/bin/activate
   python run.py
   ```

3. **Look for this message when server starts:**
   ```
   Transcription provider: Mock Provider (Testing)
   ```

4. **Try the session again**

## How to Verify

After restarting, when you start a session, you should see in server logs:
- `[MOCK] start_streaming_session called`
- `[MOCK] Starting transcription simulation`
- `[MOCK] Sending transcript chunk: ...`
- `[DEBUG] Received transcript chunk: ...`

If you don't see `[MOCK]` messages, the server is still using the old provider (soniox).

## Quick Check

Run this to see what provider is active:
```bash
curl http://localhost:3001/api/transcription/provider
```

Should return:
```json
{"name": "Mock Provider (Testing)", ...}
```

If it says "Soniox", the server needs to be restarted!




