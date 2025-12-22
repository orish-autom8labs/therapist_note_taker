# Quick Start Guide - Note Taker SDK Version

**Branch:** `sdk-rewrite`
**Last Updated:** 2025-12-22

---

## 🚀 Start the Application (2 Steps)

### Terminal 1: Start Server
```bash
cd /Users/orish/code/note_taker/server
source venv/bin/activate
python run.py
```

**Expected output:**
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:3001
```

### Terminal 2: Start Client
```bash
cd /Users/orish/code/note_taker/client
npm start
```

**Expected output:**
```
Compiled successfully!

You can now view note-taker-client in the browser.

  Local:            http://localhost:3000
  On Your Network:  http://192.168.x.x:3000
```

---

## 🎯 Quick Test (5 Minutes)

### 1. Open Browser
Navigate to: **http://localhost:3000**

### 2. Login
Click "Continue with Google" → Authorize Drive access

### 3. Create Session
- Enter patient name: **"Test Patient"**
- Click **"Start Session"**

### 4. Verify Features

**Audio Visualizer (Green Bars):**
- Should show 32 vertical bars
- Bars should move when you speak
- Green color indicates recording

**Session Timer:**
- Shows elapsed time (e.g., 0:45)
- Shows remaining time (e.g., 59:15)
- Progress bar is green and filling

**Recording Indicator:**
- Red pulsing dot with "Recording..." text

**Transcription:**
- Speak in Hebrew
- Text appears in real-time
- Gray italic = updating (non-final)
- Dark text = confirmed (final)

**Speaker Diarization:**
- Have someone else speak
- See "Speaker 0:", "Speaker 1:" labels

### 5. Auto-Save Test
- Wait 1 minute
- Open browser console (F12)
- Look for: `[SYNC] Auto-saved transcript`
- Check Google Drive for temp file

### 6. Stop Session
- Click **"Stop & Save"**
- See success screen
- Click **"View in Drive"**
- Verify file exists with correct name

---

## ⚠️ Troubleshooting

### Server Won't Start

**Problem:** `SONIOX_API_KEY is not set`

**Solution:**
```bash
cd /Users/orish/code/note_taker/server
cat .env  # Verify file exists

