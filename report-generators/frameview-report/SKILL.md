---
name: frameview-report
description: Generate a weekly FrameView Tool/SDK status report by aggregating data from Outlook emails, NVBugs, Jira, Confluence, Obsidian, and Slack — saves a richly formatted Word document to the Desktop. Use when asked for a FrameView status update, weekly report, or Tool/SDK update email.
license: MIT
metadata:
  author: Sherry Faramarz
  version: "1.0.0"
  last-updated: "2026-03-18"
---
# FrameView Report Generator

Generate a weekly FrameView "Top 5" status report by pulling live data from Outlook emails (PBR/TMF threads + notable correspondence), NVBugs, Jira, Confluence, Obsidian, and Slack — then save it as a richly formatted Word document (`.docx`) on the Desktop.

**Email subject line:** `FrameView Tool/SDK Update DD/MM/YYYY` (e.g., `FrameView Tool/SDK Update 16/03/2026`)
**Word doc filename:** `FrameView_Tool_SDK_Update_DD_MM_YYYY.docx`

## Report Format

Use the **March 13, 2026** report as the canonical format template. It is the most evolved and structured version. All generated reports must follow this exact structure:

```markdown
**<Program Name> Tool Update — Status Report**

_Release <version>  |  Target: <release date>  |  As of <today's date>_

**Overall Status:** **<ON TRACK / AT RISK / OFF TRACK>**

<One-sentence executive summary of the current state, key risks, and notable decisions.>

**QA Bug Fix Status**

**Group 1 — <Theme>**

| Bug ID | Synopsis | Status | Engineer | Last Updated | Notes |
|---|---|---|---|---|---|
| [5XXXXXX](https://nvbugspro.nvidia.com/bug/5XXXXXX) | <synopsis> | **<status>** | <engineer> | <date> | <notes or blank> |

**Group 2 — <Theme>**
...repeat for each non-empty group...

**Release Infrastructure**

| Item | Status |
|---|---|
| PBR #<id> | ✅ Completed / 🔄 In Progress / ❌ Blocked |
| TMF #<id> | ✅ Completed / 🔄 In Progress |
| [FVSDK-XX](https://jirasw.nvidia.com/browse/FVSDK-XX) (<description>) | 🔄 <status summary> |

**<Program Name> Development**

<Summary of roadmap and next-version planning.>

**Planned Features**

- <feature>
- <feature>

Reference: [FV Jira Board](https://jirasw.nvidia.com/secure/RapidBoard.jspa?rapidView=38830), [PLC Dashboard](https://jirasw.nvidia.com/secure/Dashboard.jspa?selectPageId=51845), [FV Confluence Pages](https://jirasw.nvidia.com/secure/Dashboard.jspa?selectPageId=51845)

_Bcc: Jspitzer-staff, jpaul-org, GeForce-Devtech-Managers, DevStatus_UE, Producers, Keita Iida, Jaakko Haapasalo, KLM, Alex Dunn, John spitzer, Jason Paul, Michael Songy, Nyle Usmani, Cem Cebenoyan, frameview_devs_

Best Regards,

Sherry Faramarz
```

### URL Patterns (hardcoded — never invent URLs)

| Resource | URL Pattern |
|---|---|
| NVBug | `https://nvbugspro.nvidia.com/bug/<id>` |
| Jira ticket | `https://jirasw.nvidia.com/browse/<key>` |
| PBR | `https://pbrequest.nvidia.com/r/<id>` |
| TMF | `https://grt.nvidia.com/testrequests/<id>` |
| Jira Board | `https://jirasw.nvidia.com/secure/RapidBoard.jspa?rapidView=38830` |
| PLC Dashboard | `https://jirasw.nvidia.com/secure/Dashboard.jspa?selectPageId=51845` |
| REL project (all open) | `https://jirasw.nvidia.com/projects/REL/issues/REL-23?filter=allopenissues` |
| POR | `https://confluence.nvidia.com/pages/viewpage.action?spaceKey=LightspeedStudios&title=FrameView+v1.8.0+POR` |
| Roadmap | `https://nvidia.atlassian.net/wiki/spaces/LightspeedStudios/pages/3099169705/FrameView+Roadmap` |
| Meeting Notes | `https://nvidia.atlassian.net/wiki/spaces/LightspeedStudios/pages/2422210742/FrameView+Sync+Meeting+Notes` |
| FV Checklist | `https://nvidia.atlassian.net/wiki/spaces/LightspeedStudios/pages/2422211180/FrameView+Tool+v1.8.0+Checklist` |
| VPR/TMF N1X Test Plan | `https://docs.google.com/document/d/1QKYBdR_AiXcssOMPYgTbZt5RaX_Snr1XOLW_yPIGCTI/edit?tab=t.0` |

