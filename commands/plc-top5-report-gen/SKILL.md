---
name: plc-top5-report-gen
description: Generate a "Top 5 Things" PLC status report for all LSS RTX Kit/Tools by pulling live data from Jira, nSpect APIs, and plcman findings — saves a formatted Word document to the Desktop. Use when asked for a PLC Top 5, program status report, or weekly LSS RTX status update.
---

# PLC Top 5 Report Generator

Generate a "Top 5 Things" PLC status report for all LSS RTX Kit/Tools and save it as a formatted `.docx` on the Desktop. Enriches each program row with plcman-sourced data: pillar progress fractions, nSpect verification results, show stopper flags, and lead time warnings.

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
Fields: summary, status, project, comment, labels, assignee, customfield_19907
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

## Step 2 — Enrich with plcman data

For each program found in Step 1, gather deeper PLC intelligence from child tickets and nSpect. This step transforms the report from Jira-status-only into a verified, risk-aware summary.

### 2.1 Fetch child tickets

For each parent PLC ticket, fetch all children:

```
JQL: parent = <PARENT_KEY>
Fields: key, summary, status, description, assignee, labels, comment
```

Fallback: `"Epic Link" = <KEY>` or `issue in linkedIssues(<KEY>, 'blocks')`.

### 2.2 Classify child tickets

Map each child ticket summary (case-insensitive) to a task type using plcman's classification:

| Pattern | Task Type | Tier |
|---|---|---|
| `registration`, `register` | artifact-registration | 1 |
| `vulnerability`, `CVE`, `OSS vuln` | vuln-scan | 1 |
| `contacts`, `PLC Security PIC` | release-contacts | 1 |
| `release attributes` | release-attributes | 1 |
| `export compliance` | export-compliance | 1 |
| `secret scan`, `(SS)`, `credential` | secret-scan | 1 |
| `SPP`, `SRD`, `SADD` | plc-documents | 2 |
| `threat`, `TAVA` | threat-assessment | 2 |
| `SAST`, `static analysis`, `code scan` | sast-scan | 2 |
| `OSS license`, `SWIPAT`, `OSRB` | oss-compliance | 2 |
| `malware` | malware-scan | 2 |
| `Product Legal` | product-legal | 2 |
| `privacy`, `PII` | privacy-assessment | 2 |
| `Model Card`, `MC++`, `AI Card` | tai-model-card | 2 |
| `Classification Assessment`, `TAI Classification` | tai-classification | 2 |
| `training`, `security champion` | training | 3 |
| `security review` | security-review | 3 |
| `Release Review` | release-review | SKIP |
| `Exceptions Filed` | exceptions-filed | SKIP |

Compute per program:
- `total_tasks`: count of classified children (excluding SKIP and Done-before-plcman)
- `done_tasks`: count with Jira status Done or Signed-off
- `progress`: `"{done_tasks}/{total_tasks}"`

### 2.3 Extract plcman findings

Check each child ticket's comments for `[plcman]` prefixed comments. For each, extract:
- **Status**: PASS / FAIL / IN PROGRESS / NEEDS ACTION
- **Show stopper**: FAIL on Tier 1 tasks (vuln-scan with C/H > 0, verified secrets, missing registration)

If no plcman comments exist, fall back to the Jira ticket status.

Count per program:
- `pass_count`: tickets with PASS or Done
- `fail_count`: tickets with FAIL
- `action_count`: tickets with NEEDS ACTION or IN PROGRESS
- `show_stoppers`: list of FAIL items on Tier 1 tasks

### 2.4 Query nSpect (when nSpect ID available)

Extract nSpect ID from parent ticket field `customfield_19907`. If available, query key APIs via nSpect tool or curl fallback:

```bash
NSPECT_TOOL="$HOME/.claude/commands/borrowed tools/nvsec-nspect/scripts/nspect_tool.py"
AUTH="$HOME/.claude/commands/borrowed tools/nvsec-nspect/scripts/auth.py"
TOKEN=$(python3 $AUTH ensure-token)
```

| API Call | Data Extracted |
|---|---|
| `GET /programs/{nspect_id}` | Registration status, export compliance bug link |
| `GET /programs/{nspect_id}/programVersions/name/{version}/vulns/counts` | Critical/High/Medium/Low vuln counts |
| `GET /programs/{nspect_id}/secrets` | Verified secret count, scan status |
| `GET /programs/{nspect_id}/programVersions/{version}/static-analysis` | SAST project count, latest scan status |

