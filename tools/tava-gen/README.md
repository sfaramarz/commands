# tava-gen

Generate TAVA (Threat and Vulnerability Analysis) architecture diagrams and documents from source code.

## What it does

1. **Assesses** whether a TAVA is required for your project by scanning the source for risk indicators (sensitive data, service deployments, etc.) — asks minimal questions
2. **Analyzes** the project source to build an architecture model (components, connections, protocols, trust boundaries)
3. **Generates** two TAVA 3.0 prerequisites:
   - **Architecture diagram** (Mermaid `.mmd`) — render to PNG/JPG for nSpect upload
   - **Architecture document** (Markdown `.md`) — convert to DOCX/PDF for nSpect upload

## Usage

```bash
# Full flow: assess → analyze → generate
tava-gen /path/to/project

# Skip assessment, generate directly
tava-gen /path/to/project --skip-assessment

# Only run the TAVA necessity assessment
tava-gen /path/to/project --assess-only

# Specify output directory
tava-gen /path/to/project -o ./my-tava-output
```

## Output

Files are written to `tava-output/` (or the directory specified with `-o`):

| File | Purpose |
|------|---------|
| `architecture.mmd` | Mermaid diagram — render with `mmdc -i architecture.mmd -o architecture.png` |
| `architecture.md` | Architecture document — convert with `pandoc architecture.md -o architecture.docx` |

## TAVA Process

After generating, follow the TAVA 3.0 process:

1. Review and refine the generated outputs
2. Render diagram to PNG/JPG
3. Upload diagram + document to nSpect
4. SecNeMo AI performs threat modeling (STRIDE)
5. Review and acknowledge the TAVA report

For export-controlled projects, use the manual TAVA 2.0 process instead.