### Bug Grouping Rules

Group bugs by theme. Omit any group with no bugs. Sort within each group: P0 first, then by days open (descending).

| Group | Theme |
|---|---|
| Group 1 | Performance & Capture Accuracy |
| Group 2 | Crash / Stability |
| Group 3 | Overlay UI / Positioning |
| Group 4 | SDK / CPU Metrics (GR-3647 / FVSDK) |
| Group 5 | N1x / Yukon Platform |
| Group 6 | Other |

For the **Notes** column: use the most recent NVBugs comment or audit entry. Flag action items with ⚠ (e.g., "⚠ Action needed from QA: ...").

### Release Infrastructure Rules

- PBR with ✅ = completed, 🔄 = in progress
- TMF with ✅ = completed/reviewed, 🔄 = in progress
- Jira release tasks: link each one, provide a one-line status summary
- Include security/compliance items (OSRB, vulnerability remediation)

---

## Step 0 — Verify credentials (always run first, before asking anything)

```python
import requests
from dotenv import load_dotenv
import os

load_dotenv('C:/Users/sfaramarz/jill/.env')

base_url = os.getenv('CONFLUENCE_BASE_URL')
username = os.getenv('CONFLUENCE_USERNAME')
token = os.getenv('CONFLUENCE_API_TOKEN')

resp = requests.get(
    f"{base_url}/rest/api/user/current",
    auth=(username, token),
    headers={"Accept": "application/json"},
)
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
5. **NVBugs input** — either a search query string OR a comma-separated list of bug IDs
6. **Jira project key** — e.g. `FVSDK`
7. **PBR number(s)** — e.g. `307197`, `307487`
8. **TMF number(s)** — e.g. `17998`

---

## Step 2 — Ask for additional sources

The following sources are **always fetched automatically** (no need to ask):
- Outlook emails — previous status report thread, PBR emails, TMF emails, and last-month FrameView correspondence
- Jira PLC Dashboard and REL project
- Confluence FrameView pages (Checklist, Roadmap, Meeting Notes, POR)
- Previous Obsidian status report (for continuity)
- Google Doc VPR/TMF N1X Test Plan

Ask only about optional sources using `AskUserQuestion` with `multiSelect: true`:

- **NVBugs** — provide a search query or comma-separated bug IDs (for the QA bug tables)
- **Slack messages** — search channel discussions for engineer updates (requires `SLACK_TOKEN` in `.env`)
- **Free-form context** — blockers, decisions, announcements typed directly

Follow up with one question per selected optional source.

---

## Step 3 — Gather data

**Source priority order:**
1. Outlook emails (PRIMARY) — previous status report, PBR threads, TMF threads, last-month FrameView correspondence
2. Jira PLC Dashboard — overall program status, release tasks, PBR, TMF
3. Jira REL project — all open release issues
4. NVBugs — QA bug details
5. Confluence FrameView pages — Checklist, Roadmap, Meeting Notes, POR (always fetch)
6. Previous Obsidian report — continuity / carry-forward Notes (always read)
7. Google Doc VPR/TMF Test Plan — N1X testing context (always read)
8. Slack messages — channel discussions, action items (if SLACK_TOKEN available)

---

### 3a — Jira PLC Dashboard (PRIMARY — always fetch first)

**URL:** `https://jirasw.nvidia.com/secure/Dashboard.jspa?selectPageId=51845`

Fetches overall program status, PBR/TMF items, and release task epics for the given program.

```python
import requests
from dotenv import load_dotenv
import os

load_dotenv('C:/Users/sfaramarz/jill/.env')

jira_url = os.getenv('JIRA_BASE_URL')  # https://jirasw.nvidia.com
username = os.getenv('JIRA_USERNAME')
token = os.getenv('JIRA_API_TOKEN')

jql = f'project = "{jira_project}" ORDER BY priority ASC, updated DESC'
resp = requests.get(
    f"{jira_url}/rest/api/2/search",
    params={"jql": jql, "maxResults": 100, "fields": "summary,status,assignee,priority,comment,labels,issuetype,updated"},
    auth=(username, token),
    headers={"Accept": "application/json"},
)
resp.raise_for_status()
issues = resp.json()["issues"]
```

