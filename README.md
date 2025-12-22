# Note Taker MVP

Secure session transcription app for therapists with Hebrew support.

## Features

- ✅ Real-time Hebrew transcription (no audio recording)
- ✅ Speaker identification (Speaker 1, Speaker 2)
- ✅ Modular transcription providers (easily switch between Soniox, Google, etc.)
- ✅ Auto-save to Google Drive (every 1 minute)
- ✅ Error recovery (localStorage + Drive temp files)
- ✅ Email notifications
- ✅ Zero-knowledge architecture (no data stored on our servers)

## Architecture

### Modular Transcription Providers

The app uses a pluggable provider architecture. To switch providers, simply change the `TRANSCRIPTION_PROVIDER` environment variable:

```bash
# Use Soniox (default)
TRANSCRIPTION_PROVIDER=soniox

# Use Google Cloud Speech-to-Text
TRANSCRIPTION_PROVIDER=google
```

### Adding a New Provider

1. Create a new provider class extending `TranscriptionProvider`:
   ```python
   # server/src/providers/my_new_provider.py
   from .transcription_provider import TranscriptionProvider
   
   class MyNewProvider(TranscriptionProvider):
       def get_name(self):
           return 'MyNewProvider'
       
       def supports_language(self, code):
           # ...
           pass
       
       def supports_speaker_diarization(self):
           return True
       
       async def start_streaming_session(self, options, on_transcript, on_error):
           # ...
           pass
       
       async def process_batch(self, audio_buffer, options):
           # ...
           pass
   ```

2. Register it in `provider_factory.py`:
   ```python
   case 'mynew':
       return MyNewProvider(config)
   ```

3. Add configuration in `.env` and `config.py`

### Provider Implementation Notes

**Soniox Provider:**
- The current implementation uses a placeholder structure
- You'll need to integrate with Soniox's actual API (REST or SDK)
- Check [Soniox documentation](https://docs.soniox.com) for the latest API
- The provider structure is ready - just implement the API calls

**Google Provider:**
- Requires `@google-cloud/speech` package (already in dependencies)
- Needs service account JSON credentials
- Supports streaming and batch processing
- Full speaker diarization support

## Setup

### Prerequisites

- Node.js 18+
- npm or yarn
- Google Cloud account (for Drive integration)
- Transcription provider API key (Soniox or Google)

### Installation

```bash
# Install all dependencies
npm run install-all

# Or install separately
npm install
cd server && npm install
cd ../client && npm install
```

### Configuration

1. Copy `.env.example` to `server/.env`
2. Fill in your API keys and credentials
3. Configure your transcription provider

### Running

```bash
# Development (runs both frontend and backend)
npm run dev

# Or separately:
npm run server  # Backend on :3001
npm run client  # Frontend on :3000
```

## Project Structure

```
note_taker/
├── server/                 # Backend (Node.js/Express)
│   ├── src/
│   │   ├── providers/      # Transcription provider modules
│   │   │   ├── TranscriptionProvider.js  # Abstract base class
│   │   │   ├── SonioxProvider.js        # Soniox implementation
│   │   │   ├── GoogleProvider.js         # Google implementation
│   │   │   └── ProviderFactory.js        # Provider factory
│   │   ├── services/      # Business logic
│   │   ├── routes/        # API routes
│   │   └── config.js      # Configuration
│   └── index.js           # Server entry point
├── client/                # Frontend (React)
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── services/      # API clients
│   │   └── App.js
│   └── public/
└── package.json
```

## Environment Variables

See `server/.env.example` for all required environment variables.

## Documentation

- `UX_DESIGN.md` - UI/UX design specifications
- `RECOMMENDATIONS.md` - Technical decisions and recommendations
- `TECHNICAL_ANALYSIS.md` - Detailed technical analysis

## License

ISC

