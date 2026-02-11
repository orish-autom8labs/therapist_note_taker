# Note Taker - Claude Code Context

## Quick Reference

| What | Where |
|------|-------|
| Frontend | `client/` - React 18, Soniox SDK |
| Backend | `server/` - Python 3.10, FastAPI |
| Frontend URL | http://localhost:3000 |
| Backend URL | http://localhost:3001 |
| Health check | http://localhost:3001/health |

## Start Development

```bash
# Terminal 1: Backend
cd server && source venv/bin/activate && python run.py

# Terminal 2: Frontend
cd client && npm start
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Browser (React)                                            │
│  ├── Soniox SDK → WebSocket → Soniox Cloud                 │
│  ├── useSonioxClient.js (with auto-reconnection)           │
│  ├── Audio Visualizer, Session Timer (60 min)              │
│  ├── localStorage backup (5s) + Drive sync (60s)           │
│  └── useSummaryPolling.js → polls status every 5s          │
└─────────────────────────┬───────────────────────────────────┘
                          │ REST API
┌─────────────────────────▼───────────────────────────────────┐
│  FastAPI Backend                                            │
│  ├── /v1/auth/temporary-api-key → Soniox temp keys         │
│  ├── /auth/google/* → OAuth flow                           │
│  ├── /api/sessions/*/transcript → Save to Drive + Firestore│
│  ├── /api/sessions/*/status → Summary polling endpoint     │
│  └── Background: 3-stage LLM Summarization with retry      │
│      Stage 1: Structured extraction (DeepSeek, parallel)    │
│      Stage 2: Synthesis (Claude Haiku/Sonnet)               │
│      Stage 3: Faithfulness verification (Level 3 only)      │
├─────────────────────────────────────────────────────────────┤
│  Google Cloud Firestore (metadata only)                     │
│  └── {prefix}_sessions/{id} → status, Drive IDs, costs     │
└─────────────────────────────────────────────────────────────┘
```

## Key Files by Feature

### Transcription (Client-Side)
| File | Purpose |
|------|---------|
| `client/src/hooks/useSonioxClient.js` | Soniox SDK wrapper with reconnection logic |
| `client/src/components/ActiveSession.js` | Main recording UI (transcript, timer, visualizer) |
| `client/src/services/sonioxService.js` | Fetches temporary API keys from backend |

### Session Management
| File | Purpose |
|------|---------|
| `client/src/hooks/useSessionTimer.js` | 60-min countdown with warnings |
| `client/src/hooks/useAudioVisualizer.js` | 32-bar waveform display |
| `client/src/services/transcriptSyncService.js` | Auto-save to server every 60s |
| `client/src/services/recoveryService.js` | localStorage backup every 5s |

### Backend Services
| File | Purpose |
|------|---------|
| `server/main.py` | FastAPI endpoints + Firestore integration |
| `server/src/config.py` | Configuration (incl. FirestoreConfig, SummaryLevelConfig) |
| `server/src/providers/soniox_provider.py` | Soniox temp API key generation |
| `server/src/services/drive_service.py` | Google Drive operations |
| `server/src/services/firestore_service.py` | Firestore CRUD, encrypted token storage |
| `server/src/services/summarization/` | Three-stage LLM pipeline (extraction → synthesis → verification) |
| `server/src/services/summarization/synthesis/verification.py` | Stage 3 faithfulness verifier |
| `server/src/providers/llm/retry.py` | Exponential backoff retry logic |

### Summarization Prompts (Hebrew only)
| File | Purpose |
|------|---------|
| `server/src/prompts/summarization/chunk_extraction_he.md` | Stage 1: Structured extraction with quote-grounding |
| `server/src/prompts/summarization/key_topics_he.md` | Stage 2: Key topics synthesis |
| `server/src/prompts/summarization/detailed_notes_he.md` | Stage 2: Detailed notes synthesis |
| `server/src/prompts/summarization/verification_he.md` | Stage 3: Faithfulness verification |

### Offline Tools
| File | Purpose |
|------|---------|
| `scripts/run_summary.py` | Offline CLI for running summaries on transcript files |

### Summary Polling (Client-Side)
| File | Purpose |
|------|---------|
| `client/src/hooks/useSummaryPolling.js` | Polls status endpoint every 5s |
| `client/src/components/SuccessScreen.js` | Shows transcript/summary links + status |

### Configuration
| File | Purpose |
|------|---------|
| `server/.env` | API keys and secrets |
| `server/src/config.py` | SummarizationConfig, DriveConfig, etc. |
| `client/src/config/sessionConfig.js` | Session duration, timer settings |

## Documentation Map