Extract: release task epics/stories, PBR numbers and status, TMF numbers and status, security/compliance items (OSRB, vulnerability remediation), any blockers or at-risk items.

---

### 3b — Jira REL Project (SECOND PRIORITY — always fetch)

**URL:** `https://jirasw.nvidia.com/projects/REL/issues/REL-23?filter=allopenissues`

Fetches all open release issues across programs. Filter to issues relevant to the current program by matching the program name in the summary or labels.

```python
# Fetch all open issues from the REL project
jql_rel = f'project = REL AND statusCategory != Done AND text ~ "{program_name}" ORDER BY priority ASC, updated DESC'
resp_rel = requests.get(
    f"{jira_url}/rest/api/2/search",
    params={"jql": jql_rel, "maxResults": 50, "fields": "summary,status,assignee,priority,comment,labels,issuetype,updated"},
    auth=(username, token),
    headers={"Accept": "application/json"},
)
resp_rel.raise_for_status()
rel_issues = resp_rel.json()["issues"]
```

Use REL issues to:
- Supplement or cross-check PBR/TMF status from the dashboard
- Surface any release blockers not yet in the program-specific project
- Identify cross-program dependencies that could affect the release

---

### 3c — NVBugs (QA bug tables)

Use MCP tools (`mcp__nvbugs__*`). For each bug collect: bug ID, synopsis, status, assigned engineer, severity, priority, module, days open, and the most recent comment or audit entry for the Notes column.

- Search query provided → `mcp__nvbugs__search_bugs`
- Explicit IDs provided → `mcp__nvbugs__get_bugs_bulk`
- Latest comment/note → `mcp__nvbugs__get_audit_trail` or `mcp__nvbugs__get_bug`

---

### 3d — Outlook emails (PRIMARY — always run all four searches)

Use the `mcp__outlook__*` MCP tools (already authenticated — no manual credential setup needed). Run all four searches below every time, searching both inbox and sentitems.

```
# 1. Previous status report — for continuity and carry-forward notes
mcp__outlook__outlook_list_messages(
    query="FrameView Tool Update",
    folder_name="inbox,sentitems",
    limit=5,
    sort_order="desc"
)

# 2. PBR emails — for PBR status and any comments/decisions
mcp__outlook__outlook_list_messages(
    query="PBR FrameView OR PBR #307",
    folder_name="inbox,sentitems",
    start_date="<30 days ago>",
    limit=20
)

# 3. TMF emails — for TMF status and tester feedback
mcp__outlook__outlook_list_messages(
    query="FrameView TMF OR TMF Request FrameView",
    folder_name="inbox,sentitems",
    start_date="<30 days ago>",
    limit=20
)

# 4. Notable FrameView correspondence — decisions, blockers, check-ins
mcp__outlook__outlook_list_messages(
    query="FrameView",
    folder_name="inbox,sentitems",
    start_date="<30 days ago>",
    limit=50
)

# Fetch full body of each relevant message
mcp__outlook__outlook_get_message(message_id="<id>")
```

Extract from emails:
- Previous report content → carry forward bug Notes and Release Infrastructure status unchanged since last report
- PBR thread → latest PBR comment, reviewer findings, any blockers
- TMF thread → tester progress, results, open issues (e.g. Joe Vivoli's N1X testing, Jani Joki's desktop TMF)
- Check-in / team emails → delegation decisions, upcoming OOO (e.g. Nikhil/Sukriti OOO end of March), scope changes
- Security/exception emails (nSpect, ExceptionTracker) → OSRB/vulnerability status
- Bug Jira notification emails → latest status on key FVSDK bugs
- Tensor Metrics investigation → overhead percentage, timeline, blockers
- Digital Foundry / licensing decisions → VP sign-off status, legal approvals

---

### 3e — Slack messages

Use the `SlackConnector` from `C:/Users/sfaramarz/jill/connectors/slack.py` via the jill `.env` credentials.

**Prerequisite:** `SLACK_TOKEN` must be set in `C:/Users/sfaramarz/jill/.env`. If it is empty, skip this source and note it in the report generation output. A user token (`xoxp-`) is preferred for full search access.

