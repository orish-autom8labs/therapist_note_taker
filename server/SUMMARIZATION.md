# Summarization Pipeline Documentation

**Last Updated**: 2026-02-10

## Overview

The Note Taker app uses a **two-stage hierarchical summarization pipeline** to process therapy session transcripts. This approach allows processing of long transcripts (30-60+ minutes) efficiently and cost-effectively.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FULL TRANSCRIPT                             │
│              (could be 30-60 min, thousands of tokens)              │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STAGE 1: CHUNKING                                                  │
│  ─────────────────                                                  │
│  Provider: DeepSeek (cheap, fast)                                   │
│  Model: deepseek-chat                                               │
│                                                                     │
│  Process:                                                           │
│  1. Split transcript into 3-8 minute segments                       │
│  2. Each segment → LLM call → KEY_POINTS + SUMMARY                  │
│  3. All chunks processed IN PARALLEL                                │
│                                                                     │
│  Output: List of ChunkSummary objects                               │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STAGE 2: SYNTHESIS                                                 │
│  ──────────────────                                                 │
│  Provider: Claude (quality)                                         │
│  Model: claude-3-haiku-20240307                                     │
│                                                                     │
│  Process:                                                           │
│  1. Combine all chunk summaries                                     │
│  2. Generate KEY_TOPICS summary (topic breakdown with percentages)  │
│  3. Generate DETAILED_NOTES (comprehensive paragraphs + timestamps) │
│                                                                     │
│  Output: Final formatted summaries                                  │
└─────────────────────────────────────────────────────────────────────┘
```

## Why Two Stages?

### The Problem
- A 30-minute therapy session produces ~10,000+ tokens of transcript
- Sending all of this to a quality LLM is expensive and may exceed context limits
- Single-pass summarization loses detail and nuance

### The Solution
1. **Stage 1 (Cheap Model)**: Break transcript into chunks, summarize each chunk separately
   - Reduces 10,000 tokens → ~1,500 tokens of summaries
   - Uses cheap model (DeepSeek: ~$0.001/chunk)
   - Runs in parallel for speed

2. **Stage 2 (Quality Model)**: Synthesize chunk summaries into final output
   - Input is now manageable (~1,500 tokens instead of 10,000)
   - Uses quality model (Claude Haiku) for coherent final output
   - Can generate multiple output styles

## Token Allocation

| Stage | Model | Input Size | Output Limit | Cost |
|-------|-------|------------|--------------|------|
| Stage 1 | DeepSeek | ~500-2000 tokens/chunk | 1024 tokens | ~$0.001/chunk |
| Stage 2 | Claude Haiku | ~1000-3000 tokens (all summaries) | 4096 tokens | ~$0.01-0.02 |

**Total cost for 30-min session**: ~$0.02-0.05 USD

### Why 4096 Output Tokens for Stage 2?

Claude 3 Haiku has a maximum output limit of 4096 tokens. This is sufficient for:
- Key Topics: ~500-1000 tokens
- Detailed Notes: ~2000-3500 tokens

If longer output is needed, consider upgrading to Claude 3.5 Sonnet (8192 max output).

## Configuration

All settings are in `src/config.py` (class `SummarizationConfig`):

```python
# ═══════════════════════════════════════════════════════════════════
# MASTER SWITCH
# ═══════════════════════════════════════════════════════════════════
enabled: bool = True  # Set to False to disable summarization

# ═══════════════════════════════════════════════════════════════════
# STAGE 1: CHUNKING CONFIGURATION
# ═══════════════════════════════════════════════════════════════════
stage1_provider: str = 'deepseek'           # LLM provider
stage1_model: str = 'deepseek-chat'         # Model name
stage1_approach: str = 'speaker_segments'   # Chunking strategy
stage1_chunk_minutes_min: int = 3           # Min chunk duration
stage1_chunk_minutes_max: int = 8           # Max chunk duration

