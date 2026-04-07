---
name: tava-gen
description: Generate TAVA (Threat and Vulnerability Analysis) architecture diagrams and documents from a project's source code and documentation. Collects sources from the user (repo path, Confluence pages, Slack channels, GRT links), assesses whether a TAVA is required, analyzes all sources, and outputs a Mermaid architecture diagram and Markdown architecture document ready for nSpect TAVA 3.0 upload. Use when asked to generate TAVA artifacts, create architecture diagrams for TAVA, prepare TAVA prerequisites, or assess TAVA necessity.
---

# TAVA Architecture Diagram & Document Generator

Collect project sources, assess TAVA necessity, and generate the two nSpect TAVA 3.0 prerequisites:
1. **Architecture/dataflow diagram** (Mermaid `.mmd` → render to PNG/JPG)
2. **Architecture document** (Markdown `.md` → convert to DOCX/PDF)

**Output location:** `tava-output/` in the current working directory (or user-specified)

See [references/tava-guidance.md](references/tava-guidance.md) for TAVA process reference.
See [references/diagram-tips.md](references/diagram-tips.md) for nSpect diagram requirements.

---

## Prerequisites

| Requirement | What | How to verify |
|-------------|------|---------------|
| **confluence-cli** | Fetch Confluence design docs | `confluence-cli --version` |
| **Azure AD auth** | Shared token for Confluence/Outlook/Slack CLIs | `confluence-cli auth status` |
| **Python 3.10+** | Runtime for tava-gen modules | `python --version` |

Optional (improve enrichment quality):
- **slack-cli** or **glean-cli** — fetch Slack channel history
- **mermaid-cli (mmdc)** — render `.mmd` to PNG locally

---

## Step 0 — Preflight

### 0a. Verify tools

```bash
confluence-cli --version 2>&1
```

If not found, warn the user but continue — Confluence enrichment will be skipped.

### 0b. Resolve output folder

Use `tava-output/` in the current working directory unless the user specifies another path. Create it if it doesn't exist.

---

## Step 1 — Collect sources

Ask the user for each source. Accept what they provide, skip what they don't have. Keep it conversational — don't present a wall of prompts.

### 1a. Source code repository

Ask: **"What is the path to the source code repository?"**

This is the primary source. If the user doesn't provide it, use the current working directory.

### 1b. Confluence pages

Ask: **"Any Confluence page links with design docs? (SADD, SRD, PRD, architecture docs)"**

Accept one or more URLs. For each URL, extract the page ID and fetch via:

```bash
confluence-cli page get --page-id <PAGE_ID>
```

### 1c. Slack channels

Ask: **"Any Slack channels with architecture or design discussions?"**

Accept channel names (e.g., `#my-project-arch`). Fetch recent history via:

```bash
glean-cli search "architecture design <channel>" --datasource slack --limit 20
```

### 1d. GRT links

Ask: **"Any GRT (Game Ready Testing) links?"**

Accept URLs from `grt.nvidia.com`. Fetch via:

```bash
glean-cli search "<url>" --limit 10
```

### 1e. Summarize collected sources

Print a summary of what was collected and any fetch errors. Confirm with the user before proceeding.

---

## Step 2 — Assess TAVA necessity

Scan the source repository for risk indicators to determine if a TAVA is required. The assessment auto-detects:

- **Sensitive data patterns** — credentials, PII, financial data, export-control markers
- **Service indicators** — Dockerfiles, CI/CD configs, web frameworks
- **Database connections** — connection strings, ORMs
- **External API calls** — HTTP client usage

### Decision table

| Risk Indicator | TAVA Required? | Process |
|----------------|---------------|---------|
| Sensitive Data (non-export-controlled) | Yes | nSpect TAVA 3.0 |
| Sensitive Data (export-controlled) | Yes | Manual TAVA 2.0 |
| Automotive / Safety | Yes | TARA via PLC L2/L3 |
| Internal Live Service | Yes | nSpect TAVA 3.0 |
| 3rd Party, Operated Internally | Yes | nSpect TAVA 3.0 |
| Commercially Released — Enterprise | Yes | nSpect TAVA 3.0 |
| Commercially Released — Consumer | No | — |
| 3rd Party, Operated Externally | No | Vendor risk assessment |
| Experimental / Research Only | No | — |
| Public Data Only | No | — |

**Only ask the user when the auto-detection is inconclusive.** If export-control markers are found, confirm with the user.

If TAVA is not required, inform the user and stop. If the user still wants to generate, proceed.

---

## Step 3 — Analyze sources

### 3a. Parse source code

Scan the repository for:
- **Components** — from Docker Compose services, package.json, pyproject.toml, Dockerfiles
- **Connections** — from database URIs, message queue configs, HTTP client calls
- **Component types** — service, database, cache, queue, gateway, UI, external API, storage

### 3b. Enrich from documentation

Parse fetched Confluence pages, Slack messages, and GRT data for:
- **Additional components** — named systems, databases, APIs mentioned in docs
- **Protocols** — gRPC, REST, GraphQL, WebSocket, MQTT references
- **Security observations** — authentication, authorization, encryption, PII handling, secrets management, audit logging, network controls
- **Project description** — extract from Confluence content for the TOE summary

### 3c. Report findings

Print the component and connection count. If enrichment added new components, note them.

---

## Step 4 — Generate outputs

### 4a. Architecture diagram (Mermaid)

Generate a `flowchart TD` Mermaid diagram with:
- Components shaped by type (rectangles for services, cylinders for databases, etc.)
- Trust boundaries as subgraphs
- Connections labeled with protocols
- All component blocks clearly labeled (per nSpect requirements)

Write to: `<OUTPUT_DIR>/architecture.mmd`

### 4b. Architecture document (Markdown)

Generate a Markdown document with these sections:
1. **Target of Evaluation (TOE)** — project name, description, scope
2. **System Components** — inventory table + per-component details
3. **Connections and Dataflows** — source/target/protocol table
4. **Trust Boundaries** — if detected
5. **Security Observations** — auto-detected concerns and notes

Write to: `<OUTPUT_DIR>/architecture.md`

### 4c. Report output

Print the paths to both files and their sizes.

---

## Step 5 — Next steps

Tell the user:
1. **Review** both generated files and refine as needed
2. **Render the diagram** to PNG/JPG:
   ```
   mmdc -i architecture.mmd -o architecture.png
   ```
   Or paste the Mermaid source into mermaid.live
3. **Convert the document** to DOCX if needed:
   ```
   pandoc architecture.md -o architecture.docx
   ```
4. **Upload** both to nSpect for TAVA 3.0 analysis
5. Component names in the diagram should **match** names in the document (nSpect requirement)

---

## Example Invocations

> `/tools:tava-gen`
> "What is the path to the source code repository?"
> ... collects sources, assesses, analyzes, generates outputs.

> "generate tava artifacts for our project"
> Same flow — collects sources interactively, produces diagram + document.

> "do we need a tava for this repo?"
> Runs assessment only — scans source, reports whether TAVA is required.
