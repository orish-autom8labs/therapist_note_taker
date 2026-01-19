# Note Taker Testing Plan

**Last Updated**: 2025-01-18
**Status**: IN PROGRESS

## Current Focus

Investigating transcript hang-ups during long sessions.

## Test Environment

- **App URL**: http://localhost:3000
- **API URL**: http://localhost:3001
- **Audio Source**: YouTube video https://www.youtube.com/watch?v=TXBxu2YjyyM
- **Browser**: Chrome (via Playwright)

---

## Test Scenarios

### T1: Basic Flow (Smoke Test)
**Objective**: Verify basic transcription works

| Step | Action | Expected | Actual | Status |
|------|--------|----------|--------|--------|
| 1 | Open app at localhost:3000 | App loads | | PENDING |
| 2 | Login with Google | Redirects to session setup | | PENDING |
| 3 | Enter patient name | Form accepts input | | PENDING |
| 4 | Start session | Recording indicator shows | | PENDING |
| 5 | Play YouTube audio (30s) | Transcript appears | | PENDING |
| 6 | Stop session | Success screen with Drive link | | PENDING |

### T2: Extended Session (Hang-up Detection)
**Objective**: Detect if/when transcription hangs

| Step | Action | Expected | Actual | Status |
|------|--------|----------|--------|--------|
| 1 | Start session | Recording starts | | PENDING |
| 2 | Play YouTube audio continuously | | | PENDING |
| 3 | Monitor at 1 min mark | Transcript flowing | | PENDING |
| 4 | Monitor at 2 min mark | Transcript flowing | | PENDING |
| 5 | Monitor at 5 min mark | Transcript flowing | | PENDING |
| 6 | Check console for errors | No errors | | PENDING |

### T3: Background Tab Test
**Objective**: Test browser throttling behavior

| Step | Action | Expected | Actual | Status |
|------|--------|----------|--------|--------|
| 1 | Start session with audio | Transcript flowing | | PENDING |
| 2 | Switch to different tab (30s) | Warning should appear | | PENDING |
| 3 | Return to app tab | Transcript resumes | | PENDING |
| 4 | Check for data loss | Minimal loss expected | | PENDING |

### T4: Summarization Test
**Objective**: Verify LLM summarization works

| Step | Action | Expected | Actual | Status |
|------|--------|----------|--------|--------|
| 1 | Complete 3+ min session | Session saved | | PENDING |
| 2 | Wait for summarization | Summary generated | | PENDING |
| 3 | Check Google Drive | Summary file exists | | PENDING |
| 4 | Verify summary quality | Coherent content | | PENDING |

---

## Console Log Monitoring

### Key Prefixes to Watch
- `[SONIOX]` - WebSocket and transcription events
- `[DEBUG]` - General debug info
- `[HOOK]` - React hook state changes
- `[WAKE LOCK]` - Screen lock status
- `[VISIBILITY]` - Tab visibility changes
- `[SYNC]` - Auto-save events

### Error Patterns to Flag
- `WebSocket is closed`
- `Connection closed`
- `Error 408` (timeout)
- `api_key_fetch_failed`
- Stall detection triggers

---

## Findings Log

### Session 1: 2025-01-18 ~21:45
**Setup Status**: VERIFIED
- [x] Backend running on :3001 (Soniox provider)
- [x] Frontend running on :3000
- [x] YouTube video loaded and playing (Betipul S01E44 - Hebrew therapy show, 30 min)
- [x] Playwright browser control working

**Blockers for Full Test**:
1. Google OAuth sign-in required (needs user interaction)
2. Audio routing: YouTube → microphone (needs virtual audio cable OR speakers+mic)

**Next Steps**:
- User to sign in with Google
- Confirm audio routing method
- Run test scenarios

### Test 1: Playwright Browser Test (FAILED - Expected)
**Time**: 21:41-21:42
**Duration**: 48 seconds
**Result**: NO TOKENS CAPTURED

**Findings**:
- Soniox connection: SUCCESS (API key fetched, WebSocket opened)
- Audio processing: SUCCESS (`total_audio_proc_ms` reached 42000+)
- Speech detection: FAILED (0 tokens returned)
- Save to Drive: SUCCESS (empty transcript saved)

**Root Cause**: Playwright browser uses virtual/fake microphone that sends silence.
Soniox is receiving "audio" but it contains no recognizable speech.

**Conclusion**: Cannot test real transcription via Playwright.
Must use real browser with real microphone for hang-up investigation.

### Test 2: Real Browser Test (SUCCESS)
**Time**: ~21:45
**Duration**: 2 minutes
**Audio Source**: YouTube (Betipul) through speakers → microphone
**Result**: SUCCESS - No stalls, transcription worked continuously

**Findings**:
- Session ran 2 min without hang-ups
- Transcription flowed normally
- No errors reported

**Note**: Original hang-up reports were for longer sessions. Need extended testing.

---

## Root Cause Hypotheses

| Hypothesis | Evidence For | Evidence Against | Status |
|------------|--------------|------------------|--------|
| API key expires at 60s | Code sets 60s expiry | Soniox docs say key only for connection | DISPROVEN |
| Browser throttles background tabs | Wake lock added | Need to test | TESTING |
| WebSocket silently drops | 408 errors seen | No reconnection logic | TESTING |
| Audio stream suspends | Background warning added | Need to test | TESTING |

---

## Action Items

- [ ] Run T1 (basic flow) to verify setup
- [ ] Run T2 (extended session) to detect hang timing
- [ ] Capture console logs during failure
- [ ] Identify exact failure point
