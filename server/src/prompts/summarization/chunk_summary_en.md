# Chunk Summary Prompt (English)

You are summarizing a segment of a therapy session transcript.

## Segment Information
- Time Range: {start_time} - {end_time}
- Duration: {duration_minutes} minutes

## Transcript
{transcript}

## Instructions

Analyze this segment and provide:

1. **KEY_POINTS** (2-4 bullet points):
   - What main topics were discussed?
   - What emotions or concerns were expressed?
   - Any notable therapeutic moments or insights?
   - Any action items or decisions made?

2. **SUMMARY** (2-3 sentences):
   Write a brief narrative summary that captures the essential content and emotional tone of this segment.

## Output Format

Respond EXACTLY in this format:

KEY_POINTS:
- First key point here
- Second key point here
- Third key point here (if applicable)

SUMMARY:
Your 2-3 sentence summary here, capturing the main content and tone.
