# Detailed Notes Synthesis Prompt (English)

You are creating detailed clinical notes for a therapy session.

## Session Chunk Summaries

{chunk_summaries}

## Session Information
- Total Chunks: {total_chunks}
- Total Duration: approximately {total_duration_minutes} minutes

## Instructions

Create comprehensive session notes with inline timestamps:

1. **Organize chronologically** - follow the natural flow of the session
2. **Include timestamps** [MM:SS] at key moments and topic transitions
3. **Attribute statements** to specific speakers when relevant
4. **Note therapeutic interventions** and client responses
5. **Highlight emotional shifts** and significant moments
6. **Preserve important quotes** when they capture key insights

## Guidelines

- Write in professional clinical style
- Use flowing paragraphs, organized by topic or phase
- Be specific with details, names, and examples mentioned
- Capture the narrative arc of the session
- Note any homework, action items, or follow-up plans
- Include both content (what was discussed) and process (how it was discussed)

## Output Format

Write detailed notes in flowing paragraphs with embedded timestamps. Example structure:

# Detailed Session Notes

[Opening paragraph describing how the session began and initial topics...]

[Middle paragraphs covering the main content of the session, with timestamps at key moments...]

[Closing paragraph summarizing conclusions, agreements, and next steps...]

---
*Session duration: approximately {total_duration_minutes} minutes*

## Example Output

# Detailed Session Notes

The session began [00:00] with the client reporting increased anxiety over the past week, particularly related to an upcoming presentation at work. They described difficulty sleeping and racing thoughts, rating their anxiety at 7/10.

Around [05:30], the conversation shifted to exploring the roots of this performance anxiety. The client connected their current fears to a childhood memory of being criticized during a school play, stating "I still hear my father's voice saying I embarrassed the family" [08:15]. This moment appeared emotionally significant, with visible affect.

The therapist introduced a cognitive reframing exercise [12:00], asking the client to identify evidence both supporting and contradicting their belief that "I will fail and everyone will judge me." The client identified several past successes but noted difficulty internalizing them.

At [18:45], the focus shifted to developing practical coping strategies. The client expressed interest in breathing techniques and agreed to practice the 4-7-8 method before their presentation. A behavioral experiment was designed: the client will practice their presentation in front of a trusted colleague and notice their actual response versus the feared response.

The session concluded [25:00] with the client reporting feeling "more hopeful" and rating their anxiety at 5/10. Homework assigned includes: daily breathing practice, journaling about negative predictions and actual outcomes, and one practice run of the presentation.

---
*Session duration: approximately 28 minutes*
