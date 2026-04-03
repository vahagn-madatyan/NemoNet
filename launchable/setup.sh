#!/bin/bash
# launchable/setup.sh — NVIDIA Brev Launchable boot script
#
# Runs on VM creation. Installs all prerequisites, clones NemoNet,
# installs NemoClaw from GitHub, configures the sandbox, and starts it.
#
# Required env vars (set in Brev Console):
#   NVIDIA_API_KEY — for NVIDIA inference
#
# Optional env vars:
#   GITHUB_TOKEN       — for OpenShell binary download
#   SKIP_VLLM          — set to 1 to skip local inference server
#   MIST_API_TOKEN     — Juniper Mist MCP
#   ZSCALER_CLIENT_ID  — Zscaler MCP
#   PAN_API_KEY        — Palo Alto MCP

set -euo pipefail

echo "[NemoNet] Starting Launchable setup..."

# ── Node.js 22 ────────────────────────────────────────────────────
if ! command -v node &>/dev/null; then
  echo "[NemoNet] Installing Node.js 22..."
  curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
  sudo apt-get install -y nodejs
fi
echo "[NemoNet] Node.js $(node --version)"

# ── Python / uv (for MCP servers like Zscaler, nmap) ─────────────
if ! command -v uv &>/dev/null; then
  echo "[NemoNet] Installing uv..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi

# ── Docker ────────────────────────────────────────────────────────
if ! command -v docker &>/dev/null; then
  echo "[NemoNet] Installing Docker..."
  sudo apt-get update -qq
  sudo apt-get install -y docker.io
  sudo usermod -aG docker "$(whoami)"
fi

# ── NVIDIA Container Toolkit (if GPU present) ────────────────────
if command -v nvidia-smi &>/dev/null && ! command -v nvidia-container-toolkit &>/dev/null; then
  echo "[NemoNet] Installing NVIDIA Container Toolkit..."
  distribution=$(. /etc/os-release; echo "$ID$VERSION_ID")
  curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | \
    sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
  curl -s -L "https://nvidia.github.io/libnvidia-container/${distribution}/libnvidia-container.list" | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
  sudo apt-get update -qq
  sudo apt-get install -y nvidia-container-toolkit
  sudo nvidia-ctk runtime configure --runtime=docker
  sudo systemctl restart docker
fi

# ── OpenShell CLI ─────────────────────────────────────────────────
if ! command -v openshell &>/dev/null; then
  echo "[NemoNet] Installing OpenShell CLI..."
  ARCH=$(uname -m)
  case "$ARCH" in
    x86_64)  OS_ARCH="x86_64" ;;
    aarch64) OS_ARCH="aarch64" ;;
    arm64)   OS_ARCH="aarch64" ;;
    *) echo "Unsupported architecture: $ARCH"; exit 1 ;;
  esac
  OS_URL="https://github.com/NVIDIA/OpenShell/releases/latest/download/openshell-linux-${OS_ARCH}"
  sudo curl -fsSL -o /usr/local/bin/openshell "$OS_URL"
  sudo chmod +x /usr/local/bin/openshell
fi
echo "[NemoNet] OpenShell $(openshell --version 2>/dev/null || echo 'installed')"

# ── vLLM local inference (GPU only, optional) ────────────────────
if command -v nvidia-smi &>/dev/null && [ "${SKIP_VLLM:-0}" != "1" ]; then
  echo "[NemoNet] Starting local vLLM inference server..."
  docker run -d --gpus all \
    --name nemonet-vllm \
    -p 8000:8000 \
    vllm/vllm-openai:latest \
    --model nvidia/nemotron-3-nano-30b-a3b \
    --max-model-len 4096
  echo "[NemoNet] vLLM running on port 8000"
fi

# ── Clone NemoNet ─────────────────────────────────────────────────
cd /home/ubuntu
if [ ! -d "NemoNet" ]; then
  echo "[NemoNet] Cloning NemoNet..."
  git clone --recurse-submodules https://github.com/vahagn-madatyan/NemoNet.git
fi
cd NemoNet

# ── Run NemoNet installer ─────────────────────────────────────────
# This handles: git submodules, NemoClaw from GitHub, onboard, openclaw.json
echo "[NemoNet] Running installer..."
./scripts/install.sh --profile demo --non-interactive

# ── Start NemoClaw sandbox ────────────────────────────────────────
echo "[NemoNet] Starting sandbox..."
sg docker -c "nemoclaw start"

echo ""
echo "[NemoNet] ============================================"
echo "[NemoNet] Ready — access via Brev Secure Links"
echo "[NemoNet] ============================================"
echo ""
