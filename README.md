# Note Taker

Secure real-time transcription app for therapists with Hebrew support.

## Features

- Real-time Hebrew transcription using Soniox SDK (client-side)
- Speaker diarization (Speaker A, Speaker B, ...)
- Auto-save to Google Drive (every 60 seconds)
- Session recovery from localStorage (every 5 seconds)
- 60-minute session timer with warnings
- Audio visualizer (32-bar waveform)
- Two-stage LLM summarization (DeepSeek + Claude)
- Zero-knowledge architecture (no audio/data stored on servers)
- Automatic WebSocket reconnection for mobile resilience

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     React Frontend                          │
│  • Soniox SDK (WebSocket to Soniox Cloud)                  │
│  • Audio visualizer, session timer, transcript display      │
│  • localStorage recovery, auto-save to backend             │
└─────────────────────────┬───────────────────────────────────┘
                          │ REST API
┌─────────────────────────▼───────────────────────────────────┐
│                   FastAPI Backend                           │
│  • Google OAuth & Drive integration                        │
│  • Soniox temporary API key generation                     │
│  • Two-stage LLM summarization pipeline                    │
│  • Email notifications                                      │
└─────────────────────────────────────────────────────────────┘
```

### Key Design Decisions

- **Client-side transcription**: Soniox SDK runs in browser, not proxied through server
- **Pluggable providers**: Easy to switch transcription providers (Soniox, Google, Mock)
- **Two-stage summarization**: Cheap model (DeepSeek) for chunking, quality model (Claude) for synthesis

## Quick Start

See [QUICK_START_GUIDE.md](QUICK_START_GUIDE.md) for detailed setup instructions.

### Prerequisites

- Python 3.10+
- Node.js 18+
- Google Cloud account (for OAuth & Drive)
- Soniox API key

### Installation

```bash
# Backend
cd server
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Frontend
cd client
npm install
```

### Configuration

1. Copy `server/.env.example` to `server/.env`
2. Fill in API keys:
   - `SONIOX_API_KEY` - Soniox transcription
   - `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` - OAuth
   - `DEEPSEEK_API_KEY` / `ANTHROPIC_API_KEY` - Summarization (optional)

### Running

```bash
# Terminal 1: Backend
cd server
source venv/bin/activate
python run.py
# Runs on http://localhost:3001

# Terminal 2: Frontend
cd client
npm start
# Runs on http://localhost:3000
```

## Project Structure

```
note_taker/
├── client/                     # React Frontend
│   ├── src/
│   │   ├── components/         # React components
│   │   │   ├── ActiveSession.js    # Main recording UI
│   │   │   ├── AudioVisualizer.js  # 32-bar waveform
│   │   │   ├── SessionTimer.js     # 60-min countdown
│   │   │   └── ...
│   │   ├── hooks/              # Custom React hooks
│   │   │   ├── useSonioxClient.js  # Soniox SDK wrapper
│   │   │   ├── useSessionTimer.js  # Timer logic
│   │   │   └── useAudioVisualizer.js
│   │   ├── services/           # API clients
│   │   └── config/             # Configuration
│   └── Dockerfile
│
├── server/                     # FastAPI Backend (Python)
│   ├── main.py                 # API endpoints
│   ├── run.py                  # Development runner
│   ├── src/
│   │   ├── config.py           # Configuration (Pydantic)
│   │   ├── providers/          # Transcription providers
│   │   │   ├── soniox_provider.py
│   │   │   ├── google_provider.py
│   │   │   └── llm/            # LLM providers
│   │   │       ├── deepseek_provider.py
│   │   │       └── claude_provider.py
│   │   └── services/           # Business logic
│   │       ├── drive_service.py
│   │       ├── email_service.py
│   │       └── summarization/  # Two-stage pipeline
│   ├── requirements.txt
│   └── Dockerfile
│
├── docs/                       # Documentation
│   └── README.md               # Documentation index
│
└── Key Documentation:
    ├── QUICK_START_GUIDE.md    # Setup & testing guide
    ├── PRD.md                  # Product requirements
    ├── PROVIDER_GUIDE.md       # Transcription providers
    ├── DEPLOYMENT_AND_OAUTH.md # Deployment guide
    └── CLAUDE.md               # Claude Code context
```

## Documentation

| Document | Purpose |
|----------|---------|
| [QUICK_START_GUIDE.md](QUICK_START_GUIDE.md) | Setup and testing instructions |
| [PRD.md](PRD.md) | Complete product requirements |
| [PROVIDER_GUIDE.md](PROVIDER_GUIDE.md) | Transcription provider architecture |
| [DEPLOYMENT_AND_OAUTH.md](DEPLOYMENT_AND_OAUTH.md) | Deployment and OAuth setup |
| [GOOGLE_OAUTH_SETUP.md](GOOGLE_OAUTH_SETUP.md) | Google Cloud Console setup |
| [server/SUMMARIZATION.md](server/SUMMARIZATION.md) | LLM summarization pipeline |

## Environment Variables

### Required

| Variable | Description |
|----------|-------------|
| `SONIOX_API_KEY` | Soniox API key for transcription |
| `GOOGLE_CLIENT_ID` | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | Google OAuth client secret |

### Optional (Summarization)

| Variable | Description |
|----------|-------------|
| `DEEPSEEK_API_KEY` | DeepSeek API key (Stage 1 chunking) |
| `ANTHROPIC_API_KEY` | Anthropic API key (Stage 2 synthesis) |
| `SUMMARIZATION_ENABLED` | Enable/disable summarization (default: true) |

See `server/.env.example` for complete list.

## License

ISC
