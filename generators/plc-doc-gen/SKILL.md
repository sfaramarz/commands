---
name: plc-doc-gen
description: Populate all three Confluence PLC templates (SPP, SRD, and SADD) with real content from source code, Jira, Confluence, Obsidian, emails, Teams transcripts, Glean, and NVBugs — then publish all three as new Confluence pages nested under a parent page. Use when asked to create PLC documents, a Software Project Plan, Requirements Document, or Architecture Design Document.
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

## Step 0 — Verify Confluence credentials

```bash
confluence-cli page get 2584970595 --toon 2>&1 | head -5
```

If this returns content, auth is working. If it fails with exit code 2, tell the user to run `confluence-cli auth set-token`. Stop on failure.

---

## Step 1 — Collect all info upfront

**First, ask about source code** using `AskUserQuestion`:

> "Would you like to provide a source code repository (GitHub or GitLab URL) for this program? Having access to the source code significantly improves the quality of the generated documents — I can extract architecture details, dependencies, configuration data, interfaces, error handling patterns, and test infrastructure directly from the code.
>
> If yes, please share the URL (e.g., `https://github.com/NVIDIA/my-project` or `https://gitlab-master.nvidia.com/team/my-project`). You can also provide a local path or Perforce depot path.
>
> If no, I'll generate the documents from the other sources you provide."

Then ask for the remaining info in a single `AskUserQuestion`:

**Mandatory:**
1. **Program name** — e.g. `Widget v2`, `Rendering Engine`
2. **Confluence space** — space key (e.g. `LightspeedStudios`, `NVDRV`)
3. **Parent page** — ID or URL to nest all three documents under

**Program context (mandatory) — prompt the user:**
> "Please paste or share any program materials — POR, specs, diagrams, meeting notes, emails, or anything relevant. The more context you provide, the better the documents will be."

**Optional (multi-select):**
4. **Jira project** — project key for open issues and epics
5. **Confluence pages** — existing page URLs or IDs to reference
6. **Obsidian notes** — keywords to search the local vault
7. **Outlook email keywords** — search terms to find relevant email threads
8. **Teams meeting keywords** — search terms to find relevant meeting transcripts
9. **NVBugs IDs or search** — bug IDs or search queries for related bugs
10. **Glean search keywords** — enterprise-wide search for additional context

---

## Step 2 — Gather data from all sources

Run all data-gathering commands in parallel where possible. Use `--toon` for all CLI calls to minimize token usage.

### 2.1 Source Code (if provided)

If the user provided a repo URL or local path, clone/access it and extract the following. This data feeds directly into multiple document sections — the more you extract, the better the output.

**What to extract and where it's used:**

| What to extract | How | Feeds into |
|---|---|---|
| **README / docs** | Read `README.md`, `docs/` folder, `CONTRIBUTING.md` | SPP Overview, SRD Overview, SADD Purpose |
| **Directory structure** | `ls` top-level dirs, identify major components | SADD Architectural Details, Static Design |
| **Build/config files** | Read `CMakeLists.txt`, `package.json`, `setup.py`, `Cargo.toml`, `pyproject.toml`, `Makefile` | SPP Constraints, SRD Platform Reqs, SADD Config Data |
| **Dependencies** | Parse dependency lists from build files | SPP Dependencies, SRD Interface Reqs, SADD External Interfaces |
| **API definitions** | Grep for `@api`, `@router`, `def endpoint`, proto files, header files with exports | SRD Functional Reqs, SADD External Interfaces |
| **Config/env files** | Read `.env.example`, `config/`, YAML/TOML configs | SADD 3.2.1 Configuration Data |
| **Error handling** | Grep for `try/catch`, `error`, `panic`, `raise`, error handler modules | SADD 3.3.4 Error Handling |
| **Logging** | Grep for `logger`, `log.`, `logging`, `slog` | SADD 3.3.5 Logging and Debugging |
| **Test infrastructure** | Read `tests/`, `*_test.*`, `test_*.*`, CI config (`.github/workflows/`, `.gitlab-ci.yml`) | SRD Test Automatability, SADD 3.5 Test Automation |
| **Security** | Grep for auth, crypto, TLS, token, permission patterns | SRD Security Reqs, SADD 3.4 Security Design |

