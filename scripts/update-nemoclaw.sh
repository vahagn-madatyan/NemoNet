#!/bin/bash
# scripts/update-nemoclaw.sh — Update NemoClaw runtime to latest from GitHub
#
# NemoClaw is not yet published to npm, so this pulls latest from GitHub
# and reinstalls. Once NemoClaw is on npm, this becomes: npm update -g nemoclaw

set -euo pipefail

NEMOCLAW_REPO="https://github.com/NVIDIA/NemoClaw.git"

echo "Updating NemoClaw runtime from GitHub..."

NEMOCLAW_TMP="$(mktemp -d)"
git clone --depth 1 "${NEMOCLAW_REPO}" "${NEMOCLAW_TMP}/NemoClaw"
(cd "${NEMOCLAW_TMP}/NemoClaw" && npm install && npm link)
rm -rf "$NEMOCLAW_TMP"

echo "NemoClaw $(nemoclaw --version 2>/dev/null || echo 'updated') ready"
echo ""
echo "NemoNet workspace and blueprints are unaffected."
echo "Run 'git pull' in this repo to update NemoNet itself."
