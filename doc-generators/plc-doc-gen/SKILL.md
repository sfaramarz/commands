---
name: plc-doc-gen
description: Populate all three Confluence PLC templates (SPP, SRD, and SADD) with real content from source code, Jira, Confluence, Obsidian, and program materials — then publish all three as new Confluence pages nested under a parent page. Use when asked to create PLC documents, a Software Project Plan, Requirements Document, or Architecture Design Document.
---

# PLC Document Creator

Create all three PLC documents (SPP, SRD, SADD) for a program, populate them with real content, and publish them as Confluence pages nested under a provided parent page.

## Fixed Templates

Always use these — do **not** ask the user for template URLs:

| Document Type | Template ID | URL |
|---|---|---|
| **SPP** — Software Project Plan | `2584970595` | https://nvidia.atlassian.net/wiki/spaces/RP/pages/2584970595/ |
| **SRD** — Software Requirements Document | `2584970602` | https://nvidia.atlassian.net/wiki/spaces/RP/pages/2584970602/ |
| **SADD** — Software Architecture & Design Document | `2584970600` | https://nvidia.atlassian.net/wiki/spaces/RP/pages/2584970600/ |

All three documents are **always** created. Do not ask the user which type to create.

## Document Title Naming Convention

Titles are derived automatically — do **not** ask the user for titles:

| Document Type | Title Format |
|---|---|
| **SPP** | `<Program Name> Software Project Plan` |
| **SRD** | `<Program Name> Requirement Assessment and Documentation` |
| **SADD** | `<Program Name> Design Assessment and Documentation` |

---

## Step 0 — Verify Confluence credentials (always run first)

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

Stop on any failure. Do not proceed with broken credentials.

---

## Step 1 — Collect all info upfront

Ask for everything at once using `AskUserQuestion`. Collect:

**Mandatory:**
1. **Program name** — e.g. `Widget v2`, `Rendering Engine`
2. **Confluence space** — space key (e.g. `LightspeedStudios`, `NVDRV`)
3. **Parent page** — ID or URL to nest all three documents under
4. **Source code location** — GitHub/GitLab URL, Perforce depot path, or local path

**Program context (mandatory) — prompt the user:**
> "Please paste or share any program materials — POR, specs, diagrams, meeting notes, emails, or anything relevant. The more context you provide, the better the documents will be."

**Optional (multi-select):**
5. **Jira project** — project key for open issues and epics
6. **Confluence pages** — existing page URLs or IDs to reference
7. **Obsidian notes** — keywords to search the local vault

#### Source Code Handling

- **GitHub/GitLab URL**: Fetch `README.md`, top-level directory listing, `docs/` folder via API
- **Perforce path**: Note for reference; run `p4 files <path>/...` if accessible
- **Local path**: Read `README.md`, list top-level dirs, inspect config files (`package.json`, `CMakeLists.txt`, `setup.py`)

---

## Step 2 — Generate and publish all three documents

Create SPP → SRD → SADD sequentially, each nested under the same parent page:

1. Fetch template from Confluence (Storage Format XHTML)
2. Parse section headings
3. Generate fully populated Confluence Storage Format XHTML from all gathered context
4. Publish nested under the parent page
5. Report the created URL before proceeding to the next document

```python
TEMPLATES = [
    {"type": "SPP",  "id": "2584970595", "title": f"{program_name} Software Project Plan"},
    {"type": "SRD",  "id": "2584970602", "title": f"{program_name} Requirement Assessment and Documentation"},
    {"type": "SADD", "id": "2584970600", "title": f"{program_name} Design Assessment and Documentation"},
]

for doc in TEMPLATES:
    resp = requests.get(f"{base_url}/rest/api/content/{doc['id']}",
        params={"expand": "body.storage,space,version"},
        auth=(username, token), headers={"Accept": "application/json"})
    resp.raise_for_status()
    template = resp.json()

    body = {
        "type": "page", "title": doc["title"],
        "space": {"key": space_key},
        "ancestors": [{"id": parent_id}],
        "body": {"storage": {"value": populated_html, "representation": "storage"}},
    }
    r = requests.post(f"{base_url}/rest/api/content", json=body,
        auth=(username, token),
        headers={"Content-Type": "application/json", "Accept": "application/json"})
    r.raise_for_status()
    print(f"✓ {doc['type']}: {base_url}/pages/{r.json()['id']}")
```

Print a summary after all three are published:
```
✓ SPP:  <url>
✓ SRD:  <url>
✓ SADD: <url>

All three PLC documents created under: <parent page url>
```

---

## Example Requests

> "Create PLC docs for 'NNE TensorRT for RTX Plugin' in space LightspeedStudios, parent page 3178411842."

> "Set up PLC documents for 'Rendering Engine' in NVDRV under page 987654, repo https://github.com/nvidia/rendering-engine, Jira project REND."
