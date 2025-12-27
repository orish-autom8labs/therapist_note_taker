# Product Requirements Document (PRD)
# Therapist Note Taker Application

**Version:** 1.0
**Last Updated:** December 27, 2025
**Product Owner:** Ori Shemesh
**Technical Stack:** React (Frontend), FastAPI (Backend), Soniox SDK (Speech-to-Text)

---

## Table of Contents
1. [Product Overview](#product-overview)
2. [Core Features](#core-features)
3. [Technical Architecture](#technical-architecture)
4. [Feature Specifications](#feature-specifications)
5. [User Flows](#user-flows)
6. [Testing Requirements](#testing-requirements)
7. [Configuration & Settings](#configuration--settings)
8. [Security & Privacy](#security--privacy)
9. [Performance Requirements](#performance-requirements)
10. [Future Enhancements](#future-enhancements)

---

## Product Overview

### Purpose
A secure, real-time transcription application designed for therapists conducting Hebrew-language therapy sessions. The application provides live speech-to-text transcription with speaker identification, automatically saves transcripts to the therapist's Google Drive, and ensures no audio recordings are stored anywhere.

### Target Users
- Mental health professionals (therapists, psychologists, counselors)
- Healthcare providers conducting Hebrew-language sessions
- Professionals requiring secure, compliant session documentation

### Key Value Propositions
1. **Privacy-First**: No audio recordings stored; only text transcripts
2. **Real-Time**: Live transcription during sessions with Hebrew language support
3. **Speaker Identification**: Automatic differentiation between therapist and patient
4. **Seamless Integration**: Direct save to Google Drive (Clinic/Transcripts folder)
5. **Long Session Support**: Handles up to 60-minute sessions with automatic token refresh

---

## Core Features

### 1. Authentication & Authorization
- **Google OAuth 2.0 Integration**
  - Secure login via Google account
  - Access to user's Google Drive
  - Automatic token refresh for extended sessions
  - Proper logout with token cleanup

### 2. Real-Time Speech-to-Text Transcription
- **Soniox SDK Integration**
  - Model: `stt-rt-v3` (real-time v3)
  - Hebrew language support with language identification
  - Speaker diarization (Speaker 1 vs Speaker 2)
  - Handles both final and non-final tokens
  - Audio visualization (32-bar waveform)

### 3. Session Management
- **Session Timer**
  - 60-minute maximum session duration
  - Warning at 45 minutes (15 minutes remaining)
  - Critical warning at 55 minutes (5 minutes remaining)
  - Automatic session stop at 60 minutes
  - Visual progress bar
  - Real-time elapsed/remaining time display

- **Auto-Save Functionality**
  - Saves to Google Drive every 1 minute
  - Creates temporary file during session
  - Final save with proper filename on session end
  - Filename format: `{PatientName}_{YYYY-MM-DD}_{HH-MM-SS}.txt`

- **Local Recovery**
  - Saves to localStorage every 5 seconds
  - Recovery dialog on app reload if unsaved session exists
  - Option to recover or discard previous session

### 4. Transcript Management
- **Display**
  - Right-to-left (RTL) text for Hebrew
  - Speaker labels color-coded
  - Real-time update as transcription occurs
  - Final vs non-final text styling (italic for non-final)
  - Auto-scroll to latest content

- **Formatting**
  - Speaker identification: "Speaker 1:", "Speaker 2:"
  - Timestamp for each chunk
  - Paragraph breaks on speaker change
  - Handles `<end>` tokens properly

### 5. Google Drive Integration
- **Storage**
  - Folder: `Clinic/Transcripts`
  - Creates folder structure if doesn't exist
  - Plain text (.txt) format
  - Shareable link generation

- **Auto-Save During Session**
  - Temporary file: `.temp_{PatientName}_{date}_{time}.txt`
  - Updated every 1 minute
  - Deleted after final save

- **Final Save**
  - Renames temporary file to final filename
  - Or creates new file if no temp file exists
  - Returns web view link for immediate access

### 6. Email Notifications (Optional)
- **Session Complete Email**
  - Recipient: Configured email address
  - Subject: "Session Complete - [Patient Name]"
  - Body: Link to Google Drive transcript
  - Non-blocking (doesn't fail if email fails)

### 7. Audio Visualization
- **Real-Time Waveform**
  - 32 vertical bars
  - Updates based on microphone input
  - Active only during recording
  - Visual feedback for audio levels

---

## Technical Architecture

### Frontend (React)
```
client/
├── src/
│   ├── components/
│   │   ├── LoginScreen.js          # Google OAuth login
│   │   ├── SessionSetup.js         # Patient name input, logout
│   │   ├── ActiveSession.js        # Main recording interface
│   │   ├── SessionTimer.js         # Timer display with warnings
│   │   ├── AudioVisualizer.js      # 32-bar waveform
│   │   ├── SuccessScreen.js        # Post-session summary
│   │   └── RecoveryDialog.js       # Recovery from localStorage
│   ├── hooks/
│   │   ├── useSonioxClient.js      # Soniox SDK wrapper
│   │   ├── useSessionTimer.js      # Timer logic with warnings
│   │   └── useAudioVisualizer.js   # Audio analysis
│   ├── services/
│   │   ├── authService.js          # OAuth URL generation
│   │   ├── transcriptSyncService.js # Server sync (auto-save)
│   │   └── recoveryService.js      # localStorage management
│   ├── config/
│   │   └── sessionConfig.js        # Centralized configuration
│   └── App.js                      # Main app with routing
```

### Backend (FastAPI/Python)
```
server/
├── main.py                         # API endpoints
├── src/
│   ├── config.py                   # Environment configuration
│   ├── services/
│   │   ├── drive_service.py        # Google Drive operations
│   │   ├── email_service.py        # Email notifications
│   │   └── transcription_service.py # Soniox temporary API keys
│   └── providers/
│       └── soniox_provider.py      # Soniox integration
```

### Key Endpoints
1. **GET** `/v1/auth/google-auth-url` - Get OAuth URL
2. **POST** `/v1/auth/temporary-api-key` - Get Soniox temp key
3. **POST** `/api/sessions/{session_id}/transcript` - Save transcript
4. **GET** `/health` - Health check

---

## Feature Specifications

### F1: User Authentication

**Requirement ID:** AUTH-001
**Priority:** Critical
**Status:** Implemented

#### Description
Secure Google OAuth 2.0 authentication with automatic token refresh for extended sessions.

#### Acceptance Criteria
- [ ] User can click "Sign in with Google" and authenticate
- [ ] Access token and refresh token stored in localStorage
- [ ] Tokens automatically refresh when access token expires (~1 hour)
- [ ] User can logout, clearing all tokens
- [ ] User remains logged in after page refresh (until logout)
- [ ] Re-authentication required only when refresh token expires (weeks/months)

#### Test Cases
| Test ID | Scenario | Expected Result |
|---------|----------|-----------------|
| AUTH-T001 | First-time login | Redirects to Google OAuth, returns with tokens, shows setup screen |
| AUTH-T002 | Page refresh while logged in | User stays logged in, no re-authentication needed |
| AUTH-T003 | Logout | Tokens cleared, redirected to login screen |
| AUTH-T004 | Login after logout | Fresh OAuth flow, new tokens obtained |
| AUTH-T005 | Access token expires (1 hour) | Automatic token refresh, no user interruption |
| AUTH-T006 | Refresh token expires (weeks) | User prompted to re-authenticate with clear message |

---

### F2: Real-Time Transcription

**Requirement ID:** TRANS-001
**Priority:** Critical
**Status:** Implemented

#### Description
Live Hebrew speech-to-text transcription using Soniox SDK with speaker identification.

#### Acceptance Criteria
- [ ] Transcription starts immediately when session begins
- [ ] Hebrew text appears in real-time (within 1-2 seconds)
- [ ] Speaker labels correctly identify different speakers
- [ ] Final vs non-final text visually distinguished
- [ ] No audio is recorded or stored
- [ ] Handles `<end>` tokens properly (paragraph breaks)

#### Test Cases
| Test ID | Scenario | Expected Result |
|---------|----------|-----------------|
| TRANS-T001 | Single speaker Hebrew | Text appears with "Speaker 1:" label |
| TRANS-T002 | Two speakers alternating | Correct speaker labels (Speaker 1, Speaker 2) |
| TRANS-T003 | Long continuous speech | Text continues to accumulate without loss |
| TRANS-T004 | Silence periods | Non-final text appears, then finalizes |
| TRANS-T005 | Background noise | Transcription continues, noise filtered |
| TRANS-T006 | Microphone disconnected | Error message displayed, graceful handling |
| TRANS-T007 | Network interruption | SDK handles reconnection, transcription resumes |

---

### F3: Session Timer

**Requirement ID:** TIMER-001
**Priority:** High
**Status:** Implemented

#### Description
60-minute session timer with warnings and automatic stop functionality.

#### Acceptance Criteria
- [ ] Timer starts when session begins
- [ ] Elapsed and remaining time displayed in MM:SS format
- [ ] Progress bar fills from 0% to 100% over 60 minutes
- [ ] Yellow warning banner at 45 minutes
- [ ] Red critical warning banner at 55 minutes (pulsing)
- [ ] Automatic session stop at 60 minutes
- [ ] 2-second delay before auto-stop for user awareness

#### Test Cases
| Test ID | Scenario | Expected Result |
|---------|----------|-----------------|
| TIMER-T001 | Session start | Timer shows 0:00 elapsed, 60:00 remaining |
| TIMER-T002 | Timer running | Time updates every second, progress bar advances |
| TIMER-T003 | 45 minutes reached | Yellow warning banner appears, shows "15:00 remaining" |
| TIMER-T004 | 55 minutes reached | Red critical banner replaces yellow, shows "5:00 remaining" |
| TIMER-T005 | 60 minutes reached | Auto-stop triggers, transcript saved, redirect to success |
| TIMER-T006 | Manual stop before 60 min | Timer stops, transcript saved immediately |
| TIMER-T007 | Timer visual accuracy | Elapsed + Remaining always equals 60:00 |

---

### F4: Auto-Save to Google Drive

**Requirement ID:** SAVE-001
**Priority:** Critical
**Status:** Implemented

#### Description
Automatic periodic saves to Google Drive with final save on session completion.

#### Acceptance Criteria
- [ ] Saves every 1 minute during session
- [ ] Creates `Clinic/Transcripts` folder if doesn't exist
- [ ] Temporary file created: `.temp_{PatientName}_{date}_{time}.txt`
- [ ] Final filename: `{PatientName}_{YYYY-MM-DD}_{HH-MM-SS}.txt`
- [ ] Returns Google Drive web view link
- [ ] Handles token refresh during save
- [ ] Graceful error handling with user notification

#### Test Cases
| Test ID | Scenario | Expected Result |
|---------|----------|-----------------|
| SAVE-T001 | First auto-save (1 min) | Temporary file created in Clinic/Transcripts |
| SAVE-T002 | Subsequent auto-saves | Temporary file updated with new content |
| SAVE-T003 | Session end (stop button) | Final file created, temp file deleted, link returned |
| SAVE-T004 | Session end (auto-stop) | Same as SAVE-T003 |
| SAVE-T005 | Folder doesn't exist | Clinic/Transcripts folder created automatically |
| SAVE-T006 | Token expired during save | Token refreshed automatically, save succeeds |
| SAVE-T007 | Network error during save | Error message shown, retry mechanism available |
| SAVE-T008 | Drive quota exceeded | Clear error message, suggests cleanup |

---

### F5: Local Recovery

**Requirement ID:** RECOV-001
**Priority:** Medium
**Status:** Implemented

#### Description
Auto-save to localStorage every 5 seconds with recovery dialog on page reload.

#### Acceptance Criteria
- [ ] Transcript saved to localStorage every 5 seconds
- [ ] Recovery dialog appears if unsaved session detected
- [ ] Shows patient name and last save timestamp
- [ ] Option to recover or discard
- [ ] Recovery restores full transcript state
- [ ] localStorage cleared after successful final save

#### Test Cases
| Test ID | Scenario | Expected Result |
|---------|----------|-----------------|
| RECOV-T001 | Page refresh during session | Recovery dialog appears with patient name |
| RECOV-T002 | Choose "Recover" | Session restored with full transcript |
| RECOV-T003 | Choose "Discard" | New session starts, localStorage cleared |
| RECOV-T004 | Normal session end | localStorage cleared automatically |
| RECOV-T005 | Browser crash | Recovery available on restart |
| RECOV-T006 | Multiple browser tabs | Each tab has independent recovery |

---

### F6: Audio Visualization

**Requirement ID:** VIZ-001
**Priority:** Low
**Status:** Implemented

#### Description
Real-time 32-bar audio waveform visualization for user feedback.

#### Acceptance Criteria
- [ ] 32 vertical bars displayed
- [ ] Bars respond to microphone input levels
- [ ] Active only when recording
- [ ] Smooth animation
- [ ] No performance impact on transcription

#### Test Cases
| Test ID | Scenario | Expected Result |
|---------|----------|-----------------|
| VIZ-T001 | Session start | Bars animate based on audio |
| VIZ-T002 | Silence | Bars show minimal activity |
| VIZ-T003 | Loud speech | Bars reach higher levels |
| VIZ-T004 | Session stop | Bars stop animating |
| VIZ-T005 | Microphone denied | Visualization gracefully disabled |

---

### F7: Email Notifications

**Requirement ID:** EMAIL-001
**Priority:** Low
**Status:** Implemented (Optional)

#### Description
Optional email notification on session completion with Drive link.

#### Acceptance Criteria
- [ ] Email sent only if configured (non-blocking)
- [ ] Contains patient name in subject
- [ ] Contains Google Drive link in body
- [ ] Failure doesn't prevent session completion
- [ ] Logs email send status

#### Test Cases
| Test ID | Scenario | Expected Result |
|---------|----------|-----------------|
| EMAIL-T001 | Session end with email config | Email sent with Drive link |
| EMAIL-T002 | Session end without email config | Session completes normally, no email attempt |
| EMAIL-T003 | Email service unavailable | Session completes, error logged, user unaffected |
| EMAIL-T004 | Invalid email address | Session completes, error logged |

---

## User Flows

### Flow 1: First-Time User - Complete Session

```
1. User opens application
2. Sees Login Screen
3. Clicks "Sign in with Google"
4. Redirected to Google OAuth consent
5. Grants Drive access permissions
6. Redirected back to app
7. Sees Session Setup screen
8. Enters patient name: "John Doe"
9. Clicks "Start Session"
10. Recording screen appears
    - Timer starts at 0:00
    - Microphone access requested
    - Audio visualizer starts
    - "Recording..." indicator shows
11. User speaks in Hebrew
12. Transcript appears in real-time
    - Speaker labels appear
    - Text flows right-to-left
    - Auto-scroll to latest
13. At 1 minute: Auto-save to Drive (silent)
14. At 45 minutes: Yellow warning banner
15. At 55 minutes: Red critical warning
16. User clicks "Stop & Save" button
17. Final save to Drive
18. Success screen shows:
    - "Session saved successfully"
    - "View in Drive" link (active)
    - "Start New Session" button
19. Clicks "View in Drive"
20. Google Drive opens with transcript file
```

### Flow 2: Returning User - Session with Recovery

```
1. User opens application
2. Automatically logged in (tokens from localStorage)
3. Sees Session Setup screen
4. Enters patient name: "Jane Smith"
5. Clicks "Start Session"
6. Recording starts
7. After 10 minutes, browser crashes
8. User reopens application
9. Recovery dialog appears:
   - "Recover unsaved session for Jane Smith?"
   - "Last saved: 2 seconds ago"
   - [Recover] [Discard] buttons
10. Clicks "Recover"
11. Recording screen restores with transcript
12. User continues session
13. Clicks "Stop & Save"
14. Transcript saved to Drive
15. Success screen displays
```

### Flow 3: Token Refresh During Long Session

```
1. User starts 45-minute session
2. Access token valid initially
3. At 30 minutes: Auto-save triggers
4. Server detects token will expire soon
5. Server refreshes token automatically
6. New tokens returned to client
7. Client updates tokens in state and localStorage
8. Save completes successfully
9. User sees no interruption
10. Session continues normally
11. At 45 minutes: Next auto-save uses refreshed tokens
12. Session completes successfully
```

### Flow 4: Logout and Re-login

```
1. User on Session Setup screen
2. Clicks "← Logout" button
3. Confirmation (optional): "Are you sure?"
4. Tokens cleared from localStorage
5. User state cleared
6. Redirected to Login screen
7. User clicks "Sign in with Google"
8. Google OAuth flow (may skip consent if recent)
9. New tokens obtained
10. Session Setup screen appears
11. Ready for new session
```

---

## Testing Requirements

### Test Environments

#### 1. Development Environment
- **Purpose**: Feature development and unit testing
- **Frontend**: `http://localhost:3000`
- **Backend**: `http://localhost:3001`
- **Configuration**: Test mode (30-second sessions optional)

#### 2. Staging Environment
- **Purpose**: Integration testing and QA
- **Frontend**: Deployed URL (staging)
- **Backend**: Staging server
- **Configuration**: Production settings, test Google account

#### 3. Production Environment
- **Purpose**: Live user testing and final validation
- **Frontend**: Production URL
- **Backend**: Production server
- **Configuration**: Production settings, real credentials

### Testing Checklist (All Features)

#### Pre-Release Testing Checklist

**Authentication & Authorization**
- [ ] AUTH-T001: First-time login flow
- [ ] AUTH-T002: Page refresh persistence
- [ ] AUTH-T003: Logout functionality
- [ ] AUTH-T004: Re-login after logout
- [ ] AUTH-T005: Token auto-refresh (>1 hour session)
- [ ] AUTH-T006: Expired refresh token handling

**Transcription**
- [ ] TRANS-T001: Single speaker Hebrew
- [ ] TRANS-T002: Two speakers alternating
- [ ] TRANS-T003: Long continuous speech (30+ min)
- [ ] TRANS-T004: Silence handling
- [ ] TRANS-T005: Background noise tolerance
- [ ] TRANS-T006: Microphone permission denied
- [ ] TRANS-T007: Network interruption recovery

**Session Timer**
- [ ] TIMER-T001: Timer initialization
- [ ] TIMER-T002: Timer accuracy (compare to stopwatch)
- [ ] TIMER-T003: 45-minute warning
- [ ] TIMER-T004: 55-minute critical warning
- [ ] TIMER-T005: 60-minute auto-stop
- [ ] TIMER-T006: Manual stop before 60 min
- [ ] TIMER-T007: Time display accuracy

**Google Drive Integration**
- [ ] SAVE-T001: First auto-save (1 min)
- [ ] SAVE-T002: Subsequent auto-saves
- [ ] SAVE-T003: Final save on manual stop
- [ ] SAVE-T004: Final save on auto-stop
- [ ] SAVE-T005: Folder creation
- [ ] SAVE-T006: Token refresh during save
- [ ] SAVE-T007: Network error handling
- [ ] SAVE-T008: Drive quota error

**Local Recovery**
- [ ] RECOV-T001: Page refresh detection
- [ ] RECOV-T002: Recovery workflow
- [ ] RECOV-T003: Discard workflow
- [ ] RECOV-T004: Cleanup after normal end
- [ ] RECOV-T005: Browser crash recovery
- [ ] RECOV-T006: Multiple tabs independence

**Audio Visualization**
- [ ] VIZ-T001: Visualization during recording
- [ ] VIZ-T002: Silence display
- [ ] VIZ-T003: Loud speech display
- [ ] VIZ-T004: Stop behavior
- [ ] VIZ-T005: Permission denied fallback

**Email Notifications**
- [ ] EMAIL-T001: Email with config
- [ ] EMAIL-T002: No email without config
- [ ] EMAIL-T003: Email failure handling
- [ ] EMAIL-T004: Invalid address handling

**Cross-Browser Testing**
- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)
- [ ] Mobile Chrome (Android)
- [ ] Mobile Safari (iOS)

**Performance Testing**
- [ ] 60-minute session without lag
- [ ] Smooth scrolling with 1000+ tokens
- [ ] Audio visualizer doesn't impact transcription
- [ ] Memory usage stable over time
- [ ] CPU usage acceptable (<30% average)

**Security Testing**
- [ ] Tokens stored securely
- [ ] No tokens in URL or logs
- [ ] OAuth flow secure (no CSRF)
- [ ] Drive access limited to required scopes
- [ ] No audio recording stored

---

## Configuration & Settings

### Client Configuration
**File**: `client/src/config/sessionConfig.js`

```javascript
const sessionConfig = {
  maxDuration: 60 * 60 * 1000,    // 60 minutes (change to 30 * 1000 for testing)
  autoSaveInterval: 60 * 1000,     // 1 minute
  warningThreshold: 3/4,            // Warning at 45 minutes
  criticalThreshold: 11/12,         // Critical at 55 minutes
};
```

### Server Configuration
**File**: `server/.env`

```env
# Soniox API
SONIOX_API_KEY=your_soniox_api_key

# Google Drive OAuth
GOOGLE_DRIVE_CLIENT_ID=your_client_id
GOOGLE_DRIVE_CLIENT_SECRET=your_client_secret
GOOGLE_DRIVE_REDIRECT_URI=http://localhost:3000

# Email (Optional)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_FROM=your_email@gmail.com
SMTP_TO=recipient@gmail.com

# Server
PORT=3001
```

### Environment-Specific Settings

| Setting | Development | Staging | Production |
|---------|-------------|---------|------------|
| Session Duration | 30s (testing) | 60 min | 60 min |
| API Base URL | localhost:3001 | staging-api.example.com | api.example.com |
| Frontend URL | localhost:3000 | staging.example.com | example.com |
| Google OAuth Redirect | localhost:3000 | staging.example.com | example.com |
| Email Enabled | No | Yes | Yes |
| Debug Logging | Verbose | Moderate | Minimal |

---

## Security & Privacy

### Data Security

**No Audio Recording**
- ✅ Audio is processed in real-time by Soniox SDK
- ✅ No audio files saved to disk
- ✅ No audio sent to our servers
- ✅ Only text transcript is stored

**OAuth Token Security**
- ✅ Tokens stored in localStorage (not cookies)
- ✅ No tokens in URL parameters
- ✅ Automatic token refresh (no re-login needed)
- ✅ Tokens cleared on logout

**Google Drive Access**
- ✅ Minimal scope: `drive.file` (only files created by app)
- ✅ Files stored in user's own Drive
- ✅ User controls file sharing/deletion
- ✅ No server-side file access

### Privacy Compliance

**HIPAA Considerations**
- ✅ No PHI stored on our servers
- ✅ Transcripts stored in user's Drive (BAA required from Google)
- ✅ Therapist responsible for Drive security
- ✅ No third-party access to transcripts

**GDPR Considerations**
- ✅ User controls their data (Google Drive)
- ✅ Right to deletion (user deletes from Drive)
- ✅ Data portability (export from Drive)
- ✅ Minimal data collection

### Security Best Practices

**Server**
- [ ] HTTPS only in production
- [ ] CORS configured properly
- [ ] Rate limiting on API endpoints
- [ ] Input validation on all endpoints
- [ ] Secure environment variable storage

**Client**
- [ ] Content Security Policy (CSP)
- [ ] No sensitive data in console logs (production)
- [ ] XSS protection
- [ ] Sanitize user inputs

---

## Performance Requirements

### Response Times
- Login flow: < 3 seconds
- Transcription latency: < 2 seconds (from speech to text)
- Auto-save: < 5 seconds
- Final save: < 10 seconds
- Page load: < 2 seconds

### Resource Usage
- Memory: < 500 MB sustained
- CPU: < 30% average during transcription
- Network: < 1 MB/minute sustained

### Scalability
- Support 60-minute continuous sessions
- Handle 10,000+ transcript tokens
- Support concurrent users (server-side)

---

## Future Enhancements

### Planned Features (Not Yet Implemented)

**P1: High Priority**
1. **Custom Session Durations**
   - User-configurable max duration (30, 45, 60, 90 minutes)
   - Settings page to save preference
   - Per-user settings stored in backend

2. **Transcript Editing**
   - Edit transcript after session ends
   - Save edited version to Drive
   - Track editing history

3. **Export Formats**
   - PDF export with formatting
   - DOCX export for Word
   - JSON export for data analysis

4. **Session Notes**
   - Add notes/annotations during session
   - Tag important moments
   - Searchable notes in Drive

**P2: Medium Priority**
5. **Multi-Language Support**
   - English transcription
   - Arabic transcription
   - UI language switching

6. **Session History**
   - List of past sessions
   - Quick access to Drive files
   - Search past transcripts

7. **Analytics Dashboard**
   - Session duration statistics
   - Word count metrics
   - Speaker balance analysis

8. **Templates**
   - Pre-defined session templates
   - Custom fields per template
   - Auto-fill patient information

**P3: Low Priority**
9. **Mobile App**
   - Native iOS app
   - Native Android app
   - Offline support

10. **Team Features**
    - Multiple therapists in organization
    - Shared template library
    - Admin dashboard

---

## Appendix

### A. Glossary

| Term | Definition |
|------|------------|
| **Access Token** | Short-lived OAuth token (~1 hour) for API access |
| **Refresh Token** | Long-lived token (weeks/months) to obtain new access tokens |
| **Speaker Diarization** | Identifying which speaker said what |
| **Non-Final Token** | Preliminary transcription result (may change) |
| **Final Token** | Confirmed transcription result (stable) |
| **Auto-Save** | Periodic save to Drive during session |
| **Recovery** | Restoring session from localStorage after crash |
| **Session Timer** | 60-minute countdown with warnings |

### B. Dependencies

**Frontend**
- React 18.x
- @soniox/speech-to-text-web 1.2.0+
- Modern browser with Web Audio API

**Backend**
- Python 3.8+
- FastAPI 0.100+
- Google API Client
- Soniox Python SDK

**External Services**
- Soniox Speech-to-Text API
- Google Drive API
- Google OAuth 2.0
- SMTP Server (optional)

### C. Support & Maintenance

**Issue Reporting**
- GitHub Issues: https://github.com/orish-autom8labs/therapist_note_taker/issues
- Email: support@example.com (if configured)

**Documentation**
- README.md: Setup instructions
- PRD.md: This document
- client/src/config/README.md: Configuration guide

**Version Control**
- Repository: https://github.com/orish-autom8labs/therapist_note_taker
- Branch: `sdk-rewrite` (current active branch)
- Main branch: TBD (after testing)

---

**Document Version History**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-12-27 | Ori Shemesh / Claude | Initial comprehensive PRD with all implemented features |

---

**Approval Sign-off**

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Product Owner | Ori Shemesh | _____________ | _______ |
| Technical Lead | | _____________ | _______ |
| QA Lead | | _____________ | _______ |
