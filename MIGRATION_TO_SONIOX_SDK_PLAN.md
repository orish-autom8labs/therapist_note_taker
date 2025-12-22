# Migration Plan: Note-Taker to Soniox SDK Architecture

## Executive Summary

This plan outlines the migration from our current **server-proxied WebSocket architecture** to the **Soniox SDK architecture** (like the official example), while maintaining all PRD requirements.

**Key Change**: Client connects directly to Soniox for transcription, server only handles Drive/email operations.

---

## Part 1: Architecture Comparison

### Current Architecture (Server-Proxied)

```
Browser (React)
  ↓ WebSocket → ws://localhost:3001/ws
  ↓ Sends: WebM/Opus audio (base64)
Our Server (FastAPI)
  ↓ WebSocket → wss://stt-rt.soniox.com/transcribe-websocket
  ↓ Sends: WebM/Opus audio (raw bytes)
  ↓ Receives: Tokens
  ↓ Processes: Token aggregation, speaker diarization
  ↓ Saves: To Google Drive (every 1 min + final)
  ↓ Sends: Transcripts to client
Soniox API
```

**Issues**:
- ❌ Audio format conversion problem (WebM/Opus → timeout)
- ❌ Server handles all transcription logic
- ❌ Complex WebSocket proxying

### Target Architecture (SDK-Based)

```
Browser (React)
  ↓ Soniox SDK → wss://stt-rt.soniox.com/transcribe-websocket (direct)
  ↓ SDK handles: Audio format conversion, WebSocket, tokens
  ↓ Receives: Tokens directly from Soniox
  ↓ Processes: Token aggregation, speaker diarization (client-side)
  ↓ Sends: Transcripts to our server (REST API) for Drive saves
Our Server (FastAPI)
  ↓ REST API endpoints
  ↓ Receives: Transcripts from client
  ↓ Saves: To Google Drive (every 1 min + final)
  ↓ Sends: Email notifications
Google Drive API
```

**Benefits**:
- ✅ SDK handles audio format (no timeout issues)
- ✅ Simpler server (no WebSocket proxying)
- ✅ Client has direct access to tokens
- ✅ Better separation of concerns

---

## Part 2: Implications & Requirements Analysis

### 2.1 Security Implications

#### Current (Server-Proxied)
- ✅ API key stored on server (never exposed)
- ✅ Client doesn't need Soniox credentials
- ✅ Server controls all Soniox access

#### Target (SDK-Based)
- ⚠️ Need temporary API keys (like official example)
- ⚠️ Client needs Soniox credentials (temporary)
- ✅ Server generates temporary keys (60-second expiry)
- ✅ Main API key still on server

**Solution**: Implement temporary API key server (like official example)

### 2.2 Data Flow Changes

#### Current Flow
1. Client → Server: Audio chunks (WebSocket)
2. Server → Soniox: Audio chunks (WebSocket)
3. Soniox → Server: Tokens (WebSocket)
4. Server → Client: Transcripts (WebSocket)
5. Server → Drive: Auto-save transcripts (every 1 min)
6. Server → Email: Notification on completion

#### Target Flow
1. Client → Soniox: Audio chunks (WebSocket, via SDK)
2. Soniox → Client: Tokens (WebSocket, via SDK)
3. Client processes tokens → Transcripts
4. Client → Server: Transcripts (REST API, every 1 min)
5. Server → Drive: Save transcripts
6. Client → Server: Final transcript (REST API, on stop)
7. Server → Drive: Final save
8. Server → Email: Notification on completion

### 2.3 PRD Requirements Mapping

