# FrameView Data Sources Reference

## Credentials

Load from `C:/Users/sfaramarz/jill/.env`:

| Variable | Value |
|---|---|
| `CONFLUENCE_BASE_URL` | https://nvidia.atlassian.net/wiki |
| `CONFLUENCE_USERNAME` | sfaramarz@nvidia.com |
| `CONFLUENCE_API_TOKEN` | (from .env) |
| `JIRA_BASE_URL` | https://jirasw.nvidia.com |
| `JIRA_USERNAME` | sfaramarz@nvidia.com |
| `JIRA_API_TOKEN` | (from .env) |

NVBugs: via `mcp__nvbugs__*` MCP tools — no manual setup needed.
Outlook: via `mcp__outlook__*` MCP tools — no manual setup needed.

## 3a — Jira PLC Dashboard

```python
import requests
from dotenv import load_dotenv
import os

load_dotenv('C:/Users/sfaramarz/jill/.env')
jira_url = os.getenv('JIRA_BASE_URL')
username = os.getenv('JIRA_USERNAME')
token = os.getenv('JIRA_API_TOKEN')

jql = f'project = "{jira_project}" ORDER BY priority ASC, updated DESC'
resp = requests.get(
    f"{jira_url}/rest/api/2/search",
    params={"jql": jql, "maxResults": 100,
            "fields": "summary,status,assignee,priority,comment,labels,issuetype,updated"},
    auth=(username, token), headers={"Accept": "application/json"},
)
resp.raise_for_status()
issues = resp.json()["issues"]
```

Extract: release task epics/stories, PBR/TMF numbers and status, security/compliance items (OSRB), blockers.

## 3b — Jira REL Project

```python
jql_rel = f'project = REL AND statusCategory != Done AND text ~ "{program_name}" ORDER BY priority ASC, updated DESC'
resp_rel = requests.get(
    f"{jira_url}/rest/api/2/search",
    params={"jql": jql_rel, "maxResults": 50,
            "fields": "summary,status,assignee,priority,comment,labels,issuetype,updated"},
    auth=(username, token), headers={"Accept": "application/json"},
)
rel_issues = resp_rel.json()["issues"]
```

Use to: cross-check PBR/TMF status, surface release blockers, identify cross-program dependencies.

## 3c — NVBugs

Use MCP tools. For each bug collect: bug ID, synopsis, status, engineer, severity, priority, days open, most recent comment.

- Search query → `mcp__nvbugs__search_bugs`
- Explicit IDs → `mcp__nvbugs__get_bugs_bulk`
- Latest note → `mcp__nvbugs__get_audit_trail` or `mcp__nvbugs__get_bug`

## 3d — Outlook Emails (always run all four)

```
# 1. Previous status report
mcp__outlook__outlook_list_messages(query="FrameView Tool Update",
    folder_name="inbox,sentitems", limit=5, sort_order="desc")

# 2. PBR emails
mcp__outlook__outlook_list_messages(query="PBR FrameView OR PBR #307",
    folder_name="inbox,sentitems", start_date="<30 days ago>", limit=20)

# 3. TMF emails
mcp__outlook__outlook_list_messages(query="FrameView TMF OR TMF Request FrameView",
    folder_name="inbox,sentitems", start_date="<30 days ago>", limit=20)

# 4. General FrameView correspondence
mcp__outlook__outlook_list_messages(query="FrameView",
    folder_name="inbox,sentitems", start_date="<30 days ago>", limit=50)

# Fetch full body
mcp__outlook__outlook_get_message(message_id="<id>")
```

Extract: carry-forward bug Notes, PBR/TMF status, OOO decisions, OSRB/vulnerability status, Tensor Metrics updates, Digital Foundry/licensing decisions.

## 3e — Slack (optional, requires SLACK_TOKEN)

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
    messages = slack.search_messages(
        query=f"{program_name} status OR blocker OR release", count=30)
    channel_ids = [c.strip() for c in os.getenv('SLACK_CHANNEL_IDS', '').split(',') if c.strip()]
    for cid in channel_ids:
        messages += slack.get_channel_messages(cid, limit=20)
```

## 3f — Previous Obsidian Report

```python
import glob
vault_path = "C:/Users/sfaramarz/OneDrive - NVIDIA Corporation/Documents/Work Documents/Obsidian"
pattern = f"{vault_path}/{program_name}/{program_name} Status Report Top 5/*.md"
files = sorted(glob.glob(pattern))
if files:
    with open(files[-1], encoding="utf-8") as f:
        prior_report = f.read()
```

## 3g — Confluence Pages (always fetch)

| Page | URL |
|---|---|
| FV v1.8.0 Checklist | `https://nvidia.atlassian.net/wiki/spaces/LightspeedStudios/pages/2422211180/` |
| FV Roadmap | `https://nvidia.atlassian.net/wiki/spaces/LightspeedStudios/pages/3099169705/` |
| Sync Meeting Notes | `https://nvidia.atlassian.net/wiki/spaces/LightspeedStudios/pages/2422210742/` |

```python
resp = requests.get(
    f"{base_url}/rest/api/content/{page_id}",
    params={"expand": "body.storage"},
    auth=(username, token), headers={"Accept": "application/json"},
)
```

Extract: remaining checklist tasks, 1.9 roadmap priorities, decisions from most recent sync.

## 3h — Google Doc VPR/TMF Test Plan (always read)

URL: `https://docs.google.com/document/d/1QKYBdR_AiXcssOMPYgTbZt5RaX_Snr1XOLW_yPIGCTI/edit?tab=t.0`

Use `WebFetch`. Extract: N1X test objectives, target completion date, pass/fail status.