| Document | When to Read |
|----------|--------------|
| [PRD.md](PRD.md) | Understanding features and requirements |
| [QUICK_START_GUIDE.md](QUICK_START_GUIDE.md) | Setup and testing |
| [PROVIDER_GUIDE.md](PROVIDER_GUIDE.md) | Transcription provider architecture |
| [server/SUMMARIZATION.md](server/SUMMARIZATION.md) | LLM summarization pipeline |
| [DEPLOYMENT_AND_OAUTH.md](DEPLOYMENT_AND_OAUTH.md) | Deployment and OAuth setup |
| [GOOGLE_OAUTH_SETUP.md](GOOGLE_OAUTH_SETUP.md) | Google Cloud Console setup |
| [TESTING_PLAN.md](TESTING_PLAN.md) | Test scenarios and results |
| [.claude/DEVELOPMENT_GUIDELINES.md](.claude/DEVELOPMENT_GUIDELINES.md) | Git workflow, commit format |
| [docs/README.md](docs/README.md) | Documentation index |
| [docs/architecture.md](docs/architecture.md) | System architecture with Firestore |
| [docs/decisions.md](docs/decisions.md) | Architecture Decision Records |

## Environment Variables

### Required (server/.env)
```bash
SONIOX_API_KEY=xxx           # Transcription
GOOGLE_CLIENT_ID=xxx         # OAuth
GOOGLE_CLIENT_SECRET=xxx     # OAuth
```

### Optional (Summarization)
```bash
DEEPSEEK_API_KEY=xxx         # Stage 1 - structured extraction
ANTHROPIC_API_KEY=xxx        # Stage 2 - synthesis, Stage 3 - verification
SUMMARIZATION_ENABLED=true   # Enable/disable
```

### Firestore
```bash
FIRESTORE_ENABLED=true                # Enable session tracking
GCP_PROJECT_ID=therapistnottaker      # GCP project
FIRESTORE_ENCRYPTION_KEY=xxx          # Fernet key for token encryption
FIRESTORE_COLLECTION_PREFIX=prod      # "prod" or "staging"
```

## Current Issues & Status

### Reconnection Logic (IMPLEMENTED)
- `useSonioxClient.js` now has automatic reconnection
- Exponential backoff: 1s → 2s → 4s → 8s → 16s
- Max 5 retry attempts
- UI shows blue "Reconnecting..." banner

### Session Hang-ups (UNDER INVESTIGATION)
- Long sessions on mobile sometimes stop receiving transcription
- NOT caused by 60-second API key expiry (disproven)
- Reconnection logic added as proactive fix

### Summarization Pipeline (UPGRADING)
- Three-stage pipeline with 3 quality levels (Quick/Standard/Clinical)
- Stage 1: Structured extraction with quote-grounding (DeepSeek)
- Stage 2: Anti-hallucination synthesis (Claude Haiku or Sonnet)
- Stage 3: Faithfulness verification against extractions (Level 3 only)
- All prompts Hebrew-only, patient name used throughout
- Evaluation mode: all 3 levels in one document
- Future: level tied to subscription tier
- Retry logic: 2s → 4s → 8s backoff on transient errors
- Firestore tracks status + costs (costs never shown to therapist)
- See `server/SUMMARIZATION.md` for details

### Staging Environment
- Deploy: `bash scripts/deploy_backend_staging.sh` + `bash scripts/deploy_frontend_staging.sh`
- Promote: `bash scripts/promote_staging.sh`
- Uses Cloud Run revision tags (--no-traffic --tag staging)
- Firestore isolation via collection prefix (staging vs prod)

### Hebrew-First Formatting (IMPLEMENTED)
- Speaker labels: דובר א׳, דובר ב׳ (Hebrew letters, not English)
- Compact transcript: no blank lines between speakers
- Timestamps always present, checkbox controls frequency (1-2 min vs 5 min)
- RTL-friendly: no decorative `═══` lines (break alignment in Google Docs)
- Headers, dates, all output in Hebrew

## Console Log Prefixes

| Prefix | Source |
|--------|--------|
| `[SONIOX]` | Soniox SDK events |
| `[SESSION]` | Session lifecycle |
| `[SYNC]` | Auto-save to Drive |
| `[TIMER]` | Session timer |
| `[WAKE LOCK]` | Screen lock API |
| `[VISIBILITY]` | Tab visibility |
| `[STALL DETECTOR]` | Transcript stall detection |
| `[SUMMARIZATION]` | LLM pipeline (backend) |
| `[FIRESTORE]` | Firestore session tracking |
| `[IDEMPOTENCY]` | Duplicate save detection |
| `[RETRY]` | LLM retry attempts |
| `[POLL]` | Frontend summary polling |

## Git Workflow

- Branch: `sdk-rewrite` (current development)
- See `.claude/DEVELOPMENT_GUIDELINES.md` for commit format
- Run type checks before committing:
  - Python: `ty check`
  - TypeScript: `tsc --noEmit`

## Testing

- Manual testing via `TESTING_PLAN.md`
- Playwright MCP available for browser automation
- Note: Playwright uses fake microphone (can't test real transcription)
