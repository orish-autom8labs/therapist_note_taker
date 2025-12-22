# Final Tokens Explanation

## What is a "Final Token"?

A **final token** is a piece of transcribed text that Soniox has determined is **complete and won't change**. 

### Who Decides?

**Soniox's AI model** decides when a token is final based on:

1. **Endpoint Detection** (`enable_endpoint_detection: True`):
   - Detects when the speaker pauses or stops speaking
   - After a pause (typically 0.5-2 seconds), Soniox finalizes the tokens up to that point
   - This is why we enabled `enable_endpoint_detection: True` in the config

2. **Natural Speech Boundaries**:
   - End of sentences (periods, question marks, exclamation marks)
   - Natural pauses in speech
   - Speaker changes (if speaker diarization is enabled)

3. **Model Confidence**:
   - When Soniox is highly confident the transcription is correct
   - Usually happens after processing enough audio context

### How It Works

**Non-Final Tokens**:
- Continuously updated as more audio arrives
- Example: "אנ" → "אנח" → "אנחנו" → "אנחנו ע" → ...
- These are **provisional** and can change

**Final Tokens**:
- Returned once and never change
- Example: "טוב, שלום." (after speaker pauses)
- These are **permanent** and should be displayed

### The Problem

From your logs, I can see:
- Line 917-928: Final tokens arrive: `'is_final': True` for "טוב, שלום. אני רוצה ל"
- Line 951: Backend sends: `[SONIOX] Sending FINAL transcript: "טוב, שלום. אני רוצה ל"`
- Line 954: Frontend should receive it

**But the UI isn't showing it!**

### Why Final Tokens Might Be Delayed

1. **Continuous Speech**: If you speak continuously without pausing, Soniox won't finalize tokens
2. **Endpoint Detection**: Needs a pause to trigger (0.5-2 seconds of silence)
3. **Model Processing**: Soniox needs time to process and confirm accuracy

### Solution: Fallback Mechanism

Since final tokens depend on speech pauses (which might not happen often), we'll add a **fallback**:
- **Every 5 seconds**, send accumulated text (final + non-final) even if not finalized
- This ensures users see progress even during continuous speech
- Final tokens will still be sent when they arrive (for accuracy)

This gives us:
- ✅ Real-time feedback (every 5 seconds)
- ✅ Accurate final transcripts (when Soniox finalizes)
- ✅ No letter-by-letter build-up (only send every 5 seconds)




