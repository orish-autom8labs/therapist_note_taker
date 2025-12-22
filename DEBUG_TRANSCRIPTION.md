# Debug Transcription Logging

## What I Added

I've added comprehensive debug logging so you can see transcriptions in the server logs even if they don't appear in the frontend.

## Debug Output Format

### 1. Soniox Token Processing
When Soniox sends tokens, you'll see:
```
[SONIOX] Received 5 tokens (showing first 5): [{'text': 'Hello', 'is_final': False, 'speaker': '1'}, ...]
[SONIOX TOKEN] text="Hello", speaker=1, is_final=False
[SONIOX TOKEN] text=" world", speaker=1, is_final=True
```

### 2. Transcript Chunks Being Sent
When a transcript chunk is ready to send:
```
[SONIOX] Calling on_transcript with: text="Hello world", speaker=Speaker 1
```

### 3. Transcripts Received by Main Server
When the main server receives a transcript:
```
[TRANSCRIPT] [FINAL] Speaker 1: Hello world
[DEBUG] Full transcript chunk: {'text': 'Hello world', 'speaker': 'Speaker 1', 'is_final': True, 'timestamp': 1234567890}
[DEBUG] Sending transcript to frontend: {"type":"transcript","text":"Hello world","speaker":"Speaker 1",...
```

## What to Look For

When you speak, check the server logs for:

1. **Are tokens being received?**
   - Look for: `[SONIOX] Received X tokens`
   - If you don't see this, Soniox isn't sending transcription data

2. **Are tokens being processed?**
   - Look for: `[SONIOX TOKEN] text="..."`
   - This shows individual words/tokens from Soniox

3. **Are transcripts being created?**
   - Look for: `[SONIOX] Calling on_transcript with: text="..."`
   - This shows when we're ready to send a transcript chunk

4. **Are transcripts reaching the main server?**
   - Look for: `[TRANSCRIPT] [FINAL] Speaker X: ...`
   - This shows the readable transcript format

5. **Are transcripts being sent to frontend?**
   - Look for: `[DEBUG] Sending transcript to frontend: ...`
   - This confirms the message is being sent over WebSocket

## Troubleshooting

### No `[SONIOX] Received X tokens` messages
- **Problem**: Soniox isn't sending transcription data
- **Check**: 
  - Is the connection still active? (look for connection errors)
  - Is audio being sent? (look for `[DEBUG] Sending X bytes to transcription provider`)
  - Is there a balance/error issue? (check for error messages)

### Tokens received but no `[SONIOX] Calling on_transcript`
- **Problem**: Token processing logic might have an issue
- **Check**: Look for errors in token processing loop

### Transcripts created but no `[TRANSCRIPT]` messages
- **Problem**: `on_transcript` callback might not be working
- **Check**: Look for errors in the callback

### Transcripts in logs but not in frontend
- **Problem**: Frontend WebSocket might not be receiving messages
- **Check**: 
  - Browser console for WebSocket errors
  - Network tab to see if messages are being received
  - Frontend code that handles `transcript` messages

## Example Log Flow (Working)

```
[SONIOX] Received 3 tokens (showing first 5): [{'text': 'שלום', 'is_final': False, 'speaker': '1'}, ...]
[SONIOX TOKEN] text="שלום", speaker=1, is_final=False
[SONIOX TOKEN] text=" ", speaker=1, is_final=False
[SONIOX TOKEN] text="עולם", speaker=1, is_final=True
[SONIOX] Calling on_transcript with: text="שלום עולם", speaker=Speaker 1
[TRANSCRIPT] [FINAL] Speaker 1: שלום עולם
[DEBUG] Sending transcript to frontend: {"type":"transcript","text":"שלום עולם",...
```

## Next Steps

1. **Restart your server** to pick up the new logging
2. **Start a session and speak**
3. **Watch the server logs** - you should see the flow above
4. **Share the logs** if something is missing or broken

The logs will now show you exactly where transcriptions are getting stuck!




