#!/usr/bin/env python3
"""
Split a Slack transcript export into individual thread files.

This script parses Slack thread transcript files exported in the following format:
- File starts with "# Slack Thread Results"
- Threads separated by "---" (horizontal rules)
- Each thread has ## N. Title, metadata fields, and a Full Thread code block

Channel name is extracted from the export metadata section (## Export details → **Channel:** field)

Output: One markdown file per thread with naming convention:
    thread-YYYY-MM-DD[-HHMM].md

Supports incremental import: detects existing threads by Slack link URL identity,
skips identical threads, and updates threads that have gained new replies.

Usage:
    python split_slack_threads.py <input_file> <output_dir>
"""

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import NamedTuple


class SlackThread(NamedTuple):
    """Represents a parsed Slack thread."""
    number: int
    title: str
    author: str
    date: datetime
    summary: str
    resolved: str
    reactions: str | None
    link: str
    content: str


def extract_channel_from_content(content: str) -> str:
    """
    Extract channel name from the export metadata section.

    Looks for the **Channel:** field in the ## Export details section.
    Example: "- **Channel:** ct-lss-remix-rtx" -> "ct-lss-remix-rtx"
    """
    match = re.search(r'\*\*Channel:\*\*\s*(.+)', content)
    if match:
        return match.group(1).strip()

    raise ValueError("Could not extract channel name from file content (no **Channel:** field found)")


def parse_thread_metadata(block: str) -> dict:
    """
    Parse metadata fields from a thread block.

    Fields:
    - **Author:** value
    - **Date:** YYYY-MM-DD HH:MM
    - **Summary:** value (may be multi-line)
    - **Resolved:** value
    - **Reactions (N):** value (optional)
    - **Link:** [text](url)
    """
    metadata = {}

    # Extract author
    author_match = re.search(r'\*\*Author:\*\*\s*(.+)', block)
    if author_match:
        metadata['author'] = author_match.group(1).strip()

    # Extract date
    date_match = re.search(r'\*\*Date:\*\*\s*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})', block)
    if date_match:
        metadata['date_str'] = date_match.group(1).strip()
        try:
            metadata['date'] = datetime.strptime(metadata['date_str'], '%Y-%m-%d %H:%M')
        except ValueError:
            metadata['date'] = None

    # Extract summary (can be multi-line until next field)
    summary_match = re.search(
        r'\*\*Summary:\*\*\s*(.+?)(?=\n\*\*(?:Resolved|Reactions|Link):)',
        block,
        re.DOTALL
    )
    if summary_match:
        metadata['summary'] = summary_match.group(1).strip()

    # Extract resolved
    resolved_match = re.search(r'\*\*Resolved:\*\*\s*(.+)', block)
    if resolved_match:
        metadata['resolved'] = resolved_match.group(1).strip()

    # Extract reactions (optional field)
    reactions_match = re.search(r'\*\*Reactions\s*\(\d+\):\*\*\s*(.+)', block)
    if reactions_match:
        metadata['reactions'] = reactions_match.group(1).strip()

    # Extract link
    link_match = re.search(r'\*\*Link:\*\*\s*\[.+?\]\((.+?)\)', block)
    if link_match:
        metadata['link'] = link_match.group(1).strip()

    return metadata


def parse_thread_content(block: str) -> str:
    """Extract the Full Thread content from code block."""
    # Find content between ### Full Thread and the code block
    content_match = re.search(
        r'### Full Thread\s*\n+```\n?(.*?)\n?```',
        block,
        re.DOTALL
    )
    if content_match:
        return content_match.group(1).strip()
    return ""


def extract_link_from_file(filepath: Path) -> str | None:
    """
    Extract the Slack link URL from an existing thread file.

    Looks for a line matching: **Link:** <url>
    Returns the URL string or None if not found.
    """
    try:
        text = filepath.read_text(encoding='utf-8')
    except OSError:
        return None

    match = re.search(r'^\*\*Link:\*\*\s+(\S+)', text, re.MULTILINE)
    if match:
        return match.group(1).strip()
    return None


def scan_existing_threads(output_dir: Path) -> dict[str, Path]:
    """
    Scan existing thread files in output_dir and build a link-to-path map.

    Returns a dict mapping Slack link URL -> file path for all thread files
    that contain a **Link:** field.
    """
    link_map: dict[str, Path] = {}

    if not output_dir.exists():
        return link_map

    for filepath in sorted(output_dir.glob('thread-*.md')):
        link = extract_link_from_file(filepath)
        if link:
            link_map[link] = filepath

    return link_map


