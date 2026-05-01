---
name: plcman
version: 0.1.0
description: >-
  PLC task executor agent. Given a Jira PLC parent ticket key, reads all child
  tickets, classifies each by PLC task type (including TAI/Trustworthy AI tasks),
  runs automated checks against nSpect, Confluence, and NVBugs, generates missing
  documents (SPP/SRD/SADD via plc-doc-gen, TAVA via tava-gen), initiates legal
  processes, documents findings as minimal Jira comments, and produces a Word handoff
  report. Use when asked to "clear PLC", "progress PLC tickets", "run plcman",
  "check PLC status for TICKET", "what's left on PLC for TICKET", or
  "automate PLC for TICKET".
---

# plcman — PLC Task Executor

## Input

`$ARGUMENTS` — Jira parent PLC ticket key (e.g., `FVSDK-100`). Optional: `--nspect <NSPECT-XXXX-XXXX>`, `--kb <gitlab-url>`

## Overview

1. Gather context from user (Step 0)
2. Discover parent + children via Jira, resolve nSpect ID (Step 1)
3. Classify each child ticket by task type and tier (Step 2)
4. Execute checks per tier, remediate where possible (Step 3) — see [task-handlers.md](references/task-handlers.md)
5. Post one comment per ticket with findings (Step 4)
6. Generate Word handoff report (Step 5) — see [handoff-template.md](references/handoff-template.md)

## Step 0 — Gather Context

Ask the user **once** for everything needed. Present a single prompt combining all items below — never ask them one at a time:

