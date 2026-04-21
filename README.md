# Claude Commands

A collection of Claude Code skills for LSS RTX Kit/Tools program management, document generation, and status reporting.

## Skills

### PLC Generators

Template-driven document and artifact generation for PLC (Product Life Cycle) workflows.

| Skill | Description |
|-------|-------------|
| [plc-doc-gen](plc-generators/plc-doc-gen/) | Create all three PLC documents (SPP, SRD, SADD) populated with content from source code, Jira, Confluence, Obsidian, and program materials — publishes all three as Confluence pages nested under a parent page |
| [tava-gen](plc-generators/tava-gen/) | Generate TAVA (Threat and Vulnerability Analysis) architecture diagrams and documents from a project's source code and documentation — outputs a Mermaid diagram and Word document ready for nSpect TAVA 3.0 upload |

### Report Generators

Workstream status reporting and stakeholder communication.

| Skill | Description |
|-------|-------------|
| [fv-report-gen](report-generators/fv-report-gen/) | Generate a weekly FrameView Tool/SDK status report by aggregating data from Outlook emails, NVBugs, Jira, Confluence, Obsidian, and Slack — saves a formatted Word document to the Desktop |
| [plc-top5-report-gen](report-generators/plc-top5-report-gen/) | Generate a "Top 5 Things" PLC status report for all LSS RTX Kit/Tools from the Jira PLC Dashboard and REL project — saves a formatted Word document to the Desktop |

### Tools

Utilities for document management and meeting workflows.

| Skill | Description |
|-------|-------------|
| [archivist](tools/archivist/) | Manage a vault/sources document store — ingest files from an import folder with automatic type detection, markdown conversion, classification, and filing |
| [meeting-notes](tools/meeting-notes/) | Pull a Teams meeting transcript and generate structured Markdown meeting notes — asks which meeting, finds the calendar event, reads the transcript via `transcript-cli`, and saves to the vault import folder |
| [skill-creator](tools/skill-creator/) | Guide for creating new skills — scaffolding, validation, and packaging |

## Usage

Skills are loaded automatically from this directory by Claude Code. Invoke by name:

- `/plc-generators:plc-doc-gen` — create all three PLC documents (SPP, SRD, SADD) nested under a parent Confluence page
- `/plc-generators:tava-gen` — generate TAVA architecture diagram and document for nSpect
- `/report-generators:fv-report-gen` — generate a FrameView weekly status report
- `/report-generators:plc-top5-report-gen` — generate a PLC Top 5 report for all LSS RTX programs
- `/tools:archivist` — ingest and file documents into the vault
- `/tools:meeting-notes` — generate meeting notes from a Teams transcript
- `/tools:skill-creator` — create a new skill

## Guides

### Meeting Notes Skill

The meeting-notes skill turns a Teams transcript into structured Markdown notes. Provide a meeting name or date and it handles the rest.

**Prerequisites:**
- `pip install ai-pim-utils` — provides `transcript-cli` for pulling Teams transcripts
- Run `transcript-cli auth login` once to authenticate via Azure AD device code flow (token is cached and shared across all Graph CLIs)
- Outlook MCP server must be configured in Claude Code
- Transcription must be enabled for the meeting (organizer or tenant setting) and you must be an attendee

**Output:** `YYYY-MM-DD meeting-notes <subject>.md` saved to `vault/import/` (or override with `MEETING_NOTES_OUTPUT_DIR` env var). Contains YAML frontmatter, summary, discussion topics, decisions, action items, open questions, and key data points. After saving, the skill offers to file the notes via `/tools:archivist`.

### PLC Document Creation

The plc-doc-gen skill was built by describing the workflow to Claude Code, validating it manually against real Confluence templates, then saving as a persistent skill.

**How it works:**
1. Fetches three fixed PLC templates (SPP, SRD, SADD) from Confluence in Storage Format (XHTML)
2. Gathers context from Jira, Confluence, Obsidian, meeting notes, and web search
3. Populates each template section with generated content
4. Publishes all three as new Confluence pages nested under a user-provided parent page

**Credentials:** Reads `CONFLUENCE_BASE_URL`, `CONFLUENCE_USERNAME`, `CONFLUENCE_API_TOKEN` from `~/jill/.env`.

## Dependencies

### Credentials

Report generators and doc generators require credentials in `C:/Users/sfaramarz/jill/.env`:

| Variable | Required by |
|----------|-------------|
| `CONFLUENCE_BASE_URL` / `CONFLUENCE_USERNAME` / `CONFLUENCE_API_TOKEN` | plc-doc-gen, fv-report-gen |
| `JIRA_BASE_URL` / `JIRA_USERNAME` / `JIRA_API_TOKEN` | plc-doc-gen, fv-report-gen, plc-top5-report-gen |
| `SLACK_TOKEN` | fv-report-gen (optional) |

### MCP Servers

| Server | Required by |
|--------|-------------|
| `maas-nvbugs` | fv-report-gen |
| `outlook` | meeting-notes |

### CLI Tools

| Tool | Required by | Install |
|------|-------------|---------|
| `transcript-cli` | meeting-notes | `pip install ai-pim-utils` |
| `python-docx` | fv-report-gen, plc-top5-report-gen | `pip install python-docx` |

### Environment Variables (optional)

| Variable | Purpose |
|----------|---------|
| `MEETING_NOTES_OUTPUT_DIR` | Override output folder for meeting-notes skill (auto-detects OneDrive vault if unset) |
