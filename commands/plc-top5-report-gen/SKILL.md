---
name: plc-top5-report-gen
description: Generate a "Top 5 Things" PLC status report for all LSS RTX Kit/Tools by pulling live data from the Jira PLC Dashboard and REL project — saves a formatted Word document to the Desktop. Use when asked for a PLC Top 5, program status report, or weekly LSS RTX status update.
---

# PLC Top 5 Report Generator

Generate a "Top 5 Things" PLC status report for all LSS RTX Kit/Tools and save it as a formatted `.docx` on the Desktop.

**Output:** `LSS_RTX_PLC_Top5_<YYYY-MM-DD>.docx` — single combined document for all programs.

See [references/report-format.md](references/report-format.md) for report structure, URL patterns, status rules, and formatting spec.

---

## Step 0 — Verify credentials (always run first)

```python
import requests
from dotenv import load_dotenv
import os

load_dotenv('C:/Users/sfaramarz/.claude/jill/.env')
jira_url = os.getenv('JIRA_BASE_URL')
username = os.getenv('JIRA_USERNAME')
token    = os.getenv('JIRA_API_TOKEN')

resp = requests.get(f"{jira_url}/rest/api/2/myself",
    auth=(username, token), headers={"Accept": "application/json"})
resp.raise_for_status()
print("Jira auth OK:", resp.json().get("displayName"))
```

Stop on any failure. Do not proceed with broken credentials.

---

## Step 1 — Fetch PLC programs from the LSS-PLC-L1 label

The PLC Dashboard (ID 51845) uses saved filter **"LSS PLC L1 Filter"** (ID 153065) with JQL: `labels = LSS-PLC-L1`.

The dashboard gadget API is not accessible. Instead, query the label directly:

```
JQL: labels = LSS-PLC-L1 ORDER BY project ASC, updated DESC
Fields: summary, status, project, comment, labels, assignee
Max results: 200
```

Group issues by program name (extract from `[brackets]` in the summary). Known program name patterns:
- `Kokoro-82M` → Kokoro-82M Optimized v1.0
- `Kokoro Plugin` → Kokoro Plugin v1.0
- `NNE TensorRT` → UE NNE Plugin
- `Path Tracing SDK` → RTXPT v1.8 (do NOT use "v3.0 / v1.8")
- `RTXDI` → RTXDI v3.0
- `NVRTX 5.7` → NVRTX v5.7.x
- `RTXGI` → RTXGI
- `MegaGeometry` → MegaGeometry
- `FrameView` or project=FVSDK → FrameView v1.8.x
- `UE DLSS` or label `uedlss` → UE DLSS v8.x.x
- `ComfyUI` or `1.4.0` → **merge into RTX Remix** (not a separate row)
- `IGI` or `In Game Inference` → IGI v1.x

**Important:** Comfy NV Video Prep (ComfyUI AI remaster graph) is part of RTX Remix — always merge into one row with RTX Remix as the tool name.

For each program, compute:
- Total pillars, Done count, Signed-off count, In Progress count, Backlog/To Do count
- Derive **PLC Status**: Done / In Progress / To Start (see status rules in report-format.md)

---

## Step 2 — Fetch Release Dates from REL Project

URL: `https://jirasw.nvidia.com/projects/REL/issues/REL-23?filter=allopenissues`

```
JQL: project = REL ORDER BY updated DESC
Fields: summary, status, priority, duedate, fixVersions, labels, comment, updated
```

Match each REL issue to a program by summary/labels. Use `duedate` or `fixVersions[].releaseDate` as the Release Date. If not available, check the latest comment for date mentions. If still unknown, use "TBD".

---

## Step 3 — Build the table data

For each program, produce one row: `(Tool, Definition, Release Date, PLC Status, PIC, Notes/Pending)`.

**PIC (Person In Charge):** Pull from the Jira `assignee` field of the L1 PLC parent ticket for each program.

**Content rules:**
- **PLC-only content** — only include PLC pillar status, legal/security/SAST progress, nSpect registration, and release review info. Do NOT include product bugs, dev backlog, or feature work.
- **Done items get minimal/empty notes** — once Done, clear the Notes column or keep very brief.
- **Notes must be concise, single-line** — use commas to separate items. No multi-line entries.
- **Include the parent LIGHTS/FVSDK ticket reference** in Notes (e.g., LIGHTS-538, FVSDK-14).

**Sort order:** Done first → In Progress → To Start.

**Skip fully signed-off legacy programs** (e.g., Character Rendering SDK v1.1, IGI v1.5 if signed off) unless they have open PLC work.

---

## Step 4 — Determine PLC Status per program

| Condition | PLC Status |
|---|---|
| All pillars Done or Signed-off | **Done** |
| Any pillar In Progress / Under Review / Waiting | **In Progress** |
| All pillars in Backlog or To Do (nothing started) | **To Start** |

---

## Step 5 — Save as Word document

Use `scripts/generate-report.py` with the assembled `rows` list. Requires `python-docx` (`pip install python-docx`).

Pass data as a list of tuples: `(tool_name, definition, release_date, plc_status, pic, notes)`.

---

## Example Invocations

> `/report-generators:plc-top5-report-gen`
> → Fetches all tools from PLC dashboard, generates combined report, saves to Desktop.

> "plc-top5 for FrameView, FVSDK, NvPerf only"
> → Limits to the named programs.
