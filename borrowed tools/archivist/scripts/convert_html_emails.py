#!/usr/bin/env python3
"""
Convert HTML email files to clean markdown.

Usage:
    python convert_html_emails.py <input-dir> [--delete-originals] [--verbose]

Converts all .html files in the given directory to .md files using
archivist naming conventions, then optionally deletes the originals.
"""

import argparse
import html
import json
import os
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from typing import Optional


class HTMLToText(HTMLParser):
    """Simple HTML to text converter."""

    def __init__(self):
        super().__init__()
        self.result = []
        self.skip = False
        self.in_pre = False
        self.list_depth = 0

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag in ("style", "script", "head"):
            self.skip = True
        elif tag == "br":
            self.result.append("\n")
        elif tag in ("p", "div"):
            self.result.append("\n\n")
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            level = int(tag[1])
            self.result.append(f"\n\n{'#' * level} ")
        elif tag == "li":
            self.result.append("\n- ")
            self.list_depth += 1
        elif tag in ("ul", "ol"):
            self.result.append("\n")
        elif tag == "pre":
            self.in_pre = True
            self.result.append("\n```\n")
        elif tag == "a":
            href = dict(attrs).get("href", "")
            # Unwrap safelinks
            if "safelinks.protection.outlook.com" in href:
                m = re.search(r"url=([^&]+)", href)
                if m:
                    from urllib.parse import unquote
                    href = unquote(m.group(1))
            if href and not href.startswith("mailto:"):
                self.result.append(f"[")
        elif tag == "b" or tag == "strong":
            self.result.append("**")
        elif tag == "i" or tag == "em":
            self.result.append("*")
        elif tag == "hr":
            self.result.append("\n\n---\n\n")
        elif tag == "tr":
            self.result.append("\n")
        elif tag == "td" or tag == "th":
            self.result.append(" | ")
        elif tag == "img":
            # Skip images
            pass

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in ("style", "script", "head"):
            self.skip = False
        elif tag == "pre":
            self.in_pre = False
            self.result.append("\n```\n")
        elif tag == "a":
            self.result.append("]")
        elif tag == "b" or tag == "strong":
            self.result.append("**")
        elif tag == "i" or tag == "em":
            self.result.append("*")
        elif tag in ("ul", "ol"):
            self.list_depth = max(0, self.list_depth - 1)

    def handle_data(self, data):
        if self.skip:
            return
        if not self.in_pre:
            # Collapse whitespace
            data = re.sub(r"[ \t]+", " ", data)
        self.result.append(data)

    def handle_entityref(self, name):
        if not self.skip:
            self.result.append(html.unescape(f"&{name};"))

    def handle_charref(self, name):
        if not self.skip:
            self.result.append(html.unescape(f"&#{name};"))

    def get_text(self) -> str:
        return "".join(self.result)


def html_to_markdown(html_content: str) -> str:
    """Convert HTML to clean markdown text."""
    parser = HTMLToText()
    try:
        parser.feed(html_content)
    except Exception:
        # Fallback: strip tags with regex
        text = re.sub(r"<[^>]+>", " ", html_content)
        text = html.unescape(text)
        return text

    text = parser.get_text()

    # Clean up
    text = re.sub(r"\n{3,}", "\n\n", text)  # Collapse multiple newlines
    text = re.sub(r"[ \t]+\n", "\n", text)  # Trailing whitespace
    text = re.sub(r"\n[ \t]+\n", "\n\n", text)  # Whitespace-only lines
    text = text.strip()

    return text


def extract_email_metadata(html_content: str) -> dict:
    """Extract From, To, CC, Subject, Date from HTML email headers."""
    meta = {}

    # Try to extract from header div patterns
    # Pattern: "From: Name <email>" or similar in the HTML
    for field in ["From", "To", "Cc", "CC", "Subject", "Date", "Sent"]:
        # Look for field in text content
        pattern = rf"(?:^|\n)\s*{field}:\s*(.+?)(?:\n|$)"
        m = re.search(pattern, html_content, re.IGNORECASE)
        if m:
            val = re.sub(r"<[^>]+>", "", m.group(1)).strip()
            val = html.unescape(val)
            key = field.lower()
            if key == "cc":
                key = "cc"
            if key == "sent":
                key = "date"
            meta[key] = val

    # Extract subject from <title> if not found
    if "subject" not in meta:
        m = re.search(r"<title[^>]*>([^<]+)</title>", html_content, re.IGNORECASE)
        if m:
            meta["subject"] = html.unescape(m.group(1)).strip()

    return meta


