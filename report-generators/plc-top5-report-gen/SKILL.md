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

load_dotenv('C:/Users/sfaramarz/jill/.env')
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

## Step 1 — Fetch the PLC Dashboard

Dashboard URL: `https://jirasw.nvidia.com/secure/Dashboard.jspa?selectPageId=51845`

Try the gadget config endpoint to get the program list and JQL queries. If unavailable, ask the user which programs to include.

For each program, run a JQL search: `project = "<KEY>" AND statusCategory != Done ORDER BY priority ASC, updated DESC` with fields `summary,status,assignee,priority,comment,labels,issuetype,updated,fixVersions`. Extract the **latest comment** from each issue as the primary status source.

---

## Step 2 — Fetch Release Dates from REL Project

URL: `https://jirasw.nvidia.com/projects/REL/issues/REL-23?filter=allopenissues`

JQL: `project = REL AND statusCategory != Done ORDER BY priority ASC, updated DESC` with fields `summary,status,assignee,priority,duedate,fixVersions,labels,comment,updated`.

Match each REL issue to a program by summary/labels. Use `duedate` or `fixVersions[].releaseDate` as the Release Date. If multiple matches, use the nearest future date.

---

## Step 3 — Build Top 5 Items Per Program

For each program: collect open issues (P0 first, then most recently updated), take the latest comment as the status update, select up to 5 most important items (P0/P1 blockers first, then release-blocking work, recent achievements, upcoming milestones). Prepend ⚠ to blockers. Do not pad with trivial items.

---

## Step 4 — Determine Overall Status

See status rules in [references/report-format.md](references/report-format.md). Cross-check with REL issue status and comment.

---

## Step 5 — Save as Word document

Use `scripts/generate-report.py` with the assembled `programs` list. Requires `python-docx` (`pip install python-docx`).

---

## Example Invocations

> `/report-generators:plc-top5-report-gen`
> → Fetches all tools from PLC dashboard, generates combined report, saves to Desktop.

> "plc-top5 for FrameView, FVSDK, NvPerf only"
> → Limits to the named programs.