```python
import sys
sys.path.insert(0, 'C:/Users/sfaramarz/jill')
from connectors.slack import SlackConnector
from dotenv import load_dotenv
import os

load_dotenv('C:/Users/sfaramarz/jill/.env')

slack_token = os.getenv('SLACK_TOKEN', '')
if not slack_token:
    print("SLACK_TOKEN not set — skipping Slack source")
else:
    slack = SlackConnector(token=slack_token)

    # Search for messages about the program in the last week
    messages = slack.search_messages(query=f"{program_name} status OR blocker OR release", count=30)

    # Also pull from configured program channels if channel IDs are known
    channel_ids = [c.strip() for c in os.getenv('SLACK_CHANNEL_IDS', '').split(',') if c.strip()]
    if channel_ids:
        for cid in channel_ids:
            messages += slack.get_channel_messages(cid, limit=20)
```

Extract from Slack:
- Engineer updates on bug fixes ("fixed", "merged", "blocked on")
- Decisions or context that didn't make it into Jira comments
- Action items called out in channel discussions
- Any ⚠ escalations or urgent items mentioned by team members

---

### 3f — Previous Obsidian report (continuity)

Read the most recent `.md` in the vault folder to carry forward Notes for bugs that haven't changed:

```python
import glob

vault_path = "C:/Users/sfaramarz/OneDrive - NVIDIA Corporation/Documents/Work Documents/Obsidian"
pattern = f"{vault_path}/{program_name}/{program_name} Status Report Top 5/*.md"
files = sorted(glob.glob(pattern))
if files:
    with open(files[-1], encoding="utf-8") as f:
        prior_report = f.read()
```

---

### 3g — Confluence pages (ALWAYS fetch these FrameView pages)

Always fetch the following FrameView Confluence pages for context:

| Page | URL |
|---|---|
| FV v1.8.0 Checklist | `https://nvidia.atlassian.net/wiki/spaces/LightspeedStudios/pages/2422211180/FrameView+Tool+v1.8.0+Checklist` |
| FV Roadmap | `https://nvidia.atlassian.net/wiki/spaces/LightspeedStudios/pages/3099169705/FrameView+Roadmap` |
| Sync Meeting Notes | `https://nvidia.atlassian.net/wiki/spaces/LightspeedStudios/pages/2422210742/FrameView+Sync+Meeting+Notes` |

Extract from Confluence:
- Checklist: remaining release tasks, sign-off status for each gate
- Roadmap: 1.9 planning priorities, target dates, feature scope
- Meeting notes: decisions and action items from the most recent sync

```python
# Fetch by URL — convert URL to page ID first, or use space/title lookup
resp = requests.get(
    f"{base_url}/rest/api/content",
    params={"spaceKey": "LightspeedStudios", "title": "<page title>", "expand": "body.storage"},
    auth=(username, token),
    headers={"Accept": "application/json"},
)
# Or fetch by known page ID:
resp = requests.get(
    f"{base_url}/rest/api/content/{page_id}",
    params={"expand": "body.storage"},
    auth=(username, token),
    headers={"Accept": "application/json"},
)
```

### 3h — Google Doc VPR/TMF Test Plan (ALWAYS read)

Read the N1X VPR/TMF test plan for context on what Joe Vivoli is testing:

**URL:** `https://docs.google.com/document/d/1QKYBdR_AiXcssOMPYgTbZt5RaX_Snr1XOLW_yPIGCTI/edit?tab=t.0`

Use `WebFetch` to read this document. Extract:
- Test objectives and scope for N1X FrameView testing
- Target completion date
- Any test results or pass/fail status noted in the doc

---

## Step 4 — Generate the report content

Combine all gathered data and produce the report content. Key rules:

- Keep bug IDs as hyperlinks to `https://nvbugspro.nvidia.com/bug/<id>`
- Keep Jira tickets as hyperlinks to `https://jirasw.nvidia.com/browse/<key>`
- Use ⚠ in Notes for any action items needing follow-up
- Carry forward Notes from the previous report for bugs that haven't changed
- The executive summary should be 1–2 sentences: current state + key risk or notable item
- Do not invent URLs — only use patterns from the URL table above

---

## Step 5 — Save as a formatted Word document on the Desktop

Use `python-docx` to produce a richly formatted `.docx` file. Save to the user's Desktop.

