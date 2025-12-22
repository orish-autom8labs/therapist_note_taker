# Transcription Provider Guide

## Modular Provider Architecture

The app uses a pluggable provider system. You can easily switch between providers or add new ones.

## Current Providers

### 1. Soniox (Recommended for Hebrew)

**Status:** Structure ready, needs API integration

**Configuration:**
```env
TRANSCRIPTION_PROVIDER=soniox
SONIOX_API_KEY=your_api_key
```

**Implementation Notes:**
- The `SonioxProvider` class structure is complete
- You need to integrate with Soniox's actual API
- Check [Soniox API documentation](https://docs.soniox.com) for:
  - Authentication method
  - Streaming API endpoint
  - Response format
  - Speaker diarization parameters

**To Complete Implementation:**
1. Review Soniox API documentation
2. Update `SonioxProvider.js` with actual API calls
3. Adjust `parseSonioxResponse()` based on actual response format
4. Test with Hebrew audio samples

### 2. Google Cloud Speech-to-Text

**Status:** Fully implemented

**Configuration:**
```env
TRANSCRIPTION_PROVIDER=google
GOOGLE_PROJECT_ID=your_project_id
GOOGLE_CREDENTIALS={"type":"service_account",...}
```

**Setup:**
1. Enable Cloud Speech-to-Text API in Google Cloud Console
2. Create service account
3. Download JSON credentials
4. Set `GOOGLE_CREDENTIALS` to JSON string or file path

**Features:**
- ✅ Streaming transcription
- ✅ Batch processing
- ✅ Speaker diarization
- ✅ Hebrew support (he-IL)

## Switching Providers

### Method 1: Environment Variable (Recommended)

```bash
# In server/.env
TRANSCRIPTION_PROVIDER=soniox  # or 'google'
```

Restart the server.

### Method 2: Runtime Switch (For Testing)

```javascript
// In server code
transcriptionService.switchProvider('google', {
  projectId: 'new-project',
  credentials: {...}
});
```

## Adding a New Provider

### Step 1: Create Provider Class

Create `server/src/providers/YourProvider.js`:

```javascript
import { TranscriptionProvider } from './TranscriptionProvider.js';

export class YourProvider extends TranscriptionProvider {
  constructor(config) {
    super(config);
    // Initialize your provider
  }

  getName() {
    return 'YourProvider';
  }

  supportsLanguage(languageCode) {
    // Return true if provider supports this language
    return ['he-IL', 'en-US'].includes(languageCode);
  }

  supportsSpeakerDiarization() {
    return true; // or false
  }

  async startStreamingSession(options, onTranscript, onError) {
    // options: { language, enableSpeakerDiarization }
    // onTranscript: (chunk) => void - called with { text, speaker, isFinal, timestamp }
    // onError: (error) => void
    
    // Start your streaming session
    // Return session object with:
    // - sendAudio(audioChunk): void
    // - stop(): Promise<void>
    // - isActive(): boolean
  }

  async processBatch(audioBuffer, options) {
    // Process entire audio file
    // Return array of segments: [{ text, speaker, startTime, endTime }]
  }
}
```

### Step 2: Register in Factory

Add to `server/src/providers/ProviderFactory.js`:

```javascript
import { YourProvider } from './YourProvider.js';

// In createProvider():
case 'yourprovider':
  return new YourProvider({
    apiKey: config.apiKey || process.env.YOUR_PROVIDER_API_KEY,
    // ... other config
  });
```

### Step 3: Add Configuration

In `server/src/config.js`:

```javascript
providers: {
  yourprovider: {
    apiKey: process.env.YOUR_PROVIDER_API_KEY,
    // ... other config
  },
}
```

In `server/.env`:

```env
YOUR_PROVIDER_API_KEY=your_key_here
```

### Step 4: Test

```bash
# Set provider
TRANSCRIPTION_PROVIDER=yourprovider

# Restart server
npm run server
```

## Provider Interface Requirements

All providers must implement:

1. **`startStreamingSession(options, onTranscript, onError)`**
   - Start real-time transcription
   - Call `onTranscript` with chunks: `{ text, speaker, isFinal, timestamp }`
   - Return session object with `sendAudio()`, `stop()`, `isActive()`

2. **`processBatch(audioBuffer, options)`**
   - Process complete audio file
   - Return array of transcript segments

3. **`getName()`** - Provider name
4. **`supportsLanguage(code)`** - Check language support
5. **`supportsSpeakerDiarization()`** - Check speaker diarization support

## Testing Providers

### Test Script Example

```javascript
// test-provider.js
import { ProviderFactory } from './src/providers/ProviderFactory.js';

const provider = ProviderFactory.createProvider('soniox', {
  apiKey: process.env.SONIOX_API_KEY
});

// Test streaming
const session = await provider.startStreamingSession(
  { language: 'he-IL', enableSpeakerDiarization: true },
  (chunk) => console.log('Transcript:', chunk),
  (error) => console.error('Error:', error)
);

// Send test audio
session.sendAudio(audioBuffer);

// Stop
await session.stop();
```

## Provider Comparison

| Feature | Soniox | Google |
|---------|--------|--------|
| Hebrew Accuracy | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Speaker Diarization | ✅ | ✅ |
| Streaming | ✅ | ✅ |
| Cost | Lower | Higher |
| Setup Complexity | Medium | High |
| API Documentation | Good | Excellent |

## Troubleshooting

### Provider not found
- Check provider name spelling (case-insensitive)
- Verify provider is registered in `ProviderFactory.js`

### Authentication errors
- Verify API keys/credentials are correct
- Check environment variables are loaded

### Streaming not working
- Verify provider supports streaming
- Check WebSocket connection
- Review provider-specific error messages

### Speaker diarization not working
- Verify provider supports it (`supportsSpeakerDiarization()`)
- Check options: `enableSpeakerDiarization: true`
- Review provider documentation for requirements




