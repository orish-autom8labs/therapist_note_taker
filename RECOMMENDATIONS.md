# MVP Recommendations & Technical Decisions

## Hebrew Transcription Service Selection

### Top Options for Hebrew STT:

1. **Soniox** ⭐ (Recommended for MVP)
   - Higher accuracy than Google for Hebrew
   - Real-time streaming support
   - Cost-effective
   - Speaker diarization available
   - API: `soniox.com`

2. **Speechmatics**
   - High accuracy for Hebrew (including dialects)
   - Real-time and batch processing
   - Speaker diarization
   - More expensive than Soniox
   - API: `speechmatics.com`

3. **Google Cloud Speech-to-Text**
   - Good Hebrew support (language code: `he-IL`)
   - Reliable infrastructure
   - Speaker diarization available
   - May have lower accuracy than specialized services
   - Good for integration with Google Drive

4. **OpenAI Whisper API**
   - Excellent accuracy
   - Hebrew support
   - No native speaker diarization (would need post-processing)
   - More expensive for real-time

### **Recommendation: Start with Soniox**
- Best Hebrew accuracy
- Real-time streaming
- Speaker diarization built-in
- Cost-effective for MVP testing
- Can switch later if needed

---

## UI/UX Design Decisions

### Layout Direction
**Question:** Should the UI be RTL (right-to-left) for Hebrew users?

**Recommendation:** 
- **RTL for transcript area** (Hebrew text)
- **LTR for UI controls** (standard web patterns)
- OR: Full RTL if user prefers (can be toggled)

### Patient Name Input
**Options:**
1. Free text only (simplest)
2. Dropdown with recent patients + free text

**Recommendation:** Start with **free text only** for MVP
- Less complexity
- Faster to build
- Can add autocomplete later

### Transcript Editing
**Decision:** **No editing in MVP** ✅
- Keep it minimal
- User can edit in Google Drive after saving
- Add editing feature in v2 if needed

### Transcript Display
**Decision:** **Real-time display** ✅
- Same technical complexity as end-only
- Better UX (user sees it working)
- Early error detection
- STT services support streaming natively
- See `TECHNICAL_ANALYSIS.md` for detailed comparison

### Error Recovery
**Decision:** **Hybrid approach** ✅
- **Primary:** Auto-save to Drive every 30 seconds (temp file)
- **Secondary:** LocalStorage backup every 5 seconds
- **Recovery UI:** Dialog to restore unsaved sessions
- **Maximum data loss:** 5-30 seconds
- See `TECHNICAL_ANALYSIS.md` for implementation details

---

## Technical Architecture

### Frontend Stack
- **Framework:** React + TypeScript (or Next.js for SSR)
- **Styling:** Tailwind CSS (or styled-components)
- **State Management:** React Context / Zustand (simple state)

### Backend Stack
- **Runtime:** Node.js (Express) or Python (FastAPI)
- **Real-time:** WebSocket for streaming audio
- **Storage:** Google Drive API (direct upload)
- **Email:** SendGrid or Mailgun

### Security Architecture
```
Browser → WebSocket → Backend → STT Service
                          ↓
                    Google Drive API
                          ↓
                    Email Service
```

**Data Flow:**
1. Audio streamed from browser to backend
2. Backend forwards to STT service
3. Transcript received
4. **Immediately** uploaded to user's Google Drive
5. Transcript deleted from backend memory
6. Email notification sent

**No persistent storage** on our servers.

---

## File Naming Convention

Format: `{PatientName}_{YYYY-MM-DD}_{HH-MM}.txt`

Example: `יוסי כהן_2025-12-01_14-30.txt`

**Considerations:**
- Hebrew characters in filename (Google Drive supports this)
- Date format: ISO standard (YYYY-MM-DD) for sorting
- Time format: 24-hour (HH-MM)

---

## Google Drive Integration

### Folder Structure
```
Clinic/
  └── Transcripts/
      ├── יוסי כהן_2025-12-01_14-30.txt
      ├── יוסי כהן_2025-12-05_15-00.txt
      └── שרה לוי_2025-12-01_16-00.txt
```

### OAuth Scopes Required
- `https://www.googleapis.com/auth/drive.file` (create files only)
- Minimal permissions (principle of least privilege)

---

## Email Notification

### Content
```
Subject: Session Transcript Ready - [Patient Name]

Your session transcript has been saved.

Patient: [Patient Name]
Date: [Date]
Time: [Time]

View transcript: [Google Drive Link]

---
Note: This transcript is stored in your Google Drive.
No recordings or transcripts are stored on our servers.
```

### Recipients (MVP)
- Therapist email (from Google account)
- Admin email (for debugging - can be removed later)

---

## MVP Feature Priority

### Must Have (v1.0)
- ✅ Google OAuth login
- ✅ Patient name input
- ✅ Real-time Hebrew transcription
- ✅ Speaker identification (Speaker 1, Speaker 2)
- ✅ Auto-save to Google Drive
- ✅ Email notification
- ✅ Simple start/stop interface

### Nice to Have (v2.0)
- Transcript editing before save
- Patient name autocomplete
- Session history
- Summary generation
- Integration with Clinic Smart

### Future (v3.0+)
- Multiple language support
- Custom folder organization
- Export formats (PDF, DOCX)
- Mobile app

---

## Development Phases

### Phase 1: Proof of Concept (Week 1)
- Basic web interface
- Connect to STT service (Soniox)
- Test Hebrew transcription accuracy
- Test speaker diarization

### Phase 2: Core Features (Week 2)
- Google OAuth integration
- Google Drive upload
- Email notifications
- File naming with patient/date/time

### Phase 3: Polish & Testing (Week 3)
- UI/UX refinements
- Error handling
- Security review
- User testing with Shira

---

## Decisions Made ✅

1. **UI Direction:** RTL for transcript only, LTR for UI controls ✅
2. **Patient Names:** Free text input only (no autocomplete in MVP) ✅
3. **Transcript Editing:** No editing in MVP ✅
4. **Transcript Display:** Real-time updating ✅
5. **Error Recovery:** Hybrid approach (Drive + LocalStorage) ✅

## Final Decisions ✅

1. **Auto-save frequency:** Every 1 minute (60 seconds) to Drive ✅
2. **Recovery notification:** No email on crash ✅
3. **Temp file cleanup:** Auto-delete temp files after 24 hours ✅
4. **Transcription Provider:** Modular architecture (pluggable providers) ✅
4. **Session Duration:** Any limits? (e.g., max 90 minutes)
5. **Error Handling:** If Drive upload fails, should we:
   - Show error and allow retry?
   - Offer manual download as backup?

---

## Next Steps

1. **Review the mockup** (`mockup.html`) - Open in browser to see UI
2. **Confirm UI direction** (RTL/LTR)
3. **Approve technical stack** (Soniox for STT)
4. **Start building** once approved