| Requirement | Current | Target | Status |
|------------|---------|--------|--------|
| **FR1: Authentication** | ✅ Google OAuth | ✅ Google OAuth | ✅ No change |
| **FR2: Session Management** | ✅ Server tracks | ✅ Client tracks, syncs to server | ⚠️ Minor change |
| **FR3: Transcription** | ✅ Server handles | ✅ Client handles (SDK) | ⚠️ Major change |
| **FR4: Storage & Backup** | ✅ Server auto-saves | ✅ Client sends, server saves | ⚠️ Minor change |
| **FR5: Notifications** | ✅ Server sends | ✅ Server sends | ✅ No change |
| **NFR1: Performance** | ✅ < 2s latency | ✅ < 2s latency (better) | ✅ Improved |
| **NFR2: Security** | ✅ Zero-knowledge | ✅ Zero-knowledge | ✅ Maintained |
| **NFR3: Reliability** | ✅ Recovery | ✅ Recovery (client + server) | ⚠️ Enhanced |

---

## Part 3: Detailed Migration Plan

### Phase 1: Infrastructure Setup (Week 1)

#### 1.1 Temporary API Key Server
**Goal**: Implement server endpoint to generate temporary Soniox API keys

**Tasks**:
- [ ] Create `/v1/auth/temporary-api-key` endpoint (like official example)
- [ ] Integrate with Soniox API to generate temporary keys
- [ ] Set expiry to 60 seconds (matching official example)
- [ ] Add error handling and logging

**Files to Create/Modify**:
- `server/main.py` - Add temporary key endpoint
- `server/src/services/soniox_auth_service.py` - New service for temp keys

**Estimated Time**: 4-6 hours

#### 1.2 Install Soniox SDK
**Goal**: Add Soniox SDK to client

**Tasks**:
- [ ] Install `@soniox/speech-to-text-web` package
- [ ] Create SDK wrapper/hook (similar to official example)
- [ ] Test SDK connection with temporary API key

**Files to Create/Modify**:
- `client/package.json` - Add SDK dependency
- `client/src/hooks/useSonioxClient.js` - New hook (based on official example)
- `client/src/services/sonioxService.js` - SDK integration

**Estimated Time**: 2-3 hours

#### 1.3 REST API for Transcripts
**Goal**: Create REST endpoints for client to send transcripts

**Tasks**:
- [ ] Create `POST /api/sessions/:sessionId/transcript` endpoint
- [ ] Create `POST /api/sessions/:sessionId/final` endpoint
- [ ] Add session tracking (patient name, start time, etc.)
- [ ] Integrate with Drive service for auto-save

**Files to Create/Modify**:
- `server/main.py` - Add REST endpoints
- `server/src/services/session_service.py` - New service for session tracking

**Estimated Time**: 4-6 hours

### Phase 2: Client-Side Migration (Week 2)

#### 2.1 Replace WebSocket with SDK
**Goal**: Replace current WebSocket transcription with Soniox SDK

**Tasks**:
- [ ] Remove `transcriptionService.js` WebSocket code
- [ ] Implement `useSonioxClient` hook (based on official example)
- [ ] Update `ActiveSession.js` to use SDK
- [ ] Handle token processing (final/non-final)
- [ ] Implement speaker diarization display

**Files to Modify**:
- `client/src/components/ActiveSession.js` - Replace WebSocket with SDK
- `client/src/services/transcriptionService.js` - Remove or repurpose
- `client/src/hooks/useSonioxClient.js` - New hook

**Estimated Time**: 8-10 hours

#### 2.2 Client-Side Transcript Management
**Goal**: Manage transcripts on client, send to server periodically

**Tasks**:
- [ ] Implement transcript buffer on client
- [ ] Send transcripts to server every 1 minute (auto-save)
- [ ] Send final transcript on stop
- [ ] Handle errors and retries

**Files to Modify**:
- `client/src/components/ActiveSession.js` - Add transcript sending logic
- `client/src/services/transcriptSyncService.js` - New service for syncing

**Estimated Time**: 6-8 hours

#### 2.3 Session Recovery (Client-Side)
**Goal**: Maintain session recovery capability

**Tasks**:
- [ ] Store transcripts in localStorage (existing)
- [ ] Store session state (patient name, start time)
- [ ] Implement recovery dialog (existing, may need updates)
- [ ] Handle reconnection to Soniox SDK

**Files to Modify**:
- `client/src/services/recoveryService.js` - Update for SDK
- `client/src/components/RecoveryDialog.js` - May need updates

