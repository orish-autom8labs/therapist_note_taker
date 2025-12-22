# Fix for WebSocket 404 Error

## Problem
The WebSocket connection is failing with HTTP 404, meaning the server can't find the `/ws` endpoint.

## Solution
I've updated `server/run.py` to properly import the FastAPI app. You need to **restart the server** for the fix to take effect.

## Steps to Fix

1. **Stop the current server**:
   - Find the terminal where the server is running
   - Press `Ctrl+C` to stop it

2. **Restart the server**:
   ```bash
   cd server
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   python run.py
   ```

3. **Verify the server is running**:
   - You should see messages like:
     ```
     Starting server on port 3001
     Transcription provider: Soniox (or Mock)
     INFO:     Uvicorn running on http://0.0.0.0:3001
     ```

4. **Test the WebSocket endpoint**:
   - Open your browser to `http://localhost:3000`
   - Try starting a session again
   - The WebSocket should now connect successfully

## What Changed

The `run.py` file now:
- Imports the `app` directly from `main.py` instead of using a string reference
- Ensures the Python path is set correctly
- This guarantees uvicorn can find and load the WebSocket route

## If It Still Doesn't Work

1. **Check server logs** for any import errors
2. **Verify the server is on port 3001**: Check the startup message
3. **Check browser console** for WebSocket connection errors
4. **Verify `.env` file**: Make sure `PORT=3001` is set (if needed)

## Quick Test

After restarting, you can test the health endpoint:
```bash
curl http://localhost:3001/health
```

This should return JSON with server status. If this works but WebSocket doesn't, there may be a different issue.




