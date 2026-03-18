---
name: plc-docs
description: Populate a Confluence PLC template (SPP, SRD, or SADD) with real content from Jira, Confluence, Obsidian, and meeting notes — then publish it as a new Confluence page. Use when asked to create a Software Project Plan, Requirements Document, or Architecture Design Document.
license: MIT
metadata:
  author: Sherry Faramarz
  version: "1.0.0"
  last-updated: "2026-03-18"
---
# PLC Document Creator

Populate a Confluence PLC (Product Life Cycle) template page with real content using gathered context, then publish the result as a new Confluence page.

## Fixed Templates

The following official templates are always used — do **not** ask the user for a template URL:

| Document Type | Template ID | URL |
|---|---|---|
| **SPP** — Software Project Plan | `2584970595` | https://nvidia.atlassian.net/wiki/spaces/RP/pages/2584970595/ |
| **SRD** — Software Requirements Document | `2584970602` | https://nvidia.atlassian.net/wiki/spaces/RP/pages/2584970602/ |
| **SADD** — Software Architecture & Design Document | `2584970600` | https://nvidia.atlassian.net/wiki/spaces/RP/pages/2584970600/ |

When the user invokes this skill without specifying a document type, ask them which of the three they want to create.

## Document Title Naming Convention

The title of the generated Confluence page is derived automatically from the **Program Name** and document type — do **not** ask the user for a title separately:

| Document Type | Title Format |
|---|---|
| **SPP** | `<Program Name> Software Project Plan` |
| **SRD** | `<Program Name> Requirement Assessment and Documentation` |
| **SADD** | `<Program Name> Design Assessment and Documentation` |

## How to Use

### Step 0 — Verify Confluence credentials (always run first, before asking anything)

Load `C:/Users/sfaramarz/jill/.env` and make a test API call to confirm the credentials work:

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

- If the call **succeeds**, proceed to Step 1.
- If the call **fails** (missing env vars, 401, network error), stop immediately and tell the user what is wrong (e.g. missing `CONFLUENCE_API_TOKEN`, invalid credentials). Do not proceed until credentials are valid.

### Step 1 — Collect basic info
Ask for (if not already provided):
1. **Program name**: The name of the program this document is for (e.g. `Widget v2`, `Rendering Engine`, `Audio Pipeline`)
2. **Document type**: `SPP`, `SRD`, or `SADD`
3. **Space**: Confluence space key (e.g. `LightspeedStudios`, `NVDRV`)
4. **Parent page** ID or URL to nest the new page under

Once the program name and document type are known, derive the page title automatically using the naming convention above.

### Step 2 — Ask for sources (required step, do not skip)
Once the basic info is collected, ask the user which sources to use for content generation using `AskUserQuestion` with `multiSelect: true`:

- **Jira project** — pull open issues and epics for context
- **Confluence pages** — reference existing pages (URLs or IDs)
- **Obsidian notes** — search the local vault by keyword
- **Meeting notes** — paste raw text or point to a Confluence/Obsidian source
- **Free-form context** — any extra information typed directly

Then follow up with one question per selected source to collect the actual values (project key, page URLs, search terms, etc.).

### Step 3 — Generate and publish
Proceed only after sources are confirmed.

## What I Do

1. Fetch the template page from Confluence (Storage Format XHTML)
2. Parse all section headings to understand the document structure
3. Gather context from all specified sources (Jira, Confluence pages, Obsidian, meeting notes)
4. Research the topic using web searches and available knowledge
5. Generate fully populated Confluence Storage Format XHTML for each section
6. Publish the result as a new Confluence page via the REST API

## Credentials

Loaded from `C:/Users/sfaramarz/jill/.env`:
- `CONFLUENCE_BASE_URL` = https://nvidia.atlassian.net/wiki
- `CONFLUENCE_USERNAME` = sfaramarz@nvidia.com
- `CONFLUENCE_API_TOKEN`

## Publish Script Pattern

```python
import requests
from dotenv import load_dotenv
import os

load_dotenv('C:/Users/sfaramarz/jill/.env')

base_url = os.getenv('CONFLUENCE_BASE_URL')
username = os.getenv('CONFLUENCE_USERNAME')
token = os.getenv('CONFLUENCE_API_TOKEN')

# Fetch template
resp = requests.get(
    f"{base_url}/rest/api/content/{template_id}",
    params={"expand": "body.storage,space,version"},
    auth=(username, token),
    headers={"Accept": "application/json"},
)
resp.raise_for_status()
template = resp.json()

# Publish populated page
body = {
    "type": "page",
    "title": output_title,
    "space": {"key": space_key},
    "body": {"storage": {"value": populated_html, "representation": "storage"}},
}
if parent_id:
    body["ancestors"] = [{"id": parent_id}]

r = requests.post(
    f"{base_url}/rest/api/content",
    json=body,
    auth=(username, token),
    headers={"Content-Type": "application/json", "Accept": "application/json"},
)
r.raise_for_status()
page = r.json()
print(f"Created: {base_url}/pages/{page['id']}")
```

## Document Types Supported

- **SPP** — Software Project Plan (template ID `2584970595`)
- **SRD** — Software Requirements Document (template ID `2584970602`)
- **SADD** — Software Architecture & Design Document (template ID `2584970600`)

## Example Requests

> "Create an SPP for program 'Widget v2' in space LS. Use Jira project WIDGET for context."
> → Title: `Widget v2 Software Project Plan`

> "Create an SRD for 'Rendering Engine' in space NVDRV, parent page 987654. Reference https://nvidia.atlassian.net/wiki/pages/111111."
> → Title: `Rendering Engine Requirement Assessment and Documentation`

> "Create a SADD for 'Audio Pipeline' in space LS using Jira project AUDIO and these meeting notes: text:We agreed on a microservice architecture with three components..."
> → Title: `Audio Pipeline Design Assessment and Documentation`
