"""Architecture document generator.

Produces a Markdown architecture document from an ArchitectureModel,
suitable for TAVA 3.0 upload (can be converted to DOCX/PDF).

The document covers:
- Target of Evaluation (TOE) summary
- Component inventory
- Connection and dataflow descriptions
- Security-relevant observations
"""

from __future__ import annotations

from pathlib import Path

from tava_gen.model.architecture import ArchitectureModel, ComponentType


def generate_markdown(model: ArchitectureModel) -> str:
    """Generate a Markdown architecture document.

    Returns
    -------
    str
        Markdown text.
    """
    sections: list[str] = []

    # Title
    sections.append(f"# Architecture Document — {model.project_name}\n")

    # TOE Summary
    sections.append("## 1. Target of Evaluation (TOE)\n")
    sections.append(
        f"**Project:** {model.project_name}\n\n"
        f"{model.description}\n\n"
        f"This document describes the architecture of **{model.project_name}**, "
        f"including its components, connections, and dataflows. It is intended "
        f"as a supporting document for the TAVA threat and vulnerability analysis.\n"
    )

    # Components
    sections.append("## 2. System Components\n")
    sections.append(
        "| Component | Type | Description |\n"
        "|-----------|------|-------------|\n"
    )
    for comp in model.components:
        ctype = comp.component_type.value.replace("_", " ").title()
        desc = comp.description or "—"
        sections.append(f"| {comp.name} | {ctype} | {desc} |")
    sections.append("")

    # Component details
    for comp in model.components:
        sections.append(f"### 2.{model.components.index(comp) + 1}. {comp.name}\n")
        sections.append(f"- **Type:** {comp.component_type.value.replace('_', ' ').title()}")
        if comp.language:
            sections.append(f"- **Language:** {comp.language}")
        if comp.source_path:
            sections.append(f"- **Source:** `{comp.source_path}`")
        if comp.description:
            sections.append(f"- **Description:** {comp.description}")
        if comp.security_notes:
            sections.append("- **Security notes:**")
            for note in comp.security_notes:
                sections.append(f"  - {note}")
        sections.append("")

    # Connections
    sections.append("## 3. Connections and Dataflows\n")
    if model.connections:
        sections.append(
            "| Source | Target | Protocol | Description |\n"
            "|--------|--------|----------|-------------|\n"
        )
        for conn in model.connections:
            src = model.get_component(conn.source_id)
            tgt = model.get_component(conn.target_id)
            src_name = src.name if src else conn.source_id
            tgt_name = tgt.name if tgt else conn.target_id
            proto = conn.protocol or "—"
            desc = conn.description or "—"
            sections.append(f"| {src_name} | {tgt_name} | {proto} | {desc} |")
        sections.append("")
    else:
        sections.append("No inter-component connections detected.\n")

    # Trust Boundaries
    if model.trust_boundaries:
        sections.append("## 4. Trust Boundaries\n")
        for tb in model.trust_boundaries:
            comp_names = []
            for cid in tb.component_ids:
                c = model.get_component(cid)
                comp_names.append(c.name if c else cid)
            sections.append(f"### {tb.name}\n")
            if tb.description:
                sections.append(f"{tb.description}\n")
            sections.append(f"**Components:** {', '.join(comp_names)}\n")

    # Security Observations
    sections.append("## 5. Security Observations\n")
    observations: list[str] = []
    for comp in model.components:
        if comp.component_type == ComponentType.DATABASE:
            observations.append(
                f"- **{comp.name}**: Database component — review access controls, "
                f"encryption at rest, and backup procedures."
            )
        if comp.component_type == ComponentType.EXTERNAL_API:
            observations.append(
                f"- **{comp.name}**: External API dependency — review authentication, "
                f"data classification of exchanged data, and availability impact."
            )
        for note in comp.security_notes:
            observations.append(f"- **{comp.name}**: {note}")

    for conn in model.connections:
        if conn.is_encrypted is False:
            src = model.get_component(conn.source_id)
            tgt = model.get_component(conn.target_id)
            observations.append(
                f"- Connection {src.name if src else conn.source_id} → "
                f"{tgt.name if tgt else conn.target_id}: "
                f"not encrypted — review for data-in-transit protection."
            )

    if observations:
        sections.append("\n".join(observations) + "\n")
    else:
        sections.append(
            "No specific security concerns auto-detected. "
            "Manual review is recommended as part of the TAVA process.\n"
        )

    # Footer
    sections.append("---\n")
    sections.append(
        "*This document was generated by tava-gen. "
        "Review and update before submitting to nSpect for TAVA analysis.*\n"
    )

    return "\n".join(sections)


def write_document(model: ArchitectureModel, output_path: str | Path) -> Path:
    """Write the architecture document to a Markdown file.

    Parameters
    ----------
    model:
        The architecture model.
    output_path:
        Directory or file path. If a directory, writes ``architecture.md``.

    Returns
    -------
    Path
        Path to the written file.
    """
    out = Path(output_path)
    if out.is_dir():
        out = out / "architecture.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    content = generate_markdown(model)
    out.write_text(content, encoding="utf-8")
    return out