**Estimated Time**: 4-6 hours

### Phase 3: Server-Side Simplification (Week 2-3)

#### 3.1 Remove WebSocket Transcription Logic
**Goal**: Remove server-side WebSocket transcription code

**Tasks**:
- [ ] Remove `/ws` WebSocket endpoint (or repurpose)
- [ ] Remove `TranscriptionService` WebSocket handling
- [ ] Remove `soniox_provider.py` WebSocket code
- [ ] Keep Drive and Email services

**Files to Modify**:
- `server/main.py` - Remove WebSocket endpoint
- `server/src/services/transcription_service.py` - Remove or simplify
- `server/src/providers/soniox_provider.py` - Remove (or keep for reference)

**Estimated Time**: 4-6 hours

#### 3.2 Update Drive Service
**Goal**: Update Drive service to work with REST API transcripts

**Tasks**:
- [ ] Update `DriveService` to accept transcripts via REST
- [ ] Maintain auto-save every 1 minute
- [ ] Maintain final save on session end
- [ ] Keep file naming: `{PatientName}_{Date}_{Time}.txt`
- [ ] Keep folder structure: `Clinic/Transcripts`

**Files to Modify**:
- `server/src/services/drive_service.py` - Update for REST API

**Estimated Time**: 2-4 hours

#### 3.3 Update Email Service
**Goal**: Ensure email notifications still work

**Tasks**:
- [ ] Verify email service works with new flow
- [ ] Update email content if needed
- [ ] Test email notifications

**Files to Modify**:
- `server/src/services/email_service.py` - Verify/update

**Estimated Time**: 1-2 hours

### Phase 4: Testing & Validation (Week 3)

#### 4.1 Functional Testing
**Tasks**:
- [ ] Test authentication flow
- [ ] Test session creation
- [ ] Test real-time transcription
- [ ] Test speaker diarization
- [ ] Test auto-save to Drive
- [ ] Test final save
- [ ] Test email notifications
- [ ] Test session recovery

**Estimated Time**: 8-10 hours

#### 4.2 Integration Testing
**Tasks**:
- [ ] Test end-to-end flow
- [ ] Test error scenarios
- [ ] Test network disconnection
- [ ] Test long sessions (> 1 hour)
- [ ] Test multiple sessions

**Estimated Time**: 6-8 hours

#### 4.3 Performance Testing
**Tasks**:
- [ ] Verify transcription latency < 2 seconds
- [ ] Verify UI responsiveness < 100ms
- [ ] Verify auto-save completes within 5 seconds
- [ ] Test with slow network

**Estimated Time**: 4-6 hours

---

## Part 4: Code Structure Changes

### 4.1 Client-Side Structure

#### Before (Current)
```
client/src/
  ├── components/
  │   └── ActiveSession.js (uses WebSocket)
  ├── services/
  │   ├── transcriptionService.js (WebSocket client)
  │   └── recoveryService.js
```

#### After (Target)
```
client/src/
  ├── components/
  │   └── ActiveSession.js (uses SDK)
  ├── hooks/
  │   └── useSonioxClient.js (SDK wrapper)
  ├── services/
  │   ├── transcriptSyncService.js (REST API client)
  │   ├── recoveryService.js
  │   └── sonioxService.js (temporary key fetching)
```

### 4.2 Server-Side Structure

#### Before (Current)
```
server/
  ├── main.py (WebSocket endpoint)
  ├── src/
  │   ├── services/
  │   │   ├── transcription_service.py (WebSocket handling)
  │   │   ├── drive_service.py
  │   │   └── email_service.py
  │   └── providers/
  │       └── soniox_provider.py (WebSocket client)
```

#### After (Target)
```
server/
  ├── main.py (REST endpoints + temp key endpoint)
  ├── src/
  │   ├── services/
  │   │   ├── soniox_auth_service.py (temp key generation)
  │   │   ├── session_service.py (session tracking)
  │   │   ├── drive_service.py (updated)
  │   │   └── email_service.py
  │   └── providers/ (can be removed or kept for reference)
```

