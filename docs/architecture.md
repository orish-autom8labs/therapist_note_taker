# Architecture

## Overview

Note Taker is a therapy session note-taking application that provides real-time transcription with speaker diarization, automatic summarization via a two-stage LLM pipeline, and storage to the therapist's own Google Drive. The system is designed with a strong privacy stance: no transcript text or audio is stored on the server -- only Google Drive file ID pointers are persisted.

---

## Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Frontend | React 18, Soniox SDK | UI, real-time transcription (client-side) |
| Backend | Python 3.10, FastAPI | REST API, OAuth, summarization orchestration |
| Hosting | Google Cloud Run | Serverless container deployment |
| Storage | Google Drive (via OAuth) | Transcripts and summaries as Google Docs |
| Metadata | Google Cloud Firestore | Session tracking, job status, cost tracking |
| Transcription | Soniox (real-time, WebSocket) | Speech-to-text with speaker diarization |
| LLM - Stage 1 | DeepSeek | Chunk-level transcript summarization |
| LLM - Stage 2 | Claude Haiku (Anthropic) | Final synthesis of detailed notes and key topics |

---

## System Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│  Browser (React 18)                                              │
│  ├── Soniox SDK ──WebSocket──► Soniox Cloud (transcription)      │
│  ├── useSonioxClient.js (auto-reconnection, exponential backoff) │
│  ├── Audio Visualizer (32-bar waveform)                          │
│  ├── Session Timer (60-min countdown with warnings)              │
│  └── localStorage backup (5s) + Drive sync (60s)                 │
└──────────────────────────┬───────────────────────────────────────┘
                           │ REST API (HTTPS)
