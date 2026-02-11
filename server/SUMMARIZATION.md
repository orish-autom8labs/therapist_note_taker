# Summarization Pipeline Documentation

**Last Updated**: 2026-02-11

## Overview

The Note Taker app uses a **three-stage summarization pipeline** with configurable quality levels to process therapy session transcripts. The pipeline is designed around a core principle: **structured extraction before synthesis**, which reduces hallucination by grounding every claim in the transcript.

## Architecture

```
                        FULL TRANSCRIPT
              (30-60 min, thousands of tokens)
                            |
                            v
                   CHUNK (with overlap)
              Split into 3-8 min segments
              Last 2-3 turns overlap between chunks
                            |
                            v
               STAGE 1: STRUCTURED EXTRACTION
               Provider: DeepSeek (cheap, fast)
               Process:
                 - Extract speakers, roles, topics
                 - Extract emotions WITH exact quotes
                 - Extract therapeutic moments, factual details
                 - Chain-of-thought self-check
                 - All chunks processed IN PARALLEL
               Output: Structured extractions per chunk
                            |
                            v
                    STAGE 2: SYNTHESIS
               Provider: Claude Haiku or Sonnet
               Process:
                 - Combine all structured extractions
                 - Generate KEY_TOPICS (% breakdown)
                 - Generate DETAILED_NOTES (chronological)
                 - Anti-hallucination: only use extracted facts
               Output: Draft summaries
                            |
                            v
              STAGE 3: FAITHFULNESS VERIFICATION
              (Level 3 / Clinical only)
               Provider: Claude Haiku
               Process:
                 - Compare draft vs. Stage 1 extractions
                 - Score: completeness, faithfulness, conciseness
                 - Remove ungrounded claims, add omissions
               Output: Corrected final summaries
```

## Summary Levels

Three quality tiers, designed for future subscription-based access:

| Level | Name | Stages Used | Stage 2 Model | Est. Cost | Est. Latency |
|-------|------|-------------|---------------|-----------|--------------|
| 1 | Quick | Stage 2 only (single pass, no chunking) | DeepSeek | ~$0.001 | ~3s |
| 2 | Standard | Stage 1 + Stage 2 | Claude Haiku | ~$0.005 | ~12s |
| 3 | Clinical | Stage 1 + Stage 2 + Stage 3 | Claude Sonnet | ~$0.012 | ~20s |

**Evaluation mode**: All 3 levels generated in one document for side-by-side comparison by the reviewing psychologist.

**Production mode** (future): Summary level determined by user's subscription tier.

## Why Three Stages?

### The Problem (from psychologist evaluation)
A psychologist reviewed AI-generated summaries and identified 58 issues:
- **Speaker misidentification** (~15): Confused who was speaking
- **Hallucination** (~12): Invented emotions, described events that didn't happen
- **Cross-chunk context loss** (~8): Confused daughter with partner across chunks
- **Missed themes** (~10): Failed to identify bullying, marital conflict

### Root Cause
The old Stage 1 used generic KEY_POINTS + SUMMARY format, losing critical structure. Stage 2 had to guess and hallucinate to fill gaps.

### The Solution
1. **Stage 1 (Structured Extraction)**: Force the model to ground every claim with exact quotes
2. **Stage 2 (Anti-hallucination Synthesis)**: Only generate from extracted facts
3. **Stage 3 (Verification)**: Catch remaining hallucinations and omissions

