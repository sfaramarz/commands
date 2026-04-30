---
name: archivist
description: Manage vault/sources structure, ingest files from import/ folder with automatic type detection, markdown conversion, and smart filing. Use when importing emails, meeting transcripts, meeting notes, Slack thread exports, or reference documents into the vault. Also use for vault maintenance tasks like reindexing, structure verification, or source organization.
---

# Archivist

Process files in `import/` and file them into `vault/sources/`.

## Ask Mode

When invoked as `/archivist ask <question>`, answer the question using vault sources.

### Procedure

1. **Run hybrid retrieval with embeddings:**

```bash
.venv/bin/python3 .claude/skills/doc-research/scripts/doc-retrieve.py --query "<question>" --dir vault/sources/ --top-k 10 --embed --verbose
```

2. **Read the top results.** Read the full content of the top 5-7 ranked documents (adjust based on size — aim for comprehensive coverage without exceeding useful context).

3. **Synthesize a direct answer** to the question using the retrieved content:
   - Lead with the answer, not the process
   - Cite sources inline: `(source: path/to/file.md)`
   - Use exact quotes for specific facts (dates, names, numbers, decisions)
   - Note confidence level — flag if sources are thin or contradictory
   - If the vault doesn't contain a clear answer, say so and suggest what sources might help

### Output Format

Respond directly in conversation:

```
**[concise answer]**

[supporting details with inline citations]

---
*Sources: N documents from vault/sources/*
```

### Embedding Fallback Handling

After parsing the JSON output, check the `warnings` array and `scorers` list. If `--embed` was requested but `"embed"` is not in `scorers`, alert the user:

> **Note:** Dense retrieval (embeddings) was not available for this query — results use BM25+TF-IDF only, which may be less accurate.
>
> _Reason: {warning message from warnings array}_

Then provide the applicable fix:

| Warning contains | Fix |
|---|---|
| `not installed` | `cd {repo_root} && .venv/bin/pip install -r requirements.txt` |
| `not set` | Set the `NVIDIA_API_KEY` environment variable |
| other | Show the full warning text |

### Notes

- First run against a directory with embeddings enabled embeds all documents (slow); subsequent runs use cache
---

**References:**
- [Vault structure and conventions](references/STRUCTURE.md)
- [Document classification criteria](references/CLASSIFICATION.md)
- [Topic matching and filing rules](references/FILING.md)

## Sub-Agent Delegation

Delegate token-intensive operations to sub-agents (`subagent_type: "general-purpose"`). Sub-agents have no conversation context - always provide full file paths and complete instructions.

| Operation | Trigger |
|-----------|---------|
| Transcript cleanup | Any meeting transcript |
| Summary generation | After transcript ingestion |
| Long email conversion | Email >50KB or >5 messages |
| Deep type classification | Type unclear after initial inspection |
| Deep topic matching | No strong match (>80%) found |

## Pipeline

### Step 1: Scan Import Folder

List files in `import/` (exclude `.DS_Store`, hidden files). Exit if empty.

### Step 2: Process Each File

#### 2a. Detect Document Type

Inspect the file to classify it. See [CLASSIFICATION.md](references/CLASSIFICATION.md) for the full decision tree.

| Type | Key Indicators |
|------|---------------|
| Email | HTML email headers, `.eml` extension |
| Meeting Transcript | Timestamps + speaker names throughout, dialogue format |
| Meeting Summary | Structured sections (Action Items, Discussion), no raw dialogue |
| Meeting Notes | Human-authored observations, problems/analysis/actions |
| Slack Transcript | Filename `slack_*.md`, `# Slack Thread Results` header, `**Channel:**` in export details |
| Reference | Default for other content |

If unclear after inspection, delegate classification to sub-agent with the file path and type options. If sub-agent returns low confidence, ask user.

#### 2a-transcript. Teams DOCX Transcripts (Special Handling)

Teams DOCX transcripts use the Python cleanup script directly:

```bash
.venv/bin/python3 .claude/skills/archivist/scripts/clean_teams_transcript.py "<input.docx>" "<output.md>"
```

The script runs pandoc and performs deterministic cleanup: extracts metadata (title, date, duration, participants), parses speaker turns, unescapes pandoc artifacts, joins continuation lines, merges consecutive same-speaker turns, and skips start/stop transcription markers.

No sub-agent needed for cleanup. After the script runs, continue with step 2e (determine destination) to file the output. Summary generation (step 2h) still delegates to sub-agent.

#### 2a-slack. Slack Transcripts (Special Handling)

Slack files contain multiple threads requiring the Python splitter:

```bash
.venv/bin/python3 .claude/skills/archivist/scripts/split_slack_threads.py "<input>" "<output-dir>"
```

- Input: Slack file from `import/`
- Output dir: `vault/sources/slack/[channel-name]/`
- Channel extracted from `**Channel:**` field in the file's export details metadata

