#!/bin/bash
# scripts/install-mcps.sh — Install all MCP server dependencies
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

echo "Installing MCP server dependencies..."

for mcp_dir in "${REPO_ROOT}"/mcp-servers/*/; do
  if [ -f "${mcp_dir}/package.json" ]; then
    mcp_name=$(basename "$mcp_dir")
    echo "  ${mcp_name}..."
    (cd "$mcp_dir" && npm install --production --silent)
  fi
done

echo "Done."
