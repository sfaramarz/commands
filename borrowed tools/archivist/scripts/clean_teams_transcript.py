#!/usr/bin/env python3
"""
Clean a Teams DOCX meeting transcript into structured markdown.

Converts Microsoft Teams DOCX transcripts to clean markdown via pandoc,
then performs deterministic string processing to extract metadata and
format speaker turns. No LLM needed.

Input: Teams meeting recording DOCX file
Output: Clean markdown transcript with metadata header and formatted dialogue

Usage:
    python clean_teams_transcript.py <input.docx> <output.md>
"""

import argparse
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import NamedTuple


class SpeakerTurn(NamedTuple):
    """A single speaker turn extracted from the transcript."""
    speaker: str
    timestamp: str
    lines: list[str]


def run_pandoc(input_path: Path) -> str:
    """Run pandoc to convert DOCX to markdown."""
    try:
        result = subprocess.run(
            ['pandoc', '-f', 'docx', '-t', 'markdown', '--wrap=none', str(input_path)],
            capture_output=True, text=True, check=True
        )
    except FileNotFoundError:
        print("Error: pandoc not found. Install with: brew install pandoc", file=sys.stderr)
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"Error: pandoc failed: {e.stderr}", file=sys.stderr)
        sys.exit(1)
    return result.stdout


def unescape_pandoc(text: str) -> str:
    """Remove pandoc escape sequences."""
    text = text.replace("\\'", "'")
    text = text.replace("\\[", "[")
    text = text.replace("\\]", "]")
    text = text.replace("\\*", "*")
    text = text.replace("\\-", "-")
    text = text.replace("\\#", "#")
    text = text.replace("\\>", ">")
    text = text.replace("\\@", "@")
    return text


def parse_date_to_iso(date_str: str) -> str:
    """Convert 'February 13, 2026, 8:59PM' to '2026-02-13'."""
    date_str = date_str.strip()
    for fmt in ['%B %d, %Y, %I:%M%p', '%B %d, %Y, %I:%M %p',
                '%B %d, %Y, %I:%M:%S%p', '%B %d, %Y, %I:%M:%S %p']:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime('%Y-%m-%d')
        except ValueError:
            continue
    # Fallback: extract date portion only
    match = re.search(r'(\w+ \d+, \d{4})', date_str)
    if match:
        try:
            dt = datetime.strptime(match.group(1), '%B %d, %Y')
            return dt.strftime('%Y-%m-%d')
        except ValueError:
            pass
    return date_str


def parse_title(title_line: str, fallback_name: str = "") -> str:
    """
    Extract meeting title from pandoc header line.

    Input:  **\\[Claude Code\\] NvRTX Walk-Through-20260213_125901-Meeting Recording**
    Output: [Claude Code] NvRTX Walk-Through

    Falls back to fallback_name if the title is generic (e.g., just "Transcript").
    """
    # Strip bold markers
    title = title_line.strip().strip('*')
    # Unescape brackets
    title = unescape_pandoc(title)
    # Remove -YYYYMMDD_HHMMSS-Meeting Recording suffix
    title = re.sub(r'-\d{8}_\d{6}-Meeting Recording$', '', title)
    title = title.strip()
    # If title is generic, use the fallback (typically derived from filename)
    if title.lower() in ('transcript', 'meeting transcript', '') and fallback_name:
        return fallback_name
    return title


def parse_header(text: str, fallback_name: str = "") -> tuple[str, list[str]]:
    """
    Parse header block and return (header_info, remaining_lines).

    Header format (full):
        **\\[Title\\]-YYYYMMDD_HHMMSS-Meeting Recording**
        <blank>
        Month DD, YYYY, HH:MMAM/PM
        <blank>
        Xh Xm Xs

    Header format (minimal - just "Transcript" + date, no duration):
        **Transcript**
        <blank>
        Month DD, YYYY, HH:MMAM/PM
    """
    lines = text.split('\n')

    # Find first image line (marks end of header / start of turns)
    header_end = 0
    for i, line in enumerate(lines):
        if line.startswith('![](media/'):
            header_end = i
            break

    header_lines = lines[:header_end]
    remaining = lines[header_end:]

    # Extract non-empty header content lines
    content = [l.strip() for l in header_lines if l.strip()]

    title = parse_title(content[0], fallback_name=fallback_name) if content else fallback_name or "Untitled Meeting"
    date_str = content[1] if len(content) > 1 else ""
    duration = content[2] if len(content) > 2 else ""

    date_iso = parse_date_to_iso(date_str) if date_str else ""

    return {
        'title': title,
        'date': date_iso,
        'duration': duration,
    }, remaining


