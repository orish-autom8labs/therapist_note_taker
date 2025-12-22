# Test Plan: Isolating "Invalid Temporary API Key" Error

**Status:** API Key Verified Working - Need to Test SDK Integration
**Date:** 2025-12-22
**Issue:** SDK reports "invalid temporary api key" despite successful key generation

---

## ✅ What We've Verified

1. **Soniox API Key is VALID** ✅
   ```bash
   curl -X POST https://api.soniox.com/v1/auth/temporary-api-key \
     -H "Authorization: Bearer 2dab2363efa962920fa6574e738b15b08da198e1eb8f1a0ff25ad1a6b023be8a" \
     -H "Content-Type: application/json" \
     -d '{"usage_type": "transcribe_websocket", "expires_in_seconds": 60}'

   # Result: {"api_key": "temp:...", "expires_at": "..."}  ✅ SUCCESS
   ```

2. **Our Server Generates Temporary Keys** ✅
   ```bash
   curl -X POST http://localhost:3001/v1/auth/temporary-api-key

   # Result: {"apiKey": "temp:..."}  ✅ SUCCESS
   ```

3. **Response Format is Correct** ✅
   - Soniox returns: `api_key` (snake_case)
   - Our server transforms to: `apiKey` (camelCase)
   - Our client expects: `apiKey` (camelCase)
   - **Format matches working example** ✅

---

## ❌ The Problem

Despite all the above working, the Soniox SDK reports:
```
[DEBUG] SDK onError callback: {status: 'InvalidApiKey', message: 'invalid temporary api key'}
```

**This means:**
- Temporary key is generated correctly
- SDK receives the key
- SDK attempts to use it with Soniox WebSocket
- **Soniox WebSocket rejects the key as invalid**

---

## 🔍 Test 1: Minimal SDK Test (Isolate the Issue)

**Purpose:** Test SDK with minimal code to eliminate React/app complexity

### Steps:

1. **Ensure server is running:**
   ```bash
   cd /Users/orish/code/note_taker/server
   source venv/bin/activate
   python run.py
   ```

2. **Open test file in browser:**
   ```
   open /Users/orish/code/note_taker/test_sdk_manual.html
   ```

3. **Open browser console (F12)**

4. **Run test:**
   ```javascript
   window.testSDK()
   ```

### Expected Results:

#### If test SUCCEEDS:
```
[TEST] Fetching temporary API key...
[TEST] Got response: {apiKey: "temp:..."}
[TEST] Returning apiKey: temp:...
[TEST] Creating SonioxClient...
[TEST] Starting transcription...
[TEST] State changed to: Recording
[TEST] ✅ SDK onStarted - SUCCESS!
```
**Interpretation:** SDK works! Problem is in our React app.

#### If test FAILS:
```
[TEST] Fetching temporary API key...
[TEST] Got response: {apiKey: "temp:..."}
[TEST] Returning apiKey: temp:...
[TEST] Creating SonioxClient...
[TEST] Starting transcription...
[TEST] ❌ SDK onError: {status: 'InvalidApiKey', message: 'invalid temporary api key'}
```
**Interpretation:** SDK itself has an issue. Need to investigate SDK/key interaction.

---

## 🔍 Test 2: Compare Working Example

**Purpose:** Verify the official working example still works

### Steps:

1. **Terminal 1 - Start working example server:**
   ```bash
   cd /Users/orish/code/soniox_examples/speech_to_text/apps/soniox-live-demo/server
   source .venv/bin/activate
   uvicorn main:app --port 8000
   ```

2. **Terminal 2 - Start working example client:**
   ```bash
   cd /Users/orish/code/soniox_examples/speech_to_text/apps/soniox-live-demo/react
   npm run dev
   ```

3. **Open browser:**
   ```
   http://localhost:5173
   ```

4. **Click "Start" and speak**

### Expected Result:

- ✅ **If working:** Transcription appears → Our implementation has a bug
- ❌ **If broken:** No transcription → Soniox API or environment issue

---

## 🔍 Test 3: Network Inspection

**Purpose:** See exactly what's being sent to Soniox WebSocket

### Steps:

1. **Open our app:** http://localhost:3000
2. **Open DevTools (F12) → Network tab → WS filter**
3. **Start a session**
4. **Click on the WebSocket connection**
5. **View Messages tab**

### What to Look For:

**First message from client (SDK → Soniox):**
```json
{
  "api_key": "temp:...",
  "model": "stt-rt-v3",
  "enable_language_identification": true,
  "enable_speaker_diarization": true,
  ...
}
```

**Response from Soniox:**
- ✅ **Success:** `{"status": "started"}` or similar
- ❌ **Failure:** `{"error": "invalid api key"}` or similar

**Compare with working example's WebSocket messages.**

---

## 🔍 Test 4: API Key Timing Test

**Purpose:** Check if temporary key expires before SDK uses it