┌──────────────────────────▼───────────────────────────────────────┐
│  FastAPI Backend (Cloud Run)                                      │
│  ├── /v1/auth/temporary-api-key ── Soniox temp key generation    │
│  ├── /auth/google/*             ── Google OAuth flow             │
│  ├── /api/sessions/*/transcript ── Save transcript to Drive      │
│  ├── /api/sessions/*/status     ── Poll summarization status     │
│  ├── Background: 2-stage LLM summarization (with retry)          │
│  └── Firestore: session metadata persistence                     │
├──────────────────────────────────────────────────────────────────┤
│  External Services                                                │
│  ├── Google Drive API  ── transcript + summary storage           │
│  ├── Google Firestore  ── session metadata                       │
│  ├── DeepSeek API      ── Stage 1 chunk summarization            │
│  └── Anthropic API     ── Stage 2 synthesis (Claude Haiku)       │
└──────────────────────────────────────────────────────────────────┘
```

---

## Data Flow

### Recording and Transcription

1. The therapist opens the app and authenticates via Google OAuth.
2. The browser captures microphone audio via the Web Audio API.
3. The Soniox SDK streams audio over a WebSocket to Soniox Cloud, which returns real-time transcript tokens with speaker diarization.
4. The client displays the live transcript, updating as tokens arrive.
5. A recovery service backs up the transcript to `localStorage` every 5 seconds.
6. An auto-sync service sends the transcript to the backend every 60 seconds (non-final saves).

### Save and Summarization

7. The therapist clicks "Stop & Save", triggering `POST /api/sessions/{id}/transcript` with `is_final=true`.
8. The backend saves the transcript as a Google Doc in the user's Drive (inside a patient-specific folder).
9. The backend writes a Firestore metadata document with `status=transcript_saved`.
10. A background task starts the two-stage LLM summarization pipeline (see below).
11. On success, the summary is saved as a separate Google Doc in the same patient folder.
12. Firestore is updated with `status=completed` and the summary Drive file info.
13. The frontend polls `GET /api/sessions/{id}/status` and displays a link to the summary when ready.

---

## LLM Summarization Pipeline

The pipeline is implemented in `server/src/services/summarization/` and follows a two-stage architecture designed to handle long therapy session transcripts cost-effectively.

### Stage 1: Chunking (DeepSeek)

- The transcript is split into chunks using one of two strategies:
  - **Speaker segment chunker**: Groups by speaker turns (preferred for therapy sessions).
  - **Fixed time chunker**: Splits at fixed time intervals (fallback).
- Each chunk is summarized independently via DeepSeek, enabling parallel processing.
- The prompt is language-aware (Hebrew or English, auto-detected).

### Stage 2: Synthesis (Claude Haiku)

- Chunk summaries from Stage 1 are combined into a single context.
- Claude Haiku generates two output types:
  - **Detailed notes**: Structured therapy session notes.
  - **Key topics**: High-level topic extraction.
- Maximum output: 4096 tokens (Haiku limit).

### Retry and Error Handling

- Transient errors trigger exponential backoff: 2s, 4s, 8s.
- Maximum 3 retry attempts per operation.
- Summarization failures are isolated and never block transcript saving.
- Firestore tracks attempt count and error details for debugging.

---

## Firestore Schema

**Collection**: `{prefix}_sessions/{session_id}`

The collection prefix is environment-specific (`prod`, `staging`) to isolate data between environments.

| Field | Type | Description |
|-------|------|-------------|
| `user_email` | string | Therapist's Google email |
| `patient_name` | string | Patient identifier for folder organization |
| `created_at` | timestamp | Session creation time |
| `status` | string | `transcript_saved`, `summarizing`, `completed`, `failed` |
| `transcript` | map | Drive file ID, folder ID, doc URL |
| `summaries` | map | Drive file IDs for detailed notes and key topics |
| `summarization` | map | Attempt count, total cost (USD), error details |
| `metadata` | map | Duration (minutes), token count, detected language |
| `encrypted_refresh_token` | string | Encrypted OAuth refresh token for background tasks |

### Privacy Guarantees

- No transcript text is stored in Firestore -- only Drive file ID pointers.
- No audio is recorded or stored on the server.
- Transcripts and summaries live exclusively in the therapist's own Google Drive.
- Refresh tokens are encrypted at rest.

---

## Authentication and Authorization

- Google OAuth 2.0 handles therapist authentication.
- The backend receives and stores OAuth tokens to act on behalf of the user.
- All Drive operations use the therapist's own credentials, so files are owned by them.
- Soniox temporary API keys are generated server-side and passed to the client for WebSocket auth.

---

## Frontend Architecture

### Key Hooks

| Hook | Responsibility |
|------|---------------|
| `useSonioxClient` | Soniox SDK lifecycle, auto-reconnection (exponential backoff: 1s to 16s, max 5 retries) |
| `useSessionTimer` | 60-minute session countdown with warning thresholds |
| `useAudioVisualizer` | 32-bar real-time waveform from Web Audio API |

### Key Services

| Service | Responsibility |
|---------|---------------|
| `sonioxService` | Fetches temporary API keys from the backend |
| `transcriptSyncService` | Auto-saves transcript to the server every 60 seconds |
| `recoveryService` | Backs up transcript to localStorage every 5 seconds |

---

## Deployment

### Production

- **Backend**: Google Cloud Run at `https://note-taker-backend-1049928242674.us-central1.run.app`
- **Frontend**: Google Cloud Run at `https://note-taker-frontend-1049928242674.us-central1.run.app`
- Firestore collection prefix: `prod`

### Staging

- Uses Cloud Run revision tags (`--no-traffic --tag staging`) so production traffic is unaffected.
- **Backend**: `https://staging---note-taker-backend-1049928242674.us-central1.run.app`
- **Frontend**: `https://staging---note-taker-frontend-1049928242674.us-central1.run.app`
- Separate `.env.staging.yaml` with staging-specific configuration.
- Firestore collection prefix: `staging`
- Production remains unaffected until explicit promotion of a staging revision.

---

## Key Design Decisions

1. **Client-side transcription**: The Soniox SDK runs in the browser, so audio never touches the backend. This minimizes latency and strengthens privacy.
2. **Google Drive as storage**: Therapists own their data. No central database of patient transcripts exists.
3. **Two-stage LLM pipeline**: DeepSeek handles high-volume chunk summarization cheaply; Claude Haiku produces the final polished output. This balances cost and quality.
4. **Firestore for metadata only**: Firestore tracks session status and Drive pointers but never stores clinical content.
5. **Background summarization**: Summarization runs asynchronously after transcript save, so the therapist is never blocked waiting for LLM processing.
