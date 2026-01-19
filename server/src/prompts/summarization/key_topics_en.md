# Key Topics Synthesis Prompt (English)

You are creating a "Key Topics" summary for a therapy session.

## Session Chunk Summaries

{chunk_summaries}

## Session Information
- Total Chunks: {total_chunks}
- Total Duration: approximately {total_duration_minutes} minutes

## Instructions

Create a percentage-based topic breakdown of the session:

1. **Identify 3-6 main topics** discussed throughout the session
2. **Estimate the percentage** of time spent on each topic (must sum to 100%)
3. **Provide 2-4 key bullet points** per topic
4. **Order topics** by percentage (highest first)

## Guidelines

- Topics should be thematic (e.g., "Family Dynamics", "Work Stress", "Coping Strategies")
- Percentages should reflect actual discussion time based on chunk timestamps
- Bullet points should capture specific, concrete details
- Use professional but accessible language
- Preserve important quotes or specific examples when relevant

## Output Format

Respond EXACTLY in this format:

# Key Topics

## [Topic Name] - [XX]%
- Key point about this topic
- Another key point
- Third point if applicable

## [Another Topic] - [XX]%
- Key point about this topic
- Another key point

## [Third Topic] - [XX]%
- Key point about this topic
- Another key point

---
*Session duration: approximately {total_duration_minutes} minutes*

## Example Output

# Key Topics

## Processing Workplace Conflict - 45%
- Client described ongoing tension with supervisor over project deadlines
- Expressed feelings of being undervalued and micromanaged
- Identified pattern of avoiding direct communication about needs

## Family Relationship Dynamics - 35%
- Discussed recent argument with spouse about household responsibilities
- Connected current conflict to childhood experiences of feeling responsible
- Recognized tendency to take on caretaker role

## Developing Coping Strategies - 20%
- Practiced breathing techniques for managing acute anxiety
- Set goal to practice assertive communication once this week
- Scheduled follow-up to review progress

---
*Session duration: approximately 50 minutes*
