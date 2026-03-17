# LSS RTX Kit/Tools PLC Top 5 Report Generator

Generate a "Top 5 Things" PLC (Program Level Communication) status report for all LSS RTX Kit/Tools by pulling live data from the Jira PLC Dashboard and REL project — then save it as a formatted Word document (`.docx`) on the Desktop.

## Report Format

Title: **Top 5 Things - LSS RTX Kit/Tools PLC DD/MM/YYYY**

The document contains one section per tool/program, each separated by a horizontal rule (or page break). Multiple programs always go into a **single combined document** — never separate files.

```markdown
Top 5 Things - LSS RTX Kit/Tools PLC DD/MM/YYYY

─────────────────────────────────────────────────

**<Program / Tool Name>**

Release Date: <date from REL project>
Overall Status: <ON TRACK / AT RISK / OFF TRACK>

1. <Most important status item — achievement, risk, or blocker>
2. <Second item>
3. <Third item>
4. <Fourth item>
5. <Fifth item>

─────────────────────────────────────────────────

**<Next Program / Tool Name>**

Release Date: <date from REL project>
Overall Status: <ON TRACK / AT RISK / OFF TRACK>

1. ...
...
```

Each "Top 5" item should be drawn from the **latest comment** on the Jira issue/epic, or synthesized from recent activity. Flag any blockers or action items with ⚠.

### URL Patterns (hardcoded — never invent URLs)

| Resource | URL Pattern |
|---|---|
| Jira ticket | `https://jirasw.nvidia.com/browse/<key>` |
| PLC Dashboard | `https://jirasw.nvidia.com/secure/Dashboard.jspa?selectPageId=51845` |
| REL project (all open) | `https://jirasw.nvidia.com/projects/REL/issues/REL-23?filter=allopenissues` |
| NVBug | `https://nvbugspro.nvidia.com/bug/<id>` |

---

## Step 0 — Verify credentials (always run first)

```python
import requests
from dotenv import load_dotenv
import os

load_dotenv('C:/Users/sfaramarz/jill/.env')

jira_url = os.getenv('JIRA_BASE_URL')   # https://jirasw.nvidia.com
username = os.getenv('JIRA_USERNAME')
token    = os.getenv('JIRA_API_TOKEN')

resp = requests.get(
    f"{jira_url}/rest/api/2/myself",
    auth=(username, token),
    headers={"Accept": "application/json"},
)
resp.raise_for_status()
print("Jira auth OK:", resp.json().get("displayName"))
```

Stop and report any failure. Do not proceed with broken credentials.

---

## Step 1 — Fetch the PLC Dashboard (PRIMARY source)

The dashboard at `https://jirasw.nvidia.com/secure/Dashboard.jspa?selectPageId=51845` shows all LSS RTX Kit/Tools programs. Fetch its gadget configuration to discover the JQL queries and program list.

```python
# Try dashboard gadget config endpoint
resp = requests.get(
    f"{jira_url}/rest/api/2/dashboard/{dashboard_id}/gadget",
    auth=(username, token),
    headers={"Accept": "application/json"},
)
# If that fails, fall back to a broad project/label search
```

**Fallback if dashboard API is unavailable** — query all programs by label or component. Ask the user which programs/tools to include if the dashboard cannot be queried automatically.

For each program found, run:

```python
jql = f'project = "<PROJECT_KEY>" AND statusCategory != Done ORDER BY priority ASC, updated DESC'
resp = requests.get(
    f"{jira_url}/rest/api/2/search",
    params={
        "jql": jql,
        "maxResults": 50,
        "fields": "summary,status,assignee,priority,comment,labels,issuetype,updated,fixVersions"
    },
    auth=(username, token),
    headers={"Accept": "application/json"},
)
issues = resp.json()["issues"]
```

For each issue, extract the **latest comment** body (the last entry in `fields.comment.comments`). This comment is the primary source for each Top 5 item.

---

## Step 2 — Fetch Release Dates from REL Project

**URL:** `https://jirasw.nvidia.com/projects/REL/issues/REL-23?filter=allopenissues`

```python
jql_rel = 'project = REL AND statusCategory != Done ORDER BY priority ASC, updated DESC'
resp_rel = requests.get(
    f"{jira_url}/rest/api/2/search",
    params={
        "jql": jql_rel,
        "maxResults": 100,
        "fields": "summary,status,assignee,priority,duedate,fixVersions,labels,comment,updated"
    },
    auth=(username, token),
    headers={"Accept": "application/json"},
)
rel_issues = resp_rel.json()["issues"]
```

Match each REL issue to a program by searching the `summary` or `labels` for the program name. Extract:
- `duedate` or the date in `fixVersions[].releaseDate` as the **Release Date**
- Overall status (Done / In Progress / Blocked) for the status indicator

If multiple REL issues match a program, use the one with the **nearest future due date** as the primary release.

---

## Step 3 — Build Top 5 Items Per Program

For each program/tool:

1. Collect all open issues ordered by priority (P0 first), then by most recently updated.
2. For each issue, take the **latest comment** as the status update. If no comment, use `fields.summary` + `fields.status.name`.
3. Select up to 5 most important items:
   - P0/P1 bugs or blockers always included first
   - Release-blocking items next
   - Significant in-progress work
   - Recent achievements (issues closed in the last 7 days)
   - Upcoming milestones or risks
4. Prepend ⚠ to any item that is a blocker or marked at-risk.
5. If fewer than 5 meaningful items exist, include only what is available — do not pad with trivial items.

---

## Step 4 — Determine Overall Status Per Program