```python
from datetime import date
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import os

today = date.today()
today_str = today.strftime("%d_%m_%Y")        # e.g. 16_03_2026
today_display = today.strftime("%d/%m/%Y")    # e.g. 16/03/2026  (for email subject)
desktop = os.path.join(os.path.expanduser("~"), "OneDrive - NVIDIA Corporation", "Desktop")
output_path = os.path.join(desktop, f"{program_name}_Tool_SDK_Update_{today_str}.docx")

doc = Document()

# --- Page margins ---
for section in doc.sections:
    section.top_margin = Inches(0.75)
    section.bottom_margin = Inches(0.75)
    section.left_margin = Inches(1)
    section.right_margin = Inches(1)

# --- Title ---
# Email subject: f"FrameView Tool/SDK Update {today_display}"  (e.g. "FrameView Tool/SDK Update 16/03/2026")
title = doc.add_heading(f"{program_name} Tool Update — Status Report", level=0)
title.alignment = WD_ALIGN_PARAGRAPH.CENTER
title.runs[0].font.color.rgb = RGBColor(0x76, 0xB9, 0x00)  # NVIDIA green

# --- Subtitle ---
subtitle = doc.add_paragraph()
subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = subtitle.add_run(f"Release {release_version}  |  Target: {release_date}  |  As of {today_formatted}")
run.italic = True
run.font.size = Pt(10)
run.font.color.rgb = RGBColor(0x66, 0x66, 0x66)

# --- Overall Status ---
status_para = doc.add_paragraph()
status_label = status_para.add_run("Overall Status:  ")
status_label.bold = True
status_label.font.size = Pt(12)
status_run = status_para.add_run(overall_status)
status_run.bold = True
status_run.font.size = Pt(12)
# Color by status
if overall_status == "ON TRACK":
    status_run.font.color.rgb = RGBColor(0x00, 0x80, 0x00)
elif overall_status == "AT RISK":
    status_run.font.color.rgb = RGBColor(0xFF, 0x99, 0x00)
else:  # OFF TRACK
    status_run.font.color.rgb = RGBColor(0xCC, 0x00, 0x00)

# --- Executive summary ---
summary_para = doc.add_paragraph(executive_summary)
summary_para.runs[0].font.size = Pt(10)

doc.add_paragraph()  # spacer

# --- QA Bug Fix Status heading ---
doc.add_heading("QA Bug Fix Status", level=1)

# For each bug group with bugs:
for group_name, bugs in bug_groups.items():
    if not bugs:
        continue
    doc.add_heading(group_name, level=2)

    # Table: Bug ID | Synopsis | Status | Engineer | Last Updated | Notes
    table = doc.add_table(rows=1, cols=6)
    table.style = "Table Grid"
    hdr = table.rows[0].cells
    for i, col in enumerate(["Bug ID", "Synopsis", "Status", "Engineer", "Last Updated", "Notes"]):
        hdr[i].text = col
        hdr[i].paragraphs[0].runs[0].bold = True
        hdr[i].paragraphs[0].runs[0].font.size = Pt(9)
        # Header row shading (dark grey)
        tc = hdr[i]._tc
        tcPr = tc.get_or_add_tcPr()
        shd = OxmlElement("w:shd")
        shd.set(qn("w:val"), "clear")
        shd.set(qn("w:color"), "auto")
        shd.set(qn("w:fill"), "404040")
        tcPr.append(shd)
        hdr[i].paragraphs[0].runs[0].font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    for bug in bugs:
        row = table.add_row().cells
        row[0].text = str(bug["id"])
        row[0].paragraphs[0].runs[0].font.size = Pt(9)
        row[1].text = bug["synopsis"]
        row[1].paragraphs[0].runs[0].font.size = Pt(9)
        row[2].text = bug["status"]
        row[2].paragraphs[0].runs[0].font.size = Pt(9)
        # Color status cell
        if "P0" in bug.get("priority", ""):
            row[2].paragraphs[0].runs[0].font.color.rgb = RGBColor(0xCC, 0x00, 0x00)
        row[3].text = bug["engineer"]
        row[3].paragraphs[0].runs[0].font.size = Pt(9)
        row[4].text = bug.get("last_updated", "")
        row[4].paragraphs[0].runs[0].font.size = Pt(9)
        row[5].text = bug.get("notes", "")
        row[5].paragraphs[0].runs[0].font.size = Pt(9)

    doc.add_paragraph()  # spacer after table

# --- Release Infrastructure ---
doc.add_heading("Release Infrastructure", level=1)
infra_table = doc.add_table(rows=1, cols=2)
infra_table.style = "Table Grid"
hdr = infra_table.rows[0].cells
hdr[0].text = "Item"
hdr[1].text = "Status"
for cell in hdr:
    cell.paragraphs[0].runs[0].bold = True
    cell.paragraphs[0].runs[0].font.size = Pt(9)

for item, status in release_infra.items():
    row = infra_table.add_row().cells
    row[0].text = item
    row[1].text = status
    for cell in row:
        cell.paragraphs[0].runs[0].font.size = Pt(9)

doc.add_paragraph()

# --- Development section ---
doc.add_heading(f"{program_name} Development", level=1)
doc.add_paragraph(development_summary).runs[0].font.size = Pt(10)
if planned_features:
    doc.add_heading("Planned Features", level=2)
    for feat in planned_features:
        p = doc.add_paragraph(feat, style="List Bullet")
        p.runs[0].font.size = Pt(10)

doc.add_paragraph()

# --- References ---
doc.add_heading("References", level=1)
refs = doc.add_paragraph()
refs.add_run("Jira Board  |  PLC Dashboard  |  Confluence Pages")
refs.runs[0].font.size = Pt(9)
refs.runs[0].font.color.rgb = RGBColor(0x44, 0x72, 0xC4)

# --- Bcc & Signature ---
doc.add_paragraph()
bcc = doc.add_paragraph()
bcc_run = bcc.add_run(
    "Bcc: Jspitzer-staff, jpaul-org, GeForce-Devtech-Managers, DevStatus_UE, Producers, "
    "Keita Iida, Jaakko Haapasalo, KLM, Alex Dunn, John Spitzer, Jason Paul, Michael Songy, "
    "Nyle Usmani, Cem Cebenoyan, frameview_devs"
)
bcc_run.italic = True
bcc_run.font.size = Pt(8)
bcc_run.font.color.rgb = RGBColor(0x66, 0x66, 0x66)

doc.add_paragraph()
sig = doc.add_paragraph("Best Regards,\n\nSherry Faramarz")
sig.runs[0].font.size = Pt(10)

# --- Save ---
doc.save(output_path)
print(f"Saved: {output_path}")
```

