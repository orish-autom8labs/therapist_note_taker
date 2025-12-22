# Migration Implications Summary

## Quick Overview

**What Changes**: Move from server-proxied WebSocket to Soniox SDK (client-direct connection)

**Why**: Fixes audio format timeout issues, simplifies architecture, improves reliability

**Impact**: Major refactoring, but maintains all PRD requirements

---

## Key Implications

### 1. Security Model Changes

**Before**: 
- API key stored securely on server
- Client never sees Soniox credentials

**After**:
- Server generates **temporary API keys** (60-second expiry)
- Client uses temporary keys to connect directly to Soniox
- Main API key still on server (never exposed)

**Risk Level**: Low (temporary keys expire quickly)

---

### 2. Architecture Simplification

**Before**:
- Server handles WebSocket proxying
- Server processes all tokens
- Complex audio format handling

**After**:
- Client connects directly to Soniox (via SDK)
- Client processes tokens
- Server only handles Drive/email operations

**Benefit**: Simpler, more maintainable codebase

---

### 3. Data Flow Changes

**Before**:
```
Client → Server (WebSocket) → Soniox (WebSocket) → Server → Client
Server auto-saves to Drive
```

**After**:
```
Client → Soniox (WebSocket, direct via SDK)
Client → Server (REST API) → Drive
```

**Benefit**: Direct connection = better performance, no timeout issues

---

### 4. Code Changes Required

#### Client-Side (Major Changes)
- ✅ Replace WebSocket code with Soniox SDK
- ✅ Add temporary key fetching
- ✅ Add REST API calls for transcript syncing
- ✅ Update session recovery logic

#### Server-Side (Simplification)
- ✅ Remove WebSocket transcription endpoint
- ✅ Add temporary key generation endpoint
- ✅ Add REST endpoints for transcript receiving
- ✅ Simplify Drive service (no token processing)

**Estimated Effort**: 3-4 weeks

---

### 5. PRD Requirements Status

| Requirement | Status | Notes |
|------------|--------|-------|
| **FR1: Authentication** | ✅ Maintained | No changes needed |
| **FR2: Session Management** | ✅ Maintained | Client tracks, syncs to server |
| **FR3: Transcription** | ✅ Improved | SDK handles audio format correctly |
| **FR4: Storage & Backup** | ✅ Maintained | Auto-save still works (via REST) |
| **FR5: Notifications** | ✅ Maintained | Email service unchanged |
| **NFR1: Performance** | ✅ Improved | Direct connection = lower latency |
| **NFR2: Security** | ✅ Maintained | Temporary keys, zero-knowledge |
| **NFR3: Reliability** | ✅ Enhanced | Better error handling with SDK |

**All PRD requirements maintained or improved!**

---

## What Stays the Same

✅ Google OAuth login  
✅ Patient name input  
✅ Real-time transcription  
✅ Speaker diarization  
✅ Auto-save to Drive (every 1 minute)  
✅ Final save on session end  
✅ Email notifications  
✅ Session recovery  
✅ RTL text display  
✅ File naming: `{PatientName}_{Date}_{Time}.txt`  
✅ Folder structure: `Clinic/Transcripts`  

---

## What Changes

### Client-Side
- **Transcription**: WebSocket → Soniox SDK
- **Audio**: Server handles → SDK handles (automatic)
- **Tokens**: Server processes → Client processes
- **Syncing**: Automatic (server) → Manual (client sends to server)

### Server-Side
- **WebSocket**: Remove transcription endpoint
- **New**: Temporary key generation endpoint
- **New**: REST endpoints for transcript receiving
- **Simplified**: No token processing, no audio handling

---

## Migration Phases

### Phase 1: Infrastructure (Week 1)
- Temporary API key server
- Install Soniox SDK
- REST API endpoints

### Phase 2: Client Migration (Week 2)
- Replace WebSocket with SDK
- Implement transcript syncing
- Update session recovery

### Phase 3: Server Simplification (Week 2-3)
- Remove WebSocket code
- Update Drive service
- Clean up unused code

### Phase 4: Testing (Week 3)
- Functional testing
- Integration testing
- Performance testing

---

## Risks & Mitigation

| Risk | Mitigation |
|------|------------|
| SDK compatibility | Test thoroughly, have rollback plan |
| Temporary key failures | Retry logic, error handling |
| Client-server sync issues | Retry logic, localStorage backup |
| Session recovery complexity | Test recovery scenarios |

---

## Benefits

✅ **Fixes timeout issue** (SDK handles audio format)  
✅ **Simpler architecture** (less code to maintain)  
✅ **Better performance** (direct connection)  
✅ **Easier to maintain** (SDK updates automatically)  
✅ **All PRD requirements met** (nothing lost)  

---

## Next Steps

1. **Review migration plan** (`MIGRATION_TO_SONIOX_SDK_PLAN.md`)
2. **Make key decisions** (see plan Part 8)
3. **Start Phase 1** (Infrastructure setup)
4. **Test incrementally** after each phase

---

**Ready to proceed?** The migration maintains all PRD requirements while fixing the timeout issue and simplifying the architecture.

