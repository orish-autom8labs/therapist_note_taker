# Server Start Fix

## Problem
The server wasn't starting because the `websockets` module was missing from the virtual environment.

## Solution
I've installed the missing dependencies. Now you need to restart the server.

## Steps to Start Server

1. **Make sure you're in the server directory**:
   ```bash
   cd server
   ```

2. **Activate the virtual environment**:
   ```bash
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   ```

3. **Verify dependencies are installed**:
   ```bash
   pip install -r requirements.txt
   ```
   
   This should show "Requirement already satisfied" for all packages.

4. **Start the server**:
   ```bash
   python run.py
   ```

5. **You should see**:
   ```
   Starting server on port 3001
   Transcription provider: Soniox
   INFO:     Started server process [xxxxx]
   INFO:     Waiting for application startup.
   INFO:     Application startup complete.
   INFO:     Uvicorn running on http://0.0.0.0:3001 (Press CTRL+C to quit)
   ```

## If You Still See Errors

### "ModuleNotFoundError: No module named 'websockets'"
- Make sure the virtual environment is activated (you should see `(venv)` in your prompt)
- Run: `pip install -r requirements.txt`

### "WARNING: You must pass the application as an import string..."
- This is just a warning, not an error
- The server should still start
- If reload doesn't work, that's okay for now

### "Failed to start session: server rejected WebSocket connection: HTTP 404"
- Make sure the server is running on port 3001
- Check that you see "Uvicorn running on http://0.0.0.0:3001" in the logs
- Try accessing `http://localhost:3001/health` in your browser - it should return JSON

## Quick Test

After starting the server, test it:
```bash
curl http://localhost:3001/health
```

This should return:
```json
{"status":"ok","provider":"Soniox"}
```

If this works, the server is running correctly and the WebSocket should work too.




