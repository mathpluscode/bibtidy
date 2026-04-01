#!/usr/bin/env python3
"""Validate bibtidy output format.

Checks that every changed entry follows the required format:
1. Original entry commented out (% prefix on every line, complete entry)
2. % bibtidy: source <URL> line present
3. Optional % bibtidy: crossref <URL> line present when CrossRef has a match
4. % bibtidy: <explanation> line present
5. Corrected entry follows

Also checks that unchanged entries have NO bibtidy comments.

Usage: python3 fmt.py <original.bib> <modified.bib>
  - Exit code 0 = all good, 1 = violations found.
"""

import re
import sys

from duplicates import ensure_brace_only_entries, remove_special_blocks


def parse_entries(text):
    """Extract non-commented @type{key, entries with nearby comment context."""
    ensure_brace_only_entries(text)
    entries = {}
    cleaned = remove_special_blocks(text)
    lines = text.split("\n")
    cleaned_lines = cleaned.split("\n")
    clean_lines = re.sub(r"\\[{}]", "", text).split("\n")

    i = 0
    while i < len(lines):
        match = re.match(r"^[ \t]*@\w+\{\s*([^,]+?)\s*,", cleaned_lines[i])
        if not match:
            i += 1
            continue

        key = match.group(1).strip()
        entry_start = i
        depth = clean_lines[i].count("{") - clean_lines[i].count("}")
        i += 1
        while i < len(lines) and depth > 0:
            depth += clean_lines[i].count("{") - clean_lines[i].count("}")
            i += 1

        entry_lines = lines[entry_start:i]

        context_start = entry_start - 1
        context_lines = []
        while context_start >= 0 and (lines[context_start].startswith("%") or lines[context_start].strip() == ""):
            context_lines.insert(0, lines[context_start])
            context_start -= 1

        entry_text = "\n".join(entry_lines)
        context_text = "\n".join(context_lines)
        entries[key] = {"entry": entry_text, "context": context_text, "full": "\n".join(context_lines + entry_lines)}

    return entries


def check_changed_entry(key, context):
    """Check that a changed entry has the required format."""
    errors = []

    # Check 1: commented-out original — must be a complete brace-delimited entry
    escaped_key = re.escape(key)
    has_open = re.search(rf"^%\s*@\w+\{{{escaped_key},", context, re.MULTILINE)
    if not has_open:
        errors.append("Missing commented-out original entry")
    elif not re.search(r"^%\s*\}$", context, re.MULTILINE):
        errors.append("Commented-out original appears incomplete (missing closing '% }' line)")

    # Check 2: % bibtidy: source <URL>
    if not re.search(r"^% bibtidy: source https?://", context, re.MULTILINE):
        errors.append('Missing "% bibtidy: source <URL>" line (found bare URL without prefix?)')

    # Check 3: optional % bibtidy: crossref <URL>
    crossref_lines = re.findall(r"^% bibtidy: crossref (.+)", context, re.MULTILINE)
    if any(not re.match(r"^https?://", line) for line in crossref_lines):
        errors.append('Malformed "% bibtidy: crossref <URL>" line')

    # Check 4: % bibtidy: <explanation>
    bibtidy_lines = re.findall(r"^% bibtidy: (?!source |crossref )(.+)", context, re.MULTILINE)
    if not bibtidy_lines:
        errors.append('Missing "% bibtidy: <explanation>" line')

    return errors


def main():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <original.bib> <modified.bib>")
        sys.exit(1)

    with open(sys.argv[1], encoding="utf-8") as f:
        original_text = f.read()
    with open(sys.argv[2], encoding="utf-8") as f:
        modified_text = f.read()

    try:
        modified_entries = parse_entries(modified_text)
        original_entries = parse_entries(original_text)
    except ValueError as exc:
        print(f"Error: {exc}")
        sys.exit(1)

    all_errors = []

    for key, data in modified_entries.items():
        context = data["context"]

        # Determine if entry was changed
        if key in original_entries:
            changed = original_entries[key]["entry"] != data["entry"]
        else:
            changed = True

        if changed:
            errors = check_changed_entry(key, context)
            for e in errors:
                all_errors.append(f"  [{key}] {e}")
        else:
            # Unchanged entries should have NO bibtidy comments
            # Exception: DUPLICATE flags are allowed on unchanged entries
            non_duplicate_comments = [
                line for line in context.split("\n") if re.match(r"^% bibtidy:", line) and "DUPLICATE" not in line
            ]
            if non_duplicate_comments:
                all_errors.append(f"  [{key}] Unchanged entry has bibtidy comments (should have none)")

    if all_errors:
        print("FORMAT VIOLATIONS FOUND:")
        for e in all_errors:
            print(e)
        print(f"\nTotal: {len(all_errors)} violation(s)")
        print("\nRequired format for changed entries:")
        print("  % @type{key,")
        print("  %   field={value},")
        print("  % }")
        print("  % bibtidy: source https://doi.org/...")
        print("  % bibtidy: crossref https://doi.org/...   # when CrossRef has a match")
        print("  % bibtidy: explanation of changes")
        print("  @type{key,")
        print("    field={corrected_value},")
        print("  }")
        sys.exit(1)
    else:
        print(f"Format OK — {len(modified_entries)} entries checked, no violations.")
        sys.exit(0)


if __name__ == "__main__":
    main()
