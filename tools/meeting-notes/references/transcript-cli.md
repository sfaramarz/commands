# transcript-cli Usage Reference

## Overview

`transcript-cli` retrieves Microsoft Teams meeting transcripts via the Microsoft Graph Online Meeting API. Authentication is shared with `outlook-cli` and `calendar-cli` (Azure AD device code flow).

Binary location: `C:\Users\sfaramarz\AppData\Local\ai-pim-utils\bin\transcript-cli`

## Commands

### find — Locate transcripts for a meeting

Requires either `--event-id` (calendar event ID) or `--join-url` (Teams join link).

```bash
# From a calendar event ID (preferred workflow)
transcript-cli find --event-id "<EVENT_ID>" --json

# From a Teams join URL
transcript-cli find --join-url "https://teams.microsoft.com/l/meetup-join/..." --json
```

**JSON response (success):**
```json
{
  "success": true,
  "data": [
    {
      "id": "<transcript-id>",
      "meetingId": "<meeting-id>",
      "createdDateTime": "2026-03-25T03:30:12Z",
      "endDateTime": "2026-03-25T04:27:43Z"
    }
  ]
}
```

**No transcripts:**
```json
{
  "success": true,
  "data": null
}
```

### read — Retrieve transcript content

Two methods — prefer Method 1 (simpler):

```bash
# Method 1: From calendar event ID (reads most recent transcript)
transcript-cli read --event-id "<EVENT_ID>" --json

# Method 1 with specific transcript index (0 = most recent)
transcript-cli read --event-id "<EVENT_ID>" --transcript-index 1 --json

# Method 2: Direct IDs (from find output)
transcript-cli read --meeting-id "<MEETING_ID>" --transcript-id "<TRANSCRIPT_ID>" --json
```

**Human-readable output (no --json):**
```
[00:00:10] Speaker Name: Hello everyone.
[00:00:15] Other Speaker: Hi, let's get started.
```

**JSON output:**
```json
{
  "success": true,
  "data": {
    "meetingId": "...",
    "transcriptId": "...",
    "content": "[00:00:10] Speaker Name: Hello everyone.\n..."
  }
}
```

### insights — AI-generated meeting recap (Teams Copilot)

```bash
transcript-cli insights --event-id "<EVENT_ID>" --json
```

Returns Teams Recap data: notes, action items, mentions. Only available if the meeting organizer has Teams Premium/Copilot.

## Exit Codes

| Code | Meaning | Action |
|------|---------|--------|
| 0 | Success | Continue |
| 2 | Auth failed | User must run `! transcript-cli auth login` |
| 3 | Not found | No transcript exists for this meeting |
| 4 | Validation error | Check parameters |
| 5 | Rate limited | Wait `retry_after_seconds`, retry once |
| 6 | Permission denied | User doesn't have access to this meeting's transcript |

## Output Size Considerations

Transcripts for long meetings can be very large (50-100KB+). When reading via `--json`, the content field contains the full parsed transcript. For meetings over 60 minutes, consider:
- Reading without `--json` flag and piping to a temp file
- Using the human-readable format which is already parsed with speaker labels and timestamps

## Workflow: Calendar Event ID to Transcript

1. Get event ID from `mcp__outlook__outlook_list_calendar_view`
2. `transcript-cli find --event-id <id> --json` to check if transcripts exist
3. `transcript-cli read --event-id <id>` to get the content
