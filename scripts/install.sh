#!/bin/bash
# scripts/install.sh — NemoNet installer
#
# Two-phase setup (mirrors NetClaw pattern):
#   Phase 1: Install NemoClaw runtime from GitHub (not on npm yet)
#   Phase 2: Run NemoClaw onboard with NemoNet's blueprint + workspace
#
# Usage:
#   ./scripts/install.sh                    # Interactive setup
#   ./scripts/install.sh --profile lab      # Use lab profile
#   ./scripts/install.sh --non-interactive  # Headless (Launchable, CI)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
PROFILE="${PROFILE:-}"
NON_INTERACTIVE=""
NEMOCLAW_REPO="https://github.com/NVIDIA/NemoClaw.git"

# Parse args
while [[ $# -gt 0 ]]; do
  case $1 in
    --profile) PROFILE="$2"; shift 2 ;;
    --non-interactive) NON_INTERACTIVE="--non-interactive"; shift ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

echo "=== NemoNet Installer ==="
echo ""

# ── Phase 1: NemoClaw runtime ──────────────────────────────────────
echo "Phase 1: NemoClaw runtime"

if command -v nemoclaw &>/dev/null; then
  NCVER=$(nemoclaw --version 2>/dev/null || echo "unknown")
  echo "  NemoClaw ${NCVER} already installed"
else
  echo "  Installing NemoClaw from GitHub..."
  echo "  (NemoClaw is not yet published to npm — installing from source)"

  # Clone and install NemoClaw from GitHub
  NEMOCLAW_TMP="$(mktemp -d)"
  git clone --depth 1 "${NEMOCLAW_REPO}" "${NEMOCLAW_TMP}/NemoClaw"
  (cd "${NEMOCLAW_TMP}/NemoClaw" && npm install && npm link)
  rm -rf "$NEMOCLAW_TMP"

  echo "  NemoClaw $(nemoclaw --version 2>/dev/null || echo 'installed') ready"
fi

# ── Phase 2: NemoNet onboarding ────────────────────────────────────
echo ""
echo "Phase 2: NemoNet configuration"

# Build onboard command
ONBOARD_CMD="nemoclaw onboard"
ONBOARD_CMD+=" --blueprint ${REPO_ROOT}/blueprint/blueprint.yaml"
ONBOARD_CMD+=" --workspace ${REPO_ROOT}/workspace"

if [ -n "$PROFILE" ]; then
  ONBOARD_CMD+=" --profile ${PROFILE}"
fi

if [ -n "$NON_INTERACTIVE" ]; then
  ONBOARD_CMD+=" ${NON_INTERACTIVE}"
fi

echo "  Running: ${ONBOARD_CMD}"
eval "$ONBOARD_CMD"

# ── Phase 3: Install MCP server dependencies ──────────────────────
echo ""
echo "Phase 3: MCP servers"

for mcp_dir in "${REPO_ROOT}"/mcp-servers/*/; do
  if [ -f "${mcp_dir}/package.json" ]; then
    mcp_name=$(basename "$mcp_dir")
    echo "  Installing ${mcp_name}..."
    (cd "$mcp_dir" && npm install --production --silent)
  fi
done

echo ""
echo "=== NemoNet ready ==="
echo ""
echo "  Start:   nemoclaw start"
echo "  Status:  nemoclaw status"
echo "  Profile: ${PROFILE:-default}"
echo ""
