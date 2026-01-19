# Note Taker Documentation

## Getting Started

| Document | Description |
|----------|-------------|
| [Quick Start Guide](../QUICK_START_GUIDE.md) | Get up and running in 5 minutes |
| [Google OAuth Setup](../GOOGLE_OAUTH_SETUP.md) | Configure Google Cloud Console |

## Architecture & Design

| Document | Description |
|----------|-------------|
| [Product Requirements (PRD)](../PRD.md) | Complete feature specifications and acceptance criteria |
| [Provider Guide](../PROVIDER_GUIDE.md) | Transcription provider architecture (Soniox, Google, Mock) |
| [Summarization Pipeline](../server/SUMMARIZATION.md) | Two-stage LLM summarization (DeepSeek + Claude) |

## Deployment

| Document | Description |
|----------|-------------|
| [Deployment & OAuth](../DEPLOYMENT_AND_OAUTH.md) | Deployment options and OAuth architecture |

## Development

| Document | Description |
|----------|-------------|
| [Development Guidelines](../.claude/DEVELOPMENT_GUIDELINES.md) | Git workflow, commit format, code review |
| [Testing Plan](../TESTING_PLAN.md) | Manual test scenarios and findings |

## For Claude Code

| Document | Description |
|----------|-------------|
| [CLAUDE.md](../CLAUDE.md) | Project context for Claude Code sessions |

---

## Project Overview

**Note Taker** is a secure real-time transcription application for therapists conducting Hebrew-language sessions.

### Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | React 18, Soniox SDK |
| Backend | Python 3.10, FastAPI, Uvicorn |
| Transcription | Soniox (primary), Google Speech (alternative) |
| Storage | Google Drive (per-user folders) |
| Summarization | DeepSeek (chunking) + Claude Haiku (synthesis) |
| Auth | Google OAuth 2.0 |

### Key Features

- Real-time Hebrew transcription (client-side SDK)
- Speaker diarization (Speaker A, B, C...)
- 60-minute session timer with warnings
- Auto-save every 60s to Google Drive
- Local recovery every 5s to localStorage
- Two-stage LLM summarization
- Automatic WebSocket reconnection

### Architecture Diagram

```
Browser
├── React App (localhost:3000)
│   ├── Soniox SDK → WebSocket → Soniox Cloud
│   ├── Audio Visualizer (Web Audio API)
│   ├── Session Timer (60 min max)
│   └── Transcript Display (RTL Hebrew)
│
└── REST API calls
    ↓
FastAPI Backend (localhost:3001)
├── /v1/auth/temporary-api-key  → Soniox temp keys
├── /auth/google/*              → OAuth flow
├── /api/sessions/*/transcript  → Save to Drive
└── Background: LLM Summarization
    ↓
External Services
├── Soniox Cloud (transcription)
├── Google Drive (storage)
├── DeepSeek API (chunking)
└── Anthropic API (synthesis)
```

---

## Quick Reference

### Start Development

```bash
# Terminal 1: Backend
cd server && source venv/bin/activate && python run.py

# Terminal 2: Frontend
cd client && npm start
```

### URLs

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend | http://localhost:3001 |
| Health Check | http://localhost:3001/health |

### Key Files

| File | Purpose |
|------|---------|
| `client/src/hooks/useSonioxClient.js` | Soniox SDK integration with reconnection |
| `client/src/components/ActiveSession.js` | Main recording UI |
| `server/main.py` | FastAPI endpoints |
| `server/src/config.py` | Configuration management |
| `server/src/services/summarization/` | LLM pipeline |