**Formatting spec:**
- Title: centered, NVIDIA green (`#76B900`), bold
- Subtitle: centered, italic, grey
- Overall Status: bold, color-coded — green (ON TRACK), orange (AT RISK), red (OFF TRACK)
- Bug tables: dark grey header row with white text, 9pt body, P0 bugs shown in red
- Release Infrastructure: compact 2-column table
- Bcc line: italic, small, grey
- All tables use `Table Grid` style for clean borders

**Dependency:** requires `python-docx` — install with `pip install python-docx` if not present.

---

## Credentials

From `C:/Users/sfaramarz/jill/.env`:

| Variable | Value |
|---|---|
| `CONFLUENCE_BASE_URL` | https://nvidia.atlassian.net/wiki |
| `CONFLUENCE_USERNAME` | sfaramarz@nvidia.com |
| `CONFLUENCE_API_TOKEN` | (from .env) |
| `JIRA_BASE_URL` | https://jirasw.nvidia.com |
| `JIRA_USERNAME` | sfaramarz@nvidia.com |
| `JIRA_API_TOKEN` | (from .env) |

NVBugs: via `mcp__nvbugs__*` MCP tools — no manual credential setup needed.

---

## Example Invocations

> `/frameview-report-generator`
> → Prompts for all required fields.

> "FrameView 1.8.0, target March 31, ON TRACK. NVBugs IDs: 5926419, 5912133, 5914619, 5871244, 5851147, 5854961, 5865169, 5865524, 5893490, 5900896, 5903291, 5903785. Jira: FVSDK. PBR: 307197, 307487. TMF: 17998."
> → Fetches all data (emails first: PBR #307487 thread, TMF threads, last-month FrameView correspondence; then Jira, NVBugs, Confluence, Obsidian, Google Doc), generates a formatted Word doc, saves to `C:/Users/sfaramarz/Desktop/FrameView_Tool_SDK_Update_16_03_2026.docx`.