> To run plcman on **{TICKET}**, I need a few things. Please provide what you have (skip any that don't apply):
> 1. **Source code repo** — GitLab/GitHub URL (required for SADD/TAVA quality)
> 2. **Program materials** — POR, specs, architecture docs, design docs, meeting notes
> 3. **Project KB repo** — GitLab/GitHub URL if one exists (optional, improves doc-gen)
> 4. **Known blockers** — any tickets needing special handling
>
> I'll auto-resolve: nSpect ID (from Jira `customfield_19907`), Confluence space (from existing PLC docs).
> I'll post findings as comments on each ticket and transition them out of Backlog. OK to proceed?

This is **one user interaction** — the user replies with their info + yes/no on commenting. If the user says just "go" or provides the ticket key only, proceed with auto-resolution and ask nothing further until commenting confirmation.

**Re-check runs**: If this is a 2nd+ pass (detected in Step 1.4), skip Step 0 entirely — reuse context from prior run. Go straight to discovery → classification → re-check execution.

**Auto-resolution** (no user input needed):
- **nSpect ID**: `--nspect` arg → `customfield_19907` on parent → description/labels → nSpect search. Only ask user if all fail.
- **Confluence space**: Search Confluence for existing `{program_name}` PLC documents. Extract space key from results. Only ask user if no existing docs found.

## Step 1 — Discovery

### 1.1 Fetch parent ticket

`mcp__maas-jira__jira_get_issue` → extract program name (from summary), version, nSpect ID (from description/labels), status. If the provided ticket is a child, detect parent via `issuelinks` and redirect.

### 1.2 Fetch all children

Try in order until results found:
1. `jira_search` with JQL `parent = <KEY>`
2. `jql="\"Epic Link\" = <KEY>"`
3. `jql="issue in linkedIssues(<KEY>, 'blocks')"`

Capture per child: `key`, `summary`, `status`, `description`, `assignee`, `priority`, `labels`, `comment` (all comments)

### 1.4 Detect Re-check Mode

After fetching children, check for existing `[plcman]` comments on any ticket. If found, this is a **re-check run** (2nd+ pass). Set `recheck = true` and store the prior plcman comment per ticket for comparison in Step 3.

### 1.3 Resolve nSpect ID

Priority: `--nspect` arg → Jira field `customfield_19907` ("nspect ID") on parent ticket → parent ticket description/labels (pattern `NSPECT-XXXX-XXXX`) → nSpect search by program name. Always request `customfield_19907` when fetching the parent ticket.

## Step 2 — Classification

Map each child ticket summary (case-insensitive) to a task type:

| Pattern | Task Type | Tier |
|---|---|---|
| `registration`, `register` | artifact-registration | 1 |
| `vulnerability`, `CVE`, `OSS vuln` | vuln-scan | 1 |
| `contacts`, `PLC Security PIC` | release-contacts | 1 |
| `release attributes` | release-attributes | 1 |
| `export compliance` | export-compliance | 1 |
| `secret scan`, `secret scanning`, `(SS)`, `credential` | secret-scan | 1 |
| `SPP`, `SRD`, `SADD`, `Software Project Plan`, `Requirements`, `Design` | plc-documents | 2 |
| `threat`, `TAVA` | threat-assessment | 2 |
| `SAST`, `static analysis`, `code scan` | sast-scan | 2 |
| `OSS license`, `SWIPAT`, `OSRB` | oss-compliance | 2 |
| `malware` | malware-scan | 2 |
| `Product Legal` | product-legal | 2 |
| `privacy`, `Privacy Assessment`, `PII` | privacy-assessment | 2 |
| `Model Card`, `MC++`, `Transparency Card`, `AI Card` | tai-model-card | 2 |
| `Classification Assessment`, `TAI Classification`, `AI Classification` | tai-classification | 2 |
| `Requirements Documentation`, `TAI Requirements` | tai-requirements | 2 |
| `Review Test Results`, `TAI Test` | tai-test-results | 3 |
| `Exceptions Filed`, `Approved by BU VP` | exceptions-filed | SKIP |
| `Release Review` | release-review | SKIP |
| `training`, `security champion` | training | 3 |
| `RCCA`, `root cause` | rcca | 3 |
| `security review` | security-review | 3 |

No match → `unknown` (Tier 3). Skip tickets already `Done`.

**Classification priority**: When a summary could match multiple patterns, prefer the most specific match. The `(SS)` prefix in Jira summaries always means Secret Scanning — never map it to export-compliance or any other type. If no pattern matches, classify as `unknown` (Tier 3) — never guess.

**Tiers**: 1 = auto-verify via nSpect, 2 = check + remediate, 3 = report + next steps, SKIP = special handling.

### L0 vs L1 Determination

After classification, determine release level:
- **L1 (Full)**: First release or security-relevant changes (new attack surface, dependencies, architecture, data collection). All MVSB tasks required.
- **L0 (Streamlined)**: Prior L1 completed, no security-relevant changes, all prior findings remediated. Can skip threat assessment and full security review, but must still complete: artifact registration, vuln scan, secret scan, SAST, OSS compliance, export compliance.

Check nSpect for prior versions. If none → L1. If prior versions exist → default to L0 unless ticket labels, description, or prior comments indicate security-relevant changes. Do not ask the user — infer from available data. User can override with `--l1` flag.

## Step 3 — Execution

Process Tier 1 → 2 → 3 → SKIP. For each ticket, follow the handler in [task-handlers.md](references/task-handlers.md).

### Re-check Logic (when `recheck = true`)

For each ticket that has a prior `[plcman]` comment:

1. **Read all comments** — both plcman's prior comment and any user/team comments posted after it
2. **Compare prior status vs current state**:
   - Re-run the handler's check (nSpect API, Confluence search, etc.) to get fresh data
   - Read user comments for evidence of completed work (e.g., "NVBug filed: 1234567", "OSRB approved", "scan completed", links to docs/reports)
3. **Determine outcome**:
   - **Prior NEEDS ACTION/FAIL → now passes** (API confirms or user comment provides evidence): Update status to PASS, recommend closing the ticket → "Requirement satisfied. Recommend transition to Done."
   - **Prior NEEDS ACTION/FAIL → user addressed but API not yet updated**: Status stays IN PROGRESS → "User action completed per comment. Awaiting nSpect/system update to confirm."
   - **Prior IN PROGRESS → now passes**: Same as above — recommend Done.
   - **Prior PASS → still passes**: Skip — no new comment needed.
   - **Prior status → still failing, no user action**: Post a follow-up comment with remaining actions. Reference the prior comment date.
4. **Comment format for re-check**:
   ```
   [plcman] PLC Re-check — <YYYY-MM-DD>

   Prior status (<prior-date>): <PRIOR-STATUS>
   Current status: PASS / FAIL / IN PROGRESS
   <What changed since last check>
   <If PASS: "Requirement satisfied. Recommend transition to Done.">
   <If still open: remaining actions>
   ```
5. **Transition recommendations**: When a ticket passes on re-check, suggest transitioning to Done (still requires user confirmation per rules). Batch all Done-ready tickets into a single recommendation at the end: "These tickets now pass and can be closed: {list}. Transition to Done?"

### nSpect Authentication

```bash
NSPECT_TOOL="$HOME/.claude/commands/borrowed tools/nvsec-nspect/scripts/nspect_tool.py"
AUTH="$HOME/.claude/commands/borrowed tools/nvsec-nspect/scripts/auth.py"
TOKEN=$(python3 $AUTH ensure-token); AUTH_EXIT=$?
```

Exit 0 = proceed, exit 2 = device code login. If `nspect_tool.py` returns 404, fall back to curl:
```bash
curl -s "https://nspect.nvidia.com/pm/api/v1.0/public{path}" -H "Authorization: Bearer $TOKEN"
```

## Step 4 — Documentation

**One comment per ticket.** Two only if remediation was performed and follow-up verification needed.

```
[plcman] PLC Review — <YYYY-MM-DD>

Status: PASS / FAIL / IN PROGRESS / NEEDS ACTION
Evidence: <nSpect URL, Confluence link, scan result>
<If action taken: what was done>
<If remaining work: specific next steps>
```

Add via `mcp__maas-jira__jira_update_issue` with `fields={"comment": {"add": {"body": "<text>"}}}`.

### Ticket Transitions

After commenting, transition out of Backlog: PASS/FAIL/IN PROGRESS/NEEDS ACTION → "In Progress", NOT APPLICABLE → "Not Applicable". Use `jira_get_transitions` first (IDs are workflow-specific). Never transition to Done without user confirmation. Never touch Release Review tickets.

## Step 5 — Handoff Report

Generate Word doc via `python-docx`. See [handoff-template.md](references/handoff-template.md). Save to `~/Desktop/plcman-<PROGRAM>-<DATE>.docx`.

After generating, attach the report to the parent ticket via Jira REST API:

```bash
source ~/.claude/jill/.env
curl -s -u "$JIRA_USERNAME:$JIRA_API_TOKEN" \
  -X POST -H "X-Atlassian-Token: no-check" \
  -F "file=@$HOME/Desktop/plcman-<PROGRAM>-<DATE>.docx" \
  "$JIRA_BASE_URL/rest/api/2/issue/<PARENT-KEY>/attachments"
```

## Rules

- Never post more than one comment per ticket per run (template clone link comments are separate)
- Never transition to Done without user confirmation
- Never touch Release Review tickets
- Never create OSRB tickets unless OSRB status confirms review is needed
- Never pipe content to `confluence-cli page create` via stdin — use `"$(cat file)"` command substitution
- Always load [task-handlers.md](references/task-handlers.md) before executing — never guess nSpect endpoints
- Always transition tickets out of Backlog after commenting
- Always provide direct clone links when NVBugs creation is needed (MCP lacks create/clone)
- Always publish TAVA artifacts to Confluence alongside other PLC documents
- Always calculate days-to-release and flag lead times at risk: Legal Support Form (4 weeks), Legal Tracker (2 weeks), export compliance (2 business days)
- Always flag Risk Acceptance path (Security Issue Form + Org3 VP approval) if Critical/High findings exist at release
- Never assume L0 without confirming prior L1 completion and no security-relevant changes
