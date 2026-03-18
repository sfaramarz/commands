---
name: fv-report-gen
description: Generate a weekly FrameView Tool/SDK status report by aggregating data from Outlook emails, NVBugs, Jira, Confluence, Obsidian, and Slack — saves a richly formatted Word document to the Desktop. Use when asked for a FrameView status update, weekly report, or Tool/SDK update email.
---

# FrameView Report Generator

Generate a weekly FrameView status report and save it as a formatted `.docx` on the Desktop.

**Email subject:** `FrameView Tool/SDK Update DD/MM/YYYY`
**Output file:** `FrameView_Tool_SDK_Update_DD_MM_YYYY.docx`

See [references/report-format.md](references/report-format.md) for the full report structure, URL patterns, bug grouping rules, and Word formatting spec.
See [references/data-sources.md](references/data-sources.md) for API call patterns for each data source.

---

## Step 0 — Verify credentials (always run first)

```python
import requests
from dotenv import load_dotenv
import os

load_dotenv('C:/Users/sfaramarz/jill/.env')
base_url = os.getenv('CONFLUENCE_BASE_URL')
username = os.getenv('CONFLUENCE_USERNAME')
token = os.getenv('CONFLUENCE_API_TOKEN')

resp = requests.get(f"{base_url}/rest/api/user/current",
    auth=(username, token), headers={"Accept": "application/json"})
resp.raise_for_status()
print("Confluence auth OK:", resp.json().get("displayName"))
```

Stop and report any failure. Do not proceed with broken credentials.

---

## Step 1 — Collect basic info

Ask for (only what is not already provided):

1. **Program name** — e.g. `FrameView`
2. **Release version** — e.g. `1.8.0`
3. **Release target date** — e.g. `March 31, 2026`
4. **Overall status** — `ON TRACK`, `AT RISK`, or `OFF TRACK`
5. **NVBugs input** — search query string OR comma-separated bug IDs
6. **Jira project key** — e.g. `FVSDK`
7. **PBR number(s)** — e.g. `307197`, `307487`
8. **TMF number(s)** — e.g. `17998`

---

## Step 2 — Ask for additional sources

Always fetched automatically (do not ask):
- Outlook emails — previous status report, PBR/TMF threads, 30-day FrameView correspondence
- Jira PLC Dashboard and REL project
- Confluence FrameView pages (Checklist, Roadmap, Meeting Notes, POR)
- Previous Obsidian status report
- Google Doc VPR/TMF N1X Test Plan

Ask only about optional sources using `AskUserQuestion` with `multiSelect: true`:
- **Slack messages** — requires `SLACK_TOKEN` in `.env`
- **Free-form context** — blockers, decisions, announcements typed directly

---

## Step 3 — Gather data

Priority order (see [references/data-sources.md](references/data-sources.md) for all API call patterns):

1. **Outlook emails** (PRIMARY) — previous report, PBR/TMF threads, 30-day correspondence
2. **Jira PLC Dashboard** — program status, release tasks, PBR/TMF numbers
3. **Jira REL project** — open release issues
4. **NVBugs** — QA bug details via `mcp__nvbugs__*` tools
5. **Confluence pages** — Checklist, Roadmap, Meeting Notes, POR
6. **Previous Obsidian report** — carry-forward Notes for unchanged bugs
7. **Google Doc VPR/TMF Test Plan** — N1X testing context
8. **Slack** — engineer updates and action items (if SLACK_TOKEN set)

---

## Step 4 — Generate report content

- Keep bug IDs as hyperlinks: `https://nvbugspro.nvidia.com/bug/<id>`
- Keep Jira tickets as hyperlinks: `https://jirasw.nvidia.com/browse/<key>`
- Flag action items with ⚠ in Notes
- Carry forward Notes from previous report for unchanged bugs
- Executive summary: 1–2 sentences — current state + key risk
- Do not invent URLs — only use patterns from [references/report-format.md](references/report-format.md)

---

## Step 5 — Save as Word document

Use `scripts/generate-report.py` with the assembled data. Requires `python-docx` (`pip install python-docx`).

---

## Example Invocations

> `/report-generators:fv-report-gen`
> → Prompts for required fields.

> "FrameView 1.8.0, target March 31, ON TRACK. NVBugs IDs: 5926419, 5912133, 5914619. Jira: FVSDK. PBR: 307197, 307487. TMF: 17998."
> → Fetches all data sources, generates report, saves `FrameView_Tool_SDK_Update_18_03_2026.docx` to Desktop.