If nSpect ID is missing or API calls fail, skip gracefully — the report still works with Jira-only data. Note in the report extra_note which programs lacked nSpect data.

### 2.5 Compute risk assessment

For each program, determine `risk_level` and compose `risk_summary`:

| Condition | Risk Level |
|---|---|
| Critical or High vulns > 0 | `blocker` |
| Verified secrets > 0 | `blocker` |
| No artifacts registered (Health Score = 0) AND release < 4w away | `blocker` |
| Release < 2w away + legal/EC not started | `warning` |
| Registration Health Score < 500 AND release < 4w away | `warning` |
| SAST not configured AND release < 4w away | `warning` |
| All clear | `none` |

**Lead time checks** (compute days between today and release date):
- Product Legal Support Form: needs 4 weeks
- Legal Tracker / EC bug: needs 2 weeks
- If product-legal or export-compliance child ticket is still in Backlog/To Do and release date is within the lead time → `warning`

Compose `risk_summary` as a short string: e.g., `"2C/1H vulns, EC pending (2w left)"` or `""` if none.

---

## Step 3 — Fetch Release Dates from REL Project

URL: `https://jirasw.nvidia.com/projects/REL/issues/REL-23?filter=allopenissues`

```
JQL: project = REL ORDER BY updated DESC
Fields: summary, status, priority, duedate, fixVersions, labels, comment, updated
```

Match each REL issue to a program by summary/labels. Use `duedate` or `fixVersions[].releaseDate` as the Release Date. If not available, check the latest comment for date mentions. If still unknown, use "TBD".

---

## Step 4 — Build the table data

For each program, produce one row dict:

```python
{
    "tool": "FrameView v1.9",
    "definition": "Frame time & GPU/CPU performance measurement tool",
    "release_date": "2026-06-02",
    "plc_status": "In Progress",       # Done / In Progress / To Start / At Risk
    "pic": "John Doe",
    "notes": "FVSDK-14, 10/14 done, EC pending (2w left)",
    "progress": "10/14",               # "{done}/{total}" from Step 2.2
    "risk_level": "warning",           # "none" / "warning" / "blocker"
}
```

### PLC Status derivation (enhanced)

| Condition | PLC Status |
|---|---|
| All pillars Done or Signed-off | **Done** |
| `risk_level` = `blocker` | **At Risk** |
| Any pillar In Progress / Under Review / Waiting | **In Progress** |
| All pillars in Backlog or To Do (nothing started) | **To Start** |

### PIC

Pull from the Jira `assignee` field of the L1 PLC parent ticket.

### Notes composition

Build the Notes string by concatenating (comma-separated, single line):

1. **Parent ticket ref** — always first (e.g., `LIGHTS-538`)
2. **Progress fraction** — `"{done}/{total} done"` (omit if Done status)
3. **Key blockers** from `risk_summary` — only the top 2-3 items (e.g., `"2C vulns, SAST not configured"`)
4. **Lead time warnings** — `"legal 3w left (needs 4w)"` (only if at risk)

**Content rules (unchanged):**
- **PLC-only content** — no product bugs, dev backlog, or feature work.
- **Done items get minimal/empty notes** — clear or keep very brief.
- **Single-line** — commas to separate. No multi-line entries.

**Sort order:** Done → In Progress → At Risk → To Start.

**Skip fully signed-off legacy programs** unless they have open PLC work.

---

## Step 5 — Save as Word document

Use `scripts/generate-report.py` with the assembled row dicts. Requires `python-docx` (`pip install python-docx`).

Pass data as a list of dicts (see Step 4 format). The generator renders:
- **Progress** as a sub-line in the PLC Status cell (smaller grey text)
- **At Risk** rows with red treatment (light red background, red status text)
- **Blocker rows** get a bold red marker in the Tool cell

If nSpect was unavailable for some programs, pass `extra_note="nSpect data unavailable for: {list}. Status based on Jira only."`.

---

## Example Invocations

> `/commands:plc-top5-report-gen`
> → Fetches all tools from PLC dashboard, enriches with plcman data, generates combined report.

> "plc-top5 for FrameView, FVSDK, NvPerf only"
> → Limits to the named programs, still enriches with nSpect/plcman data.
