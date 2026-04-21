"""CLI entry point for tava-gen."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from tava_gen.assessment import run_assessment, print_result, TavaVerdict
from tava_gen.analyzer.code_parser import analyze_project
from tava_gen.analyzer.doc_enricher import enrich_from_sources
from tava_gen.generators.diagram import write_mermaid
from tava_gen.generators.document import write_document
from tava_gen.sources import collect_sources, SourceBundle


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="tava-gen",
        description="Generate TAVA architecture diagrams and documents from source code.",
    )
    parser.add_argument(
        "-o", "--output",
        default="tava-output",
        help="Output directory for generated files (default: tava-output).",
    )
    parser.add_argument(
        "--skip-assessment",
        action="store_true",
        help="Skip the TAVA necessity assessment and generate directly.",
    )
    parser.add_argument(
        "--assess-only",
        action="store_true",
        help="Only run the assessment, do not generate outputs.",
    )

    args = parser.parse_args(argv)
    output = Path(args.output)

    # --- Step 1: Collect sources ---
    print("Step 1: Collect sources")
    bundle = collect_sources()

    if not bundle.repo_path and not bundle.sources:
        print("Error: No sources provided. Need at least a repository path.", file=sys.stderr)
        return 1

    project = bundle.repo_path or Path(".").resolve()

    # --- Step 2: Assessment ---
    if not args.skip_assessment:
        print("\nStep 2: TAVA necessity assessment")
        result = run_assessment(project)
        print_result(result)

        if not result.tava_required:
            print("\nNo TAVA outputs needed. Exiting.")
            return 0

        if result.verdict == TavaVerdict.REQUIRED_V2_MANUAL:
            print(
                "\nNote: Export-controlled project — use TAVA 2.0 manual process."
                "\ntava-gen will still generate the diagram and document to assist."
            )

        if args.assess_only:
            return 0
    else:
        print("\nStep 2: Assessment skipped")

    # --- Step 3: Analyze ---
    print(f"\nStep 3: Analyzing sources ...")

    # Analyze source code
    model = analyze_project(project)
    print(f"  Code analysis: {len(model.components)} component(s), {len(model.connections)} connection(s)")

    # Enrich from documentation sources (Confluence, Slack, GRT)
    if bundle.sources:
        enrich_from_sources(model, bundle)
        print(f"  After enrichment: {len(model.components)} component(s), {len(model.connections)} connection(s)")

    # --- Step 4: Generate ---
    print(f"\nStep 4: Generating outputs ...")
    output.mkdir(parents=True, exist_ok=True)

    diagram_path = write_mermaid(model, output)
    print(f"  Diagram: {diagram_path}")

    doc_path = write_document(model, output)
    print(f"  Document: {doc_path}")

    print(f"\nDone. Outputs in: {output.resolve()}")
    print(
        "\nNext steps:"
        "\n  1. Review and refine the generated diagram and document."
        "\n  2. Render the .mmd diagram to PNG/JPG:"
        "\n     mmdc -i architecture.mmd -o architecture.png"
        "\n  3. Upload both to nSpect for TAVA 3.0 analysis."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
