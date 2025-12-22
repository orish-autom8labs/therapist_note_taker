# WebSocket 404 Error Troubleshooting

## Current Status
- ✅ Server is running on port 3001
- ✅ Health endpoint works: `curl http://localhost:3001/health`
- ✅ WebSocket route `/ws` is registered in the app
- ❌ Browser gets HTTP 404 when trying to connect

## Possible Causes

### 1. Server Not Restarted After Code Changes
**Solution**: Restart the server:
```bash
# Stop the server (Ctrl+C)
cd server
source venv/bin/activate
python run.py
```

### 2. Wrong WebSocket URL in Frontend
**Check**: Open browser console and verify the WebSocket URL:
- Should be: `ws://localhost:3001/ws`
- NOT: `ws://localhost:3000/ws` or `wss://localhost:3001/ws`

### 3. Uvicorn Reload Mode Issue
When using `reload=True` with string imports, sometimes routes don't load correctly.

**Solution**: Try disabling reload temporarily:
```bash
# In server/.env, set:
NODE_ENV=production
```

Then restart the server.

### 4. Multiple Server Instances
There might be an old server instance running.

**Check and kill old processes**:
```bash
# Find all Python processes on port 3001
lsof -i :3001

# Kill the old ones (replace PID with actual process ID)
kill -9 <PID>
```

### 5. Browser Cache
The browser might be caching an old version.

**Solution**: 
- Hard refresh: `Cmd+Shift+R` (Mac) or `Ctrl+Shift+R` (Windows)
- Or open in incognito/private mode

## Debug Steps

1. **Check server logs** when you try to connect:
   - You should see: `[DEBUG] New WebSocket connection established`
   - If you don't see this, the connection isn't reaching the server

2. **Check browser console**:
   - Look for WebSocket connection errors
   - Check the exact URL being used

3. **Test WebSocket directly**:
   ```bash
   # Install wscat if needed: npm install -g wscat
   wscat -c ws://localhost:3001/ws
   ```

4. **Verify server is using latest code**:
   ```bash
   cd server
   python -c "from main import app; print([r.path for r in app.routes if 'ws' in r.path])"
   ```
   Should output: `['/ws']`

## Quick Fix to Try

1. **Stop the server completely** (Ctrl+C)

2. **Kill any remaining processes**:
   ```bash
   pkill -f "python.*run.py"
   pkill -f "uvicorn.*main"
   ```

3. **Restart fresh**:
   ```bash
   cd server
   source venv/bin/activate
   python run.py
   ```

4. **Wait for**: `INFO:     Uvicorn running on http://0.0.0.0:3001`

5. **Test in browser** again

## If Still Not Working

Check the server terminal for any error messages when you try to connect. The debug logs I added should show:
- `[DEBUG] New WebSocket connection established` - if connection succeeds
- Nothing - if connection is rejected before reaching the handler

Share the server logs and browser console output for further debugging.




