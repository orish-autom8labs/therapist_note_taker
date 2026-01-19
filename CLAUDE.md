# Note Taker - Claude Code Instructions

## Project Overview

Real-time medical transcription app with:
- **Frontend**: React app (client/) - captures audio, displays transcript
- **Backend**: Python FastAPI (server/) - handles Soniox API, Google Drive, LLM summarization

## Architecture

```
Browser (React)
    ↓ Audio stream
Soniox SDK (@soniox/speech-to-text-web)
    ↓ WebSocket to Soniox cloud
    ↓ Transcription tokens
Server (FastAPI)
    ↓ Save to Google Drive
    ↓ Summarize with LLM (DeepSeek → Claude)
```

## Key Files

| Component | Path | Purpose |
|-----------|------|---------|
| Soniox Client Hook | `client/src/hooks/useSonioxClient.js` | SDK integration |
| Active Session UI | `client/src/components/ActiveSession.js` | Main recording UI |
| Soniox Provider | `server/src/providers/soniox_provider.py` | Direct WebSocket (unused?) |
| Summarization | `server/src/services/summarization/` | LLM pipeline |
| Main Server | `server/main.py` | FastAPI endpoints |

## Running the App

```bash
# Terminal 1: Backend
cd server
source venv/bin/activate
python main.py

# Terminal 2: Frontend
cd client
npm start
```

App runs at http://localhost:3000, API at http://localhost:3001

## Known Issues Being Investigated

### Transcript Hang-ups (HIGH PRIORITY)
- Sessions sometimes stop receiving transcription
- **NOT caused by** 60-second API key expiry (key only used for connection setup)
- Potential causes: browser throttling, WebSocket drops, audio stream issues

### LLM Summarization
- Two-stage pipeline: DeepSeek (chunking) → Claude (synthesis)
- Check API keys in `.env` if failing

## Testing Guidelines

- Use `TESTING_PLAN.md` for current test scenarios and results
- Browser testing with Playwright MCP for E2E scenarios
- Monitor console logs with prefixes: `[SONIOX]`, `[DEBUG]`, `[HOOK]`

## Environment Variables

Required in `server/.env`:
- `SONIOX_API_KEY` - Soniox transcription
- `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` - OAuth
- `DEEPSEEK_API_KEY` - Stage 1 summarization
- `ANTHROPIC_API_KEY` - Stage 2 summarization

## Git Workflow

See `.claude/DEVELOPMENT_GUIDELINES.md` - never commit untested code.

## Type Checking

- Python: Run `ty check` before committing
- TypeScript: Run `tsc --noEmit` before committing
