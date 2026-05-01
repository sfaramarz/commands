# Changelog

All notable changes to plcman will be documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0-alpha.1] — 2026-05-01

Initial prerelease. Core PLC automation workflow functional for L0 and L1 releases.

### Added

- 5-step execution workflow: discovery, classification, execution, documentation, handoff
- Jira integration: parent/child discovery, commenting, ticket transitions
- nSpect integration: artifact verification, vulnerability lookups, compliance checks
- Task classification engine mapping ticket summaries to 20+ PLC task types
- Tiered execution: Tier 1 (auto-verify), Tier 2 (check + remediate), Tier 3 (report)
- L0 vs L1 release determination with prior-version detection
- TAI/Trustworthy AI task handlers: model card, classification, requirements, test results
- Word handoff report generation via python-docx
- Confluence page publishing via confluence-cli
- NVBugs integration for clone link generation
- Jira attachment upload for handoff reports

### Dependencies

- MCP servers: maas-jira, maas-confluence, maas-nvbugs
- CLI tools: python-docx, requests, confluence-cli
- Borrowed tools: nvsec-nspect (auth + API scripts)
