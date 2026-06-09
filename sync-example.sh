#!/usr/bin/env bash
# sync-example.sh — copy the canonical example/ folder into docs/example/
# so GitHub Pages (which serves from docs/) can publish it.
#
# Run this whenever you regenerate the example output, then commit both copies.
#   ./sync-example.sh
#
# Why two copies: example/ is the tool's real output and lives at the repo root
# where it belongs. GitHub Pages serves the site from docs/, so the site needs
# its own published copy under docs/example/. This script keeps them identical.

set -euo pipefail
cd "$(dirname "$0")"

if [ ! -d example ]; then
  echo "Error: example/ not found at repo root." >&2
  exit 1
fi

rm -rf docs/example
cp -r example docs/example
echo "Synced example/ -> docs/example/"
