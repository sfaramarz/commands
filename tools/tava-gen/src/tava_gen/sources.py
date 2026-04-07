"""Source intake — collect and fetch from all input sources.

Prompts the user for:
  1. Source code repository path
  2. Slack channel(s) for architecture/design discussions
  3. GRT (Game Ready Testing) link(s)
  4. Confluence page link(s) with design/architecture docs

Then fetches content from each source and returns a unified SourceBundle
that the analyzer uses to build a richer ArchitectureModel.
"""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable


@dataclass
class SourceContent:
    """Content fetched from a single source."""

    source_type: str  # "repo", "slack", "grt", "confluence"
    identifier: str   # path, channel name, URL, page ID
    text: str = ""
    metadata: dict = field(default_factory=dict)
    error: str = ""

    @property
    def ok(self) -> bool:
        return bool(self.text) and not self.error


@dataclass
class SourceBundle:
    """All collected sources for a TAVA generation run."""

    repo_path: Path | None = None
    sources: list[SourceContent] = field(default_factory=list)

    @property
    def confluence_sources(self) -> list[SourceContent]:
        return [s for s in self.sources if s.source_type == "confluence" and s.ok]

    @property
    def slack_sources(self) -> list[SourceContent]:
        return [s for s in self.sources if s.source_type == "slack" and s.ok]

    @property
    def grt_sources(self) -> list[SourceContent]:
        return [s for s in self.sources if s.source_type == "grt" and s.ok]

    @property
    def all_text(self) -> str:
        """Combined text from all successful sources."""
        parts = [s.text for s in self.sources if s.ok]
        return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------