# If missing, create it:
echo "SONIOX_API_KEY=2dab2363efa962920fa6574e738b15b08da198e1eb8f1a0ff25ad1a6b023be8a" > .env
echo "TRANSCRIPTION_PROVIDER=soniox" >> .env
```

### Client Won't Start

**Problem:** `Module not found: @soniox/speech-to-text-web`

**Solution:**
```bash
cd /Users/orish/code/note_taker/client
npm install
```

### No Microphone Access

**Problem:** Audio visualizer stays gray, no transcription

**Solution:**
1. Browser will prompt for microphone access
2. Click "Allow"
3. If denied, check browser settings:
   - Chrome: Settings → Privacy → Site Settings → Microphone
   - Firefox: Preferences → Privacy → Permissions → Microphone
4. Refresh page after granting permission

### Transcription Not Appearing

**Problem:** Audio visualizer works, but no text

**Solution:**
1. Check browser console (F12) for errors
2. Verify server is running (Terminal 1 should show activity)
3. Check that you're speaking in Hebrew (SDK configured for Hebrew)
4. Try speaking louder/clearer

### Temporary API Key Fails

**Problem:** Console error: "Failed to get temporary API key"

**Solution:**
1. Verify server is running on port 3001
2. Test endpoint manually:
   ```bash
   curl -X POST http://localhost:3001/v1/auth/temporary-api-key
   ```
3. Should return: `{"apiKey":"temp:..."}`
4. If error, check server `.env` file has correct `SONIOX_API_KEY`

### Drive Save Fails

**Problem:** "Failed to save to Drive"

**Solution:**
1. Verify Google OAuth tokens are valid
2. Re-login: Logout and login again
3. Check Drive API is enabled in Google Cloud Console
4. Verify OAuth consent screen is configured

---

## 🎨 Feature Verification

### Audio Visualizer ✅
- **Location:** Below session timer
- **Appearance:** 32 green bars
- **Test:** Speak → bars should move
- **Issue:** Bars don't move → Check microphone access

### Session Timer ✅
- **Location:** Top of session
- **Display:** Elapsed / Remaining
- **Test:** Wait 1 minute → elapsed should show 1:00
- **Colors:**
  - 0-45 min: Green
  - 45-55 min: Orange warning
  - 55-60 min: Red critical
  - 60 min: Auto-stops

### Transcription ✅
- **Direction:** Right-to-left (RTL) for Hebrew
- **Non-final:** Gray italic with "(updating...)"
- **Final:** Dark text
- **Test:** Speak → see text appear in real-time

### Speaker Diarization ✅
- **Display:** "Speaker 0:", "Speaker 1:", etc.
- **Test:** Two people speak → labels appear
- **Note:** Labels appear only when speaker changes

### Auto-Save ✅
- **Frequency:** Every 1 minute
- **Verify:** Browser console → `[SYNC] Auto-saved`
- **Drive:** Check for `.temp_` files in Drive

---

## 📊 Expected Behavior

### Successful Session Flow

1. **Start (0:00)**
   - Login screen → OAuth
   - Patient name entry
   - Click "Start Session"

2. **Recording (0:01 - 59:59)**
   - Audio visualizer animating
   - Timer counting (green)
   - Transcription appearing
   - Auto-saves every 1 min

3. **Warning (45:00)**
   - Timer turns orange
   - Yellow banner: "⚠️ 15 minutes remaining"

4. **Critical (55:00)**
   - Timer turns red
   - Red banner: "🔴 5 minutes remaining"

5. **Auto-Stop (60:00)** OR **Manual Stop**
   - Transcription stops
   - Final save to Drive
   - Email notification sent
   - Success screen shows

6. **Success Screen**
   - Shows file name
   - "View in Drive" button works
   - Can start new session

---

## 🔍 Console Debug Messages

### Good Messages (Expected)
```
[SESSION] Transcription started
[TIMER] Warning: warning, 15 minutes remaining
[TIMER] Warning: critical, 5 minutes remaining
[SYNC] Auto-saved transcript
[SESSION] Final save result: {...}
[SESSION] Stopping session...
```

### Bad Messages (Need Attention)
```
[ERROR] Failed to get temporary API key
[ERROR] Failed to save final transcript
[SONIOX] Transcription error: ...
[AUDIO] Failed to get microphone: ...
```

---

## 📝 Testing Checklist

### Quick Test (5 min)
- [ ] Server starts without errors
- [ ] Client starts without errors
- [ ] Login works (Google OAuth)
- [ ] Patient name accepts Hebrew characters
- [ ] Session starts (mic access granted)
- [ ] Audio visualizer shows green bars
- [ ] Timer starts counting
- [ ] Speak → transcription appears
- [ ] Stop → file saves to Drive

### Full Test (15 min)
- [ ] All quick test items
- [ ] Wait 1 minute → auto-save logs appear
- [ ] Speaker diarization (2 people speak)
- [ ] Non-final tokens show as gray italic
- [ ] Final tokens show as dark text
- [ ] localStorage saves every 5 sec
- [ ] Stop session → email sent
- [ ] "View in Drive" button works
- [ ] File content is correct (speakers + text)

### Stress Test (60 min - Optional)
- [ ] Session runs for 45 minutes → yellow warning
- [ ] Session runs for 55 minutes → red warning
- [ ] Session runs for 60 minutes → auto-stop
- [ ] Long transcription (lots of text)
- [ ] Many speaker changes

---

## 🎓 Tips

1. **Hebrew Keyboard:** Make sure Hebrew input is enabled for patient name
2. **Microphone Quality:** Better mic = better transcription
3. **Quiet Environment:** Less background noise = better accuracy
4. **Speaker Distance:** Speak 30-50cm from microphone
5. **Clear Speech:** Speak clearly and at normal pace
6. **Multiple Speakers:** Wait ~1 second between speakers for better diarization

---

## 📞 Support

### Check Documentation
- `IMPLEMENTATION_COMPLETE.md` - Full technical details
- `PHASE1_SDK_VERIFICATION.md` - SDK architecture explained
- `HANDOVER_DOCUMENT.md` - Original project context

### Debug Steps
1. Check browser console (F12) for errors
2. Check server terminal for error messages
3. Verify `.env` file has correct API keys
4. Test Soniox API key:
   ```bash
   curl -X POST http://localhost:3001/v1/auth/temporary-api-key
   ```
5. Test Google Drive API (re-login if needed)

---

**Ready to test!** 🚀

Follow the "Quick Test (5 Minutes)" section above to verify everything works.