### Hypothesis:
Maybe there's a delay between:
1. SDK requests temporary key
2. SDK tries to connect
3. Key expires (60 seconds)

### Test:

1. **Generate a temporary key manually:**
   ```bash
   curl -X POST http://localhost:3001/v1/auth/temporary-api-key
   ```

2. **Copy the apiKey value**

3. **Immediately test with SDK (within 10 seconds):**
   ```javascript
   // In browser console
   const { SonioxClient } = await import('https://cdn.jsdelivr.net/npm/@soniox/speech-to-text-web@1.2.0/dist/index.mjs');

   const client = new SonioxClient({
     apiKey: async () => "PASTE_KEY_HERE"  // Paste the temp key
   });

   await client.start({
     model: 'stt-rt-v3',
     onStarted: () => console.log('✅ Started!'),
     onError: (s, m) => console.error('❌ Error:', s, m),
     onPartialResult: (r) => console.log('📝 Tokens:', r.tokens.length)
   });
   ```

4. **Observe:** Does it work with a fresh key?

---

## 🔍 Test 5: Server Logs Deep Dive

**Purpose:** See exactly what our server is doing

### Steps:

1. **Stop the server (Ctrl+C)**

2. **Start with verbose logging:**
   ```bash
   cd /Users/orish/code/note_taker/server
   source venv/bin/activate
   python run.py
   ```

3. **Watch the terminal while starting a session**

### Look For:

```
INFO:     POST /v1/auth/temporary-api-key 200 OK
```

**If you see 400/500 errors:** Server is failing to generate keys

**If you see 200:** Server is working, issue is elsewhere

---

## 📊 Decision Tree

```
Start
  |
  ├─ Test 1 (Minimal SDK Test)
  |    ├─ ✅ Works → Problem is in React app code
  |    └─ ❌ Fails → Continue to Test 2
  |
  ├─ Test 2 (Working Example)
  |    ├─ ✅ Works → Our implementation differs from working example
  |    └─ ❌ Fails → Soniox API or environment issue
  |
  ├─ Test 3 (Network Inspection)
  |    ├─ See what exact error Soniox WebSocket returns
  |    └─ Compare with working example's WebSocket messages
  |
  ├─ Test 4 (Timing Test)
  |    ├─ ✅ Works with manual key → Timing/caching issue
  |    └─ ❌ Still fails → Key format or SDK issue
  |
  └─ Test 5 (Server Logs)
       └─ Verify server behavior matches expectations
```

---

## 🎯 Next Steps (For User)

**Please run tests in this order:**

1. **Test 1 (5 min):** Minimal SDK test - This will immediately tell us if SDK integration works
2. **Test 2 (5 min):** Working example - Verify environment is okay
3. **Test 3 (5 min):** Network inspection - See actual WebSocket error
4. **Test 4 (2 min):** Manual key test - Check if key itself is usable
5. **Test 5 (2 min):** Server logs - Verify server behavior

**Total time: ~20 minutes**

---

## 💡 Hypotheses to Test

### Hypothesis 1: React State/Timing Issue
- **Test:** Test 1 (minimal SDK)
- **If true:** SDK works outside React, fails inside React
- **Fix:** Review React component lifecycle, useEffect dependencies

### Hypothesis 2: SDK Version Mismatch
- **Test:** Compare package.json versions
- **If true:** Our SDK version differs from working example
- **Fix:** Match SDK versions exactly

### Hypothesis 3: CORS or Network Issue
- **Test:** Test 3 (network inspection)
- **If true:** WebSocket connection fails or is blocked
- **Fix:** Check CORS headers, firewall, network proxy

### Hypothesis 4: Key Format Issue
- **Test:** Test 4 (manual key)
- **If true:** Manually provided key works, function-generated doesn't
- **Fix:** Review async key fetching pattern

### Hypothesis 5: Server Configuration Issue
- **Test:** Test 5 (server logs) + Test 2 (working example)
- **If true:** Our server behaves differently than working example
- **Fix:** Compare server implementations line by line

---

## 📝 Report Template

**After running tests, please provide:**

```
Test 1 (Minimal SDK):
- Result: [SUCCESS/FAILURE]
- Console output: [paste]

Test 2 (Working Example):
- Result: [WORKING/BROKEN]
- Observations: [describe]

Test 3 (Network Inspection):
- WebSocket status: [101 Switching Protocols / Failed]
- First message to Soniox: [paste JSON]
- Response from Soniox: [paste JSON or error]

Test 4 (Manual Key):
- Generated key: temp:...
- Result when used manually: [SUCCESS/FAILURE]

Test 5 (Server Logs):
- Server output during session start: [paste last 20 lines]
```

---

**Ready to isolate the issue!** 🔍

Start with **Test 1** - it's the quickest way to identify if the problem is in the SDK integration itself or in our React app.
