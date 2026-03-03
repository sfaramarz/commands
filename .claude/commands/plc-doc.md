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

## How to Use

Tell me:
1. **Document type**: `SPP`, `SRD`, or `SADD` (selects the template automatically)
2. **Title**: Title for the new page
3. **Space**: Confluence space key (e.g. `LightspeedStudios`, `NVDRV`)
4. *(optional)* **Parent page** ID to nest the new page under
5. *(optional)* **Jira project** key to fetch open issues from
6. *(optional)* **Reference Confluence pages** (URLs or IDs) for additional context
7. *(optional)* **Obsidian search terms** to pull in relevant notes
8. *(optional)* **Meeting notes** — Confluence URL/ID, `obsidian:<term>`, or `text:<raw text>`
9. *(optional)* **Free-form context** (any extra information I should know)

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

> "Create an SPP titled 'Widget v2 Software Project Plan' in space LS. Use Jira project WIDGET for context."

> "Create an SRD titled 'Rendering Engine SRD' in space NVDRV, parent page 987654. Reference https://nvidia.atlassian.net/wiki/pages/111111."

> "Create a SADD titled 'Audio Pipeline SADD' in space LS using Jira project AUDIO and these meeting notes: text:We agreed on a microservice architecture with three components..."
