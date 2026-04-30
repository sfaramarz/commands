#!/usr/bin/env python3
"""
Safely clean processed files from the import/ directory.

Usage:
    python clean_import.py --import-dir <import-path> --processed <file1> <file2> ...
    python clean_import.py --import-dir <import-path> --processed-json <json-file>

Safety checks:
- Only removes files explicitly listed as processed
- Verifies each file exists in import/ before removing
- Skips files not found in import/ (already cleaned or wrong path)
- Never removes directories, hidden files, or files outside import/
- Reports what was removed, skipped, and any errors

The --processed-json option accepts a JSON file containing a list of filenames.
"""

import argparse
import json
import os
import sys
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(
        description="Safely clean processed files from import/"
    )
    parser.add_argument(
        "--import-dir",
        required=True,
        help="Path to the import/ directory"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--processed",
        nargs="+",
        help="List of filenames (not paths) that were successfully processed"
    )
    group.add_argument(
        "--processed-json",
        help="Path to JSON file containing list of processed filenames"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be removed without removing"
    )
    return parser.parse_args()


def main():
    args = parse_args()

    import_dir = Path(args.import_dir).resolve()

    if not import_dir.exists():
        print(json.dumps({
            "error": f"Import directory not found: {import_dir}",
            "removed": [],
            "skipped": [],
            "errors": []
        }))
        sys.exit(1)

    # Get list of processed filenames
    if args.processed_json:
        json_path = Path(args.processed_json)
        if not json_path.exists():
            print(json.dumps({
                "error": f"JSON file not found: {json_path}",
                "removed": [],
                "skipped": [],
                "errors": []
            }))
            sys.exit(1)
        with open(json_path) as f:
            processed = json.load(f)
        if not isinstance(processed, list):
            print(json.dumps({
                "error": "JSON file must contain a list of filenames",
                "removed": [],
                "skipped": [],
                "errors": []
            }))
            sys.exit(1)
    else:
        processed = args.processed

    removed = []
    skipped = []
    errors = []

    for filename in processed:
        # Safety: only bare filenames, no path traversal
        if os.sep in filename or filename.startswith('.'):
            skipped.append({
                "filename": filename,
                "reason": "Invalid filename (contains separator or starts with dot)"
            })
            continue

        filepath = import_dir / filename

        # Safety: ensure resolved path is within import_dir
        try:
            resolved = filepath.resolve()
            if not str(resolved).startswith(str(import_dir)):
                skipped.append({
                    "filename": filename,
                    "reason": "Path traversal detected"
                })
                continue
        except Exception as e:
            errors.append({
                "filename": filename,
                "error": f"Path resolution failed: {e}"
            })
            continue

        # Check file exists
        if not filepath.exists():
            skipped.append({
                "filename": filename,
                "reason": "File not found in import/"
            })
            continue

        # Safety: only remove files, not directories
        if not filepath.is_file():
            skipped.append({
                "filename": filename,
                "reason": "Not a file (directory or special)"
            })
            continue

        # Remove the file
        if args.dry_run:
            removed.append({
                "filename": filename,
                "action": "would_remove"
            })
        else:
            try:
                filepath.unlink()
                removed.append({
                    "filename": filename,
                    "action": "removed"
                })
            except Exception as e:
                errors.append({
                    "filename": filename,
                    "error": str(e)
                })

    result = {
        "import_dir": str(import_dir),
        "dry_run": args.dry_run,
        "removed": removed,
        "skipped": skipped,
        "errors": errors,
        "summary": {
            "total_processed": len(processed),
            "removed": len(removed),
            "skipped": len(skipped),
            "errors": len(errors)
        }
    }

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
