#!/usr/bin/env python3
"""Verify that all version strings across the project are in sync."""

import json
import os
import re

REPO_ROOT = os.path.join(os.path.dirname(__file__), "..")


def _read(relpath):
    with open(os.path.join(REPO_ROOT, relpath), encoding="utf-8") as f:
        return f.read()


def test_versions_match():
    # pyproject.toml
    m = re.search(r'^version\s*=\s*"([^"]+)"', _read("pyproject.toml"), re.MULTILINE)
    assert m, "Could not find version in pyproject.toml"
    pyproject_ver = m.group(1)

    # plugin.json
    plugin = json.loads(_read(".claude-plugin/plugin.json"))
    plugin_ver = plugin["version"]

    assert pyproject_ver == plugin_ver, f"pyproject.toml ({pyproject_ver}) != plugin.json ({plugin_ver})"

    # marketplace.json (version is optional — check if present)
    marketplace = json.loads(_read(".claude-plugin/marketplace.json"))
    marketplace_ver = marketplace["plugins"][0].get("version")
    if marketplace_ver is not None:
        assert pyproject_ver == marketplace_ver, (
            f"pyproject.toml ({pyproject_ver}) != marketplace.json ({marketplace_ver})"
        )
