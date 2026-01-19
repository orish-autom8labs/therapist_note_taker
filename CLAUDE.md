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
│  └── localStorage backup (5s) + Drive sync (60s)           │
└─────────────────────────┬───────────────────────────────────┘
                          │ REST API
┌─────────────────────────▼───────────────────────────────────┐
│  FastAPI Backend                                            │
│  ├── /v1/auth/temporary-api-key → Soniox temp keys         │
│  ├── /auth/google/* → OAuth flow                           │
│  ├── /api/sessions/*/transcript → Save to Google Drive     │
│  └── Background: LLM Summarization (DeepSeek → Claude)     │
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
| `server/main.py` | FastAPI endpoints |
| `server/src/config.py` | Configuration (Pydantic) |
| `server/src/providers/soniox_provider.py` | Soniox temp API key generation |
| `server/src/services/drive_service.py` | Google Drive operations |
| `server/src/services/summarization/` | Two-stage LLM pipeline |

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

## Environment Variables

### Required (server/.env)
```bash
SONIOX_API_KEY=xxx           # Transcription
GOOGLE_CLIENT_ID=xxx         # OAuth
GOOGLE_CLIENT_SECRET=xxx     # OAuth
```

### Optional (Summarization)
```bash
DEEPSEEK_API_KEY=xxx         # Stage 1 - chunking
ANTHROPIC_API_KEY=xxx        # Stage 2 - synthesis
SUMMARIZATION_ENABLED=true   # Enable/disable
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

### Summarization Pipeline (WORKING)
- Two-stage: DeepSeek (chunking) → Claude Haiku (synthesis)
- Max 4096 output tokens (Haiku limit)
- See `server/SUMMARIZATION.md` for details

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
