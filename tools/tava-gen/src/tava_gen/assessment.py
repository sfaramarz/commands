"""TAVA necessity assessment — automated with minimal user input.

Infers as much as possible from the source repository and documentation,
then asks only the questions that cannot be determined automatically.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Callable


class TavaVerdict(Enum):
    """Outcome of the TAVA necessity assessment."""

    REQUIRED_V3 = "required_v3"
    REQUIRED_V2_MANUAL = "required_v2_manual"
    REQUIRED_TARA = "required_tara"
    NOT_REQUIRED = "not_required"


@dataclass
class DetectedSignals:
    """Signals automatically detected from the project source."""

    has_database: bool = False
    has_auth: bool = False
    has_encryption: bool = False
    has_pii_patterns: bool = False
    has_financial_patterns: bool = False
    has_export_control_markers: bool = False
    has_dockerfile: bool = False
    has_ci_cd: bool = False
    has_external_apis: bool = False
    is_service: bool = False
    is_library: bool = False
    detected_frameworks: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)


@dataclass
class AssessmentResult:
    """Result of the TAVA necessity assessment."""

    verdict: TavaVerdict
    signals: DetectedSignals
    risk_category: str
    explanation: str

    @property
    def tava_required(self) -> bool:
        return self.verdict in (
            TavaVerdict.REQUIRED_V3,
            TavaVerdict.REQUIRED_V2_MANUAL,
            TavaVerdict.REQUIRED_TARA,
        )


# ---------------------------------------------------------------------------
# Automated signal detection
# ---------------------------------------------------------------------------

_SENSITIVE_DATA_PATTERNS = [
    (r"(?i)(password|secret|api[_-]?key|token|credential)", "auth/credentials"),
    (r"(?i)(ssn|social.security|date.of.birth|passport)", "PII"),
    (r"(?i)(credit.card|payment|billing|stripe|paypal)", "financial data"),
    (r"(?i)(encrypt|decrypt|aes|rsa|tls|ssl|certificate)", "encryption"),
    (r"(?i)(gdpr|hipaa|sox|pci[_-]?dss|compliance)", "compliance markers"),
    (r"(?i)(itar|ear|export.control|eccn|usml)", "export control"),
]

_SERVICE_INDICATORS = {
    "Dockerfile", "docker-compose.yml", "docker-compose.yaml",
    "compose.yml", "compose.yaml", "kubernetes", "k8s",
    "Procfile", "app.yaml", "serverless.yml",
}

_DB_PATTERNS = [
    r"(?i)(postgres|mysql|mongodb|sqlite|redis|dynamodb|cassandra)",
    r"(?i)(sqlalchemy|sequelize|prisma|mongoose|typeorm|diesel)",
    r"(?i)(CREATE\s+TABLE|SELECT\s+.+\s+FROM|INSERT\s+INTO)",
]

_WEB_FRAMEWORK_PATTERNS = [
    (r"(?i)(flask|fastapi|django|express|koa|spring|gin|actix|axum)", "web framework"),
    (r"(?i)(grpc|protobuf|graphql|rest.api|openapi|swagger)", "API framework"),
]


def detect_signals(project_path: str | Path) -> DetectedSignals:
    """Scan the project for TAVA-relevant signals."""
    root = Path(project_path).resolve()
    signals = DetectedSignals()
    scanned = 0
    max_files = 500  # limit scan scope

    scannable_extensions = {
        ".py", ".js", ".ts", ".go", ".java", ".rs", ".cpp", ".c", ".h",
        ".yaml", ".yml", ".toml", ".json", ".env", ".cfg", ".ini", ".md",
        ".txt", ".rst", ".dockerfile",
    }

    for dirpath, dirnames, filenames in os.walk(root):
        # Skip common non-source dirs
        dirnames[:] = [
            d for d in dirnames
            if d not in {"node_modules", ".git", "__pycache__", "venv", ".venv", "dist", "build"}
        ]

        for fname in filenames:
            if scanned >= max_files:
                break

            fpath = Path(dirpath) / fname

            # Check service indicators by filename
            if fname in _SERVICE_INDICATORS or fname.lower() == "dockerfile":
                signals.is_service = True
                signals.has_dockerfile = fname.lower().startswith("docker")
                signals.evidence.append(f"Service indicator: {fname}")

            if fname in (".gitlab-ci.yml", ".github", "Jenkinsfile", "azure-pipelines.yml"):
                signals.has_ci_cd = True

            # Only read scannable files
            if fpath.suffix.lower() not in scannable_extensions and fname.lower() != "dockerfile":
                continue

            try:
                text = fpath.read_text(errors="ignore")[:20_000]  # cap per-file
            except Exception:
                continue
            scanned += 1

            # Sensitive data patterns
            for pattern, category in _SENSITIVE_DATA_PATTERNS:
                if re.search(pattern, text):
                    if "PII" in category:
                        signals.has_pii_patterns = True
                    elif "financial" in category:
                        signals.has_financial_patterns = True
                    elif "export control" in category:
                        signals.has_export_control_markers = True
                    elif "auth" in category:
                        signals.has_auth = True
                    elif "encryption" in category:
                        signals.has_encryption = True
                    signals.evidence.append(f"{category} signal in {fpath.relative_to(root)}")

            # Database patterns
            for pattern in _DB_PATTERNS:
                if re.search(pattern, text):
                    signals.has_database = True
                    break

            # Web frameworks
            for pattern, category in _WEB_FRAMEWORK_PATTERNS:
                match = re.search(pattern, text)
                if match:
                    fw = match.group(1).lower()
                    if fw not in signals.detected_frameworks:
                        signals.detected_frameworks.append(fw)
                    signals.is_service = True

            # External API calls
            if re.search(r"https?://[^\s\"']+", text):
                signals.has_external_apis = True

    # Check for library-only (no service indicators)
    if not signals.is_service:
        for item in root.iterdir():
            if item.name in ("setup.py", "setup.cfg", "pyproject.toml", "package.json", "Cargo.toml"):
                signals.is_library = True
                break

    return signals


# ---------------------------------------------------------------------------
# Assessment logic — minimal questions
# ---------------------------------------------------------------------------

def _ask_yes_no(prompt: str, ask_fn: Callable[[str], str]) -> bool:
    """Ask a yes/no question."""
    while True:
        answer = ask_fn(f"{prompt} [y/n]: ").strip().lower()
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False
        ask_fn("  Please answer y or n.\n")


def run_assessment(
    project_path: str | Path,
    ask_fn: Callable[[str], str] | None = None,
) -> AssessmentResult:
    """Run the TAVA necessity assessment.

    Automatically scans the project for signals, then asks only the
    questions that cannot be inferred from the source.

    Parameters
    ----------
    project_path:
        Path to the project root to assess.
    ask_fn:
        Input function for the few remaining questions. Defaults to ``input``.
    """
    if ask_fn is None:
        ask_fn = input

    signals = detect_signals(project_path)

    print("\n── TAVA Necessity Assessment ──\n")
    print("Detected signals from source:")
    if signals.evidence:
        for ev in signals.evidence[:10]:
            print(f"  • {ev}")
        if len(signals.evidence) > 10:
            print(f"  ... and {len(signals.evidence) - 10} more")
    else:
        print("  (no notable signals detected)")

    has_sensitive = (
        signals.has_pii_patterns
        or signals.has_financial_patterns
        or signals.has_auth
        or signals.has_database
    )

    # --- Only ask what we can't infer ---

    # 1. If we found export-control markers, confirm
    if signals.has_export_control_markers:
        is_export = _ask_yes_no(
            "\nExport-control markers detected. Is this project export-controlled?",
            ask_fn,
        )
        if is_export:
            return AssessmentResult(
                verdict=TavaVerdict.REQUIRED_V2_MANUAL,
                signals=signals,
                risk_category="Sensitive Data (Export-Controlled)",
                explanation=(
                    "TAVA is REQUIRED (manual TAVA 2.0).\n"
                    "Export-controlled projects cannot use AI-assisted TAVA 3.0.\n"
                    "tava-gen will generate the diagram and document for the manual process."
                ),
            )

    # 2. If sensitive data detected, TAVA required
    if has_sensitive:
        return AssessmentResult(
            verdict=TavaVerdict.REQUIRED_V3,
            signals=signals,
            risk_category="Sensitive Data",
            explanation=(
                "TAVA is REQUIRED (nSpect AI-Powered TAVA 3.0).\n"
                "Sensitive data patterns detected in source.\n"
                "tava-gen will generate the architecture diagram and document."
            ),
        )

    # 3. If it's a deployable service, TAVA likely required
    if signals.is_service and signals.has_dockerfile:
        is_commercial = _ask_yes_no(
            "\nThis looks like a deployable service. Is it commercially released\n"
            "or a continuously running internal service?",
            ask_fn,
        )
        if is_commercial:
            return AssessmentResult(
                verdict=TavaVerdict.REQUIRED_V3,
                signals=signals,
                risk_category="Commercially Released / Live Service",
                explanation=(
                    "TAVA is REQUIRED (nSpect AI-Powered TAVA 3.0).\n"
                    "tava-gen will generate the architecture diagram and document."
                ),
            )

    # 4. Last resort — ask directly
    needs_tava = _ask_yes_no(
        "\nCould not auto-determine TAVA necessity.\n"
        "Does your project handle sensitive data, run as a live service,\n"
        "or get commercially released (enterprise-type)?",
        ask_fn,
    )

    if needs_tava:
        return AssessmentResult(
            verdict=TavaVerdict.REQUIRED_V3,
            signals=signals,
            risk_category="User-confirmed",
            explanation=(
                "TAVA is REQUIRED (nSpect AI-Powered TAVA 3.0).\n"
                "tava-gen will generate the architecture diagram and document."
            ),
        )

    return AssessmentResult(
        verdict=TavaVerdict.NOT_REQUIRED,
        signals=signals,
        risk_category="None",
        explanation="TAVA is NOT required based on analysis and your confirmation.",
    )


def print_result(result: AssessmentResult) -> None:
    """Print the assessment result to the terminal."""
    border = "─" * 50
    tag = "REQUIRED" if result.tava_required else "NOT REQUIRED"
    print(f"\n┌{border}┐")
    print(f"│ TAVA: {tag:<43}│")
    print(f"├{border}┤")
    for line in result.explanation.split("\n"):
        print(f"│ {line:<49}│")
    print(f"└{border}┘")
