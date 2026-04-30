# PLC Top 5 Report Format Reference

## Report Structure

**Format:** Single-page table — NOT per-program sections with numbered lists.

The report is a single table with 6 columns: **Tool | Definition | Release Date | PLC Status | PIC | Notes / Pending**.

Programs are sorted: **Done → In Progress → To Start**.

```
Top 5 Things

Mission: Drive secure, compliant releases for NVIDIA's RTX developer tools
and UE plugins (and more) through structured PLC governance.

Dashboard contains live updates.

| Tool | Definition | Release Date | PLC Status | PIC | Notes / Pending |
|------|------------|--------------|------------|-----|-----------------|
| ...  | ...        | 2026-Q2      | Done       | ... | ...             |
| ...  | ...        | 2026-04-15   | In Progress| ... | ...             |
| ...  | ...        | TBD          | To Start   | ... | ...             |

Thanks,
Sherry Faramarz

Bcc: Jspitzer-staff, jpaul-org, GeForce-Devtech-Managers, DevStatus_UE,
Producers, Keita Iida, Jaakko Haapasalo, KLM, Alex Dunn, John Spitzer,
Jason Paul, Michael Songy, Nyle Usmani, Cem Cebenoyan
```

## Content Rules

- **PLC-only** — only PLC pillar progress, legal/security/SAST, nSpect, release review. No product bugs or dev backlog.
- **Done items → minimal/empty notes** — no need to elaborate on completed programs.
- **Notes: concise, single-line** — commas to separate items. No multi-line entries.
- **Include parent ticket ref** in Notes (e.g., LIGHTS-538, FVSDK-14).
- **PIC** — Person In Charge, pulled from the Jira assignee of the L1 PLC parent ticket.
- **Comfy NV Video Prep = RTX Remix** — merge into one row, never separate.
- **RTXPT** — use "RTXPT v1.8", never "v3.0 / v1.8".

## Known Tool Definitions (italic in table)

| Tool | Definition |
|---|---|
| RTXDI v3.0 | Efficient dynamic lighting via ReSTIR spatiotemporal resampling |
| NVRTX v5.7.x | NVIDIA-maintained UE branch for RTX feature prototyping |
| RTX Remix v1.x.x | AI-powered RTX remastering tool for classic games |
| FrameView v1.x.x | Frame time & GPU/CPU performance measurement tool |
| UE NNE Plugin | TensorRT AI/ML inference plugin for Unreal Engine |
| Kokoro Plugin v1.0 | Real-time AI text-to-speech for in-game use |
| Kokoro-82M Optimized v1.0 | Optimized AI text-to-speech model for real-time inference |
| RTXPT v1.8 | Open-source real-time path tracing SDK (DX12 / Vulkan) |
| UE DLSS v8.x.x | DLSS SR, FG, MFG, RR, DLAA & Reflex for Unreal Engine |
| IGI v1.x | SDK for on-device AI inference in games |
| MegaGeometry | Ray tracing for massive Nanite scenes with fine-grain LOD |
| RTXGI | Real-time ray traced global illumination SDK |
| Comfy NV Video Prep | ComfyUI AI remaster graph for RTX Remix asset prep |

## URL Patterns (hardcoded — never invent URLs)

| Resource | URL Pattern |
|---|---|
| Jira ticket | `https://jirasw.nvidia.com/browse/<key>` |
| PLC Dashboard | `https://jirasw.nvidia.com/secure/Dashboard.jspa?selectPageId=51845` |
| REL project | `https://jirasw.nvidia.com/projects/REL/issues/REL-23?filter=allopenissues` |
| LSS PLC L1 Filter | `labels = LSS-PLC-L1` (Jira filter ID 153065) |
| NVBug | `https://nvbugspro.nvidia.com/bug/<id>` |

## PLC Status Rules

| Condition | PLC Status |
|---|---|
| All pillars Done or Signed-off | **Done** |
| Any pillar In Progress / Under Review / Waiting | **In Progress** |
| All pillars in Backlog or To Do (nothing started) | **To Start** |

## Word Document Formatting Spec

### Layout
- **Title**: "Top 5 Things" — Heading 1, NVIDIA green (`#76B900`)
- **Mission**: bold label + italic text, 10pt
- **Dashboard**: bold+underline+dark blue link + italic text, 10pt
- **Sign-off**: "Thanks,\nSherry Faramarz" — 10pt
- **Bcc line**: italic, 8pt, grey (`#7F7F7F`)

### Table
- **Header row**: dark blue background (`#1F497D`), white bold text, 10pt, centered
- **Done rows**: light green background (`#E2F0D9`), green status text (`#008000`)
- **In Progress rows**: light yellow background (`#FFF2CC`), amber status text (`#BF8F00`)
- **To Start rows**: light grey background (`#F2F2F2`), grey status text (`#7F7F7F`)
- **Tool column**: bold, 10pt
- **Definition column**: italic, 10pt
- **Release Date column**: normal, 10pt, centered
- **PLC Status column**: bold, colored, centered, 10pt
- **PIC column**: 9pt normal
- **Notes column**: 9pt normal
- Column widths: Tool 3.0cm, Definition 4.2cm, Release Date 2.2cm, PLC Status 2.2cm, PIC 2.8cm, Notes 4.5cm

### Output
- Path: `C:/Users/sfaramarz/OneDrive - NVIDIA Corporation/Desktop/LSS_RTX_PLC_Top5_<YYYY-MM-DD>.docx`
- Margins: 0.75in top/bottom, 1in left/right
