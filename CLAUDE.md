# bibtidy

A Claude Code plugin that validates and fixes BibTeX files.

## Project structure

```
bibtidy/
├── .claude-plugin/
│   └── marketplace.json        ← marketplace catalog
├── plugins/
│   └── bibtidy/
│       ├── .claude-plugin/
│       │   └── plugin.json     ← plugin manifest
│       └── skills/
│           └── bibtidy/
│               ├── SKILL.md    ← the skill
│               └── tools/
│                   ├── crossref.py    ← CrossRef API client
│                   ├── duplicates.py  ← duplicate detector
│                   └── fmt.py         ← output format validator
├── tests/
│   ├── fixtures/
│   │   ├── input.bib           ← test input
│   │   └── expected.bib        ← expected output
│   ├── run.sh                  ← end-to-end test runner
│   ├── validate.py             ← structural validation
│   ├── conftest.py             ← pytest path setup
│   ├── test_crossref.py        ← unit tests for crossref.py
│   ├── test_duplicates.py      ← unit tests for duplicates.py
│   ├── test_fmt.py             ← unit tests for fmt.py
│   └── test_validate.py        ← unit tests for validate.py
├── pyproject.toml              ← project config and pytest settings
├── CLAUDE.md
├── LICENSE
└── README.md
```

## How it works

The skill is invoked via `/bibtidy refs.bib`. Claude reads the .bib file, dispatches parallel subagents to verify entries against Google Scholar (WebSearch) and CrossRef (bundled `crossref.py`), then applies fixes sequentially using targeted Edit tool replacements. Every change includes the original entry commented out and a source URL for verification.
