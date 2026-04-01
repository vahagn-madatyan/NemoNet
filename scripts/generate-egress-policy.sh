#!/bin/bash
# scripts/generate-egress-policy.sh
# Generates NemoNet egress policy YAML from manifest.json
#
# Usage: ./scripts/generate-egress-policy.sh [profile] > policy-fragment.yaml

set -euo pipefail

PROFILE="${1:-all}"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MANIFEST="${REPO_ROOT}/manifest.json"

if [ ! -f "$MANIFEST" ]; then
  echo "Error: manifest.json not found at ${MANIFEST}" >&2
  exit 1
fi

echo "# Auto-generated egress policy fragment"
echo "# Profile: ${PROFILE}"
echo "# Source: NemoNet manifest.json"
echo "# Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo ""

jq -r '
  .skills[]
  | select(.egressEndpoints | length > 0)
  | "# Skill: \(.name) (safety: \(.safetyTier))\n" +
    (.egressEndpoints | map("  - \"\(.)\"") | join("\n"))
' "$MANIFEST"
