# Claude Commands

A collection of Claude Code skills for LSS RTX Kit/Tools program management, document generation, and status reporting.

## Skills

### Doc Generators

Template-driven document generation for Confluence PLC workflows.

| Skill | Description |
|-------|-------------|
| [plc-doc-gen](doc-generators/plc-doc-gen/) | Create all three PLC documents (SPP, SRD, SADD) populated with content from source code, Jira, Confluence, Obsidian, and program materials — publishes all three as Confluence pages nested under a parent page |

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

- `/doc-generators:plc-doc-gen` — create all three PLC documents (SPP, SRD, SADD) nested under a parent Confluence page
- `/report-generators:fv-report-gen` — generate a FrameView weekly status report
- `/report-generators:plc-top5-report-gen` — generate a PLC Top 5 report for all LSS RTX programs
- `/tools:archivist` — ingest and file documents into the vault
- `/tools:meeting-notes` — generate meeting notes from a Teams transcript
- `/tools:skill-creator` — create a new skill

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
| `nvbugs` | fv-report-gen |
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
