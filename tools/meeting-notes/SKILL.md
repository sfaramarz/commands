---
name: meeting-notes
description: Generate detailed meeting notes from a Teams meeting transcript. Asks the user which meeting they want notes for, finds it on their calendar, pulls the transcript via transcript-cli, and saves a formatted Markdown file to the Archivist import folder. Use when asked for meeting notes, meeting summary, transcript notes, or to document a meeting.
---

# Meeting Notes Generator

Pull a Teams meeting transcript and produce detailed, structured Markdown meeting notes.

**Output location:** Resolved at runtime (see Step 0)
**Filename:** `YYYY-MM-DD meeting-notes <meeting subject>.md`

See [references/notes-format.md](references/notes-format.md) for the full output format specification.
See [references/transcript-cli.md](references/transcript-cli.md) for transcript-cli usage patterns.

---

## Prerequisites

This skill requires the following to be installed and configured:

| Requirement | What | How to verify |
|-------------|------|---------------|
| **ai-pim-utils** | Provides `transcript-cli` and Outlook MCP server | `transcript-cli --version` |
| **Outlook MCP server** | Calendar event lookup via `mcp__outlook__outlook_list_calendar_view` | Must be configured in Claude Code MCP settings |
| **Azure AD auth** | Shared token for transcript-cli / outlook-cli / calendar-cli | `transcript-cli auth status` or run any command to trigger device code flow |
| **Teams transcription** | Meetings must have transcription enabled (organizer or tenant setting) | User must be an attendee of the meeting |
| **Output folder** | A writable directory for saving meeting notes | Set via `MEETING_NOTES_OUTPUT_DIR` env var, or auto-detected from OneDrive |

---

## Step 0 — Preflight checks

### 0a. Verify transcript-cli

```bash
transcript-cli --version
```

If not found, tell the user to install ai-pim-utils: `pip install ai-pim-utils`

### 0b. Verify authentication

```bash
transcript-cli auth status 2>&1 || transcript-cli health 2>&1
```

If auth fails, tell the user to run `! transcript-cli auth login` to authenticate.

### 0c. Resolve output folder

Determine the output directory using this priority order:

1. **`MEETING_NOTES_OUTPUT_DIR` environment variable** — use if set
2. **OneDrive auto-detection** — scan for `~/OneDrive*/Documents/Work Documents/vault/import/` or `~/OneDrive*/Documents/vault/import/`
3. **Fallback** — `~/Documents/meeting-notes/`

Verify the resolved path exists. If it does not, create it. Store the resolved path for Step 4.

---

## Step 1 — Identify the meeting

Ask the user (via `AskUserQuestion`) which meeting they want notes for. Accept any of:
- A meeting name or keyword (e.g. "FrameView sync", "1:1 with Tion")
- A specific date (e.g. "last Tuesday", "March 25")
- Both (e.g. "DLSS Production Meeting on Monday")

If the user provided the meeting name in their initial message, skip this step.

---

## Step 2 — Find the calendar event

Use `mcp__outlook__outlook_list_calendar_view` to search the user's calendar:

1. Determine the date range — if user gave a specific date, search that day. Otherwise search the last 7 days.
2. Filter results by subject match against the user's query.
3. If multiple matches, present a numbered list and ask the user to pick one.
4. If no matches, widen the search to 14 days and retry. If still none, report and stop.

Extract the **event ID** from the matched event.

---

## Step 3 — Pull the transcript

Use `transcript-cli` to retrieve the meeting transcript:

```bash
transcript-cli find --event-id "<EVENT_ID>" --json
```

If transcripts are found, read the most recent one:

```bash
transcript-cli read --event-id "<EVENT_ID>" --json
```

**Error handling:**
- If `find` returns `count: 0` — inform the user that no transcript exists for this meeting. Ask if they'd like to try a different meeting.
- If authentication fails (exit code 2) — tell the user to run `! transcript-cli auth login` to re-authenticate.
- If rate limited (exit code 5) — wait the indicated retry period and retry once.

---

## Step 4 — Generate meeting notes

Parse the transcript content and produce structured meeting notes following [references/notes-format.md](references/notes-format.md).

**Guidelines:**
- Identify all speakers from the transcript
- Extract key discussion topics and organize into logical sections
- Capture all action items with assignees when mentioned
- Capture decisions made during the meeting
- Note any deadlines, dates, or milestones mentioned
- Include relevant data points, metrics, or figures discussed
- Preserve technical details accurately — do not generalize
- Use direct quotes sparingly, only for critical statements
- Flag open questions or unresolved items

---

## Step 5 — Save the file

Write the Markdown file to the output folder resolved in Step 0c:

```
<OUTPUT_DIR>/YYYY-MM-DD meeting-notes <meeting subject>.md
```

Where:
- `<OUTPUT_DIR>` is the path resolved in Step 0c
- `YYYY-MM-DD` is the meeting date
- `<meeting subject>` is the calendar event subject, lowercased, spaces preserved, special characters removed

After saving, report the file path and a brief summary (3-5 bullet points) of the key takeaways.

---

## Step 6 — Offer follow-up

Ask if the user would like to:
1. Run `/tools:archivist` to file the notes into the vault
2. Pull notes for another meeting

---

## Example Invocations

> `/tools:meeting-notes`
> "Which meeting would you like notes for?"

> "meeting notes for the FrameView sync last Tuesday"
> Finds the event, pulls transcript, generates notes, saves to import folder.

> "document yesterday's DLSS Production Meeting"
> Same flow — finds yesterday's DLSS meeting, pulls transcript, writes notes.
