#!/bin/bash
# scripts/install.sh — NemoNet installer
#
# Setup phases:
#   Phase 0: Initialize git submodules (skills)
#   Phase 1: Install NemoClaw runtime from GitHub (not on npm yet)
#   Phase 2: Deploy openclaw.json (MCP server configuration)
#   Phase 3: Run NemoClaw onboard with NemoNet's blueprint + workspace
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
OPENCLAW_DIR="${HOME}/.openclaw"

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

# ── Phase 0: Git submodules (skills) ─────────────────────────────
echo "Phase 0: Skills (netsec-skills-suite)"

if [ -f "${REPO_ROOT}/.gitmodules" ]; then
  echo "  Initializing git submodules..."
  (cd "$REPO_ROOT" && git submodule update --init --recursive)
  SKILL_COUNT=$(ls -d "${REPO_ROOT}/workspace/skills/netsec-skills-suite/skills"/*/ 2>/dev/null | wc -l | tr -d ' ')
  echo "  ${SKILL_COUNT} skills loaded"
else
  echo "  No submodules configured — skipping"
fi

echo ""

# ── Phase 1: NemoClaw runtime ──────────────────────────────────────
echo "Phase 1: NemoClaw runtime"

if command -v nemoclaw &>/dev/null; then
  NCVER=$(nemoclaw --version 2>/dev/null || echo "unknown")
  echo "  NemoClaw ${NCVER} already installed"
else
  echo "  Installing NemoClaw from GitHub..."
  echo "  (NemoClaw is not yet published to npm — installing from source)"

  NEMOCLAW_TMP="$(mktemp -d)"
  git clone --depth 1 "${NEMOCLAW_REPO}" "${NEMOCLAW_TMP}/NemoClaw"
  (cd "${NEMOCLAW_TMP}/NemoClaw" && npm install && npm link)
  rm -rf "$NEMOCLAW_TMP"

  echo "  NemoClaw $(nemoclaw --version 2>/dev/null || echo 'installed') ready"
fi

# ── Phase 2: Deploy openclaw.json (MCP servers) ──────────────────
echo ""
echo "Phase 2: MCP server configuration"

mkdir -p "$OPENCLAW_DIR"

if [ -f "${OPENCLAW_DIR}/openclaw.json" ]; then
  echo "  Existing openclaw.json found — merging NemoNet MCP servers"
  # If jq is available, merge; otherwise warn and skip
  if command -v jq &>/dev/null; then
    # Merge NemoNet's mcpServers into existing config (NemoNet entries win on conflict)
    jq -s '.[0] * {mcpServers: (.[0].mcpServers // {} ) * .[1].mcpServers}' \
      "${OPENCLAW_DIR}/openclaw.json" \
      "${REPO_ROOT}/config/openclaw.json" > "${OPENCLAW_DIR}/openclaw.json.tmp"
    mv "${OPENCLAW_DIR}/openclaw.json.tmp" "${OPENCLAW_DIR}/openclaw.json"
    echo "  Merged successfully"
  else
    echo "  WARNING: jq not found — cannot merge. Back up existing and replace."
    cp "${OPENCLAW_DIR}/openclaw.json" "${OPENCLAW_DIR}/openclaw.json.bak"
    cp "${REPO_ROOT}/config/openclaw.json" "${OPENCLAW_DIR}/openclaw.json"
  fi
else
  cp "${REPO_ROOT}/config/openclaw.json" "${OPENCLAW_DIR}/openclaw.json"
  echo "  Deployed openclaw.json to ${OPENCLAW_DIR}/"
fi

# Count configured MCP servers
MCP_COUNT=$(grep -c '"command"\|"url"' "${OPENCLAW_DIR}/openclaw.json" || echo "0")
echo "  ${MCP_COUNT} MCP servers configured"

# ── Phase 3: NemoClaw onboard ─────────────────────────────────────
echo ""
echo "Phase 3: NemoClaw onboard"

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

echo ""
echo "=== NemoNet ready ==="
echo ""
echo "  Start:   nemoclaw start"
echo "  Status:  nemoclaw status"
echo "  Profile: ${PROFILE:-default}"
echo ""
echo "  MCP servers: ${MCP_COUNT} configured in ~/.openclaw/openclaw.json"
echo "  Skills:      ${SKILL_COUNT:-0} loaded from netsec-skills-suite"
echo ""