def generate_filename(original_name: str) -> str:
    """Convert HTML filename to markdown filename using archivist conventions."""
    # Extract date from ISO timestamp in filename
    date_match = re.search(r"(\d{4})-(\d{2})-(\d{2})T", original_name)
    date_str = f"{date_match.group(1)}-{date_match.group(2)}-{date_match.group(3)}" if date_match else ""

    # Extract subject part (before the timestamp)
    subject_part = re.sub(r"-\d{4}-\d{2}-\d{2}T.*$", "", original_name)
    subject_part = re.sub(r"\.html$", "", subject_part, flags=re.IGNORECASE)

    # Strip Re_/RE_/FW_/Fwd_ prefixes
    subject_part = re.sub(r"^(?:Re_\s*|RE_\s*|FW_\s*|Fwd_\s*)+", "", subject_part)
    # Also strip parenthetical prefixes like "(_internal_) RE_"
    subject_part = re.sub(r"^\(_[^)]*\)\s*(?:RE_\s*|Re_\s*)?", "", subject_part)

    # Convert to kebab-case
    slug = subject_part.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")

    # Trim to ~50 chars at word boundary
    if len(slug) > 50:
        slug = slug[:50]
        last_dash = slug.rfind("-")
        if last_dash > 30:
            slug = slug[:last_dash]

    if date_str:
        return f"{slug}-{date_str}.md"
    return f"{slug}.md"


def convert_file(html_path: Path, verbose: bool) -> Optional[dict]:
    """Convert a single HTML email to markdown. Returns info dict or None on failure."""
    try:
        content = html_path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return {"error": str(e), "source": html_path.name}

    # Extract metadata from HTML
    meta = extract_email_metadata(content)

    # Convert body to markdown
    body = html_to_markdown(content)

    # Generate output filename
    md_name = generate_filename(html_path.name)
    md_path = html_path.parent / md_name

    # Build output
    subject = meta.get("subject", html_path.stem.split("-20")[0].replace("_", " "))
    # Clean subject of Re:/FW: for heading
    clean_subject = re.sub(r"^(?:Re:\s*|RE:\s*|FW:\s*|Fwd:\s*)+", "", subject).strip()

    date_match = re.search(r"(\d{4}-\d{2}-\d{2})", html_path.name)
    date_str = date_match.group(1) if date_match else ""

    lines = []
    lines.append(f"# {clean_subject}")
    lines.append("")
    lines.append(f"**Type:** Email Thread")
    lines.append(f"**Date:** {date_str}")
    if meta.get("from"):
        lines.append(f"**From:** {meta['from']}")
    if meta.get("to"):
        lines.append(f"**To:** {meta['to']}")
    if meta.get("cc"):
        lines.append(f"**CC:** {meta['cc']}")
    lines.append(f"**Subject:** {subject}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(body)
    lines.append("")

    output = "\n".join(lines)

    # Write markdown
    md_path.write_text(output, encoding="utf-8")

    return {
        "source": html_path.name,
        "output": md_name,
        "subject": subject,
        "date": date_str,
        "size_html": len(content),
        "size_md": len(output),
    }


def main():
    parser = argparse.ArgumentParser(description="Convert HTML emails to markdown")
    parser.add_argument("input_dir", help="Directory containing HTML email files")
    parser.add_argument("--delete-originals", action="store_true",
                        help="Delete HTML files after successful conversion")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    input_dir = Path(args.input_dir).resolve()
    if not input_dir.exists():
        print(json.dumps({"error": f"Directory not found: {input_dir}"}))
        sys.exit(1)

    html_files = sorted(f for f in input_dir.iterdir() if f.suffix == ".html")
    if not html_files:
        print(json.dumps({"message": "No HTML files found", "converted": []}))
        return

    converted = []
    failed = []
    deleted = []

    for html_path in html_files:
        if args.verbose:
            print(f"[convert] {html_path.name}", file=sys.stderr)

        result = convert_file(html_path, args.verbose)
        if result and "error" not in result:
            converted.append(result)
            if args.delete_originals:
                try:
                    html_path.unlink()
                    deleted.append(html_path.name)
                except Exception as e:
                    failed.append({"file": html_path.name, "error": f"Delete failed: {e}"})
        else:
            failed.append(result or {"file": html_path.name, "error": "Unknown"})

    print(json.dumps({
        "input_dir": str(input_dir),
        "converted": converted,
        "deleted": deleted,
        "failed": failed,
        "summary": {
            "total_html": len(html_files),
            "converted": len(converted),
            "deleted": len(deleted),
            "failed": len(failed),
        }
    }, indent=2))


if __name__ == "__main__":
    main()