---

## Part 5: Risk Assessment & Mitigation

### 5.1 Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **SDK compatibility issues** | High | Low | Test thoroughly, have fallback plan |
| **Temporary key generation fails** | High | Medium | Implement retry logic, error handling |
| **Client-server sync issues** | Medium | Medium | Implement retry logic, localStorage backup |
| **Session recovery complexity** | Medium | Low | Test recovery scenarios thoroughly |
| **Performance degradation** | Low | Low | SDK should improve performance |

### 5.2 Rollback Plan

If migration fails:
1. Keep current code in `main` branch
2. Create `sdk-migration` branch for new code
3. Can revert to current architecture if needed
4. Test new architecture thoroughly before merging

---

## Part 6: Implementation Checklist

### Phase 1: Infrastructure
- [ ] Implement temporary API key server endpoint
- [ ] Install Soniox SDK on client
- [ ] Create SDK wrapper hook
- [ ] Create REST API endpoints for transcripts
- [ ] Test temporary key generation

### Phase 2: Client Migration
- [ ] Replace WebSocket with SDK in ActiveSession
- [ ] Implement client-side transcript management
- [ ] Implement auto-save sync to server
- [ ] Update session recovery for SDK
- [ ] Test transcription flow

### Phase 3: Server Simplification
- [ ] Remove WebSocket transcription endpoint
- [ ] Update Drive service for REST API
- [ ] Update Email service if needed
- [ ] Clean up unused code
- [ ] Test server endpoints

### Phase 4: Testing
- [ ] Functional testing (all PRD requirements)
- [ ] Integration testing
- [ ] Performance testing
- [ ] Error scenario testing
- [ ] User acceptance testing

---

## Part 7: Timeline Estimate

### Total Estimated Time: 3-4 weeks

- **Week 1**: Infrastructure setup (10-15 hours)
- **Week 2**: Client migration (18-24 hours)
- **Week 3**: Server simplification + Testing (18-24 hours)
- **Week 4**: Buffer for issues and polish (10-15 hours)

### Milestones

1. **Week 1 End**: Temporary key server working, SDK installed
2. **Week 2 End**: Client using SDK, transcripts syncing to server
3. **Week 3 End**: Server simplified, all tests passing
4. **Week 4 End**: Production-ready, all PRD requirements met

---

## Part 8: Key Decisions Needed

### Decision 1: Keep WebSocket Endpoint?
**Question**: Should we keep the `/ws` endpoint for other purposes, or remove it entirely?

**Options**:
- A: Remove entirely (cleaner)
- B: Keep for future features (flexibility)

**Recommendation**: Remove for now, can add back if needed.

### Decision 2: Session Tracking
**Question**: How should we track sessions on the server?

**Options**:
- A: In-memory dictionary (simple, current approach)
- B: Database (more robust, future-proof)

**Recommendation**: Start with in-memory, migrate to database later if needed.

### Decision 3: Auto-Save Frequency
**Question**: Should we keep 1-minute auto-save, or adjust?

**Options**:
- A: Keep 1 minute (current PRD requirement)
- B: Adjust based on performance

**Recommendation**: Keep 1 minute, can optimize later.

---

## Part 9: Success Criteria

### Must Have (MVP)
- ✅ Real-time Hebrew transcription works (no timeouts)
- ✅ Speaker diarization works
- ✅ Auto-save to Drive every 1 minute
- ✅ Final save on session end
- ✅ Email notifications work
- ✅ Session recovery works
- ✅ All PRD requirements met

### Nice to Have
- ⭐ Better performance than current
- ⭐ Cleaner codebase
- ⭐ Easier to maintain

---

## Next Steps

1. **Review this plan** with stakeholders
2. **Make key decisions** (Decisions 1-3)
3. **Start Phase 1** (Infrastructure setup)
4. **Test incrementally** after each phase
5. **Deploy to production** after all tests pass

---

**Ready to proceed?** 🚀