# ═══════════════════════════════════════════════════════════════════
# STAGE 2: SYNTHESIS CONFIGURATION
# ═══════════════════════════════════════════════════════════════════
stage2_provider: str = 'claude'                      # LLM provider
stage2_model: str = 'claude-3-haiku-20240307'        # Model name
stage2_styles: list = ['key_topics', 'detailed_notes']  # Output styles
```

### Environment Variables

Override defaults via environment:

```bash
# Providers
SUMMARIZATION_STAGE1_PROVIDER=deepseek
SUMMARIZATION_STAGE1_MODEL=deepseek-chat
SUMMARIZATION_STAGE2_PROVIDER=claude
SUMMARIZATION_STAGE2_MODEL=claude-3-haiku-20240307

# Chunking
SUMMARIZATION_STAGE1_APPROACH=speaker_segments  # or 'fixed_time'
SUMMARIZATION_CHUNK_MIN_MINUTES=3
SUMMARIZATION_CHUNK_MAX_MINUTES=8

# API Keys
DEEPSEEK_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here

# Safety
SUMMARIZATION_MAX_COST_USD=0.50  # Max cost per session
SUMMARIZATION_ENABLED=true       # Master switch
```

## Chunking Strategies

### 1. Speaker Segments (Default)

Breaks transcript at speaker changes, merging small segments:
- Respects conversation flow
- Keeps speaker context together
- Chunks are 3-8 minutes (configurable)

### 2. Fixed Time

Breaks transcript at fixed intervals:
- Simpler, more predictable
- May split mid-conversation
- Use when speaker diarization is unreliable

## Output Styles

### Key Topics

Percentage-based topic breakdown:

```
## Key Topics

### Session Management (15%)
Discussion of scheduling and logistics...

### Anxiety and Work Stress (40%)
Patient expressed concerns about upcoming presentation...

### Coping Strategies (30%)
Therapist introduced breathing techniques...

### Action Items (15%)
- Practice 4-7-8 breathing daily
- Journal about negative predictions vs outcomes
```

### Detailed Notes

Comprehensive clinical notes with timestamps:

```
## Detailed Session Notes

The session began [00:00] with the patient reporting increased anxiety...

Around [05:30], the conversation shifted to exploring the roots of
performance anxiety. The patient connected current fears to a childhood
memory, stating "I still hear my father's voice saying I embarrassed
the family" [08:15]. This moment appeared emotionally significant.

The therapist introduced a cognitive reframing exercise [12:00]...

---
*Session duration: approximately 28 minutes*
```

## File Structure

```
server/src/
├── config.py                          # Configuration (SummarizationConfig)
├── services/
│   └── summarization/
│       ├── __init__.py
│       ├── summarization_service.py   # Main orchestrator
│       ├── language_detector.py       # Hebrew/English detection
│       ├── prompt_loader.py           # Loads prompt templates
│       ├── chunking/
│       │   ├── base_chunker.py        # Abstract base class
│       │   ├── speaker_chunker.py     # Speaker-based chunking
│       │   └── fixed_time_chunker.py  # Time-based chunking
│       └── synthesis/
│           ├── base_synthesizer.py    # Abstract base class
│           ├── key_topics.py          # Key topics synthesizer
│           └── detailed_notes.py      # Detailed notes synthesizer
└── prompts/
    └── summarization/
        ├── chunk_summary_en.md        # Stage 1 prompt (English)
        ├── chunk_summary_he.md        # Stage 1 prompt (Hebrew)
        ├── key_topics_en.md           # Stage 2 key topics (English)
        ├── key_topics_he.md           # Stage 2 key topics (Hebrew)
        ├── detailed_notes_en.md       # Stage 2 detailed notes (English)
        └── detailed_notes_he.md       # Stage 2 detailed notes (Hebrew)