def _run_cmd(cmd: list[str], timeout: int = 60) -> tuple[str, str]:
    """Run a shell command, return (stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout
        )
        return result.stdout.strip(), result.stderr.strip()
    except FileNotFoundError:
        return "", f"Command not found: {cmd[0]}"
    except subprocess.TimeoutExpired:
        return "", f"Command timed out after {timeout}s"
    except Exception as e:
        return "", str(e)


# ---------------------------------------------------------------------------
# Fetchers
# ---------------------------------------------------------------------------

def fetch_confluence_page(url: str) -> SourceContent:
    """Fetch a Confluence page by URL using confluence-cli."""
    # Extract page ID from URL
    page_id_match = re.search(r"/pages/(\d+)", url)
    if not page_id_match:
        return SourceContent(
            source_type="confluence",
            identifier=url,
            error=f"Could not extract page ID from URL: {url}",
        )

    page_id = page_id_match.group(1)
    stdout, stderr = _run_cmd(["confluence-cli", "page", "get", "--page-id", page_id])

    if stderr and not stdout:
        return SourceContent(
            source_type="confluence",
            identifier=url,
            error=f"confluence-cli error: {stderr}",
        )

    return SourceContent(
        source_type="confluence",
        identifier=url,
        text=stdout,
        metadata={"page_id": page_id},
    )


def fetch_slack_channel(channel: str) -> SourceContent:
    """Fetch recent messages from a Slack channel.

    Looks for architecture/design discussions in recent history.
    """
    # Normalize channel name
    channel = channel.lstrip("#").strip()

    # Try reading recent messages via slack-cli or teams-cli
    stdout, stderr = _run_cmd([
        "slack-cli", "channel", "history", channel, "--limit", "100",
    ])

    if stderr and not stdout:
        # Fall back: try glean search scoped to slack
        stdout, stderr = _run_cmd([
            "glean-cli", "search",
            f"architecture design {channel}",
            "--datasource", "slack",
            "--limit", "20",
        ])

    if stderr and not stdout:
        return SourceContent(
            source_type="slack",
            identifier=channel,
            error=f"Could not fetch Slack channel #{channel}: {stderr}",
        )

    return SourceContent(
        source_type="slack",
        identifier=channel,
        text=stdout,
        metadata={"channel": channel},
    )


def fetch_grt(url: str) -> SourceContent:
    """Fetch GRT (Game Ready Testing) data from a URL.

    GRT lives at grt.nvidia.com — we attempt to fetch via web or CLI.
    """
    # Try glean search for GRT content
    stdout, stderr = _run_cmd([
        "glean-cli", "search", url, "--limit", "10",
    ])

    if stdout:
        return SourceContent(
            source_type="grt",
            identifier=url,
            text=stdout,
            metadata={"url": url},
        )

    # Fall back to web fetch
    stdout, stderr = _run_cmd(["curl", "-sS", "-L", url])

    if stderr and not stdout:
        return SourceContent(
            source_type="grt",
            identifier=url,
            error=f"Could not fetch GRT link: {stderr}",
        )

    return SourceContent(
        source_type="grt",
        identifier=url,
        text=stdout,
        metadata={"url": url},
    )


# ---------------------------------------------------------------------------
# Interactive intake
# ---------------------------------------------------------------------------

def collect_sources(
    ask_fn: Callable[[str], str] | None = None,
) -> SourceBundle:
    """Interactively collect all source inputs from the user.

    Asks for each source type, fetches content, and returns a SourceBundle.

    Parameters
    ----------
    ask_fn:
        Input function. Defaults to ``input``.
    """
    if ask_fn is None:
        ask_fn = input

    bundle = SourceBundle()

    print("\n── Source Collection ──\n")
    print("Provide the sources for TAVA generation.")
    print("Press Enter to skip any source you don't have.\n")

    # 1. Source code repository
    repo = ask_fn("Source code repository path: ").strip()
    if repo:
        repo_path = Path(repo).expanduser().resolve()
        if repo_path.is_dir():
            bundle.repo_path = repo_path
            print(f"  -> Repo: {repo_path}")
        else:
            print(f"  -> Warning: {repo_path} is not a valid directory, skipping.")

    # 2. Confluence pages
    print("\nConfluence page URLs (design docs, architecture, SADD, SRD, PRD).")
    print("Enter one URL per line. Empty line to finish.")
    while True:
        url = ask_fn("  Confluence URL: ").strip()
        if not url:
            break
        print(f"  -> Fetching {url} ...")
        content = fetch_confluence_page(url)
        bundle.sources.append(content)
        if content.ok:
            print(f"     Fetched ({len(content.text)} chars)")
        else:
            print(f"     Error: {content.error}")

    # 3. Slack channels
    print("\nSlack channel(s) with architecture/design discussions.")
    print("Enter channel names (e.g., #my-project-arch). Empty line to finish.")
    while True:
        channel = ask_fn("  Slack channel: ").strip()
        if not channel:
            break
        print(f"  -> Fetching #{channel.lstrip('#')} ...")
        content = fetch_slack_channel(channel)
        bundle.sources.append(content)
        if content.ok:
            print(f"     Fetched ({len(content.text)} chars)")
        else:
            print(f"     Error: {content.error}")

    # 4. GRT links
    print("\nGRT (Game Ready Testing) links.")
    print("Enter URLs (e.g., https://grt.nvidia.com/...). Empty line to finish.")
    while True:
        url = ask_fn("  GRT URL: ").strip()
        if not url:
            break
        print(f"  -> Fetching {url} ...")
        content = fetch_grt(url)
        bundle.sources.append(content)
        if content.ok:
            print(f"     Fetched ({len(content.text)} chars)")
        else:
            print(f"     Error: {content.error}")

    # Summary
    ok_count = sum(1 for s in bundle.sources if s.ok)
    err_count = sum(1 for s in bundle.sources if s.error)
    print(f"\n── Sources collected: {ok_count} OK, {err_count} errors ──")
    if bundle.repo_path:
        print(f"   Repo: {bundle.repo_path}")
    for s in bundle.sources:
        status = "OK" if s.ok else f"FAILED ({s.error[:60]})"
        print(f"   [{s.source_type}] {s.identifier} — {status}")

    return bundle