**Clone strategy:**
- **GitHub**: `git clone --depth 1 <url> /tmp/plc-repo-<name>`
- **GitLab (NVIDIA)**: `git clone --depth 1 <url> /tmp/plc-repo-<name>` (uses SSH or token auth)
- **Perforce**: `p4 files <path>/...` to list, `p4 print` for specific files
- **Local path**: Read directly

After cloning, use the Explore agent or Grep/Glob tools to efficiently extract each category above. Do NOT read every file — target the specific patterns listed.

### 2.2 Confluence — existing pages

```bash
# Fetch referenced pages for context
confluence-cli page get <page-id> --toon

# Search for related pages in the space
confluence-cli search text "<program name>" --space <space-key> --toon --max-results 10
```

### 2.3 Jira — epics, issues, sprints

```bash
# Open issues and epics
atlassian-cli jira issue find "project = <KEY> AND status != Done ORDER BY priority DESC" --toon --max-results 50

# Epics specifically
atlassian-cli jira issue find "project = <KEY> AND issuetype = Epic ORDER BY priority DESC" --toon --max-results 20

# Recent sprint work
atlassian-cli jira board list --toon
atlassian-cli jira sprint current <board-id> --toon
```

### 2.4 Outlook — email threads (optional)

```bash
# Search for relevant emails by keyword
outlook-cli email list --search "<program name>" --limit 10 --toon

# Read specific email for detail
outlook-cli email get <message-id> --toon
```

### 2.5 Teams — meeting transcripts (optional)

```bash
# Find recent meetings about the program
calendar-cli event list --search "<program name>" --days 90 --toon

# Get transcript from a specific meeting
transcript-cli get <meeting-id> --toon
```

### 2.6 NVBugs (optional)

```bash
# Search for related bugs
nvbugs-cli search "<program name>" --toon --max-results 20

# Get specific bug details
nvbugs-cli get <bug-id> --toon
```

### 2.7 Glean — enterprise search (optional)

```bash
# Broad enterprise search for additional context
glean-cli search "<program name> requirements architecture" --output raw
```

### 2.8 Obsidian vault (optional)

Search the local Obsidian vault for relevant notes using Grep tool with the provided keywords.

---

## Step 3 — Fetch templates

Try fetching live templates from Confluence first. If that fails (auth error, network issue, timeout), fall back to the bundled local copies.

```bash
# Try live fetch first
confluence-cli page get 2584970595 --format html --toon  # SPP
confluence-cli page get 2584970602 --format html --toon  # SRD
confluence-cli page get 2584970600 --format html --toon  # SADD
```

**Fallback — bundled local templates** (use if any live fetch fails):

| Document | Local path |
|---|---|
| **SPP** | `~/.claude/commands/plc-generators/plc-doc-gen/template-spp.xhtml` |
| **SRD** | `~/.claude/commands/plc-generators/plc-doc-gen/template-srd.xhtml` |
| **SADD** | `~/.claude/commands/plc-generators/plc-doc-gen/template-sadd.xhtml` |

Read the local `.xhtml` file with the Read tool if the corresponding `confluence-cli` call fails. These are snapshots of the live templates — functionally identical.

Parse each template's storage-format XHTML. Preserve the exact XHTML structure, table formats, macros (`ac:structured-macro`), and styling. Only replace placeholder text (`<Enter your text here>`, `<doc title>`, etc.) with real content.

---

## Step 4 — Populate each document section-by-section

For every section below, synthesize content from **all gathered sources** — do not rely on a single source. Cross-reference Jira issues with code structure, emails with meeting transcripts, etc.

### SPP — Software Project Plan

