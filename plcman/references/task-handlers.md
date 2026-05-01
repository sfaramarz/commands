# Task Handlers — Per-Type Playbooks

## Table of Contents

- [Common Setup](#common-setup) — nSpect auth, curl fallback, confluence-cli gotchas
- **Tier 1** — [artifact-registration](#artifact-registration) | [vuln-scan](#vuln-scan) | [release-contacts](#release-contacts) | [release-attributes](#release-attributes) | [export-compliance](#export-compliance) | [secret-scan](#secret-scan)
- **Tier 2** — [plc-documents](#plc-documents) | [threat-assessment](#threat-assessment) | [sast-scan](#sast-scan) | [oss-compliance](#oss-compliance) | [malware-scan](#malware-scan) | [product-legal](#product-legal) | [privacy-assessment](#privacy-assessment) | [tai-model-card](#tai-model-card) | [tai-classification](#tai-classification) | [tai-requirements](#tai-requirements)
- **Tier 3** — [training](#training) | [rcca](#rcca) | [security-review](#security-review) | [tai-test-results](#tai-test-results)
- **SKIP** — [exceptions-filed](#exceptions-filed) | [release-review](#release-review)

---

## Common Setup

### nSpect tool paths

```
NSPECT_TOOL="$HOME/.claude/commands/borrowed tools/nvsec-nspect/scripts/nspect_tool.py"
AUTH="$HOME/.claude/commands/borrowed tools/nvsec-nspect/scripts/auth.py"
```

All nSpect calls: `python3 $NSPECT_TOOL <METHOD> <PATH> [--data JSON]`

### nSpect curl fallback

`nspect_tool.py` can 404 due to Python redirect handling. Fall back to curl:

```bash
TOKEN=$(python3 $AUTH ensure-token)
curl -s "https://nspect.nvidia.com/pm/api/v1.0/public{path}" -H "Authorization: Bearer $TOKEN"
```

### confluence-cli gotchas

- `page create` has no `--space` flag — set `export CONFLUENCE_CLI_SPACE=<key>` instead
- `page create` has no `--file` flag — use `"$(cat /path/to/file.xhtml)"` as content argument
- Piping via stdin (`-`) silently produces an empty page — always use command substitution
- `page update` may be blocked in read-only mode — use `page create --update-if-exists` instead
- Search uses `--limit`, not `--max-results`

---

## Tier 1 — Auto-Verify

### artifact-registration

**API**: `GET /programs/{nspect_id}` + `GET /programs/{nspect_id}/programVersions/name/{version}`

**Pass**: Program + version exist, at least one artifact registered. Target Registration Health Score = 1000.

**Fail**: No artifacts → "Register containers/binaries/repos in nSpect. Target Registration Health Score = 1000."

**nSpect initiation check**: For new programs (no prior versions), verify nSpect was initiated during Planning. Flag late initiation as process gap.

**Evidence**: `https://nspect.nvidia.com/review?id={nspect_id}` + Health Score

---

### vuln-scan

**API**: `GET /programs/{nspect_id}/programVersions/{version}/vulns/counts`

**Pass**: Critical = 0, High = 0 (or all have approved VEX exceptions).

**Fail**: List C/H/M/L counts → "Remediate critical/high vulnerabilities or file VEX exceptions in nSpect Exception Tracker."

**Evidence**: Vuln counts + nSpect URL

---

### release-contacts

**API**: `GET /programs/{nspect_id}/members`

**Pass**: All required roles present — Owner, Risk Signatory, PLC Security PIC, QA Security PIC (if applicable).

**Role details**:
- **PLC Security PIC**: Assigned by Product Security. Drives PLC security tasks. 15-20% time commitment during release cycle.
- **QA Security PIC**: Ensures SRD security requirements are in test plans and results documented.
- **Risk Signatory**: BU VP or delegate for risk acceptance sign-off.

**Fail**: "Missing role(s): {roles}. Assign via nSpect. Contact Product Security if PLC Security PIC unassigned."

**Evidence**: Contact list from API

---

### release-attributes

**API**: `GET /programs/{nspect_id}/programVersions/name/{version}`

**Pass**: releaseType set, releaseDate set (for non-Internal), description populated.

**Fail**: "Missing: {fields}. Update version details in nSpect."

**Evidence**: Version metadata summary

---

### export-compliance

**Step 1 — Check nSpect first**: `GET /programs/{nspect_id}` — look for `export-compliance-bug` in the response metadata.
- If metadata shows an EC bug is linked (value is NOT "No export compliance bug linked to this program version.") → **PASS**. Evidence: nSpect EC status + `https://nspect.nvidia.com/export-compliance/bug?id={nspect_id}`
- Also check the program's Registration Health Score via `GET /programs/{nspect_id}/healthscore` — if EC component shows complete/1000, that's additional confirmation.

**Step 2 — Fallback search**: If nSpect metadata is inconclusive, search NVBugs (`nvbugs_search` for "export compliance {program_name}") and Jira (`summary ~ "export compliance"`).

**Pass**: EC bug linked in nSpect OR EC bug/ticket found in NVBugs/Jira.

**Lead time**: Minimum **2 business days**. Flag urgency if release within 1 week.

**Fail (not found)**: NVBugs MCP lacks create/clone. Post direct clone link:
- URL: `https://nvbugs.nvidia.com/NvBugs5/SWBug/CloneBug.aspx?BugID=4702316`
- Rename synopsis to: `{program_name} — Export Compliance MVSB Questionnaire`
- Link new NVBug back to PLC ticket
- Mark as show stopper

**Evidence**: nSpect EC metadata status, NVBugs ID, or Jira key

---

### secret-scan

**API**: `GET /programs/{nspect_id}/secrets`

**Response parsing**: The API returns secrets grouped by repo/branch. Each entry has metadata fields:
- `scan-complete`: `SUCCESS` means scan ran; anything else means scan incomplete
- `verified`: integer count of **verified (live) credentials** — only these block release
- Unverified and allowlisted secrets are excluded from pass/fail

**Pass**: `scan-complete` = `SUCCESS` AND `verified` = 0 across all repos/branches.

**Fail (verified > 0)**: "{count} verified secret(s) found. Rotate compromised credentials immediately, remove from source, rebuild, and re-scan. See nSpect secrets dashboard."

**Fail (scan incomplete)**: "Secret scan not completed. Trigger scan in nSpect → Program → Secrets."

**Ignore**: Unverified secrets (detected but not confirmed live) — do NOT count these as failures.

**Evidence**: Per-repo verified count + `https://nspect.nvidia.com/review?id={nspect_id}` (Secrets tab)

---

## Tier 2 — Check + Remediate

### plc-documents

**Check**: Search Confluence for `{program_name} Software Project Plan`, `Requirement Assessment`, and `Design Assessment`.

**All found**: PASS — link to each.

**Any missing**: Generate via `/plc-generators:plc-doc-gen` (with program name, space, parent page, repo, Jira key). Source code repo is required — if not provided in Step 0, ask for it now before generating. Without source code, SADD quality is severely degraded.

**Evidence**: Confluence page URLs for SPP, SRD, SADD

---

### threat-assessment

**API**: `GET /programs/{nspect_id}/version/{version}/tava/report`

If 404 from nspect_tool.py → use curl fallback. A 400 "Input payload validation failed" = no TAVA exists.

**TAVA exists**: PASS — link to report.

**TAVA missing**: Generate via `/plc-generators:tava-gen` (with program name, version, architecture, nSpect ID). Source code repo is required for quality output — if not provided in Step 0, ask for it now.

**After generation**, publish to Confluence:
1. Convert `~/Desktop/tava-output/architecture.md` to Confluence XHTML via Python
2. Add `<ac:image>` macro referencing `architecture.png` attachment
3. Create page:
   ```bash
   export CONFLUENCE_CLI_SPACE={space_key}
   confluence-cli page create "{program_name} Threat and Vulnerability Assessment" \
     "$(cat /c/tmp/tava_content.xhtml)" \
     --parent {parent_page_id} --format xhtml --update-if-exists --json
   ```
4. Attach files:
   ```bash
   confluence-cli attachment upload {page_id} ~/Desktop/tava-output/architecture.png
   confluence-cli attachment upload {page_id} ~/Desktop/tava-output/architecture.docx
   confluence-cli attachment upload {page_id} ~/Desktop/tava-output/architecture.mmd
   ```

**Evidence**: TAVA report URL or nSpect link + Confluence page URL

---

### sast-scan

**API**: `GET /programs/{nspect_id}/programVersions/{version}/static-analysis`

**Pass**: At least one SAST project associated AND latest scan completed with no critical/high findings (or exceptions filed).

**Two-ticket pattern**: SAST often has "Initiate" (configure) and "Execute" (run) tickets. If Execute depends on Initiate and Initiate is not done → mark Execute as blocked.

**Associated + scanned**: PASS — project names, scan date, finding counts.
**Associated + not scanned**: IN PROGRESS — "Run a scan and verify results in nSpect."
**None**: NEEDS ACTION — "Configure Coverity (C/C++) or SonarQube (other languages) in nSpect → Program Version → Static Analysis → Add Project."

**Evidence**: Static analysis project list + scan results

---

### oss-compliance

**Check**: Per container/binary artifact:
- `GET /programs/{nspect_id}/program-versions/{version}/container-images`
- `GET /programs/{nspect_id}/versions/{version}/binary-artifacts`

Check OSRB status on each.

**Pass**: All have OSRB approved or "Low Risk - Auto Approved".

**OSRB Needed**: Create OSRB ticket for those artifacts only. Link to PLC ticket. Comment: `OSS License OSRB review bug created — NVBug <id>`
**Pending**: IN PROGRESS — "Awaiting SWIPAT approval."
**SBOM correction needed**: "Allow up to 2 weeks."

**Evidence**: Per-artifact OSRB status

---

### malware-scan

**API**: `GET /programs/{nspect_id}/versions/{version}/binary-artifacts`

Check malware scan fields per binary (not container).

**Pass**: All binaries scan status = CLEAN.
**Suspicious/malicious**: FAIL — "Binary {name} flagged as {status}. Investigate and re-scan."
**Not scanned**: NEEDS ACTION — "Trigger malware scan in nSpect."

**Evidence**: Per-binary scan status

---

### product-legal

**API**: `GET /programs/{nspect_id}` + `GET /programs/{nspect_id}/programVersions/name/{version}`

**Lead times** (calculate days-to-release, flag if at risk):

| Artifact | Lead Time |
|---|---|
| Product Legal Support Form | **4 weeks** before release |
| Software Release Legal Tracker | **2 weeks** before release |
| Cloud Service Legal Tracker | **2 weeks** before release |
| Non-commercial NVBug | **2 weeks** for review |

**Action by release category**:
- **Internal only**: "Internal project — close as Not Applicable"
- **Non-commercial**: Clone NVBug 3508089 (`https://nvbugs.nvidia.com/NvBugs5/SWBug/CloneBug.aspx?BugID=3508089`). Contact: TechLicensing_Legal@exchange.nvidia.com
- **Open source**: Contact OSRB via NVBug 2885991 (`https://nvbugs.nvidia.com/NvBugs5/SWBug/CloneBug.aspx?BugID=2885991`). Include license type, repo URL, contribution scope.
- **Commercial model/container**: Initiate via nSpect → Actions → Legal (Model/Software tab).
- **Commercial software (other)**: Product Legal Support Form (4w) + Software Release Legal Tracker (2w). Comment with deadlines.
- **Cloud service**: Product Legal Support Form (4w) + Cloud Service Legal Tracker (2w). Comment with deadlines.

After commenting, schedule follow-up with legal assignee once Legal assigns a PIC.

**Evidence**: Release category + legal process + lead time assessment

---

### privacy-assessment

**API**: `GET /programs/{nspect_id}` — look for Personal Data field in Data Classification.

**No PII**: PASS — "No PII present per nSpect registration. Close as Not Applicable."

**Yes/Unknown → decision tree**:
1. Check ticket comments and prior version tickets for previous privacy review
2. Prior review exists + no new PII → "No new Personal Data. Prior review: {link}. Close as Done."
3. No prior review or new PII → NEEDS ACTION — "Tag Ade Adegboyega (aadegboyega@nvidia.com) and Alexander von Bruhl (alexvb@nvidia.com). Allow 14 business days."

**Evidence**: Personal Data classification + decision outcome

---

### tai-model-card

**Applies to**: AI/ML programs with model artifacts registered in nSpect.

**API**: `GET /programs/{nspect_id}` — check for AI Card section. Also check nSpect UI: `https://nspect.nvidia.com/actions/compliance/ai-card?id={nspect_id}`

**AI Card workflow stages**: In Development → Ready for Review → Completed Review: Team to Implement Updates → Approved, pending licensing → Approved → Released

**Check**:
1. Query nSpect program for AI Card status
2. If AI Card exists, check current workflow stage

**Pass**: AI Card status is "Approved" or "Released".

**In Progress**: AI Card exists but in earlier stage → comment with current stage and next steps for that stage.

**Needs Action (no AI Card)**:
1. "Create Model Card++ (MC++) via Model Card Generator: https://trustworthy-ai-product.nvidia.com/model-card-generator/"
2. "Submit MC++ via GitLab MR (required since Aug 1, 2025)"
3. "Share with Dina Yared (dyared@nvidia.com) for review"
4. "RACI: Responsible = Model PIC, Approves = Dina Yared & Michael Boone"

**Evidence**: nSpect AI Card URL + workflow stage

---

### tai-classification

**Applies to**: AI/ML programs requiring Trustworthy AI classification.

**Check**: Search Jira ticket description and comments for classification assessment completion evidence. Check nSpect program for TAI classification metadata.

**Pass**: Classification assessment completed and documented (link to assessment).

**Needs Action**: "Complete TAI Classification Assessment for this AI product. Determine risk tier (Tier 1–4) based on: (1) intended use, (2) data sensitivity, (3) autonomy level, (4) impact scope. Submit via nSpect AI Card section. Contact Trustworthy AI team if unsure about tier."

**Evidence**: Classification tier + assessment link

---

## Tier 3 — Report + Next Steps

### training

**Check**: Search ticket comments for completion evidence. Check nSpect members for Security Champion listing.

**Completed**: PASS — reference evidence.
**Not completed**: NEEDS ACTION — "Complete security champion training. Security Champions: 15-20% time commitment during release cycle. Resources: https://nvidia.atlassian.net/wiki/spaces/PRODSEC/pages/2569241545/Secure+Development"

**Evidence**: Training completion evidence or gap

---

### rcca

**Check**: Search Confluence for `{program_name} RCCA root cause corrective action`. Check nSpect for prior version findings.

**Prior RCCA exists**: PASS — link, verify it covers most recent release findings.
**Prior findings, no RCCA**: NEEDS ACTION — "Follow PSIRT RCCA Guide. Document: (1) root cause, (2) corrective actions, (3) preventive measures. Submit on Confluence and link here."
**No prior findings**: PASS — "No prior security findings. Close as N/A."

**Evidence**: RCCA link or N/A determination

---

### security-review

**Check**: Search NVBugs (`"security review {program_name}"`) and Jira (`summary ~ "security review"`). Check nSpect for Security PIC.

**Completed**: PASS — link to review.
**In progress**: IN PROGRESS — "PIC: {name}. Expected: {date}."
**Not found**: NEEDS ACTION — "PLC Security PIC to coordinate with Product Security. Review covers: architecture review, threat model validation, code review of security-critical paths, SRD security requirements verification."

**QA handoff**: If review complete, verify security test requirements handed off to QA Security PIC.

**Evidence**: Review bug/report + QA handoff status

---

### tai-requirements

**Applies to**: AI/ML programs with TAI Requirements Documentation tasks.

**Check**: Search ticket description and comments for requirements documentation evidence. Search Confluence for `{program_name} TAI requirements` or `AI requirements`.

**Completed**: PASS — link to requirements doc.
**Not found**: Generate SRD via `/plc-generators:plc-doc-gen` (with program name, space, parent page, repo, Jira key — SRD only). The SRD covers TAI requirements including intended use, training data provenance, evaluation metrics, fairness/bias considerations, and safety guardrails. Source code repo is required — if not provided in Step 0, ask for it now.

**Evidence**: SRD Confluence page URL or requirements doc link

---

### tai-test-results

**Applies to**: AI/ML programs with TAI Review Test Results tasks.

**Check**: Search ticket description and comments for test result review evidence. Check for linked test reports or evaluation summaries.

**Completed**: PASS — link to reviewed test results.
**Not found**: NEEDS ACTION — "Complete TAI test results review: (1) evaluate model performance against documented metrics, (2) review bias/fairness test outcomes, (3) verify safety guardrail effectiveness, (4) document any deviations from requirements. Attach results summary to this ticket."

**Evidence**: Test results review link or gap description

---

## SKIP — Special Handling

### exceptions-filed

Transition directly to "Not Applicable" via `jira_get_transitions` → `jira_transition_issue`. No comment needed.

**Risk Acceptance** (when open findings exist at release time):
1. File **Security Issue Form** in nSpect for each open finding
2. **Critical/High**: requires **Org3-level VP approval** (Risk Signatory)
3. **Medium/Low**: program owner approval
4. Accepted risks tracked with remediation timelines; expire at next release

Flag in handoff under "Show Stoppers" if Critical/High vulns exist and team wants to proceed.

---

### release-review

**DO NOT touch.** No comment, no transition. User initiates last after all other tasks pass.

In handoff report: "Pending — user to initiate after all other tasks pass."

**Release process** (for handoff reference):
1. **Create Release Review** — owner initiates in nSpect
2. **Security PIC Review** — verifies all MVSB tasks complete
3. **Risk Signatory Approval** — VP sign-off on open risks
4. **Release** — SRM finalizes or program self-releases (if eligible)

**Self-release eligibility**: Prior L1 + no open Critical/High + no new security-relevant changes → L0 attestation.
