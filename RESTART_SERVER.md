# Restart Server Instructions

## The Issue
The WebSocket route exists but the browser is getting HTTP 404. This is likely because:
1. The server needs to be restarted to pick up the latest code
2. Uvicorn reload mode with string imports can sometimes miss WebSocket routes

## Solution
I've updated `run.py` to import the app directly (which ensures all routes load) and disabled reload mode temporarily.

## Steps to Fix

1. **Stop the current server**:
   - Go to the terminal where the server is running
   - Press `Ctrl+C` to stop it
   - Or run: `pkill -f "python.*run.py"`

2. **Start the server fresh**:
   ```bash
   cd server
   source venv/bin/activate
   python run.py
   ```

3. **You should see**:
   ```
   Starting server on port 3001
   Transcription provider: Soniox
   Server starting on http://0.0.0.0:3001
   WebSocket endpoint: ws://localhost:3001/ws
   INFO:     Started server process [xxxxx]
   INFO:     Waiting for application startup.
   INFO:     Application startup complete.
   INFO:     Uvicorn running on http://0.0.0.0:3001 (Press CTRL+C to quit)
   ```

4. **Test the connection**:
   - Open your browser to `http://localhost:3000`
   - Try starting a session
   - Check the server terminal - you should see:
     ```
     [DEBUG] New WebSocket connection established
     [DEBUG] WebSocket client: ...
     ```

## What Changed

- **Direct app import**: Instead of using string `"main:app"`, we now import the app directly
- **Reload disabled**: Temporarily disabled to ensure routes load correctly
- **Better logging**: Added startup messages showing the WebSocket endpoint

## If It Still Doesn't Work

1. **Check browser console** for the exact error
2. **Check server logs** for any connection attempts
3. **Verify the WebSocket URL** in browser console:
   - Should be: `ws://localhost:3001/ws`
   - Open browser DevTools → Console → Look for WebSocket connection logs

## Re-enabling Reload Mode

Once everything works, you can re-enable reload by changing `use_reload = False` to `use_reload = True` in `run.py`, but you'll need to use the string import method again. For now, let's get it working first!