| Condition | Status |
|---|---|
| Any P0 open bug or release blocker | **OFF TRACK** |
| Any P1 open bug or risk item | **AT RISK** |
| All items on schedule, no blockers | **ON TRACK** |

Use the REL issue status and comment to cross-check.

---

## Step 5 — Save as a Formatted Word Document on the Desktop

Use `python-docx`. Save to `C:/Users/sfaramarz/Desktop/LSS_RTX_PLC_Top5_<YYYY-MM-DD>.docx`.

**Always produce a single combined `.docx` for all programs — never separate files per program.**

```python
from datetime import date
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import os

today = date.today()
today_str = today.strftime("%Y-%m-%d")
today_display = today.strftime("%d/%m/%Y")

desktop = os.path.join(os.path.expanduser("~"), "Desktop")
output_path = os.path.join(desktop, f"LSS_RTX_PLC_Top5_{today_str}.docx")

doc = Document()

# --- Page margins ---
for section in doc.sections:
    section.top_margin    = Inches(0.75)
    section.bottom_margin = Inches(0.75)
    section.left_margin   = Inches(1)
    section.right_margin  = Inches(1)

# --- Document title ---
title = doc.add_heading(f"Top 5 Things - LSS RTX Kit/Tools PLC  {today_display}", level=0)
title.alignment = WD_ALIGN_PARAGRAPH.CENTER
if title.runs:
    title.runs[0].font.color.rgb = RGBColor(0x76, 0xB9, 0x00)  # NVIDIA green

doc.add_paragraph()  # spacer

# --- One section per program ---
# programs = list of dicts:
#   { "name": str, "release_date": str, "overall_status": str, "items": [str, ...] }

STATUS_COLORS = {
    "ON TRACK":  RGBColor(0x00, 0x80, 0x00),
    "AT RISK":   RGBColor(0xFF, 0x99, 0x00),
    "OFF TRACK": RGBColor(0xCC, 0x00, 0x00),
}

for i, prog in enumerate(programs):
    # Horizontal rule between programs (after the first)
    if i > 0:
        # Add a paragraph with a bottom border to simulate a horizontal rule
        p = doc.add_paragraph()
        pPr = p._p.get_or_add_pPr()
        pBdr = OxmlElement("w:pBdr")
        bottom = OxmlElement("w:bottom")
        bottom.set(qn("w:val"), "single")
        bottom.set(qn("w:sz"), "6")
        bottom.set(qn("w:space"), "1")
        bottom.set(qn("w:color"), "AAAAAA")
        pBdr.append(bottom)
        pPr.append(pBdr)

    # Program name header
    prog_heading = doc.add_heading(prog["name"], level=1)
    if prog_heading.runs:
        prog_heading.runs[0].font.color.rgb = RGBColor(0x1F, 0x49, 0x7D)  # Dark blue

    # Release Date row
    rel_para = doc.add_paragraph()
    rel_label = rel_para.add_run("Release Date:  ")
    rel_label.bold = True
    rel_label.font.size = Pt(10)
    rel_date_run = rel_para.add_run(prog.get("release_date", "TBD"))
    rel_date_run.font.size = Pt(10)

    # Overall Status row
    status_para = doc.add_paragraph()
    status_label = status_para.add_run("Overall Status:  ")
    status_label.bold = True
    status_label.font.size = Pt(10)
    status_run = status_para.add_run(prog["overall_status"])
    status_run.bold = True
    status_run.font.size = Pt(10)
    color = STATUS_COLORS.get(prog["overall_status"], RGBColor(0x00, 0x00, 0x00))
    status_run.font.color.rgb = color

    doc.add_paragraph()  # spacer before items

    # Top 5 items as a numbered list
    for idx, item in enumerate(prog["items"], start=1):
        p = doc.add_paragraph(style="List Number")
        run = p.add_run(item)
        run.font.size = Pt(10)
        if item.startswith("⚠"):
            run.font.color.rgb = RGBColor(0xCC, 0x00, 0x00)

    doc.add_paragraph()  # spacer after items

# --- Signature ---
doc.add_paragraph()
sig = doc.add_paragraph("Best Regards,\n\nSherry Faramarz")
sig.runs[0].font.size = Pt(10)

# --- Save ---
doc.save(output_path)
print(f"Saved: {output_path}")
```

**Formatting spec:**
- Title: centered, NVIDIA green (`#76B900`), bold
- Program name: dark blue (`#1F497D`), Heading 1
- Release Date / Overall Status: bold labels, 10pt
- Status color-coded: green (ON TRACK), orange (AT RISK), red (OFF TRACK)
- Top 5 items: numbered list, 10pt; items starting with ⚠ shown in red
- Programs separated by a grey horizontal rule
- Single combined `.docx` — never separate files

**Dependency:** requires `python-docx` — install with `pip install python-docx` if not present.

---

## Credentials

From `C:/Users/sfaramarz/jill/.env`:

| Variable | Value |
|---|---|
| `JIRA_BASE_URL` | https://jirasw.nvidia.com |
| `JIRA_USERNAME` | sfaramarz@nvidia.com |
| `JIRA_API_TOKEN` | (from .env) |

---

## Example Invocations

> `/plc-top5-generator`
> → Fetches all tools from the PLC dashboard, reads latest comments for status, reads REL project for release dates, and saves `C:/Users/sfaramarz/Desktop/LSS_RTX_PLC_Top5_2026-03-16.docx`.

> `/plc-top5-generator FrameView, FVSDK, NvPerf`
> → Limits the report to the named programs only.