def parse_turns(lines: list[str]) -> list[SpeakerTurn]:
    """
    Parse speaker turns from pandoc output lines.

    Each turn starts with an image line followed by speaker name + timestamp.
    """
    turns = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # Look for image line that starts a speaker block
        if not line.startswith('![](media/'):
            i += 1
            continue

        # Image line found. Next line should be: SpeakerName** TIMESTAMP\ or marker
        i += 1
        if i >= len(lines):
            break

        speaker_line = lines[i]

        # Parse: "Speaker Name** TIMESTAMP\" or "Speaker Name** started/stopped transcription"
        # The ** closes the bold that opened on the image line
        match = re.match(r'^(.+?)\*\*\s+(.+)$', speaker_line)
        if match:
            speaker = match.group(1).strip()
            rest = match.group(2).rstrip('\\').strip()
        elif speaker_line.strip() == '**':
            # Empty speaker name - bold opened/closed with no name, on separate line
            # Timestamp is on the next line
            speaker = "Unknown"
            i += 1
            if i >= len(lines):
                break
            rest = lines[i].rstrip('\\').strip()
        elif re.match(r'^\d+:\d+', speaker_line.rstrip('\\')):
            # Bare timestamp line - empty speaker name was on the image line (**\**)
            speaker = "Unknown"
            rest = speaker_line.rstrip('\\').strip()
        else:
            i += 1
            continue

        # Skip start/stop transcription markers
        if rest in ('started transcription', 'stopped transcription'):
            i += 1
            continue

        # rest is the timestamp, possibly with trailing backslash already stripped
        timestamp = rest

        # Collect dialogue lines until next image line or EOF
        i += 1
        dialogue_lines = []
        while i < len(lines) and not lines[i].startswith('![](media/'):
            raw = lines[i]
            # Strip trailing backslash (pandoc line continuation)
            cleaned = raw.rstrip('\\').rstrip()
            if cleaned:  # skip blank lines within a turn
                dialogue_lines.append(unescape_pandoc(cleaned))
            i += 1

        turns.append(SpeakerTurn(
            speaker=speaker,
            timestamp=timestamp,
            lines=dialogue_lines
        ))

    return turns


def merge_consecutive_turns(turns: list[SpeakerTurn]) -> list[SpeakerTurn]:
    """Merge consecutive turns by the same speaker into single blocks."""
    if not turns:
        return []

    merged = [turns[0]]
    for turn in turns[1:]:
        if turn.speaker == merged[-1].speaker:
            # Same speaker - merge lines, keep earlier timestamp
            merged[-1] = SpeakerTurn(
                speaker=merged[-1].speaker,
                timestamp=merged[-1].timestamp,
                lines=merged[-1].lines + turn.lines
            )
        else:
            merged.append(turn)

    return merged


def format_timestamp(ts: str) -> str:
    """Wrap timestamp in brackets: '0:08' -> '[0:08]'."""
    return f"[{ts}]"


def collect_participants(turns: list[SpeakerTurn]) -> list[str]:
    """Collect unique speaker names in order of first appearance."""
    seen = set()
    participants = []
    for turn in turns:
        if turn.speaker not in seen:
            seen.add(turn.speaker)
            participants.append(turn.speaker)
    return participants


def format_output(header: dict, turns: list[SpeakerTurn]) -> str:
    """Format the final clean markdown output."""
    participants = collect_participants(turns)

    lines = [
        f"# {header['title']}",
        "",
        f"**Date:** {header['date']}",
    ]
    if header['duration']:
        lines.append(f"**Duration:** {header['duration']}")
    lines.extend([
        f"**Participants:** {', '.join(participants)}",
        "",
        "---",
        "",
        "## Transcript",
        "",
    ])

    for turn in turns:
        lines.append(f"**{turn.speaker}** {format_timestamp(turn.timestamp)}")
        for dialogue_line in turn.lines:
            lines.append(dialogue_line)
        lines.append("")

    return '\n'.join(lines)


def clean_teams_transcript(input_path: Path, output_path: Path) -> dict:
    """
    Full pipeline: DOCX -> pandoc -> parse -> clean -> write markdown.

    Returns stats dict for reporting.
    """
    # Step 1: Run pandoc
    raw_md = run_pandoc(input_path)

    # Step 2: Parse header (use filename as fallback title)
    fallback_name = input_path.stem  # filename without extension
    header, remaining_lines = parse_header(raw_md, fallback_name=fallback_name)

    # Step 3: Parse speaker turns
    raw_turns = parse_turns(remaining_lines)

    # Step 4: Merge consecutive same-speaker turns
    merged_turns = merge_consecutive_turns(raw_turns)

    # Step 5: Format output
    output = format_output(header, merged_turns)

    # Step 6: Write
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(output, encoding='utf-8')

    return {
        'output_path': output_path,
        'participants': len(collect_participants(merged_turns)),
        'raw_turns': len(raw_turns),
        'merged_turns': len(merged_turns),
        'turns_merged': len(raw_turns) - len(merged_turns),
    }


def main():
    parser = argparse.ArgumentParser(
        description='Clean a Teams DOCX meeting transcript into structured markdown.'
    )
    parser.add_argument(
        'input_file',
        type=Path,
        help='Path to the Teams DOCX transcript file'
    )
    parser.add_argument(
        'output_file',
        type=Path,
        help='Path for the output markdown file'
    )

    args = parser.parse_args()

    if not args.input_file.exists():
        print(f"Error: Input file not found: {args.input_file}", file=sys.stderr)
        sys.exit(1)

    stats = clean_teams_transcript(args.input_file, args.output_file)

    print(f"Converted: {stats['output_path']}")
    print(f"Participants: {stats['participants']}")
    print(f"Speaker turns: {stats['merged_turns']} (from {stats['raw_turns']} raw turns, {stats['turns_merged']} merged)")


if __name__ == '__main__':
    main()