def count_transcript_messages(content: str) -> int:
    """
    Count message lines in a thread transcript.

    Counts lines that start with a timestamp pattern (YYYY-MM-DD HH:MM:SS)
    or a reply marker (Reply YYYY-MM-DD), which correspond to individual
    messages in the Slack thread.
    """
    count = 0
    for line in content.split('\n'):
        stripped = line.strip()
        # Match: YYYY-MM-DD HH:MM:SS (main messages and replies in transcript)
        if re.match(r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}', stripped):
            count += 1
        # Match: Reply YYYY-MM-DD (reply markers)
        elif re.match(r'Reply\s+\d{4}-\d{2}-\d{2}', stripped):
            count += 1
    return count


def extract_transcript_content(file_text: str) -> str:
    """Extract the transcript code block content from a thread file."""
    match = re.search(r'## Thread Transcript\s*\n+```\n?(.*?)\n?```', file_text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return ""


def parse_threads(content: str) -> list[SlackThread]:
    """
    Parse all threads from a Slack transcript file.

    Threads are separated by "---" (horizontal rules).
    Each thread starts with "## N. Title"
    """
    threads = []

    # Split by horizontal rules, keeping thread boundaries
    # The first split might be the header "# Slack Thread Results"
    blocks = re.split(r'\n---\n', content)

    for block in blocks:
        # Skip empty blocks
        if not block.strip():
            continue

        # If block starts with "# Slack Thread Results", strip that header
        # but continue processing (first thread may be in same block)
        if block.strip().startswith('# Slack Thread Results'):
            # Remove the header and continue with the rest
            block = re.sub(r'^#\s+Slack Thread Results\s*\n*', '', block.strip())
            if not block.strip():
                continue

        # Parse thread header: ## N. Title
        header_match = re.match(r'##\s+(\d+)\.\s+(.+)', block.strip())
        if not header_match:
            # This block might just be the header, skip it
            if '## ' not in block:
                continue
            # Try to find the header anywhere in the block
            header_match = re.search(r'##\s+(\d+)\.\s+(.+)', block)
            if not header_match:
                continue

        number = int(header_match.group(1))
        title = header_match.group(2).strip()

        # Parse metadata
        metadata = parse_thread_metadata(block)

        # Parse thread content
        thread_content = parse_thread_content(block)

        thread = SlackThread(
            number=number,
            title=title,
            author=metadata.get('author', 'Unknown'),
            date=metadata.get('date'),
            summary=metadata.get('summary', ''),
            resolved=metadata.get('resolved', 'unknown'),
            reactions=metadata.get('reactions'),
            link=metadata.get('link', ''),
            content=thread_content
        )
        threads.append(thread)

    return threads


def generate_thread_markdown(thread: SlackThread, channel: str) -> str:
    """Generate markdown content for a single thread file."""
    lines = [
        f"# {thread.title}",
        "",
        f"**Channel:** {channel}",
        f"**Author:** {thread.author}",
        f"**Date:** {thread.date.strftime('%Y-%m-%d %H:%M') if thread.date else 'Unknown'}",
        f"**Resolved:** {thread.resolved}",
    ]

    if thread.reactions:
        lines.append(f"**Reactions:** {thread.reactions}")

    if thread.link:
        lines.append(f"**Link:** {thread.link}")

    lines.extend([
        "",
        "## Summary",
        "",
        thread.summary,
        "",
        "## Thread Transcript",
        "",
        "```",
        thread.content,
        "```",
    ])

    return '\n'.join(lines)


def generate_filename(thread: SlackThread, existing_files: set[str]) -> str:
    """
    Generate a unique filename for the thread.

    Pattern: thread-YYYY-MM-DD[-HHMM].md
    Adds -HHMM suffix if date conflicts with existing file.
    Adds -N suffix if both date and time conflict.
    """
    if not thread.date:
        # Fallback for threads without parseable dates
        base = f"thread-unknown-{thread.number}"
        if f"{base}.md" not in existing_files:
            return f"{base}.md"
        return f"{base}-{thread.number}.md"

    date_str = thread.date.strftime('%Y-%m-%d')
    time_str = thread.date.strftime('%H%M')

    # Try date-only first
    base = f"thread-{date_str}"
    if f"{base}.md" not in existing_files:
        return f"{base}.md"

    # Try with time suffix
    base_with_time = f"thread-{date_str}-{time_str}"
    if f"{base_with_time}.md" not in existing_files:
        return f"{base_with_time}.md"

    # Add sequential suffix for same date+time
    counter = 1
    while f"{base_with_time}-{counter}.md" in existing_files:
        counter += 1
    return f"{base_with_time}-{counter}.md"


def split_slack_threads(input_file: Path, output_dir: Path, dry_run: bool = False) -> dict[str, list[Path]]:
    """
    Split a Slack transcript file into individual thread files.

    Supports incremental import: detects existing threads by Slack link URL,
    skips identical threads, and updates threads with new replies.

    Args:
        input_file: Path to the Slack transcript file
        output_dir: Directory to write thread files
        dry_run: If True, don't write files, just report what would be done

    Returns:
        Dict with keys 'created', 'updated', 'skipped' mapping to lists of paths
    """
    # Read input file
    content = input_file.read_text(encoding='utf-8')

    # Extract channel name from file metadata
    channel = extract_channel_from_content(content)

    # Parse threads
    threads = parse_threads(content)

    if not threads:
        print(f"No threads found in {input_file}", file=sys.stderr)
        return {'created': [], 'updated': [], 'skipped': []}

    # Scan existing threads for incremental import
    existing_map = scan_existing_threads(output_dir)

    # Create output directory if needed
    if not dry_run:
        output_dir.mkdir(parents=True, exist_ok=True)

    # Track filenames for collision detection (include existing files)
    created_files: set[str] = set()
    for path in existing_map.values():
        created_files.add(path.name)

    results: dict[str, list[Path]] = {'created': [], 'updated': [], 'skipped': []}

    for thread in threads:
        # Generate markdown content for the incoming thread
        markdown = generate_thread_markdown(thread, channel)
        import_msg_count = count_transcript_messages(thread.content)

        # Check if this thread already exists in the vault
        existing_path = existing_map.get(thread.link) if thread.link else None

        if existing_path is not None:
            # Thread exists - compare message counts to decide action
            existing_text = existing_path.read_text(encoding='utf-8')
            existing_transcript = extract_transcript_content(existing_text)
            existing_msg_count = count_transcript_messages(existing_transcript)

            if import_msg_count > existing_msg_count:
                # Import has more messages - update the existing file
                if dry_run:
                    print(f"Would update: {existing_path} ({existing_msg_count} → {import_msg_count} messages)")
                else:
                    existing_path.write_text(markdown, encoding='utf-8')
                    print(f"Updated: {existing_path} ({existing_msg_count} → {import_msg_count} messages)")
                results['updated'].append(existing_path)
            elif import_msg_count < existing_msg_count:
                # Import has fewer messages - skip with warning
                if dry_run:
                    print(f"Would skip (vault has more): {existing_path} (vault {existing_msg_count}, import {import_msg_count})")
                else:
                    print(f"Skipped (vault has more): {existing_path} (vault {existing_msg_count}, import {import_msg_count})")
                results['skipped'].append(existing_path)
            else:
                # Same message count - skip as identical
                if dry_run:
                    print(f"Would skip (identical): {existing_path}")
                else:
                    print(f"Skipped (identical): {existing_path}")
                results['skipped'].append(existing_path)
        else:
            # New thread - generate filename and create
            filename = generate_filename(thread, created_files)
            created_files.add(filename)
            output_path = output_dir / filename

            if dry_run:
                print(f"Would create: {output_path}")
            else:
                output_path.write_text(markdown, encoding='utf-8')
                print(f"Created: {output_path}")
            results['created'].append(output_path)

    return results


def main():
    parser = argparse.ArgumentParser(
        description='Split Slack transcript export into individual thread files.'
    )
    parser.add_argument(
        'input_file',
        type=Path,
        help='Path to the Slack transcript file'
    )
    parser.add_argument(
        'output_dir',
        type=Path,
        help='Directory to write thread files'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without writing files'
    )

    args = parser.parse_args()

    if not args.input_file.exists():
        print(f"Error: Input file not found: {args.input_file}", file=sys.stderr)
        sys.exit(1)

    results = split_slack_threads(args.input_file, args.output_dir, args.dry_run)

    n_created = len(results['created'])
    n_updated = len(results['updated'])
    n_skipped = len(results['skipped'])
    total = n_created + n_updated + n_skipped
    print(f"\nProcessed {total} threads: {n_created} new, {n_updated} updated, {n_skipped} skipped")


if __name__ == '__main__':
    main()