Research backing: [TN-Eval (ACL 2025)](https://arxiv.org/html/2503.20648), [Clinical Text Summarization (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC10635391/), [Self-Critique for Faithful Summarization (arXiv)](https://arxiv.org/abs/2512.05387)

## Quality Rubric

The same three dimensions guide all stages:

| Dimension | Stage 1 (Extraction) | Stage 2 (Synthesis) | Stage 3 (Verification) |
|-----------|---------------------|--------------------|-----------------------|
| **Completeness** | Extract ALL clinically relevant items | Include all extracted items | Check: any extracted fact missing? |
| **Faithfulness** | Include exact quotes as evidence | Only state what's in extractions | Check: any claim not in extractions? |
| **Conciseness** | Only extract clinically relevant info | No redundancy between sections | Check: any redundant content? |

## Stage 1: Structured Extraction

### Prompt Schema (Hebrew only)

The extraction prompt requires:

```
SPEAKERS:
- [Speaker with role if identifiable: therapist/patient/other]

TOPICS:
- [Topic label]: [1-sentence description]

EMOTIONS_EXPRESSED:
- [Speaker]: [Emotion] - "[Exact quote from transcript]"

THERAPEUTIC_MOMENTS:
- [What happened and who initiated it]

SIGNIFICANT_QUOTES:
- "[Exact quote]" - [Speaker]

FACTUAL_DETAILS:
- [Names, relationships, events, places mentioned]

SUMMARY:
2-3 sentence narrative.
```

**Quote-grounding rule**: If the model can't provide an exact quote, it must mark the claim as `[inferred]`.

**Self-check**: The prompt ends with instructions to re-read the transcript and verify speaker identification, emotion evidence, and topic completeness.

### Configuration
- **Model**: DeepSeek (`deepseek-chat`)
- **Temperature**: 0.1 (extractive task — minimize creativity)
- **Max tokens**: 2048 per chunk (richer than old 1024)
- **Parallelism**: All chunks processed concurrently

## Stage 2: Synthesis

### Anti-Hallucination Instructions
Added to both key_topics and detailed_notes prompts:
- Only include information directly supported by the chunk extractions
- Use the patient's own words when describing emotional states
- Do not name therapeutic techniques unless explicitly named in the transcript
- If only 2 speakers are identified, do NOT add a third
- Use the patient's actual name throughout (from `{patient_name}`)

### Output Styles

**Key Topics**: Percentage-based topic breakdown (3-6 topics, totaling 100%)

**Detailed Notes**: Chronological clinical notes with timestamps at topic transitions

### Configuration
- **Model (Level 2)**: Claude Haiku
- **Model (Level 3)**: Claude Sonnet
- **Temperature**: 0.3
- **Max tokens**: 4096

## Stage 3: Faithfulness Verification

Only runs for Level 3 (Clinical).

### Process
1. Input: Stage 1 extractions + Stage 2 draft summary
2. For each claim in the draft:
   - GROUNDED: maps to a specific extracted fact
   - INFERRED: reasonable inference but not directly stated
   - UNGROUNDED: no basis in the extractions
3. Output: Corrected summary that removes/softens ungrounded claims and adds omitted facts

### Configuration
- **Model**: Claude Haiku
- **Temperature**: 0.2
- **Max tokens**: 4096

## Chunking Strategy

### Speaker Segments with Overlap (Default)

- Groups consecutive speaker turns (3-8 min chunks)
- **Overlap**: Last 2-3 speaker turns of previous chunk included as context prefix in next chunk
- Overlap prevents cross-chunk context loss (the main failure mode for long sessions)

### Fixed Time (Fallback)
- Splits at fixed intervals
- Use when speaker diarization is unreliable

## Configuration

All settings in `src/config.py` (class `SummarizationConfig`):

```python
# Master switch
enabled: bool = True

# Stage 1: Extraction
stage1_provider: str = 'deepseek'
stage1_model: str = 'deepseek-chat'
stage1_approach: str = 'speaker_segments'
stage1_chunk_minutes_min: int = 3
stage1_chunk_minutes_max: int = 8
stage1_temperature: float = 0.1

# Stage 2: Synthesis
stage2_provider: str = 'claude'
stage2_model: str = 'claude-3-haiku-20240307'
stage2_styles: list = ['key_topics', 'detailed_notes']

# Stage 3: Verification (Level 3 only)
stage3_provider: str = 'claude'
stage3_model: str = 'claude-3-haiku-20240307'

# Summary levels
summary_levels: list = ['quick', 'standard', 'clinical']  # Evaluation mode: all
# summary_levels: list = ['standard']  # Production: single level per subscription
```

### Environment Variables

```bash
# Providers
SUMMARIZATION_STAGE1_PROVIDER=deepseek
SUMMARIZATION_STAGE1_MODEL=deepseek-chat
SUMMARIZATION_STAGE2_PROVIDER=claude
SUMMARIZATION_STAGE2_MODEL=claude-3-haiku-20240307
SUMMARIZATION_STAGE3_PROVIDER=claude
SUMMARIZATION_STAGE3_MODEL=claude-3-haiku-20240307

# Chunking
SUMMARIZATION_STAGE1_APPROACH=speaker_segments
SUMMARIZATION_CHUNK_MIN_MINUTES=3
SUMMARIZATION_CHUNK_MAX_MINUTES=8

# API Keys
DEEPSEEK_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here

# Safety
SUMMARIZATION_MAX_COST_USD=0.50
SUMMARIZATION_ENABLED=true
```

## Prompts

All prompts are **Hebrew-only** (no English maintenance).

```
server/src/prompts/summarization/
  chunk_extraction_he.md      # Stage 1: Structured extraction
  key_topics_he.md            # Stage 2: Key topics synthesis
  detailed_notes_he.md        # Stage 2: Detailed notes synthesis
  verification_he.md          # Stage 3: Faithfulness verification
```

## File Structure

```
server/src/
  config.py                                # SummarizationConfig + SummaryLevelConfig
  services/
    summarization/
      summarization_service.py             # Main orchestrator (3 stages + levels)
      language_detector.py                 # Hebrew/English detection
      prompt_loader.py                     # Loads prompt templates
      chunking/
        base_chunker.py                    # Abstract base class
        speaker_chunker.py                 # Speaker-based chunking (with overlap)
        fixed_time_chunker.py              # Time-based chunking
      synthesis/
        base_synthesizer.py                # Abstract base class
        key_topics.py                      # Key topics synthesizer
        detailed_notes.py                  # Detailed notes synthesizer
        verification.py                    # Stage 3 faithfulness verifier (NEW)
  prompts/
    summarization/
      chunk_extraction_he.md               # Stage 1 structured extraction (NEW)
      key_topics_he.md                     # Stage 2 key topics
      detailed_notes_he.md                 # Stage 2 detailed notes
      verification_he.md                   # Stage 3 verification (NEW)

scripts/
  run_summary.py                           # Offline CLI tool (NEW)
```

## Offline CLI Tool

`scripts/run_summary.py` runs summarization on existing transcript files without a live session.

```bash
# Run all 3 levels
python scripts/run_summary.py --transcript path/to/file.txt --patient "שם" --all-levels

# Run specific level
python scripts/run_summary.py --transcript path/to/file.txt --patient "שם" --level clinical

# Compare against psychologist annotations
python scripts/run_summary.py --transcript path/to/file.txt --patient "שם" --all-levels \
  --compare path/to/annotations.docx
```

Uses API keys from `server/.env`. No Drive, Firestore, or server needed.

## Retry Logic

All LLM calls use `complete_with_retry()` with exponential backoff:

```
Attempt 1 -> fail -> wait 2s
Attempt 2 -> fail -> wait 4s
Attempt 3 -> fail -> wait 8s
Attempt 4 -> fail -> raise error
```

**Retryable**: ConnectError, ReadError, TimeoutError, HTTP 429/503/529
**Non-retryable**: HTTP 401/402/403/404

Implementation: `server/src/providers/llm/retry.py`

## Firestore Tracking

Session lifecycle tracked in Firestore:

```
transcript_saved -> summarizing -> completed
                                -> summarization_failed
```

Document fields include status, attempt count, error details, total cost, and summary Drive links. Costs are tracked internally but **never shown to the therapist**.

## Error Handling

The summarization service **never fails the transcript save**:
1. All errors caught and wrapped in `SummaryResult`
2. Transcript always saved to Google Drive first
3. Error reports saved as separate files (max 1 per session)
4. Firestore tracks failed attempts for debugging

## Cost Estimation

For a typical 30-minute session (5 chunks):

| Level | Components | Est. Cost |
|-------|-----------|-----------|
| Quick | 1x DeepSeek call | ~$0.001 |
| Standard | 5x DeepSeek extraction + 2x Claude Haiku synthesis | ~$0.005 |
| Clinical | 5x DeepSeek extraction + 2x Claude Sonnet synthesis + 1x Claude Haiku verification | ~$0.012 |
| **All levels (evaluation)** | | **~$0.018** |

Monthly cost for 100 sessions (evaluation mode): ~$1.80 USD
