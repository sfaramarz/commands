# FrameView Report Format Reference

## Report Structure

All generated reports must follow this exact structure:

```
**<Program Name> Tool Update — Status Report**

_Release <version>  |  Target: <release date>  |  As of <today's date>_

**Overall Status:** **<ON TRACK / AT RISK / OFF TRACK>**

<One-sentence executive summary of the current state, key risks, and notable decisions.>

**QA Bug Fix Status**

**Group 1 — <Theme>**

| Bug ID | Synopsis | Status | Engineer | Last Updated | Notes |
|---|---|---|---|---|---|
| [5XXXXXX](https://nvbugspro.nvidia.com/bug/5XXXXXX) | <synopsis> | **<status>** | <engineer> | <date> | <notes or blank> |

**Group 2 — <Theme>**
...repeat for each non-empty group...

**Release Infrastructure**

| Item | Status |
|---|---|
| PBR #<id> | ✅ Completed / 🔄 In Progress / ❌ Blocked |
| TMF #<id> | ✅ Completed / 🔄 In Progress |
| [FVSDK-XX](https://jirasw.nvidia.com/browse/FVSDK-XX) (<description>) | 🔄 <status summary> |

**<Program Name> Development**

<Summary of roadmap and next-version planning.>

**Planned Features**

- <feature>

Reference: [FV Jira Board](...), [PLC Dashboard](...), [FV Confluence Pages](...)

_Bcc: Jspitzer-staff, jpaul-org, GeForce-Devtech-Managers, DevStatus_UE, Producers,
Keita Iida, Jaakko Haapasalo, KLM, Alex Dunn, John spitzer, Jason Paul, Michael Songy,
Nyle Usmani, Cem Cebenoyan, frameview_devs_

Best Regards,
Sherry Faramarz
```

## URL Patterns (hardcoded — never invent URLs)

| Resource | URL Pattern |
|---|---|
| NVBug | `https://nvbugspro.nvidia.com/bug/<id>` |
| Jira ticket | `https://jirasw.nvidia.com/browse/<key>` |
| PBR | `https://pbrequest.nvidia.com/r/<id>` |
| TMF | `https://grt.nvidia.com/testrequests/<id>` |
| Jira Board | `https://jirasw.nvidia.com/secure/RapidBoard.jspa?rapidView=38830` |
| PLC Dashboard | `https://jirasw.nvidia.com/secure/Dashboard.jspa?selectPageId=51845` |
| REL project | `https://jirasw.nvidia.com/projects/REL/issues/REL-23?filter=allopenissues` |
| POR | `https://confluence.nvidia.com/pages/viewpage.action?spaceKey=LightspeedStudios&title=FrameView+v1.8.0+POR` |
| FV Roadmap | `https://nvidia.atlassian.net/wiki/spaces/LightspeedStudios/pages/3099169705/FrameView+Roadmap` |
| Meeting Notes | `https://nvidia.atlassian.net/wiki/spaces/LightspeedStudios/pages/2422210742/FrameView+Sync+Meeting+Notes` |
| FV Checklist | `https://nvidia.atlassian.net/wiki/spaces/LightspeedStudios/pages/2422211180/FrameView+Tool+v1.8.0+Checklist` |
| VPR/TMF N1X Test Plan | `https://docs.google.com/document/d/1QKYBdR_AiXcssOMPYgTbZt5RaX_Snr1XOLW_yPIGCTI/edit?tab=t.0` |

## Bug Grouping Rules

Group bugs by theme. Omit any group with no bugs. Sort within each group: P0 first, then by days open (descending).

| Group | Theme |
|---|---|
| Group 1 | Performance & Capture Accuracy |
| Group 2 | Crash / Stability |
| Group 3 | Overlay UI / Positioning |
| Group 4 | SDK / CPU Metrics (GR-3647 / FVSDK) |
| Group 5 | N1x / Yukon Platform |
| Group 6 | Other |

For the **Notes** column: use the most recent NVBugs comment or audit entry. Flag action items with ⚠.

## Release Infrastructure Rules

- PBR: ✅ = completed, 🔄 = in progress
- TMF: ✅ = completed/reviewed, 🔄 = in progress
- Jira release tasks: link each one, provide a one-line status summary
- Include security/compliance items (OSRB, vulnerability remediation)

## Word Document Formatting Spec

- **Title**: centered, NVIDIA green (`#76B900`), bold
- **Subtitle**: centered, italic, grey
- **Overall Status**: bold, color-coded — green (ON TRACK `#008000`), orange (AT RISK `#FF9900`), red (OFF TRACK `#CC0000`)
- **Bug tables**: dark grey (`#404040`) header row with white text, 9pt body, P0 bugs in red
- **Release Infrastructure**: compact 2-column table
- **Bcc line**: italic, 8pt, grey
- All tables use `Table Grid` style
