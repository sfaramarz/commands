# Meeting Notes Skill — User Guide

## What it does

The meeting-notes skill turns a Microsoft Teams meeting transcript into structured Markdown notes. You provide a meeting name or date, and it handles the rest — finding the event, pulling the transcript, and generating organized notes saved to your vault.

## Prerequisites

Before first use, verify you have the following:

### 1. Install ai-pim-utils

```bash
pip install ai-pim-utils
```

This provides `transcript-cli`, which pulls Teams transcripts via the Microsoft Graph API.

Verify: `transcript-cli --version`

### 2. Authenticate with Azure AD

All Graph-based CLIs (transcript-cli, outlook-cli, calendar-cli) share a single Azure AD token. Authenticate once:

```bash
transcript-cli auth login
```

This opens a browser for device code flow. After completing sign-in, the token is cached and shared across all Graph CLIs.

Verify: `transcript-cli auth status`

### 3. Configure the Outlook MCP server

The skill uses `mcp__outlook__outlook_list_calendar_view` to search your calendar. This requires the Outlook MCP server in your Claude Code settings.

If you installed ai-pim-utils, the MCP server is already available — just ensure it's listed in your Claude Code MCP configuration.

### 4. Ensure Teams transcription is enabled

Transcripts are only available for meetings where transcription was turned on (either by the organizer or via tenant policy). You must also be an attendee of the meeting.

### 5. Set your output folder (optional)

By default, the skill auto-detects your OneDrive vault import folder:

```
~/OneDrive*/Documents/Work Documents/vault/import/
~/OneDrive*/Documents/vault/import/
```

To override, set the environment variable:

```bash
export MEETING_NOTES_OUTPUT_DIR="/path/to/your/folder"
```

If neither is found, notes are saved to `~/Documents/meeting-notes/`.

---

## How to use

### Invoke the skill

```
/tools:meeting-notes
```

Or just describe what you want in natural language:

- "meeting notes for the FrameView sync last Tuesday"
- "document yesterday's DLSS Production Meeting"
- "pull notes from my 1:1 with Tion on March 24"

### What happens next

1. **Asks which meeting** — If you didn't specify, it presents recent calendar events to choose from
2. **Searches your calendar** — Finds the event by subject match within the last 7 days (or specific date you gave)
3. **Pulls the transcript** — Uses `transcript-cli` to retrieve the Teams transcript for that event
4. **Generates notes** — Produces structured Markdown with:
   - Summary (3-5 sentence overview)
   - Discussion (topics grouped by importance, attributed to speakers)
   - Decisions made
   - Action items (table with owner and due date)
   - Open questions
   - Key data points (metrics, build numbers, dates)
   - Next meeting info
5. **Saves the file** — Writes to your output folder as `YYYY-MM-DD meeting-notes <subject>.md`
6. **Offers follow-up** — Option to file via `/tools:archivist` or pull notes for another meeting

---

## Output format

The generated file looks like this:

```markdown
---
title: "Meeting Notes: Weekly Sync"
date: 2026-03-25
time: "14:00 - 14:45 PST"
attendees:
  - Alice
  - Bob
type: meeting-notes
source: teams-transcript
---

# Weekly Sync

**Date:** 2026-03-25 | **Time:** 14:00 - 14:45 PST
**Attendees:** Alice, Bob

---

## Summary
...

## Discussion
### Topic 1
...

## Decisions
- **Decision** — description

## Action Items
| # | Action | Owner | Due Date |
|---|--------|-------|----------|
| 1 | Do the thing | Alice | 2026-03-28 |

## Open Questions
- Unresolved item

## Key Data Points
- Build 820.5 showed 8.5% regression
```

---

## Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| "transcript-cli not found" | ai-pim-utils not installed | `pip install ai-pim-utils` |
| "Authentication failed" (exit code 2) | Token expired or never set | Run `transcript-cli auth login` |
| "No transcript found" (count: 0) | Transcription wasn't enabled for the meeting | No fix — transcript must exist. Try a different meeting. |
| "Permission denied" (exit code 6) | You weren't an attendee | You can only access transcripts for meetings you attended |
| "Rate limited" (exit code 5) | Too many Graph API requests | Wait a few seconds and retry |
| No calendar events found | Wrong date range or meeting name | Try a broader search term or different date |
| Output folder not found | OneDrive not synced or env var not set | Set `MEETING_NOTES_OUTPUT_DIR` explicitly |

---

## Integration with Archivist

After saving, the skill offers to run `/tools:archivist` which will:
1. Detect the file as type "Meeting Notes"
2. Classify it by topic
3. Move it from `vault/import/` to `vault/sources/meeting-notes/<topic>/`
4. Update index files
