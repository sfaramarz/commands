# Filing Rules

Topic matching, filename generation, and conflict resolution for vault source ingestion.

## Destination Mapping

| Document Type | Destination |
|---------------|-------------|
| Email | `vault/sources/emails/[topic]/` |
| Meeting Transcript | `vault/sources/meetings/[topic]/` |
| Meeting Summary | `vault/sources/meetings/[topic]/` |
| Meeting Notes | `vault/sources/meetings/[topic]/` |
| Slack Thread | `vault/sources/slack/[channel]/` (script-handled) |
| Reference | `vault/sources/references/[topic]/` |
| Strategic Note | `vault/sources/notes/[topic]/` |
| Jira Issues | `vault/sources/jira/[project-key]/` (managed by `/jira-dump`) |
| Social Media Export | `vault/sources/social-media/[platform]/` (manually placed) |

All sources must go into a topic folder. No files at the type level.

**Note:** Jira issues are not imported via the archivist. They are managed exclusively by the `/jira-dump` skill.

**Note:** Social media exports are not imported via the archivist. They are manually placed from platform data exports.

## Topic Matching

### Scoring Approach

For each candidate subfolder in the target type, evaluate:
- **Filename keywords** - Does the import filename contain the topic name?
- **Subject/title match** - Does email subject or doc title relate to topic?
- **Content overlap** - Do key terms appear in both?
- **Participants** - For emails/meetings, do participants overlap?

### Confidence Actions

| Confidence | Action |
|------------|--------|
| >80% | File directly |
| 50-80% | Verify with quick content check of existing files |
| <50% | Delegate deep matching to sub-agent |

### Deep Matching Sub-Agent

When no strong match found, delegate to a `general-purpose` sub-agent:

```
Analyze the document at [full-path] for topic matching.

Document type: [type]
Document subject/title: [extracted subject or title]

Existing topic folders in vault/sources/[type]/:
[list of existing folders]

For each candidate folder:
1. Read the folder's _index.md for topic description
2. Sample 1-2 existing files to understand content patterns
3. Score match likelihood based on subject matter overlap

If a strong match exists (>80%), report matched folder and reasoning.
If no strong match, propose a new kebab-case folder name.
```

- Sub-agent finds strong match: use it
- Sub-agent proposes new folder: confirm with user before creating

### New Folder Naming

- Kebab-case: `game-ready-process`, `dpt-generative-tpm`
- Descriptive but concise
- Meeting series: use the meeting name
- Email threads: use the primary subject/project
- References: use the document topic

## Filename Generation

### Email Subject to Filename

1. Extract subject line
2. Remove prefixes: `Re:`, `RE:`, `Fwd:`, `FW:`, `Fw:`
3. Convert to kebab-case (lowercase, spaces/special chars to hyphens)
4. Trim to ~50 chars at word boundary
5. Append `-YYYY-MM-DD`

Example: "RE: Feedback on P1 Game GTM Process Update" becomes `feedback-on-p1-game-gtm-process-update-2026-01-26.md`

### Conflict Resolution

When a file with the same name exists in the destination:

1. **Add `-HHMM` timestamp** from the document:
   - Emails: `Received:` header time
   - Transcripts: first timestamp or meeting start time from filename
   - Summaries: corresponding transcript time or file modification time
   - Example: `transcript-2026-01-26-1423.md`

2. **Multiple at same time**: add `-1`, `-2`, etc.
   - Example: `transcript-2026-01-26-1423-1.md`

## Examples

### Email matching existing topic
```
Input: "Re_ Feedback on P1 Game GTM Process Update-2026-01-25.html"
Subject: "Re: Feedback on P1 Game GTM Process Update"
Existing folders: game-ready-process/, neural-materials-dogfooding/
Match: game-ready-process (high confidence - "Game" + "Process")
Slug: feedback-on-p1-game-gtm-process-update
Output: vault/sources/emails/game-ready-process/feedback-on-p1-game-gtm-process-update-2026-01-25.md
```

### Transcript for known meeting series
```
Input: "DPT Generative TPM 2026-01-28.docx"
Filename: "DPT Generative TPM"
Existing: dpt-generative-tpm/, rtx-prod-sync/
Match: dpt-generative-tpm (exact match)
Output: vault/sources/meetings/dpt-generative-tpm/transcript-2026-01-28.md
```

### Email requiring new topic
```
Input: "Re_ Neural Rendering Pipeline Discussion-2026-01-20.html"
Subject: "Re: Neural Rendering Pipeline Discussion"
Existing: game-ready-process/, neural-materials-dogfooding/
No strong match → create "neural-rendering-pipeline" (confirm with user)
Output: vault/sources/emails/neural-rendering-pipeline/neural-rendering-pipeline-discussion-2026-01-20.md
```
