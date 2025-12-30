# Development Guidelines

## Git Workflow Rules

### ⚠️ CRITICAL: Never Commit Untested Code

**Rule**: Do NOT create git commits until changes have been tested and verified working.

**Workflow**:
1. Make code changes
2. **TEST the changes** (run the app, verify functionality)
3. User confirms changes work correctly
4. **THEN** commit with descriptive message

**Why**: Committing untested code can introduce bugs into the codebase and makes it harder to identify when issues were introduced.

**Exception**: Only commit untested code if explicitly requested by the user (e.g., "commit this now, I'll test later").

---

## Testing Before Commits

Before committing any changes, ensure:

- [ ] Backend changes: Server starts without errors
- [ ] Frontend changes: App loads and functions work
- [ ] Integration changes: End-to-end flow tested
- [ ] User has confirmed the fix works as expected

---

## Commit Message Format

Use descriptive commit messages following this format:

```
Brief summary of change (imperative mood)

Detailed explanation:
- What was the problem?
- What was the solution?
- Why was this approach chosen?

Testing: [Brief description of how it was tested]

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

---

## Code Review Checklist

Before marking work as "complete":

- [ ] Code tested locally
- [ ] User confirmed functionality
- [ ] No console errors
- [ ] Changes committed with clear message
- [ ] Ready for deployment