| Section | What to write | Key sources |
|---|---|---|
| **Document Control** | Set Title to SPP title, Author to user's name, Revision to today's date, State to "Development" | User input |
| **Introduction > Overview** | 2-3 paragraphs: what the project is, its purpose, and high-level goals. Include the business motivation and target audience. | README, POR, specs, Glean, emails |
| **Introduction > Assumptions** | Bulleted list of technical and organizational assumptions (e.g., "CUDA 12.x available", "team has access to DGX cluster") | Specs, meeting notes, emails |
| **Introduction > Constraints** | Bulleted list: platform constraints, development environment, legacy dependencies, compliance requirements | Source code configs, Jira, specs |
| **Introduction > Dependencies** | Populate the table with team/company names and what they deliver. Pull from Jira linked issues, cross-team epics, and meeting notes. | Jira epics, emails, transcripts |
| **Introduction > Definitions, Acronyms** | Extract domain-specific terms from all sources. Include acronyms found in code, Jira, and docs. | All sources |
| **Introduction > References** | Link to SRD, SADD (will be created), source repo, Jira project, Confluence space, any specs or POR documents. | All sources |
| **Key Dates** | Populate Planning/Implementation/Validation rows. Pull from Jira sprint dates, roadmap, POR milestones. Leave Actual Date blank if not yet occurred. | Jira sprints, POR, calendar events, emails |

### SRD — Software Requirements Document

| Section | What to write | Key sources |
|---|---|---|
| **Document Control** | Same as SPP but with SRD title and template reference | User input |
| **1.1 Overview** | Answer all five sub-questions: Why developed? What problem? Main functions? Primary stakeholders? Who is developing? Each answer should be 2-4 sentences. | README, POR, specs, Glean |
| **1.2 Assumptions** | Same approach as SPP Assumptions but focused on requirement-level assumptions | Specs, emails |
| **1.3 Constraints** | Same approach as SPP Constraints but focused on requirement-level constraints | Source code, Jira |
| **1.4 Dependencies** | Populate dependency table — focus on teams whose deliverables affect requirements | Jira, emails, transcripts |
| **1.5 Definitions, Acronyms** | Same as SPP | All sources |
| **1.6 References** | Link to SPP, SADD, repo, Jira, specs | All sources |
| **2. Use Cases** | Extract use cases from specs, README features, Jira epics. Each row: use case name + 2-3 sentence description. | README features, Jira epics, specs, emails |
| **3. Requirements** | **Critical section.** Create REQ-1, REQ-2, etc. Extract from: Jira epics/stories → functional reqs; code configs → platform reqs; specs → KPI reqs; security notes → security reqs. Populate both the simple 4-column table AND the enhanced 8-column table if applicable. Include all requirement types: Functional, Non-Functional, Interface, Safety, KPI, Platform, Security, Legal, Telemetry, Backward Compatibility, Virtualization, Test Automatability. | Jira issues, specs, README, source code, NVBugs |
| **4. Test Automatability** | Keep sections 4.1 and 4.2 (security implications and best practices) as-is from template — they are standard boilerplate. Populate 4.3 checklist table with program-specific details for each requirement row. | Source code test infrastructure, Jira test issues |

### SADD — Software Architecture & Design Document