The script handles incremental imports automatically:
- New threads: created
- Threads with new replies: updated (same filename preserved)
- Identical threads: skipped

After the script runs, update index files and skip remaining pipeline steps for this file.

#### 2b. Convert to Markdown

| Format | Approach |
|--------|----------|
| HTML email (<50KB) | Extract headers, strip HTML/CSS, preserve thread structure |
| HTML email (>50KB or >5 messages) | Delegate to sub-agent |
| DOCX | `pandoc -f docx -t markdown --wrap=none` then clean artifacts |
| Other | Minimal cleanup |

#### 2c. Clean and Normalize

- **Teams DOCX transcripts**: Use the cleanup script (step 2a-transcript). No sub-agent needed.
- **Other transcripts**: Delegate to sub-agent. Remove filler words, transcription artifacts, redundant timestamps. Preserve speaker names, one timestamp per turn, full dialogue.
- **Other types**: Clean directly - remove boilerplate, formatting artifacts, tracking links. Preserve content, dates, names.

#### 2d. Extract Date

| Type | Source |
|------|--------|
| Email | `Received:` header |
| Transcript | Filename or first timestamp |
| Summary | Filename or content |
| Reference | File modification date |

Format: `YYYY-MM-DD`

#### 2e. Determine Destination

See [FILING.md](references/FILING.md) for detailed matching rules and examples.

Map type to folder, then match to existing topic subfolder:
- **>80% confidence**: file directly
- **50-80%**: verify with content check
- **<50%**: delegate deep matching to sub-agent

If no match, propose new kebab-case folder name and confirm with user.

| Type | Destination |
|------|-------------|
| Email | `vault/sources/emails/[topic]/` |
| Transcript / Summary / Notes | `vault/sources/meetings/[topic]/` |
| Slack | `vault/sources/slack/[channel]/` (script-handled) |
| Reference | `vault/sources/references/[topic]/` |
| Strategic Note | `vault/sources/notes/[topic]/` |
| Jira Issues | `vault/sources/jira/[project-key]/` (**not archivist-managed** — use `/jira-dump`) |

#### 2f. Check for Duplicates

Generate target filename, check if exists, compare content:
- >90% similar: skip as duplicate
- Different content: use conflict resolution (see [FILING.md](references/FILING.md))

#### 2g. Write Output

See [FILING.md](references/FILING.md) for filename patterns and conflict resolution.

| Type | Pattern |
|------|---------|
| Email | `[subject-slug]-YYYY-MM-DD.md` |
| Transcript | `transcript-YYYY-MM-DD.md` |
| Summary | `summary-YYYY-MM-DD.md` |
| Notes | `notes-YYYY-MM-DD.md` |
| Slack Thread | `thread-YYYY-MM-DD.md` |
| Reference | `[descriptive-name].md` |

Create folder if needed, write file.

#### 2h. Generate Summary for Transcripts

For meeting transcripts only (not notes): delegate summary generation to sub-agent using the `/meeting-summary` skill. Output `summary-YYYY-MM-DD.md` in the same topic folder.

#### 2i. Update Index Files

1. Update topic `_index.md` with new file entry
2. Update type `_index.md` with counts/dates
3. If new topic: create `[topic]/_index.md`, update `vault/sources/_topics.md`

See [STRUCTURE.md](references/STRUCTURE.md) for index file format.

### Step 3: Clean Up Import and Report Results

After all files are processed, clean up successfully-processed files from `import/` using the cleanup script:

```bash
.venv/bin/python3 .claude/skills/archivist/scripts/clean_import.py \
    --import-dir import/ \
    --processed "file1.md" "file2.docx" "file3.html"
```

Pass only the **filenames** (not paths) of files that were successfully processed (written to vault). Do NOT include:
- Files that were skipped as duplicates
- Files that failed processing
- Files that were not processed (e.g., temp files like `~$...`)

The script verifies each file exists in `import/` before removing and reports results as JSON.

Then report to the user:

```
## Ingestion Complete

### Processed
- [filename] -> [output-path] (NEW)
- [filename] -> [output-path] (NEW, summary generated)

### Skipped
- [filename] - Duplicate of [existing]

### Cleaned from import/
- [N] files removed from import/

### New Folders
- vault/sources/[type]/[new-topic]/

### Indexes Updated
- [list of updated _index.md files]
```

## Error Handling

- **Conversion failure**: Log, skip, report in summary
- **Ambiguous type**: Sub-agent first, then ask user if still unclear
- **Topic uncertainty**: Propose folder name, confirm with user
- **Missing pandoc**: Report `brew install pandoc`

## Quality Checklist

- [ ] Document type correctly identified
- [ ] Clean, readable markdown
- [ ] Date extracted correctly
- [ ] Filed in topic folder (no root-level files)
- [ ] No duplicates created
- [ ] Transcript: summary generated
- [ ] Index files updated
