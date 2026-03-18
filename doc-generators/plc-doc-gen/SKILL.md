---
name: plc-docs
description: Populate all three Confluence PLC templates (SPP, SRD, and SADD) with real content from source code, Jira, Confluence, Obsidian, and program materials — then publish all three as new Confluence pages nested under a parent page. Use when asked to create PLC documents, a Software Project Plan, Requirements Document, or Architecture Design Document.
license: MIT
metadata:
  author: Sherry Faramarz
  version: "2.0.0"
  last-updated: "2026-03-18"
---
# PLC Document Creator

Create all three PLC documents (SPP, SRD, SADD) for a program, populate them with real content, and publish them as Confluence pages nested under a provided parent page.

## Fixed Templates

The following official templates are always used — do **not** ask the user for template URLs:

| Document Type | Template ID | URL |
|---|---|---|
| **SPP** — Software Project Plan | `2584970595` | https://nvidia.atlassian.net/wiki/spaces/RP/pages/2584970595/ |
| **SRD** — Software Requirements Document | `2584970602` | https://nvidia.atlassian.net/wiki/spaces/RP/pages/2584970602/ |
| **SADD** — Software Architecture & Design Document | `2584970600` | https://nvidia.atlassian.net/wiki/spaces/RP/pages/2584970600/ |

All three documents are **always** created. Do not ask the user which type to create.

## Document Title Naming Convention

Titles are derived automatically from the **Program Name** — do **not** ask the user for titles:

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
- If the call **fails** (missing env vars, 401, network error), stop immediately and tell the user what is wrong. Do not proceed until credentials are valid.

### Step 1 — Collect all info upfront (single unified step)

Ask for everything at once using `AskUserQuestion`. Collect:

**Document basics (all mandatory):**
1. **Program name** — e.g. `Widget v2`, `Rendering Engine`, `Audio Pipeline`
2. **Confluence space** — space key where pages will be created (e.g. `LightspeedStudios`, `NVDRV`)
3. **Parent page** — ID or URL of the Confluence page to nest all three documents under (required — do not proceed without this)

**Source code (mandatory):**
4. **Source code location** — GitHub/GitLab repo URL, Perforce depot path, or local file system path (e.g. `https://github.com/org/repo`, `//depot/project/main`, `C:/repos/my-project`)

**Program context — paste or share anything relevant (mandatory):**

Explicitly prompt the user with:
> "Please paste or share any program materials you have — the more context you provide, the better the documents will be. This can include:
> - **Word documents or PDFs** — project briefs, specs, proposals
> - **POR (Plan of Record)** — feature lists, priorities, milestones
> - **Diagrams or architecture drawings** — paste descriptions or image content
> - **Meeting notes or decisions** — any recorded discussions or agreements
> - **Emails or Slack threads** — relevant communications
> - **Anything else** related to this program
>
> Paste the text directly, or describe what you have and I'll guide you."

**Optional additional sources (multi-select):**
5. **Jira project** — project key to pull open issues and epics
6. **Confluence pages** — existing page URLs or IDs to reference
7. **Obsidian notes** — keywords to search the local vault

#### Source Code Handling

Based on the source code location type, gather context as follows:

- **GitHub / GitLab URL**: Fetch the repo's `README.md`, top-level directory listing, and any `CONTRIBUTING.md` or `docs/` folder content via the platform's API or raw URLs. Identify languages, frameworks, and major components.
- **Perforce depot path**: Note the path for reference in the document. If accessible via the `p4` CLI, run `p4 files <path>/...` to list top-level structure.
- **Local path**: Read `README.md`, list top-level directories and files, and identify key config files (e.g. `package.json`, `CMakeLists.txt`, `setup.py`) to infer tech stack and architecture.

Use the gathered source code context to populate architecture, dependencies, and component sections across all three documents.

### Step 2 — Generate and publish all three documents

Proceed only after all info and context are collected.

Create all three documents sequentially (SPP → SRD → SADD), each nested under the same parent page:

1. Fetch each template from Confluence (Storage Format XHTML)
2. Parse the section headings for that document type
3. Generate fully populated Confluence Storage Format XHTML using all gathered context
4. Publish the page nested under the parent page
5. Report the created page URL before moving to the next document

After all three are published, print a summary:

```
✓ SPP:  <url>
✓ SRD:  <url>
✓ SADD: <url>

All three PLC documents created under: <parent page url>
```

## What I Do

1. Verify Confluence credentials
2. Collect program name, parent page, space, source code location, program context, and optional sources — all in one step
3. Gather context from the source code (README, directory structure, tech stack)
4. Gather context from optional sources (Jira, Confluence pages, Obsidian)
5. Research the program using web searches and available knowledge
6. For each of the three document types (SPP, SRD, SADD):
   a. Fetch the official template from Confluence
   b. Generate fully populated Confluence Storage Format XHTML
   c. Publish as a new page nested under the parent page
7. Report all three page URLs on completion

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

TEMPLATES = [
    {"type": "SPP",  "id": "2584970595", "title": f"{program_name} Software Project Plan"},
    {"type": "SRD",  "id": "2584970602", "title": f"{program_name} Requirement Assessment and Documentation"},
    {"type": "SADD", "id": "2584970600", "title": f"{program_name} Design Assessment and Documentation"},
]

created_pages = []

for doc in TEMPLATES:
    # Fetch template
    resp = requests.get(
        f"{base_url}/rest/api/content/{doc['id']}",
        params={"expand": "body.storage,space,version"},
        auth=(username, token),
        headers={"Accept": "application/json"},
    )
    resp.raise_for_status()
    template = resp.json()

    # populated_html is generated per document type using all gathered context
    populated_html = generate_content(doc["type"], template, context)

    # Publish page nested under parent
    body = {
        "type": "page",
        "title": doc["title"],
        "space": {"key": space_key},
        "ancestors": [{"id": parent_id}],
        "body": {"storage": {"value": populated_html, "representation": "storage"}},
    }
    r = requests.post(
        f"{base_url}/rest/api/content",
        json=body,
        auth=(username, token),
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    r.raise_for_status()
    page = r.json()
    url = f"{base_url}/pages/{page['id']}"
    created_pages.append({"type": doc["type"], "url": url})
    print(f"✓ {doc['type']}: {url}")

print(f"\nAll three PLC documents created under: {base_url}/pages/{parent_id}")
```

## Example Requests

> "Create PLC docs for 'NNE TensorRT for RTX Plugin' in space LightspeedStudios, parent page 3178411842."
> → Creates three pages nested under 3178411842:
>   - `NNE TensorRT for RTX Plugin Software Project Plan`
>   - `NNE TensorRT for RTX Plugin Requirement Assessment and Documentation`
>   - `NNE TensorRT for RTX Plugin Design Assessment and Documentation`

> "Set up PLC documents for 'Rendering Engine' in NVDRV under page 987654, repo https://github.com/nvidia/rendering-engine, Jira project REND."
> → Creates all three documents under page 987654 in the NVDRV space.
