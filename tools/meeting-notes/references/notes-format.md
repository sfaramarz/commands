# Meeting Notes Format Specification

## File Structure

Every meeting notes file follows this exact structure:

```markdown
---
title: "Meeting Notes: <Meeting Subject>"
date: YYYY-MM-DD
time: HH:MM - HH:MM (timezone)
attendees:
  - Name 1
  - Name 2
type: meeting-notes
source: teams-transcript
---

# <Meeting Subject>

**Date:** YYYY-MM-DD | **Time:** HH:MM - HH:MM
**Attendees:** Name 1, Name 2, Name 3

---

## Summary

A 3-5 sentence executive summary of the meeting. What was discussed, what was decided, and what the next steps are.

---

## Discussion

### <Topic 1 Heading>

Detailed notes on the first major topic discussed. Include:
- Key points raised by each speaker
- Data, metrics, or figures referenced
- Context and background provided
- Concerns or risks identified

### <Topic 2 Heading>

Continue with each major topic as its own subsection.

---

## Decisions

- **Decision 1** — Brief description of what was decided and by whom
- **Decision 2** — ...

If no explicit decisions were made, omit this section.

---

## Action Items

| # | Action | Owner | Due Date |
|---|--------|-------|----------|
| 1 | Description of task | Person Name | Date or TBD |
| 2 | Description of task | Person Name | Date or TBD |

If no action items, omit this section.

---

## Open Questions

- Question or unresolved topic that needs follow-up
- ...

If none, omit this section.

---

## Key Data Points

Bullet list of any specific metrics, build numbers, test results, bug IDs, or other quantitative information referenced during the meeting. Include enough context for each to be useful standalone.

If none, omit this section.

---

## Next Meeting

Date/time of the next occurrence if mentioned, or "TBD".
```

## Formatting Rules

1. **Headings** — Use `##` for top-level sections, `###` for discussion sub-topics. Never use `#` except for the document title.
2. **Speaker attribution** — In the Discussion section, attribute points to speakers naturally (e.g., "Nyle raised concerns about...") rather than using transcript-style `[Speaker]:` format.
3. **Timestamps** — Do not include transcript timestamps in the output.
4. **Quotes** — Use blockquotes (`>`) only for critical verbatim statements that must be preserved exactly.
5. **Links** — Preserve any URLs, bug IDs (as `https://nvbugspro.nvidia.com/bug/<id>`), or Jira tickets (as `https://jirasw.nvidia.com/browse/<KEY>`) mentioned in the meeting.
6. **Tables** — Use tables only for Action Items and structured data comparisons.
7. **Length** — Be thorough. A 30-minute meeting should produce 300-600 words of notes. A 60-minute meeting should produce 500-1200 words. Do not pad, but do not under-document.

## Topic Extraction Guidelines

- Group related discussion into coherent topics even if the conversation jumped around
- Name topics descriptively (e.g., "PBR Test Results for FV 1.8" not "Testing")
- If a topic was brief (< 1 minute of discussion), fold it into a related topic or list it as a bullet under a "Brief Updates" heading
- Order topics by importance/time spent, not chronologically, unless chronological order is more logical
