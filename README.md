# Claude Commands

A collection of Claude Code skills for LSS RTX Kit/Tools program management, document generation, and status reporting.

## Skills

### Doc Generators

Template-driven document generation for Confluence PLC workflows.

| Skill | Description |
|-------|-------------|
| [plc-doc-gen](doc-generators/plc-doc-gen/) | Populate a Confluence PLC template (SPP, SRD, or SADD) with real content from Jira, Confluence, Obsidian, and meeting notes — then publish as a new Confluence page |

### Report Generators

Workstream status reporting and stakeholder communication.

| Skill | Description |
|-------|-------------|
| [fv-report-gen](report-generators/fv-report-gen/) | Generate a weekly FrameView Tool/SDK status report by aggregating data from Outlook emails, NVBugs, Jira, Confluence, Obsidian, and Slack — saves a formatted Word document to the Desktop |
| [plc-top5-report-gen](report-generators/plc-top5-report-gen/) | Generate a "Top 5 Things" PLC status report for all LSS RTX Kit/Tools from the Jira PLC Dashboard and REL project — saves a formatted Word document to the Desktop |

## Usage

Skills are loaded automatically from this directory by Claude Code. Invoke by name:

- `/doc-generators:plc-doc-gen` — create an SPP, SRD, or SADD on Confluence
- `/report-generators:fv-report-gen` — generate a FrameView weekly status report
- `/report-generators:plc-top5-report-gen` — generate a PLC Top 5 report for all LSS RTX programs

## Dependencies

All skills require credentials in `C:/Users/sfaramarz/jill/.env`:

| Variable | Required by |
|----------|-------------|
| `CONFLUENCE_BASE_URL` / `CONFLUENCE_USERNAME` / `CONFLUENCE_API_TOKEN` | plc-docs, frameview-report |
| `JIRA_BASE_URL` / `JIRA_USERNAME` / `JIRA_API_TOKEN` | all skills |
| `SLACK_TOKEN` | frameview-report (optional) |

NVBugs access is via `mcp__nvbugs__*` MCP tools — no manual setup needed.

All skills that generate Word documents require `python-docx`:

```bash
pip install python-docx
```
