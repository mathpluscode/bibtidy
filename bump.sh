#!/usr/bin/env bash
# Bump version across all files.
# Usage: ./bump.sh 1.2.0

set -euo pipefail

if [[ $# -ne 1 ]]; then
    echo "Usage: $0 <version>"
    exit 1
fi

VERSION="$1"
REPO_DIR="$(cd "$(dirname "$0")" && pwd)"

# pyproject.toml
sed -i '' "s/^version = \".*\"/version = \"$VERSION\"/" "$REPO_DIR/pyproject.toml"

# plugin.json
sed -i '' "s/\"version\": \".*\"/\"version\": \"$VERSION\"/" "$REPO_DIR/.claude-plugin/plugin.json"

# marketplace.json
sed -i '' "s/\"version\": \".*\"/\"version\": \"$VERSION\"/" "$REPO_DIR/.claude-plugin/marketplace.json"

echo "Bumped to $VERSION in:"
echo "  pyproject.toml"
echo "  .claude-plugin/plugin.json"
echo "  .claude-plugin/marketplace.json"