| Section | What to write | Key sources |
|---|---|---|
| **Document Control** | Same pattern with SADD title and template reference | User input |
| **1.1 Purpose and Scope** | State that this document describes the architecture and design realizing the SRD requirements. Reference the SRD by name. | SRD content |
| **1.2 Assumptions** | Architecture-level assumptions (e.g., "microservice architecture", "GPU memory > 8GB") | Source code, specs |
| **1.3 Constraints** | Architecture-level constraints | Source code configs, Jira |
| **1.4 Dependencies** | Brief — point to section 3.2.3 for details | Jira |
| **1.5 Definitions, Acronyms** | Same as other docs | All sources |
| **1.6 References** | Link to SPP, SRD, repo, design docs | All sources |
| **2. Architectural Details** | High-level architecture description with block diagram description (describe components and their relationships). Cover static aspects (component structure) and dynamic aspects (runtime interactions). List key assumptions/limitations. | Source code structure, README, design docs, meeting transcripts |
| **3.1 Design Alternatives** | Describe design options that were considered and why the chosen approach was selected. Pull from meeting transcripts, emails, design docs. | Transcripts, emails, Confluence pages |
| **3.2.1 Configuration Data** | List config files, environment variables, registry keys, startup parameters found in the source code. | Source code (`*.config`, `*.yaml`, `*.json`, `*.toml`, env files) |
| **3.2.2 External Interfaces** | For each external interface: name, owner, interface details, data transfer format, security considerations. Derive from API definitions, import statements, SDK usage in code. | Source code imports, API docs, specs |
| **3.2.3 Dependencies** | Populate table with team, deliverable, section reference, commitment status. Include integration validation plan in 3.2.3.1. | Jira cross-team links, emails, meeting notes |
| **3.3.1 Functionality and Behavior** | Describe what each major component does and how it behaves at runtime | Source code, README, specs |
| **3.3.2 Control Flow** | Describe the main control flow paths. Reference sequence diagrams if available. | Source code, design docs |
| **3.3.3 Data Flow** | Describe data flow between components. Mention data formats, serialization. | Source code, API specs |
| **3.3.4 Error Handling** | Describe error handling patterns in the codebase. How errors are logged, propagated, and secured. | Source code error handling patterns |
| **3.3.5 Logging and Debugging** | Describe logging framework, log levels, debug interfaces | Source code logging config |
| **3.3.6 State Machine** | If applicable, describe state transitions. Otherwise note "Not applicable." | Source code, specs |
| **3.4 Security Design** | Describe security measures: authentication, authorization, data protection, threat model. Reference NVBugs security issues if any. | Source code, NVBugs, security specs |
| **3.5 Test Automation** | Describe how test automatability requirements from SRD section 4 are met in the design. Cover open-box testing, closed-box testing, CI/CD hooks. | Source code test infrastructure, Jira test issues |
| **3.6.1 Resource Limits** | Populate resource table: RAM, GPU DRAM, memory bandwidth, PCIe, power, GPU cores, etc. | Source code, specs, benchmarks |
| **3.6.2 High Availability** | Describe HA approach or note "Not applicable" | Source code, specs |
| **3.6.3 Scalability** | Describe scalability approach | Source code, specs |
| **3.6.4 Future Work** | List planned improvements from Jira backlog, roadmap emails, meeting discussions | Jira backlog, emails, transcripts |

---

## Step 5 — Publish all three documents

Create SPP → SRD → SADD sequentially, each nested under the same parent page:

```bash
# Create SPP
confluence-cli page create "<Program Name> Software Project Plan" \
  "<populated XHTML content>" \
  --space <space-key> \
  --parent <parent-id> \
  --format xhtml \
  --json

# Create SRD
confluence-cli page create "<Program Name> Requirement Assessment and Documentation" \
  "<populated XHTML content>" \
  --space <space-key> \
  --parent <parent-id> \
  --format xhtml \
  --json

# Create SADD
confluence-cli page create "<Program Name> Design Assessment and Documentation" \
  "<populated XHTML content>" \
  --space <space-key> \
  --parent <parent-id> \
  --format xhtml \
  --json
```

**IMPORTANT:** If content is too long for a single CLI argument, write the XHTML to a temp file and use `cat` to pipe it:
```bash
cat /tmp/spp_content.xhtml | confluence-cli page create "<title>" - --space <key> --parent <id> --format xhtml --json
```

After each creation, extract the page ID from the JSON response and construct the URL.

Print a summary after all three are published:
```
SPP:  <url>
SRD:  <url>
SADD: <url>

All three PLC documents created under: <parent page url>
```

---

## Content Quality Rules

1. **Never leave placeholder text** — every `<Enter your text here>` must be replaced with real content or "Not applicable — [reason]"
2. **Cross-reference sources** — don't just dump Jira titles; synthesize into coherent prose
3. **Preserve XHTML structure** — keep all table column widths, highlight classes, macro tags intact
4. **Requirements must be traceable** — each REQ-N should map to a Jira epic/story where possible
5. **Use specific data** — include actual dates, team names, component names; avoid generic filler
6. **Security sections are mandatory** — even if minimal, describe the security posture
7. **Tables must have real rows** — don't leave empty placeholder rows; either populate or remove

---

## Example Requests

> "Create PLC docs for 'NNE TensorRT for RTX Plugin' in space LightspeedStudios, parent page 3178411842."

> "Set up PLC documents for 'Rendering Engine' in NVDRV under page 987654, repo https://github.com/nvidia/rendering-engine, Jira project REND."

> "Create PLC docs for 'FrameView SDK' in space LightspeedStudios, parent 123456. Source: gitlab.com/nvidia/frameview-sdk. Jira: FVSDK. Also search my emails for 'FrameView SDK requirements' and check NVBugs 4001234, 4001235."
