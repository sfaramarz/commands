# TAVA Process Reference

Quick reference for the TAVA (Threat and Vulnerability Analysis) process and nSpect TAVA 3.0 workflow.

---

## TAVA 3.0 Prerequisites

Before starting a TAVA 3.0 run in nSpect, you need:

1. **Architecture/dataflow diagram** — `.jpg`, `.jpeg`, `.png`, `.vsdx`, or Lucidchart
2. **Supporting documents** — `.PDF`, `.DOCX`, `.txt`, `.MD` describing the target of evaluation
3. **nSpect program** — target registered with at least one release version
4. **Training completed** — TAVA 3.0 training via NVLearn

## TAVA 3.0 Steps (in nSpect)

| Step | Action |
|------|--------|
| 1 | Upload architecture/dataflow diagram |
| 2 | Review and update detected connections |
| 3 | Upload architecture/design documents |
| 4 | Run threat and requirements analysis (~10-15 min) |
| 5 | View the generated TAVA report |
| 6 | Review and edit (mandatory — AI output must be verified) |
| 7 | Acknowledge or reject report (PLC Security PIC only) |
| 8 | Access acknowledged report |
| 9 | Risk mitigation — develop POA&M |

## TAVA 2.0 (Manual)

Use TAVA 2.0 when:
- Project is **export-controlled** (AI-assisted analysis not permitted)
- Cannot meet diagram/documentation prerequisites for TAVA 3.0

## Risk Analysis Logic (TAVA 3.0)

```
Attacker × Vulnerability Severity = Impact Likelihood
Attacker Motivation × Impact Likelihood = Threat Likelihood
Impact Level × Threat Likelihood = Initial Risk Level
Initial Risk Level − Mitigation Strength = Residual Risk Level
```

Mitigation Score: `(mitigated requirements / total requirements) × 100`

| Score | Strength |
|-------|----------|
| 0-29% | Very Low |
| 30-49% | Low |
| 50-69% | Moderate |
| 70-89% | High |
| 90-100% | Very High |

## Risk Mitigation Priority

| Risk Level | Action Required |
|------------|----------------|
| Very Low / Low | Implementation optional |
| Moderate | Must implement before release (or documented exception) |
| High / Very High | **Must** implement before release |

## Threat Modeling: STRIDE

| Letter | Threat | Property Violated |
|--------|--------|-------------------|
| S | Spoofing | Authenticity |
| T | Tampering | Integrity |
| R | Repudiation | Accountability |
| I | Information Disclosure | Confidentiality |
| D | Denial of Service | Availability |
| E | Elevation of Privilege | Authorization |

## Support

- nSpect support: `#securitytools-support` on Slack
- Security questions: `#ask-security` on Slack
- Bugs/features: `https://nv/sectools-feedback` (select TAVA SecNeMo component)
- Intake form: `https://nv/ProdSecArchForm`
