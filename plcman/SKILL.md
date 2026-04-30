---
name: plcman
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

`$ARGUMENTS` — Jira parent PLC ticket key (e.g., `FVSDK-100`). Optional: `--nspect <NSPECT-XXXX-XXXX>`

## Overview

1. Gather context from user (Step 0)
2. Discover parent + children via Jira, resolve nSpect ID (Step 1)
3. Classify each child ticket by task type and tier (Step 2)
4. Execute checks per tier, remediate where possible (Step 3) — see [task-handlers.md](references/task-handlers.md)
5. Post one comment per ticket with findings (Step 4)
6. Generate Word handoff report (Step 5) — see [handoff-template.md](references/handoff-template.md)

## Step 0 — Gather Context

Ask the user for:
1. **Program materials** — POR, specs, architecture diagrams, design docs, meeting notes
2. **Source code repo** — GitHub/GitLab URL or local path
3. **nSpect ID** — if not in the Jira ticket or `--nspect` arg
4. **Confluence space** — where PLC documents live or should be published
5. **Known blockers** — tickets needing special handling
6. **Commenting authorization** — confirm before posting any Jira comments

## Step 1 — Discovery

### 1.1 Fetch parent ticket

`mcp__maas-jira__jira_get_issue` → extract program name (from summary), version, nSpect ID (from description/labels), status. If the provided ticket is a child, detect parent via `issuelinks` and redirect.

### 1.2 Fetch all children

Try in order until results found:
1. `jira_search` with JQL `parent = <KEY>`
2. `jql="\"Epic Link\" = <KEY>"`
3. `jql="issue in linkedIssues(<KEY>, 'blocks')"`

Capture per child: `key`, `summary`, `status`, `description`, `assignee`, `priority`, `labels`

### 1.3 Resolve nSpect ID

Priority: `--nspect` arg → user-provided → parent ticket description/labels (pattern `NSPECT-XXXX-XXXX`) → nSpect search by program name.

## Step 2 — Classification

Map each child ticket summary (case-insensitive) to a task type:

| Pattern | Task Type | Tier |
|---|---|---|
| `registration`, `register` | artifact-registration | 1 |
| `vulnerability`, `CVE`, `OSS vuln` | vuln-scan | 1 |
| `contacts`, `PLC Security PIC` | release-contacts | 1 |
| `release attributes` | release-attributes | 1 |
| `export compliance` | export-compliance | 1 |
| `secret scan`, `credential` | secret-scan | 1 |
| `SPP`, `SRD`, `SADD`, `Software Project Plan`, `Requirements`, `Design` | plc-documents | 2 |
| `threat`, `TAVA` | threat-assessment | 2 |
| `SAST`, `static analysis`, `code scan` | sast-scan | 2 |
| `OSS license`, `SWIPAT`, `OSRB` | oss-compliance | 2 |
| `malware` | malware-scan | 2 |
| `Product Legal` | product-legal | 2 |
| `privacy`, `Privacy Assessment`, `PII` | privacy-assessment | 2 |
| `Model Card`, `MC++`, `Transparency Card`, `AI Card` | tai-model-card | 2 |
| `Classification Assessment`, `TAI Classification`, `AI Classification` | tai-classification | 2 |
| `Requirements Documentation`, `TAI Requirements` | tai-requirements | 3 |
| `Review Test Results`, `TAI Test` | tai-test-results | 3 |
| `Exceptions Filed`, `Approved by BU VP` | exceptions-filed | SKIP |
| `Release Review` | release-review | SKIP |
| `training`, `security champion` | training | 3 |
| `RCCA`, `root cause` | rcca | 3 |
| `security review` | security-review | 3 |

No match → `unknown` (Tier 3). Skip tickets already `Done`.

**Tiers**: 1 = auto-verify via nSpect, 2 = check + remediate, 3 = report + next steps, SKIP = special handling.

### L0 vs L1 Determination

After classification, determine release level:
- **L1 (Full)**: First release or security-relevant changes (new attack surface, dependencies, architecture, data collection). All MVSB tasks required.
- **L0 (Streamlined)**: Prior L1 completed, no security-relevant changes, all prior findings remediated. Can skip threat assessment and full security review, but must still complete: artifact registration, vuln scan, secret scan, SAST, OSS compliance, export compliance.

Check nSpect for prior versions. If none → L1. If prior versions exist → ask user about security-relevant changes.

## Step 3 — Execution

Process Tier 1 → 2 → 3 → SKIP. For each ticket, follow the handler in [task-handlers.md](references/task-handlers.md).

### nSpect Authentication

```bash
NSPECT_TOOL="$HOME/.claude/commands/tools/nvsec-nspect/scripts/nspect_tool.py"
AUTH="$HOME/.claude/commands/tools/nvsec-nspect/scripts/auth.py"
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
