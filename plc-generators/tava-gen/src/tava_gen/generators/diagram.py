"""Architecture diagram generator.

Produces Mermaid diagrams from an ArchitectureModel, suitable for
rendering to PNG/JPG for nSpect TAVA 3.0 upload.
"""

from __future__ import annotations

from pathlib import Path

from tava_gen.model.architecture import ArchitectureModel, ComponentType


# Mermaid shape mapping by component type
_SHAPES = {
    ComponentType.SERVICE: ("[", "]"),       # rectangle
    ComponentType.DATABASE: ("[(", ")]"),    # cylinder
    ComponentType.QUEUE: ("[[", "]]"),       # subroutine
    ComponentType.CACHE: ("[(", ")]"),       # cylinder
    ComponentType.EXTERNAL_API: ("((", "))"),  # circle
    ComponentType.GATEWAY: ("{{", "}}"),     # hexagon
    ComponentType.UI: ("[/", "\\]"),         # parallelogram
    ComponentType.STORAGE: ("[(", ")]"),     # cylinder
    ComponentType.LIBRARY: ["(", ")"],       # rounded
    ComponentType.UNKNOWN: ("[", "]"),
}


def generate_mermaid(model: ArchitectureModel) -> str:
    """Generate a Mermaid flowchart from the architecture model.

    Returns
    -------
    str
        Mermaid diagram source text.
    """
    lines: list[str] = ["flowchart TD"]

    # Trust boundaries as subgraphs
    bounded_ids: set[str] = set()
    for tb in model.trust_boundaries:
        lines.append(f"    subgraph {tb.id}[{tb.name}]")
        for cid in tb.component_ids:
            comp = model.get_component(cid)
            if comp:
                left, right = _SHAPES.get(comp.component_type, ("[", "]"))
                lines.append(f"        {comp.id}{left}{comp.name}{right}")
                bounded_ids.add(comp.id)
        lines.append("    end")

    # Unbounded components
    for comp in model.components:
        if comp.id not in bounded_ids:
            left, right = _SHAPES.get(comp.component_type, ("[", "]"))
            lines.append(f"    {comp.id}{left}{comp.name}{right}")

    # Connections
    for conn in model.connections:
        label = conn.protocol
        if conn.description and not conn.protocol:
            label = conn.description
        if label:
            lines.append(f"    {conn.source_id} -->|{label}| {conn.target_id}")
        else:
            lines.append(f"    {conn.source_id} --> {conn.target_id}")

    return "\n".join(lines)


def write_mermaid(model: ArchitectureModel, output_path: str | Path) -> Path:
    """Write the Mermaid diagram to a .mmd file.

    Parameters
    ----------
    model:
        The architecture model.
    output_path:
        Directory or file path. If a directory, writes ``architecture.mmd``.

    Returns
    -------
    Path
        Path to the written file.
    """
    out = Path(output_path)
    if out.is_dir():
        out = out / "architecture.mmd"
    out.parent.mkdir(parents=True, exist_ok=True)
    content = generate_mermaid(model)
    out.write_text(content, encoding="utf-8")
    return out
