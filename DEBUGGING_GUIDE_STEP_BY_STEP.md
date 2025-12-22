# Debugging Guide: Transcription Not Appearing

**Last Updated:** 2025-12-22
**Purpose:** Systematic approach to identify where the transcription process fails

---

## Quick Debug Checklist

Before diving deep, check these first:

- [ ] **Server is running** on port 3001
- [ ] **Client is running** on port 3000
- [ ] **Browser console is open** (F12 or Cmd+Option+J)
- [ ] **Microphone permission granted** (audio visualizer bars moving = mic working)
- [ ] **Network tab open** in browser dev tools

---

## Step-by-Step Debugging Process

### STEP 1: Open Browser Console (CRITICAL!)

**This is the most important step - you MUST do this to see what's happening.**

**How to open:**
1. Open the application in browser (http://localhost:3000)
2. **Press F12** (or right-click → "Inspect" → "Console" tab)
3. **Keep console open** while you test

**The console shows ALL debug messages and errors.**

---

### STEP 2: Start a Session and Watch Console

**Do this:**
1. Login with Google
2. Enter patient name
3. Click "Start Session"
4. **Immediately look at console**

**You should see this sequence:**

```javascript
// Step 2.1: Debug logs for session start
[DEBUG] startTranscription called
[DEBUG] Resetting tokens and starting SDK
[DEBUG] Calling sonioxClient.start() with config: {model: 'stt-rt-v3', ...}

// Step 2.2: API key fetch
[DEBUG] Fetching temporary API key from: http://localhost:3001/v1/auth/temporary-api-key
[DEBUG] Temporary API key response status: 200
[DEBUG] Temporary API key received: SUCCESS

// Step 2.3: SDK callbacks
[DEBUG] SDK onStarted callback triggered
[SESSION] Transcription started
```

**STOP HERE if you see errors. Note the exact error message.**

---

### STEP 3: Speak and Watch for Token Messages

**Now speak into your microphone.**

**You should see:**

```javascript
[HOOK] Received result: {tokens: Array(5), ...}
[HOOK] New final tokens: [...]
[HOOK] New non-final tokens: [...]
[HOOK] Updated finalTokens: [...]
[HOOK] Setting nonFinalTokens: [...]
```

**If you DON'T see these messages, the problem is identified:**
- SDK is running BUT Soniox is not sending tokens

---

## Problem Diagnosis Table

Use this table to identify your specific issue:

| What You See in Console | Problem | Solution |
|--------------------------|---------|----------|
| **Nothing** | Console not open OR JavaScript crashed | Open console (F12), refresh page |
| `[DEBUG] startTranscription called` but nothing after | SDK failed to start | Check next error message |
| `Failed to fetch ...temporary-api-key` | Server not running OR wrong port | Check server is on port 3001 |
| `[DEBUG] Temporary API key response status: 400` | Server error with API key | Check server logs, verify .env file |
| `[DEBUG] Temporary API key response status: 500` | Soniox API error | Check Soniox API key validity |
| `[DEBUG] SDK onStarted callback triggered` but no tokens when speaking | Microphone issue OR Soniox not receiving audio | Check steps 4 & 5 below |
| `[HOOK] Received result` appears when you speak | ✅ Working! Tokens are being received | Check UI rendering (Step 6) |
| `[DEBUG] SDK onError callback: ...` | Soniox API error | Read the error message carefully |

---

## STEP 4: Check Network Tab for WebSocket

**This shows if SDK is connecting to Soniox.**

1. Open browser DevTools (F12)
2. Click **"Network"** tab
3. Click **"WS"** filter (WebSocket)
4. Start a session
5. You should see: **Connection to `wss://stt-rt.soniox.com/transcribe-websocket`**

**Status:**
- ✅ **Green/101 Switching Protocols** = Connected successfully
- ❌ **Red/Failed** = Connection problem

**If no WebSocket appears:**
- Temporary API key failed
- SDK didn't initialize

---

## STEP 5: Check Microphone Access

**The audio visualizer proves mic is working.**

- ✅ **Green bars moving** = Microphone is working
- ❌ **Gray bars, not moving** = Microphone issue

**If bars don't move:**
1. Browser should prompt for microphone permission
2. Click "Allow"
3. If already denied: Settings → Privacy → Microphone → Allow for localhost
4. Refresh page

---

## STEP 6: Check UI Rendering (If Tokens Are Received)

**If console shows `[HOOK] Received result` but UI shows nothing:**

**Look for:**
```javascript
[COMPONENT] finalTokens: [...]
[COMPONENT] nonFinalTokens: [...]
[COMPONENT] allTokens: [...]
```

**If these show tokens but UI is empty:**
- React rendering issue
- CSS display issue
- Check browser Elements tab for the transcript div

---

## STEP 7: Test Server Endpoint Manually

**Test if server is working independently.**

**Open a new terminal:**

```bash
curl -X POST http://localhost:3001/v1/auth/temporary-api-key
```

**Expected response:**
```json
{"apiKey":"temp:ABC123..."}
```

**Error responses:**

| Response | Problem | Fix |
|----------|---------|-----|
| `Connection refused` | Server not running | Start server: `cd server && source venv/bin/activate && python run.py` |
| `{"detail":"SONIOX_API_KEY is not set"}` | Missing API key | Check `server/.env` file exists with valid key |
| `{"detail":"Soniox API error: ..."}` | Invalid Soniox API key | Get new key from Soniox console |
| Timeout | Port blocked / firewall | Check firewall settings |

---

## STEP 8: Check Server Logs

**If temporary API key fails, check server terminal.**

**Server terminal should show:**
```
INFO:     POST /v1/auth/temporary-api-key 200 OK
```

**Common errors:**
```
ERROR: SONIOX_API_KEY is not set
ERROR: Connection to Soniox API failed
ERROR: Invalid API key
```

**Fix:**
1. Check `server/.env` file exists
2. Verify API key is correct
3. Test API key directly with Soniox

---

## Common Issues & Solutions

### Issue 1: "Failed to fetch temporary API key"

**Symptoms:** Console shows fetch error immediately on session start

**Causes:**
- Server not running
- Wrong port (should be 3001)
- CORS issue

**Solutions:**
```bash
# 1. Check server is running
ps aux | grep "python run.py"

# 2. Check port 3001 is listening
lsof -i :3001

# 3. Restart server
cd /Users/orish/code/note_taker/server
source venv/bin/activate
python run.py
```

---

### Issue 2: "SDK starts but no tokens received"

**Symptoms:**
- `[DEBUG] SDK onStarted callback triggered` appears
- Audio visualizer works (bars moving)
- But no `[HOOK] Received result` messages

**Causes:**
- Soniox API issue
- Wrong SDK configuration
- Network blocking WebSocket

**Solutions:**

1. **Check WebSocket in Network tab** (see Step 4)
2. **Try with English speech** (test if language is the issue)
3. **Check Soniox API status**: https://status.soniox.com/
4. **Verify API key has credit**: https://console.soniox.com/

---

### Issue 3: "Tokens received but UI shows nothing"

**Symptoms:**
- Console shows `[HOOK] Received result: {tokens: Array(X)}`
- Console shows `[HOOK] Updated finalTokens: [...]`
- But UI transcript area is empty

**Solution:**
Check if tokens are actually being set:

**In browser console, type:**
```javascript
// This should show token arrays
console.log(window.__REACT_DEVTOOLS_GLOBAL_HOOK__)
```

**Or check React DevTools:**
1. Install React Developer Tools extension
2. Open DevTools → Components tab
3. Find `ActiveSession` component
4. Check `finalTokens` and `nonFinalTokens` state

---

### Issue 4: "Everything works in console but text doesn't appear"

**This is a rendering issue, not a transcription issue.**

**Check:**
1. Browser Elements tab → Find `<div>` with transcript
2. Check if it has content but CSS is hiding it
3. Check `direction: rtl` is working for Hebrew

**Temporary fix:**
Look at the raw data in console:
```javascript
[HOOK] Updated finalTokens: [{text: "שלום", speaker: "Speaker 0", is_final: true}]
```

If you see Hebrew text here, transcription IS working, just UI has issue.

---

## Debug Checklist for Support

**When asking for help, provide:**

1. ✅ **Full console output** (copy entire console when starting session + speaking)
2. ✅ **Server terminal output** (last 20 lines)
3. ✅ **Network tab screenshot** (showing WS connection status)
4. ✅ **Result of:** `curl -X POST http://localhost:3001/v1/auth/temporary-api-key`
5. ✅ **Browser and version** (Chrome 120, Firefox 121, etc.)
6. ✅ **Operating System** (macOS 14, Windows 11, etc.)

---

## Expected Complete Console Output (Success)

**This is what you should see when everything works:**

```javascript
// Session start
[DEBUG] startTranscription called
[DEBUG] Resetting tokens and starting SDK
[DEBUG] Calling sonioxClient.start() with config: {model: 'stt-rt-v3', enableLanguageIdentification: true, enableSpeakerDiarization: true}
[DEBUG] Fetching temporary API key from: http://localhost:3001/v1/auth/temporary-api-key
[DEBUG] Temporary API key response status: 200
[DEBUG] Temporary API key received: SUCCESS
[DEBUG] SDK onStarted callback triggered
[SESSION] Transcription started

// When you speak
[HOOK] Received result: {tokens: Array(3), final_speaker_labels: {…}, ...}
[HOOK] New final tokens: []
[HOOK] New non-final tokens: [{text: "שלום", speaker: "Speaker 0", is_final: false, ...}]
[HOOK] Setting nonFinalTokens: [{text: "שלום", ...}]

// As you continue speaking
[HOOK] Received result: {tokens: Array(5), ...}
[HOOK] New final tokens: [{text: "שלום ", speaker: "Speaker 0", is_final: true, ...}]
[HOOK] New non-final tokens: [{text: "עולם", speaker: "Speaker 0", is_final: false, ...}]
[HOOK] Updated finalTokens: [{text: "שלום ", ...}]
[HOOK] Setting nonFinalTokens: [{text: "עולם", ...}]
```

**If your console looks like this, transcription IS WORKING!**

---

## Quick Test Command

**Reload client and paste this in console to test API:**

```javascript
fetch('http://localhost:3001/v1/auth/temporary-api-key', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'}
})
.then(r => r.json())
.then(d => console.log('API Key Test:', d.apiKey ? 'SUCCESS' : 'FAILED'))
.catch(e => console.error('API Key Test FAILED:', e));
```

**Expected output:**
```
API Key Test: SUCCESS
```

---

## Still Not Working?

**If you've followed all steps and still have issues:**

1. **Copy your entire console output** (Ctrl+A in console, Ctrl+C)
2. **Save it to a file**
3. **Share:**
   - Console output
   - Server terminal output
   - What you see in Network tab → WS filter
   - Result of the curl command above

**We can then pinpoint the exact failure point.**

---

**Last Resort: Compare with Working Example**

**The official Soniox example is confirmed working:**

```bash
# Run the working example
cd /Users/orish/code/soniox_examples/speech_to_text/apps/soniox-live-demo/

# Terminal 1
cd server && source .venv/bin/activate && uvicorn main:app --port 8000

# Terminal 2
cd react && npm run dev

# Open http://localhost:5173
```

**If the official example works but ours doesn't:**
- Compare console output between the two
- The difference shows where our implementation diverges

---

**Generated:** 2025-12-22
**Purpose:** Help user systematically identify transcription issues
**Next:** Follow steps 1-3, report what you see in console
