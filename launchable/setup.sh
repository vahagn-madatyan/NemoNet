#!/bin/bash
# launchable/setup.sh — NVIDIA Brev Launchable boot script
#
# This runs on VM creation. It installs NemoClaw, clones NemoNet,
# and starts the sandbox.

set -euo pipefail

echo "[NemoNet] Starting Launchable setup..."

# Install Node.js if needed
if ! command -v node &>/dev/null; then
  curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
  sudo apt-get install -y nodejs
fi

# Clone NemoNet
cd /home/ubuntu
git clone https://github.com/vahagn-madatyan/NemoNet.git
cd NemoNet

# Run NemoNet installer (clones NemoClaw from GitHub + configures)
./scripts/install.sh --profile demo --non-interactive

# Start services
nemoclaw start

echo "[NemoNet] Ready -- access via Secure Links"
