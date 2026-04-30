# Document Classification Reference

Detailed criteria for classifying imported documents into the correct source type.

## Classification Decision Tree

```
1. Is filename pattern slack_*.md with `# Slack Thread Results` header?
   → YES: Slack Transcript (special handling)
   → NO: Continue

2. Is file extension .eml?
   → YES: Email
   → NO: Continue

3. Is file HTML with email headers?
   (Look for: <h1>Subject:, From:, To:, Received: at top)
   → YES: Email
   → NO: Continue

4. Is file DOCX or MD with dialogue patterns?
   (Look for: **Speaker Name** timestamp, or "Name HH:MM")
   → YES: Likely Meeting content
   → Continue to step 5

5. Does meeting content have raw dialogue with timestamps throughout?
   (Pattern: speaker names followed by timestamps, conversational flow)
   → YES: Meeting Transcript
   → NO: Continue to step 6

6. Does meeting content have structured sections with action-item format?
   (Look for: ## Action Items, ## Key Discussion Items with insights/decisions format)
   → YES: Meeting Summary
   → NO: Continue to step 7

7. Is content structured meeting notes without transcript or summary format?
   (Look for: Problems/Analysis/Actions sections, numbered lists, human-authored observations)
   → YES: Meeting Notes
   → NO: Continue

8. Default: Reference Document
```

## Slack Transcript Detection

### Primary Indicators (must match)

1. **Filename pattern**: `slack_*_YYYYMMDD_HHMMSS.md`
   - Example: `slack_results_20260218_030052.md`

2. **File header**: `# Slack Thread Results`

3. **Export details section** with `**Channel:**` field

4. **Thread structure**: Numbered sections `## N. Thread Title` with metadata fields

### File Structure

```markdown
# Slack Thread Results

## Export details

- **Export date:** YYYY-MM-DD HH:MM:SS
- **Query:** ```query parameters```
- **Channel:** channel-name

---

## 1. Thread Title

**Author:** username
**Date:** YYYY-MM-DD HH:MM
**Summary:** Brief description of the thread
**Resolved:** yes/no/not an issue
**Reactions (N):** :emoji: count, :emoji: count
**Link:** [url](url)

### Full Thread

\`\`\`
YYYY-MM-DD HH:MM:SS username: message content
Reply YYYY-MM-DD HH:MM:SS username: reply content
\`\`\`

---

## 2. Next Thread Title
...
```

### Key Characteristics

- Multiple threads in a single file (can be hundreds)
- Each thread separated by `---` horizontal rule
- Channel name in `## Export details` metadata section, not in filename
- Thread content in fenced code blocks
- Metadata includes author, date, summary, resolved status, reactions, and Slack link

### Processing

Slack transcripts require special handling:
1. Extract channel name from `**Channel:**` field in export details
2. Run Python splitter script to separate into individual thread files
3. Output to `vault/sources/slack/[channel-name]/thread-YYYY-MM-DD.md`

See the splitter script at `.claude/skills/archivist/scripts/split_slack_threads.py`

---

## Email Detection

### Primary Indicators (any one = email)

1. **File extension**: `.eml`

2. **HTML email header block** at document start:
   ```html
   <h1>Subject: [text]</h1>
   From: [email] <br/>
   To: [email] <br/>
   ...
   Received: [timestamp] <br/>
   ```

3. **RFC 822 headers** (for .eml files):
   ```
   From: sender@domain.com
   To: recipient@domain.com
   Subject: Email subject line
   Date: Mon, 27 Jan 2026 10:00:00 -0800
   ```

### Secondary Indicators

- Reply/forward thread markers (`From:`, `Sent:`, `To:`, `Subject:` in body)
- Email signatures with contact info
- Disclaimer footers
- "RE:", "FW:", "Re:", "Fwd:" in subject/filename
- Outlook-specific HTML patterns (WordSection1, MsoNormal)

### Filename Patterns

Common email export patterns:
- `Re_ Subject Line-2026-01-26T20_10_51+00_00.html` (Outlook export)
- `Subject Line.eml`
- `FW_ Topic Discussion.html`

## Meeting Transcript Detection

### Primary Indicators

1. **Speaker + timestamp pattern** repeated throughout:
   ```
   **Speaker Name** 1:23
   What they said...

   **Another Speaker** 1:45
   Their response...
   ```

2. **Timestamp-only lines** (auto-transcription artifact):
   ```
   0:22
   Hello.

   **Simona Vilutiene** 0:26
   Oh, hi.
   ```

3. **Continuous dialogue flow** - conversational back-and-forth

### Secondary Indicators

- File from Teams/Zoom/Meet (often .docx or .vtt)
- Filename contains meeting name or "transcript"
- Multiple distinct speakers
- Timestamps increment chronologically
- Informal speech patterns, interruptions, filler words

### Distinguishing from Summary

Transcripts have:
- Raw dialogue (word-for-word speech)
- Many timestamps throughout
- Conversational tone with informal language
- Speaker turns every few sentences
- No structured sections like "Action Items"

Summaries have:
- Structured markdown sections
- Bullet points and organized content
- No timestamps in body
- Formal, edited language
- Clear "Action Items" or "Discussion Items" sections
- Specific format: numbered discussion items with **Key Insights** and **Decisions** sub-sections

## Meeting Summary Detection

### Primary Indicators

1. **Structured sections** with headers:
   ```markdown
   ## Action Items
   1. Task description - **Owner: Name**

   ## Key Discussion Items
   1. **Topic Name**
      - **Key Insights:**
      - **Decisions:**
   ```

2. **No raw timestamps** in content body

3. **Edited, formal language** - not verbatim speech

### Secondary Indicators

- Filename contains "summary"
- Clear hierarchy (H2, bullet lists)
- Owner assignments for action items
- No speaker attribution on individual lines
- Content is analysis/synthesis, not transcription

## Meeting Notes Detection

### Primary Indicators

1. **Human-authored structure** without standard summary format:
   ```markdown
   # Problems:
   1. Issue description
      1. Follow-up or sub-point

   # Analysis:
   * Observation about the problem
     * Supporting detail

   # Actions:
   * Specific action to take
   ```

2. **Problem/Analysis/Action pattern** or similar human synthesis structures

3. **Personal observations and judgments** - direct human voice, not synthesized

### Secondary Indicators

- Filename contains "notes"
- Uses numbered lists with nested sub-points
- Mix of markdown styles (headers, bullets, numbered lists)
- Contains specific names, dates, decisions in context
- No **Key Insights**/**Decisions** sub-section pattern (differentiates from summary)
- No speaker timestamps (differentiates from transcript)

### Distinguishing Notes from Summaries

**Meeting Notes** are:
- Human-authored during or after a meeting
- Informal structure decided by the author
- May focus on specific aspects (e.g., just problems and actions)
- Personal observations and conclusions
- Variable formatting

**Meeting Summaries** are:
- Generated from transcripts using the `/meeting-summary` skill
- Standardized format with Action Items + Key Discussion Items
- Each discussion item has **Key Insights** and **Decisions** sub-sections
- Comprehensive coverage of all meeting topics
- Consistent formatting

### Notes Examples

**Post-mortem notes:**
```markdown
# 1.3 Post-Mortem

# Problems:
1. Churn from pivoting away from the graph
   1. In future don't pivot towards risky things
2. Scope of QA work was too much

# Analysis:
* Tickets marked as "done" skip QA
* We didn't communicate bugs soon enough

# Actions:
* Communicate more clearly about verification process
* Nyle try to "persuade" NVApp to change the model
```

**Meeting notes:**
```markdown
# Team Sync Notes

Key takeaways:
- Launch delayed to next week
- Budget approved for Q2

Open questions:
1. Who owns the API migration?
2. Timeline for security review?

My observations:
- Team seems stretched thin
- Need to follow up on hiring
```

## Reference Document Detection

### Default Category

If document doesn't match email, transcript, or summary patterns, classify as reference.

### Common Reference Types

1. **Process documentation**
   - How-to guides
   - Standard operating procedures
   - Checklists and templates

2. **Specifications**
   - Technical specs
   - Requirements documents
   - Design documents

3. **Informational content**
   - Glossaries, concept guides
   - Policy documents
   - Training materials

4. **External documents**
   - Vendor documentation
   - Industry reports
   - Shared reference materials

### Filename Indicators

- Descriptive names without dates: `nvidia-values.md`
- Topic-focused: `game-ready-checklist.docx`
- Version indicators: `process-guide-v2.pdf`

## Handling Ambiguous Cases

### When Multiple Types Seem Possible

1. **Email with meeting notes attached**
   - Classify as email
   - Note: meeting content may need separate extraction

2. **Transcript that's been partially cleaned**
   - If timestamps remain: transcript
   - If fully restructured: summary

3. **Meeting notes that aren't a summary**
   - Has some structure but not full summary format
   - If dialogue-focused with timestamps: transcript
   - If structured with **Key Insights**/**Decisions** pattern: summary
   - If human-authored observations (problems/analysis/actions): notes
   - If general documentation not tied to a specific meeting: reference

### When Type is Truly Unclear

Use sub-agent for deeper analysis:
1. Read full document content
2. Count patterns (timestamps, speakers, sections, headers)
3. Analyze language style (formal vs. conversational)
4. Make determination or escalate to user

### Escalation Criteria

Ask user when:
- Document has mixed characteristics (e.g., email containing meeting notes)
- Content is in unexpected format
- Classification confidence is below 50%
- Document appears corrupted or incomplete

## Content Extraction Guidelines by Type

### Emails

**Keep:**
- Subject line
- From/To/Date metadata
- Body text content
- Thread history (preserve context)

**Remove:**
- HTML styling and CSS
- Tracking pixels
- Elaborate signatures
- Legal disclaimers (unless substantive)
- Duplicate thread quotes (keep most recent complete version)

### Transcripts

**Keep:**
- Speaker names
- Timestamps (normalized format)
- Full dialogue
- Date/time of meeting

**Remove:**
- Filler words if excessive (`um`, `uh`, `like`)
- Transcription artifacts (`[inaudible]`, `[crosstalk]`)
- Auto-generated headers/footers
- Redundant timestamps (keep one per speaker turn)

### Summaries

**Keep:**
- All structured content
- Action items and owners
- Discussion points and decisions
- Date and meeting identifier

**Remove:**
- Source references or citations
- Formatting artifacts
- Auto-generated metadata

### Meeting Notes

**Keep:**
- All substantive observations and analysis
- Problems, issues, and concerns identified
- Actions and recommendations
- Names, dates, and specific details
- Personal judgments and conclusions
- Original structure and formatting

**Remove:**
- Excessive formatting artifacts
- Redundant whitespace
- Auto-generated headers/footers

**Note:** Meeting notes are human-authored, so preserve the author's original structure and voice.

### References

**Keep:**
- All substantive content
- Document structure
- Any metadata (author, date, version)

**Remove:**
- Excessive formatting
- Navigation elements
- Print artifacts
