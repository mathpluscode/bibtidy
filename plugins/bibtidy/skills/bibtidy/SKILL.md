---
name: bibtidy
description: Use when the user wants to validate, check, or fix a BibTeX (.bib) reference file — wrong authors, stale arXiv preprints, incorrect metadata, duplicate entries, formatting issues
---

Validate and fix the BibTeX file at: $ARGUMENTS

If `$ARGUMENTS` is empty or the file does not exist, tell the user:
"Usage: /bibtidy <path-to-file.bib>"

You are a meticulous academic reference checker. Process the .bib file entry by entry, verifying each against external sources and fixing errors in-place.

## Quick Reference

| Tool | Command |
|------|---------|
| CrossRef DOI lookup | `python3 $TOOLS_DIR/crossref.py doi <DOI>` |
| CrossRef title search | `python3 $TOOLS_DIR/crossref.py search "<title>"` |
| Duplicate detection | `python3 $TOOLS_DIR/duplicates.py <file.bib>` |
| Format validation | `python3 $TOOLS_DIR/fmt.py <orig.bib> <modified.bib>` |
| Web verification | WebSearch tool (preferred) or CrossRef scripts (fallback) |

## Script Path Resolution

All bundled tools live in the `tools/` directory next to this SKILL.md. Before running any tool, resolve the absolute path once:

```
TOOLS_DIR="$HOME/.claude/skills/bibtidy/tools"
if [ ! -f "$TOOLS_DIR/crossref.py" ]; then
  echo "Error: bibtidy tools not found. Reinstall the skill." >&2
  exit 1
fi
```

Use `$TOOLS_DIR` in every invocation.

## Output Format for Changed Entries

The Edit tool replacement text MUST contain all four parts in order:

```
% @<type>{<key>,
%   <original field 1>,
%   <original field 2>,
%   ...
% }
% bibtidy: source <URL>
% bibtidy: <what changed>
@<type>{<key>,
  <corrected field 1>,
  <corrected field 2>,
  ...
}
```

- **Part 1** — entire original entry, every line prefixed by `% `. All lines, not just the first.
- **Part 2** — `% bibtidy: source ` followed by a URL. Must be exactly `% bibtidy: source https://...`.
- **Part 3** — `% bibtidy: ` followed by explanation of what changed.
- **Part 4** — corrected entry.

For unchanged entries, do NOT add any comments or URLs.

## Workflow

1. Read the .bib file, note the file path
2. Back up for format validation: `cp <file>.bib <file>.bib.orig`
3. Preserve `@string`, `@preamble`, `@comment` blocks verbatim
4. Run duplicate detection
5. **Verify entries in parallel** — dispatch subagents to look up entries concurrently (see below)
6. Apply fixes **sequentially** via Edit tool — do NOT rewrite the entire file
7. Run format validation; fix violations and re-run until clean
8. Delete backup: `rm <file>.bib.orig`
9. Print summary: total entries, verified, fixed, needs manual review

## Parallel Verification with Subagents

Use the Agent tool to verify multiple entries concurrently. This dramatically reduces wall-clock time (e.g., 7 entries: ~1 min parallel vs ~5 min sequential; 100 entries: ~3 min vs ~40 min).

**Step 1 — Dispatch lookup agents:** For each entry (or batch of entries), launch a subagent that:
- Resolves `$TOOLS_DIR` (same command as above)
- Runs CrossRef lookup (`crossref.py doi` or `crossref.py search`)
- Optionally runs WebSearch for verification
- Returns a JSON summary: key, whether entry needs changes, what changed, source URL

Launch all agents in a single message so they run concurrently. Group into batches of ~10 if there are many entries.

**Step 2 — Collect results:** Read each agent's returned summary.

**Step 3 — Apply edits sequentially:** Using the lookup results, apply Edit tool changes one entry at a time. Edits MUST be sequential (parallel edits to the same file cause conflicts).

**Example agent prompt:**
```
Verify this BibTeX entry against CrossRef. Return ONLY valid JSON with no markdown formatting or conversational text. Keys: "key", "needs_fix" (bool), "fixes" (list of changes), "source_url", "corrected_fields" (dict).

TOOLS_DIR="$(dirname "$(find ~/.claude -path '*/skills/bibtidy/tools/crossref.py' -print -quit 2>/dev/null)")"

Entry:
@article{smith2020deep,
  title={Deep Learning for NLP},
  author={Smith, John},
  journal={arXiv preprint arXiv:2001.12345},
  year={2020}
}
```

## Duplicate Detection

```
python3 $TOOLS_DIR/duplicates.py <file.bib>
```

Returns JSON array of duplicate pairs (by key, DOI, title, or preprint+published). For each duplicate, add: `% bibtidy: DUPLICATE of <other_key> — consider removing`

## Per-Entry Checks

For each `@article`, `@inproceedings`, `@book`, etc.:

**1. Verify existence** — Search for `"<title>" <first author last name>`. If not found: `% bibtidy: NOT FOUND — verify manually`

**2. Cross-check metadata** — If DOI exists, fetch via `crossref.py doi <DOI>`. Otherwise `crossref.py search "<title>"`. Compare title, year, authors, journal, volume, pages.

**3. Check for published preprints** — If journal contains "arxiv"/"biorxiv"/"chemrxiv", search for published version. Update title, venue, year, volume, pages, entry type. Only update if confirmed via DOI or two independent sources.

**4. Apply fixes** — DOI URL prefix stripping, page hyphen fix (`-` → `--`), year whitespace, empty field removal, author corrections, venue/year/volume/pages corrections, preprint upgrades.

**Always apply the best-available fix.** If confidence is low (sources conflict, data incomplete, or only partial match), still apply the fix but add `% bibtidy: REVIEW — <reason>` explaining why it needs human attention.

## Saving Changes

- Use Edit tool for targeted replacements — not whole-file rewrites
- For large files (>30 entries), process in batches of ~15, reporting progress
- Verify entry count before and after — must match

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Missing `% bibtidy: source` URL | Every changed entry needs a source URL — use DOI URL or venue page |
| Incomplete commented original | Comment out ALL lines of the original, including closing `}` |
| Adding comments to unchanged entries | Only changed entries get bibtidy comments |
| Rewriting entire file | Use Edit tool for each entry individually |
| Deleting duplicate entries | Flag with comment only — never delete |
| Losing `@string`/`@preamble` blocks | Preserve verbatim, don't touch |
| Single hyphen in page ranges | Always use `--` (double hyphen) for BibTeX page ranges |

## Preserve

- Entry order, all unchanged fields, empty lines between entries
- User comments (`%` lines not starting with `% bibtidy:`)
- `@string`, `@preamble`, `@comment` blocks
- LaTeX macros and brace-protected capitalization in titles
- If rate-limited, note and continue with next entry