```

## Retry Logic

All LLM calls use `complete_with_retry()` with exponential backoff:

```
Attempt 1 → fail → wait 2s
Attempt 2 → fail → wait 4s
Attempt 3 → fail → wait 8s
Attempt 4 → fail → raise error
```

**Retryable errors** (transient, worth retrying):
- `ConnectError`, `ReadError`, `TimeoutError` — network issues
- HTTP 429 — rate limit
- HTTP 503, 529 — server overloaded

**Non-retryable errors** (fail immediately):
- HTTP 401 — bad API key
- HTTP 402 — billing issue
- HTTP 403, 404 — permanent errors

Implementation: `server/src/providers/llm/retry.py`

## Firestore Tracking

Each session's summarization lifecycle is tracked in Firestore:

```
transcript_saved → summarizing → completed
                                → summarization_failed
```

**Document fields** (`{prefix}_sessions/{session_id}`):
- `status`: Current state
- `summarization.attempts`: Number of attempts
- `summarization.last_error`: Error message (if failed)
- `summarization.total_cost_usd`: Total LLM cost
- `summaries.detailed_notes`: Drive file info for summary

The frontend polls `GET /api/sessions/{id}/status` every 5 seconds to show summary progress and enable the "View Summary" button when ready.

## Error Handling

The summarization service **never fails the transcript save**:

1. All errors are caught and wrapped in `SummaryResult`
2. If summarization fails, an error report is generated instead
3. The transcript is always saved to Google Drive
4. Error reports include:
   - Error type and message
   - Transcript info (size, first text)
   - Configuration at time of error
   - Full traceback
5. Max 1 error file per session (overwrites existing)

Error reports are saved as separate files: `{patient}_Summary_ERROR.txt`

## Adding New Providers

1. Create provider class in `src/providers/llm/`:

```python
class NewProvider(LLMProvider):
    async def complete(self, prompt, max_tokens, temperature) -> LLMResponse:
        # Implementation
        pass
```

2. Register in `LLMProviderFactory`

3. Add API key to `SummarizationConfig`

4. Update environment variables

## Adding New Output Styles

1. Create synthesizer in `src/services/summarization/synthesis/`:

```python
class NewStyleSynthesizer(BaseSynthesizer):
    def get_style_name(self) -> str:
        return "new_style"

    async def synthesize(self, chunk_summaries, total_duration_minutes) -> SynthesisResult:
        # Implementation
        pass
```

2. Add prompt templates: `prompts/summarization/new_style_en.md`, `new_style_he.md`

3. Register in `SummaryStyle` enum and `_create_synthesizer()` method

4. Add to `stage2_styles` config list

## Debugging

### Enable Verbose Logging

Check server logs for `[SUMMARIZATION]` prefix:

```
[SUMMARIZATION] Service initialized - Stage1: deepseek, Stage2: claude
[SUMMARIZATION] Background task started for session session_123
[SUMMARIZATION] Starting background summarization...
[SUMMARIZATION] Language detected: he
[SUMMARIZATION] Chunked into 5 segments
[SUMMARIZATION] Stage 1 complete: 5 chunk summaries, cost: $0.005
[SUMMARIZATION] Stage 2 complete: key_topics + detailed_notes, cost: $0.018
[SUMMARIZATION] Total cost: $0.023
```

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| `max_tokens > 4096` | Output limit exceeds Haiku's max | Reduce max_tokens in synthesizer |
| `API key invalid` | Missing or wrong API key | Check env vars |
| `Timeout` | Long transcript, slow model | Increase timeout or chunk size |
| Empty summaries | Transcript too short | Check minimum duration settings |

## Cost Estimation

For a typical 30-minute session:

| Component | Tokens | Cost |
|-----------|--------|------|
| Stage 1 (5 chunks × DeepSeek) | ~5000 input, ~1500 output | ~$0.005 |
| Stage 2 Key Topics (Claude) | ~1500 input, ~800 output | ~$0.008 |
| Stage 2 Detailed Notes (Claude) | ~1500 input, ~3000 output | ~$0.015 |
| **Total** | | **~$0.03** |

Monthly cost for 100 sessions: ~$3.00 USD
