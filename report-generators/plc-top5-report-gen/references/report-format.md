# PLC Top 5 Report Format Reference

## Report Structure

Title: **Top 5 Things - LSS RTX Kit/Tools PLC DD/MM/YYYY**

Single combined document — one section per program, separated by grey horizontal rules. Never separate files.

```
Top 5 Things - LSS RTX Kit/Tools PLC DD/MM/YYYY

─────────────────────────────────────────────────

**<Program / Tool Name>**

Release Date: <date from REL project>
Overall Status: <ON TRACK / AT RISK / OFF TRACK>

1. <Most important status item — achievement, risk, or blocker>
2. <Second item>
3. <Third item>
4. <Fourth item>
5. <Fifth item>

─────────────────────────────────────────────────
```

Each item is drawn from the **latest comment** on the Jira issue/epic. Flag blockers with ⚠.

## URL Patterns (hardcoded — never invent URLs)

| Resource | URL Pattern |
|---|---|
| Jira ticket | `https://jirasw.nvidia.com/browse/<key>` |
| PLC Dashboard | `https://jirasw.nvidia.com/secure/Dashboard.jspa?selectPageId=51845` |
| REL project | `https://jirasw.nvidia.com/projects/REL/issues/REL-23?filter=allopenissues` |
| NVBug | `https://nvbugspro.nvidia.com/bug/<id>` |

## Overall Status Rules

| Condition | Status |
|---|---|
| Any P0 open bug or release blocker | **OFF TRACK** |
| Any P1 open bug or risk item | **AT RISK** |
| All items on schedule, no blockers | **ON TRACK** |

## Word Document Formatting Spec

- **Title**: centered, NVIDIA green (`#76B900`), bold
- **Program name**: dark blue (`#1F497D`), Heading 1
- **Release Date / Overall Status**: bold labels, 10pt
- **Status**: color-coded — green (ON TRACK `#008000`), orange (AT RISK `#FF9900`), red (OFF TRACK `#CC0000`)
- **Top 5 items**: numbered list, 10pt; items starting with ⚠ shown in red (`#CC0000`)
- **Programs**: separated by grey (`#AAAAAA`) horizontal rule
- **Output**: `C:/Users/sfaramarz/Desktop/LSS_RTX_PLC_Top5_<YYYY-MM-DD>.docx`
