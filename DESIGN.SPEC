# DESIGN.SPEC — NemoNet Integration Plan

> **NemoNet — Network Automation Agent Platform on NemoClaw**
>
> NemoNet is built ON TOP of NemoClaw (not a fork). NemoClaw is consumed as a
> runtime dependency. NemoNet provides the network-specific configuration layer:
> blueprints, workspace files, skills, MCP servers, and egress policies.
>
> See NEMONET.md for architecture overview, EXPANSION.md for detailed plan.
>
> NOTE: This spec predates the fork-to-dependency migration. Some sections may
> reference the old fork-based architecture. NEMONET.md and EXPANSION.md are
> the authoritative sources for the current non-fork architecture.

---

## Table of Contents

1. [Context & Vision](#1-context--vision)
2. [Architecture Overview](#2-architecture-overview)
3. [What NemoNet Is](#3-what-nemonet-is)
4. [Skill Consumption Strategy](#4-skill-consumption-strategy)
5. [Required Changes to netsec-skills-suite](#5-required-changes-to-netsec-skills-suite)
6. [NemoNet Repo Integration](#6-nemonet-repo-integration)
7. [Deployment Targets](#7-deployment-targets)
8. [MCP Server Coordination](#8-mcp-server-coordination)
9. [ClawHub Publication](#9-clawhub-publication)
10. [Security Considerations](#10-security-considerations)
11. [Naming Decision](#11-naming-decision)
12. [NemoNet Scripts](#12-nemonet-scripts)
13. [Repo Hygiene](#13-repo-hygiene)
14. [Implementation Checklist](#14-implementation-checklist)

---

## 1. Context & Vision

`netsec-skills-suite` is a curated collection of 30+ AI agent skills for network
and security operations. Each skill is a structured SKILL.md procedure covering
device triage, firewall auditing, protocol analysis, compliance assessment, and
incident response across Cisco, Juniper, Arista, Palo Alto, Fortinet, Check Point,
and multi-cloud environments.

**NemoNet** is a thin fork of NVIDIA's [NemoClaw](https://github.com/NVIDIA/NemoClaw)
that bundles these skills alongside network-specific MCP servers, custom egress
policies, and inference routing into a single deployable package — a sandboxed
network automation agent platform.

The goal: an operator clicks one button on NVIDIA Brev, and within minutes they
have a running, sandboxed AI agent pre-loaded with all 30+ network security skills,
connected to their vendor APIs via MCP servers, with every API call policy-controlled
and auditable.

This repo (`netsec-skills-suite`) remains the **single source of truth** for all
skills. NemoNet consumes them — it does not duplicate them.

---

## 2. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    NVIDIA Brev Launchable                       │
│                    (or AWS EC2 / DGX Spark)                     │
├─────────────────────────────────────────────────────────────────┤
│  NemoNet (forked NemoClaw)                                      │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  OpenShell Sandbox (Landlock + seccomp + netns)           │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │  OpenClaw Agent Runtime                             │  │  │
│  │  │  ┌───────────────┐  ┌────────────────────────────┐  │  │  │
│  │  │  │ Agentic Loop  │  │ Memory Layer               │  │  │  │
│  │  │  │ Context →     │  │ AGENTS.md / SOUL.md        │  │  │  │
│  │  │  │ Inference →   │  │ MEMORY.md / HEARTBEAT.md   │  │  │  │
│  │  │  │ Tool Exec →   │  │                            │  │  │  │
│  │  │  │ Persist       │  │                            │  │  │  │
│  │  │  └───────┬───────┘  └────────────────────────────┘  │  │  │
│  │  │          │                                          │  │  │
│  │  │          ▼                                          │  │  │
│  │  │  ┌─────────────────────────────────────────────┐    │  │  │
│  │  │  │ netsec-skills-suite (THIS REPO)             │    │  │  │
│  │  │  │ ├── cisco-device-health/SKILL.md            │    │  │  │
│  │  │  │ ├── palo-alto-firewall-audit/SKILL.md       │    │  │  │
│  │  │  │ ├── aws-networking-audit/SKILL.md           │    │  │  │
│  │  │  │ ├── bgp-analysis/SKILL.md                   │    │  │  │
│  │  │  │ ├── zero-trust-assessment/SKILL.md          │    │  │  │
│  │  │  │ └── ... (30+ skills)                        │    │  │  │
│  │  │  └──────────────────┬──────────────────────────┘    │  │  │
│  │  │                     │ tool calls                    │  │  │
│  │  │                     ▼                               │  │  │
│  │  │  ┌─────────────────────────────────────────────┐    │  │  │
│  │  │  │ MCP Servers (separate repo or embedded)     │    │  │  │
│  │  │  │ ├── juniper-mist-mcp                        │    │  │  │
│  │  │  │ ├── palo-alto-mcp                           │    │  │  │
│  │  │  │ ├── aws-network-mcp                         │    │  │  │
│  │  │  │ ├── cno-mcp                                 │    │  │  │
│  │  │  │ └── meraki-mcp                              │    │  │  │
│  │  │  └──────────────────┬──────────────────────────┘    │  │  │
│  │  └─────────────────────┼───────────────────────────────┘  │  │
│  │                        │ egress (policy-controlled)       │  │
│  │  ┌─────────────────────▼───────────────────────────────┐  │  │
│  │  │  Egress Policy Engine (network-ops-sandbox.yaml)    │  │  │
│  │  │  ├── api.mist.com:443           allowed             │  │  │
│  │  │  ├── panorama.mcd-net.com:443   allowed             │  │  │
│  │  │  ├── *.amazonaws.com:443        allowed             │  │  │
│  │  │  └── unknown-host.com           blocked → TUI       │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  Inference: Nemotron 120B (NVIDIA Cloud) / Claude Opus / NIM   │
└─────────────────────────────────────────────────────────────────┘
         │                          │                    │
         ▼                          ▼                    ▼
   Juniper Mist Cloud      Palo Alto Panorama       AWS Networking
   (14K sites, 140K APs)   (15K+ firewalls)         (VPCs, TGW, R53)
```

---

## 3. What NemoNet Is

NemoNet is a **thin fork** of [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw)
(Apache 2.0) — the open-source stack that sandboxes
[OpenClaw](https://openclaw.ai) agents inside the
[NVIDIA OpenShell](https://github.com/NVIDIA/OpenShell) runtime.

NemoClaw provides:

- **Sandbox isolation** — Landlock LSM, seccomp filters, network namespace
- **Inference routing** — all LLM calls intercepted by OpenShell gateway
- **Declarative egress policy** — YAML-defined network allow/deny rules
- **Blueprint lifecycle** — versioned artifacts for reproducible sandbox setup
- **Single CLI** — `nemoclaw` orchestrates gateway, sandbox, inference, and policy

NemoNet extends this with:

- **Network-specific blueprint** — pre-configured egress for Mist, Panorama, AWS, CNO
- **Pre-loaded skills** — this repo (`netsec-skills-suite`) installed at build time
- **MCP servers** — vendor API integrations bundled in the container image
- **Deployment profiles** — `mcd-production`, `mcd-staging`, `lab`, `launchable-demo`
- **NVIDIA Brev Launchable** — one-click deploy to GPU cloud

### NemoNet Repo Structure

```
nemonet/
├── nemoclaw/                         # git subtree from NVIDIA/NemoClaw upstream
│   ├── nemoclaw/                     # TypeScript CLI plugin (untouched)
│   ├── nemoclaw-blueprint/           # Original blueprint (reference only)
│   └── ...
│
├── nemonet-blueprint/                # Custom network blueprint
│   ├── blueprint.yaml                # Profiles: mcd-prod, launchable-demo, lab
│   ├── orchestrator/
│   │   └── runner.py                 # Extended: vendor API health checks
│   └── policies/
│       ├── network-ops-sandbox.yaml  # Base egress policy
│       ├── mcd-production.yaml       # McDonald's strict profile
│       ├── mcd-govcloud.yaml         # GovCloud + FIPS endpoints
│       └── lab.yaml                  # Permissive for development
│
├── skills/                           # git submodule → netsec-skills-suite
│   └── netsec-skills-suite/          # THIS REPO (pinned version)
│
├── mcp-servers/                      # Network MCP tool servers
│   ├── juniper-mist-mcp/
│   ├── palo-alto-mcp/
│   ├── aws-network-mcp/
│   ├── cno-mcp/
│   ├── meraki-mcp/
│   └── git-netops-mcp/
│
├── docker/
│   ├── Dockerfile.sandbox            # OpenShell + MCP + skills
│   ├── Dockerfile.govcloud           # FIPS variant
│   └── docker-compose.yaml           # Brev Launchable stack
│
├── launchable/                       # NVIDIA Brev Launchable config
│   ├── setup.sh                      # VM boot script
│   ├── docker-compose.yaml           # Compose stack for Container Mode
│   └── README.md                     # Launch badge + instructions
│
├── install.sh
├── package.json
├── pyproject.toml
└── README.md
```

---

## 4. Skill Consumption Strategy

The skills in this repo are consumed by NemoNet through **three parallel paths**.
All three draw from this single source of truth — no duplication.

### Path 1: Git Submodule (Production — Pinned Versions)

The NemoNet repo references `netsec-skills-suite` as a git submodule. This gives
deterministic, auditable builds for production deployments.

```bash
# In the NemoNet repo (one-time setup)
git submodule add https://github.com/vahagn-madatyan/netsec-skills-suite.git \
    skills/netsec-skills-suite

# To update to latest
git submodule update --remote skills/netsec-skills-suite
git add skills/netsec-skills-suite
git commit -m "chore: update netsec-skills-suite to latest"
```

In `Dockerfile.sandbox`:

```dockerfile
# Copy skills from submodule (pinned at build time)
COPY skills/netsec-skills-suite/skills/ /sandbox/skills/
```

**Pros:** Version pinned, reproducible, auditable, works in air-gapped builds.
**Use:** McDonald's production, GovCloud, any regulated deployment.

### Path 2: Git Clone in Setup Script (Demo — Always Latest)

The Launchable setup script or `nemonet onboard` clones the latest `main`
from this repo at deploy time.

```bash
# In launchable/setup.sh or nemonet onboard hook
git clone --depth 1 https://github.com/vahagn-madatyan/netsec-skills-suite.git \
    /tmp/netsec-skills
bash /tmp/netsec-skills/scripts/nemonet-install.sh /sandbox/skills/
rm -rf /tmp/netsec-skills
```

**Pros:** Always latest, no submodule management, simple.
**Use:** Demos, labs, evaluation Launchables.

### Path 3: Direct Install via npx (Standalone — No NemoNet)

The existing install command works outside NemoNet for users who just want the
skills in their own OpenClaw or agent-skills setup:

```bash
npx skills add vahagn-madatyan/netsec-skills-suite
```

**Pros:** Works anywhere, no NemoNet dependency.
**Use:** Individual engineers, non-NemoNet OpenClaw users, ClawHub discovery.

---

## 5. Required Changes to netsec-skills-suite

The following changes need to be made **in this repo** to enable NemoNet integration.
All changes are additive — backward compatibility with the existing `agent-skills`
spec and `npx skills add` workflow is fully preserved.

### 5.1 Add OpenClaw-Native Frontmatter to Each SKILL.md

OpenClaw's skill router requires specific YAML frontmatter fields for auto-discovery
and eligibility filtering. Add a `metadata.openclaw` block to each skill's
existing frontmatter.

**Before (current):**

```yaml
---
name: palo-alto-firewall-audit
description: PAN-OS zone-based security policy audit
version: 1.0.0
---
```

**After (with OpenClaw metadata):**

```yaml
---
name: palo-alto-firewall-audit
description: PAN-OS zone-based security policy audit
version: 1.0.0
metadata:
  openclaw:
    emoji: "🔥"
    safetyTier: read-only
    requires:
      bins: []
      env:
        - PAN_API_KEY
    tags:
      - palo-alto
      - firewall
      - audit
      - security
    mcpDependencies:
      - palo-alto-mcp
    egressEndpoints:
      - "*.paloaltonetworks.com:443"
---
```

The `metadata.openclaw` fields serve these purposes:

| Field              | Purpose                                                       |
|--------------------|---------------------------------------------------------------|
| `emoji`            | Displayed in OpenClaw skill listings and TUI                  |
| `safetyTier`       | Maps to NemoNet sandbox permissions (read-only vs read-write) |
| `requires.bins`    | Binary dependencies the sandbox needs installed               |
| `requires.env`     | Environment variables the skill expects (API keys, etc.)      |
| `tags`             | Used by skill router for intent matching                      |
| `mcpDependencies`  | Which MCP servers this skill calls (NemoNet-specific)         |
| `egressEndpoints`  | Network endpoints this skill needs access to (NemoNet policy) |

**Scope:** All 30+ skills need this frontmatter addition.

### 5.2 Add MCP Tool References to Skill Bodies

Skills that interact with vendor APIs should declare which MCP tools they use.
This enables the dual-mode operation: MCP-native (inside NemoNet sandbox) and
CLI-fallback (standalone SSH access).

Add a `## Tool Requirements` section to each relevant skill body:

```markdown
## Tool Requirements

**MCP Mode (NemoNet/OpenClaw):**
This skill uses the following MCP tools when available:
- `palo-alto-mcp.get_security_rules` — Pull active rulebase from Panorama
- `palo-alto-mcp.get_security_profiles` — Audit Security Profile Groups
- `palo-alto-mcp.get_zone_protection` — Zone protection profile settings
- `palo-alto-mcp.get_nat_rules` — NAT policy for exposure analysis

**CLI Fallback Mode:**
If MCP tools are unavailable, use `exec` tool with SSH to the target device
and run PAN-OS operational/XML API commands directly.
```

**Scope:** The following skills need MCP references added:

| Skill                        | MCP Server Dependency   |
|------------------------------|-------------------------|
| `palo-alto-firewall-audit`   | `palo-alto-mcp`         |
| `cisco-firewall-audit`       | (SSH/CLI or cisco-mcp)  |
| `fortigate-firewall-audit`   | (SSH/CLI or forti-mcp)  |
| `checkpoint-firewall-audit`  | (SSH/CLI or cp-mcp)     |
| `aws-networking-audit`       | `aws-network-mcp`       |
| `azure-networking-audit`     | (az CLI or azure-mcp)   |
| `gcp-networking-audit`       | (gcloud or gcp-mcp)     |
| `cloud-security-posture`     | `aws-network-mcp` + others |
| `source-of-truth-audit`      | (Nautobot/NetBox API)   |
| `ipam-dns-audit`             | (IPAM API)              |
| `wireless-security-audit`    | `juniper-mist-mcp` or vendor MCP |
| `change-verification`        | `git-netops-mcp`        |
| `config-management`          | `git-netops-mcp`        |

Skills that are pure procedure/analysis (protocol analysis, compliance assessment)
with no vendor API dependency do not need MCP references.

### 5.3 Create `manifest.json` at Repo Root

This manifest enables NemoNet's setup scripts to auto-discover skills, resolve
MCP dependencies, and generate egress policy entries.

```json
{
  "name": "netsec-skills-suite",
  "version": "1.0.0",
  "description": "Network & Security Skills Suite for NemoNet",
  "repository": "https://github.com/vahagn-madatyan/netsec-skills-suite",
  "license": "Apache-2.0",
  "nemonet": {
    "minVersion": "0.1.0",
    "defaultProfile": "all"
  },
  "profiles": {
    "all": {
      "description": "Install all skills",
      "skills": "*"
    },
    "networking-only": {
      "description": "Device health, routing protocols, topology, interfaces",
      "skills": [
        "cisco-device-health",
        "juniper-device-health",
        "arista-device-health",
        "bgp-analysis",
        "ospf-analysis",
        "eigrp-analysis",
        "isis-analysis",
        "interface-health",
        "network-topology-discovery"
      ]
    },
    "security-only": {
      "description": "Firewall audits, compliance, vulnerability, incident response",
      "skills": [
        "palo-alto-firewall-audit",
        "fortigate-firewall-audit",
        "checkpoint-firewall-audit",
        "cisco-firewall-audit",
        "acl-rule-analysis",
        "cis-benchmark-audit",
        "nist-compliance-assessment",
        "vulnerability-assessment",
        "siem-log-analysis",
        "incident-response-network",
        "vpn-ipsec-troubleshooting",
        "zero-trust-assessment",
        "wireless-security-audit"
      ]
    },
    "cloud-only": {
      "description": "AWS, Azure, GCP networking and cloud security posture",
      "skills": [
        "aws-networking-audit",
        "azure-networking-audit",
        "gcp-networking-audit",
        "cloud-security-posture",
        "source-of-truth-audit",
        "ipam-dns-audit"
      ]
    },
    "mcd-production": {
      "description": "McDonald's production subset — Cisco, Juniper, PAN, AWS",
      "skills": [
        "cisco-device-health",
        "juniper-device-health",
        "bgp-analysis",
        "ospf-analysis",
        "interface-health",
        "network-topology-discovery",
        "palo-alto-firewall-audit",
        "acl-rule-analysis",
        "zero-trust-assessment",
        "aws-networking-audit",
        "change-verification",
        "config-management",
        "incident-response-network",
        "incident-response-lifecycle",
        "wireless-security-audit"
      ]
    }
  },
  "skills": [
    {
      "name": "example-device-health",
      "path": "skills/example-device-health",
      "safetyTier": "read-only",
      "mcpDependencies": [],
      "egressEndpoints": []
    },
    {
      "name": "cisco-device-health",
      "path": "skills/cisco-device-health",
      "safetyTier": "read-only",
      "mcpDependencies": [],
      "egressEndpoints": []
    },
    {
      "name": "juniper-device-health",
      "path": "skills/juniper-device-health",
      "safetyTier": "read-only",
      "mcpDependencies": [],
      "egressEndpoints": []
    },
    {
      "name": "arista-device-health",
      "path": "skills/arista-device-health",
      "safetyTier": "read-only",
      "mcpDependencies": [],
      "egressEndpoints": []
    },
    {
      "name": "bgp-analysis",
      "path": "skills/bgp-analysis",
      "safetyTier": "read-only",
      "mcpDependencies": [],
      "egressEndpoints": []
    },
    {
      "name": "ospf-analysis",
      "path": "skills/ospf-analysis",
      "safetyTier": "read-only",
      "mcpDependencies": [],
      "egressEndpoints": []
    },
    {
      "name": "eigrp-analysis",
      "path": "skills/eigrp-analysis",
      "safetyTier": "read-only",
      "mcpDependencies": [],
      "egressEndpoints": []
    },
    {
      "name": "isis-analysis",
      "path": "skills/isis-analysis",
      "safetyTier": "read-only",
      "mcpDependencies": [],
      "egressEndpoints": []
    },
    {
      "name": "interface-health",
      "path": "skills/interface-health",
      "safetyTier": "read-only",
      "mcpDependencies": [],
      "egressEndpoints": []
    },
    {
      "name": "network-topology-discovery",
      "path": "skills/network-topology-discovery",
      "safetyTier": "read-only",
      "mcpDependencies": [],
      "egressEndpoints": []
    },
    {
      "name": "change-verification",
      "path": "skills/change-verification",
      "safetyTier": "read-write",
      "mcpDependencies": ["git-netops-mcp"],
      "egressEndpoints": [],
      "requiresApproval": true
    },
    {
      "name": "config-management",
      "path": "skills/config-management",
      "safetyTier": "read-write",
      "mcpDependencies": ["git-netops-mcp"],
      "egressEndpoints": [],
      "requiresApproval": true
    },
    {
      "name": "palo-alto-firewall-audit",
      "path": "skills/palo-alto-firewall-audit",
      "safetyTier": "read-only",
      "mcpDependencies": ["palo-alto-mcp"],
      "egressEndpoints": ["*.paloaltonetworks.com:443"]
    },
    {
      "name": "fortigate-firewall-audit",
      "path": "skills/fortigate-firewall-audit",
      "safetyTier": "read-only",
      "mcpDependencies": [],
      "egressEndpoints": []
    },
    {
      "name": "checkpoint-firewall-audit",
      "path": "skills/checkpoint-firewall-audit",
      "safetyTier": "read-only",
      "mcpDependencies": [],
      "egressEndpoints": []
    },
    {
      "name": "cisco-firewall-audit",
      "path": "skills/cisco-firewall-audit",
      "safetyTier": "read-only",
      "mcpDependencies": [],
      "egressEndpoints": []
    },
    {
      "name": "acl-rule-analysis",
      "path": "skills/acl-rule-analysis",
      "safetyTier": "read-only",
      "mcpDependencies": [],
      "egressEndpoints": []
    },
    {
      "name": "cis-benchmark-audit",
      "path": "skills/cis-benchmark-audit",
      "safetyTier": "read-only",
      "mcpDependencies": [],
      "egressEndpoints": []
    },
    {
      "name": "nist-compliance-assessment",
      "path": "skills/nist-compliance-assessment",
      "safetyTier": "read-only",
      "mcpDependencies": [],
      "egressEndpoints": []
    },
    {
      "name": "vulnerability-assessment",
      "path": "skills/vulnerability-assessment",
      "safetyTier": "read-only",
      "mcpDependencies": [],
      "egressEndpoints": []
    },
    {
      "name": "siem-log-analysis",
      "path": "skills/siem-log-analysis",
      "safetyTier": "read-only",
      "mcpDependencies": [],
      "egressEndpoints": []
    },
    {
      "name": "incident-response-network",
      "path": "skills/incident-response-network",
      "safetyTier": "read-only",
      "mcpDependencies": [],
      "egressEndpoints": []
    },
    {
      "name": "vpn-ipsec-troubleshooting",
      "path": "skills/vpn-ipsec-troubleshooting",
      "safetyTier": "read-only",
      "mcpDependencies": [],
      "egressEndpoints": []
    },
    {
      "name": "zero-trust-assessment",
      "path": "skills/zero-trust-assessment",
      "safetyTier": "read-only",
      "mcpDependencies": [],
      "egressEndpoints": []
    },
    {
      "name": "wireless-security-audit",
      "path": "skills/wireless-security-audit",
      "safetyTier": "read-only",
      "mcpDependencies": ["juniper-mist-mcp"],
      "egressEndpoints": ["api.mist.com:443", "api.eu.mist.com:443"]
    },
    {
      "name": "aws-networking-audit",
      "path": "skills/aws-networking-audit",
      "safetyTier": "read-only",
      "mcpDependencies": ["aws-network-mcp"],
      "egressEndpoints": ["*.amazonaws.com:443"]
    },
    {
      "name": "azure-networking-audit",
      "path": "skills/azure-networking-audit",
      "safetyTier": "read-only",
      "mcpDependencies": [],
      "egressEndpoints": ["management.azure.com:443"]
    },
    {
      "name": "gcp-networking-audit",
      "path": "skills/gcp-networking-audit",
      "safetyTier": "read-only",
      "mcpDependencies": [],
      "egressEndpoints": ["compute.googleapis.com:443"]
    },
    {
      "name": "cloud-security-posture",
      "path": "skills/cloud-security-posture",
      "safetyTier": "read-only",
      "mcpDependencies": ["aws-network-mcp"],
      "egressEndpoints": ["*.amazonaws.com:443", "management.azure.com:443", "*.googleapis.com:443"]
    },
    {
      "name": "source-of-truth-audit",
      "path": "skills/source-of-truth-audit",
      "safetyTier": "read-only",
      "mcpDependencies": [],
      "egressEndpoints": []
    },
    {
      "name": "ipam-dns-audit",
      "path": "skills/ipam-dns-audit",
      "safetyTier": "read-only",
      "mcpDependencies": [],
      "egressEndpoints": []
    },
    {
      "name": "monitoring-dashboard-audit",
      "path": "skills/monitoring-dashboard-audit",
      "safetyTier": "read-only",
      "mcpDependencies": [],
      "egressEndpoints": []
    },
    {
      "name": "network-log-analysis",
      "path": "skills/network-log-analysis",
      "safetyTier": "read-only",
      "mcpDependencies": [],
      "egressEndpoints": []
    },
    {
      "name": "incident-response-lifecycle",
      "path": "skills/incident-response-lifecycle",
      "safetyTier": "read-only",
      "mcpDependencies": [],
      "egressEndpoints": []
    }
  ]
}
```

---

## 6. NemoNet Repo Integration

### 6.1 Submodule Setup (NemoNet repo)

```bash
cd nemonet/
git submodule add https://github.com/vahagn-madatyan/netsec-skills-suite.git \
    skills/netsec-skills-suite
git commit -m "feat: add netsec-skills-suite as submodule"
```

### 6.2 Dockerfile.sandbox

```dockerfile
FROM ghcr.io/nvidia/openshell-community/sandboxes/openclaw:latest

# --- Install MCP servers ---
COPY mcp-servers/ /opt/mcp-servers/
RUN cd /opt/mcp-servers/juniper-mist-mcp && npm install --production
RUN cd /opt/mcp-servers/palo-alto-mcp && npm install --production
RUN cd /opt/mcp-servers/aws-network-mcp && npm install --production

# --- Install skills from netsec-skills-suite submodule ---
COPY skills/netsec-skills-suite/skills/ /sandbox/skills/

# --- Copy network-specific workspace files ---
COPY workspace/AGENTS.md /sandbox/workspace/AGENTS.md
COPY workspace/SOUL.md /sandbox/workspace/SOUL.md
```

### 6.3 Launchable setup.sh

```bash
#!/bin/bash
set -euo pipefail

# Clone NemoNet (includes netsec-skills-suite submodule)
cd /home/ubuntu
git clone --recurse-submodules https://github.com/your-org/nemonet.git
cd nemonet

# Install NemoClaw CLI
npm install -g nemoclaw

# Run NemoNet onboard
nemonet onboard --profile launchable-demo --non-interactive

# Start services
docker compose -f docker/docker-compose.yaml up -d

echo "[NemoNet] Ready — access via Secure Links"
```

---

## 7. Deployment Targets

| Target                      | Use Case              | Skills Source                    | Inference          |
|-----------------------------|-----------------------|----------------------------------|--------------------|
| **NVIDIA Brev Launchable**  | Demos, evaluation     | `git clone` (latest HEAD)        | NVIDIA Cloud       |
| **AWS EC2 (production)**    | McDonald's 24/7 ops   | Submodule (pinned version)       | Claude Opus/Sonnet |
| **DGX Spark**               | Air-gapped demos      | Baked into container image       | Local Nemotron NIM |
| **EKS / OpenShift**         | Multi-tenant SaaS     | Container image per release      | Mixed              |

---

## 8. MCP Server Coordination

Skills in this repo reference MCP servers by name in their `mcpDependencies`.
The MCP servers themselves live in the NemoNet repo (or their own repos). The
mapping is:

| MCP Server             | Vendor API                       | Skills That Use It              |
|------------------------|----------------------------------|---------------------------------|
| `juniper-mist-mcp`    | api.mist.com                     | `wireless-security-audit`       |
| `palo-alto-mcp`       | Panorama REST/XML API            | `palo-alto-firewall-audit`      |
| `aws-network-mcp`     | AWS SDK (Boto3)                  | `aws-networking-audit`, `cloud-security-posture` |
| `cno-mcp`             | CNO Platform API                 | (future skills)                 |
| `meraki-mcp`          | Meraki Dashboard API             | (future skills)                 |
| `git-netops-mcp`      | Git + GitHub/GitLab API          | `change-verification`, `config-management` |

Skills without MCP dependencies operate in CLI-fallback mode using SSH/exec.

---

## 9. ClawHub Publication

For broader community adoption, individual skills should be published to
[ClawHub](https://clawhub.com) — the official OpenClaw skill registry.

Steps:

1. Fork `github.com/openclaw/clawhub`
2. Add each skill as a folder under the appropriate category
3. Ensure each SKILL.md has the `metadata.openclaw` frontmatter
4. Open a pull request

This makes all 30+ skills discoverable to the 250,000+ OpenClaw user base.
For enterprise deployments (McDonald's), use the submodule path rather than
ClawHub to avoid supply chain risks.

---

## 10. Security Considerations

### Existing Security Pipeline (Preserved)

This repo already runs a multi-layer security pipeline that carries forward:

- **SkillCheck security audit** — scans for command injection, prompt injection,
  safety tier mismatches, credential harvesting, obfuscation
- **VirusTotal scan** — 70+ antivirus engines on every PR and release
- **OpenSSF Scorecard** — weekly repository security posture evaluation
- **Claude Code Review** — AI-powered review on pull requests

### NemoNet-Specific Security

- **Sandbox isolation** — skills execute inside OpenShell sandbox with Landlock,
  seccomp, and network namespace isolation
- **Egress policy** — skills can only reach endpoints declared in their
  `egressEndpoints` manifest entry. All other traffic is blocked.
- **Safety tier enforcement** — `read-write` skills (`change-verification`,
  `config-management`) require explicit operator approval in the OpenShell TUI
  before executing write operations
- **No public ClawHub dependency** — production deployments use the submodule
  path, avoiding exposure to supply chain attacks on the public registry

---

## 11. Naming Decision

The NemoClaw fork is named **NemoNet** (working title — alternatives under
consideration). Candidate names and rationale:

| Name          | Signal                                         | CLI Feel             |
|---------------|------------------------------------------------|----------------------|
| **NemoNet**   | NemoClaw + networking. Clean, obvious.          | `nemonet deploy`     |
| **NemoWire**  | NemoClaw + wire/infrastructure. Physical feel.  | `nemowire onboard`   |
| **InfraClaw** | Infrastructure + OpenClaw. Domain-first.        | `infraclaw connect`  |
| **NemoGrid**  | NemoClaw + grid/topology. Multi-site feel.      | `nemogrid status`    |
| **NemoLink**  | NemoClaw + network link. Simple.                | `nemolink deploy`    |
| **ClawOps**   | OpenClaw + NetOps. Punchy, product-like.        | `clawops policy set` |
| **NemoEdge**  | NemoClaw + edge networking. DGX Spark aligned.  | `nemoedge connect`   |

All names signal lineage to NVIDIA NemoClaw while indicating network/infrastructure
specialization. Final decision pending — will be reflected in repo name, CLI binary,
and Launchable listing.

---

## 12. NemoNet Scripts

### 12.1 `scripts/nemonet-install.sh`

Profile-aware installer that NemoNet calls during onboard or Launchable setup.

```bash
#!/bin/bash
# scripts/nemonet-install.sh
# Installs netsec-skills-suite into a NemoNet sandbox or OpenClaw workspace.
#
# Usage:
#   ./scripts/nemonet-install.sh [target-dir] [profile]
#
# Arguments:
#   target-dir  Where to install skills (default: /sandbox/skills)
#   profile     Install profile from manifest.json (default: all)
#
# Examples:
#   ./scripts/nemonet-install.sh                           # all skills -> /sandbox/skills
#   ./scripts/nemonet-install.sh /sandbox/skills mcd-production
#   ./scripts/nemonet-install.sh ~/.openclaw/skills security-only

set -euo pipefail

TARGET="${1:-/sandbox/skills}"
PROFILE="${2:-all}"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MANIFEST="${REPO_ROOT}/manifest.json"

echo "netsec-skills-suite installer"
echo "  Profile: ${PROFILE}"
echo "  Target:  ${TARGET}"
echo ""

mkdir -p "${TARGET}"

# If jq is available, use profile filtering
if command -v jq &>/dev/null && [ -f "$MANIFEST" ]; then
  if [ "$PROFILE" = "all" ]; then
    SKILL_DIRS=("${REPO_ROOT}/skills"/*)
  else
    SKILL_NAMES=$(jq -r \
      ".profiles[\"${PROFILE}\"].skills[]" \
      "$MANIFEST" 2>/dev/null) || {
      echo "[ERROR] Profile '${PROFILE}' not found in manifest.json"
      echo "Available profiles:"
      jq -r '.profiles | keys[]' "$MANIFEST"
      exit 1
    }
    SKILL_DIRS=()
    for name in $SKILL_NAMES; do
      SKILL_DIRS+=("${REPO_ROOT}/skills/${name}")
    done
  fi
else
  # Fallback: install all skills if jq unavailable
  echo "[WARN] jq not found — installing all skills"
  SKILL_DIRS=("${REPO_ROOT}/skills"/*)
fi

INSTALLED=0
SKIPPED=0

for skill_dir in "${SKILL_DIRS[@]}"; do
  if [ ! -d "$skill_dir" ]; then
    echo "  SKIP ${skill_dir} (not found)"
    ((SKIPPED++))
    continue
  fi

  skill_name=$(basename "$skill_dir")

  # Skip non-skill directories
  if [ ! -f "${skill_dir}/SKILL.md" ]; then
    continue
  fi

  cp -r "$skill_dir" "${TARGET}/${skill_name}"
  echo "  OK ${skill_name}"
  ((INSTALLED++))
done

echo ""
echo "Installed: ${INSTALLED} skills"
[ "$SKIPPED" -gt 0 ] && echo "Skipped:   ${SKIPPED}"
echo "Location:  ${TARGET}"
```

### 12.2 `scripts/generate-egress-policy.sh`

Reads `manifest.json` and generates a NemoNet-compatible egress policy YAML
fragment for all skills that declare `egressEndpoints`.

```bash
#!/bin/bash
# scripts/generate-egress-policy.sh
# Generates NemoNet egress policy YAML from manifest.json
#
# Usage: ./scripts/generate-egress-policy.sh [profile] > policy-fragment.yaml

set -euo pipefail

PROFILE="${1:-all}"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MANIFEST="${REPO_ROOT}/manifest.json"

echo "# Auto-generated egress policy fragment"
echo "# Profile: ${PROFILE}"
echo "# Source: netsec-skills-suite/manifest.json"
echo "# Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo ""

jq -r '
  .skills[]
  | select(.egressEndpoints | length > 0)
  | "# Skill: \(.name) (safety: \(.safetyTier))\n" +
    (.egressEndpoints | map("  - \"\(.)\"") | join("\n"))
' "$MANIFEST"
```

---

## 13. Repo Hygiene

The following items should be addressed in this repo:

- [ ] **Remove stray files from root:** `compass_artifact_wf-3c00d46c-*.md` and
  `compass_artifact_wf-c0136c8b-*.md` are accidentally committed artifacts.
  Remove them or move to `docs/artifacts/` if they contain useful reference material.
  These could confuse OpenClaw's skill loader if it scans for `.md` files at root.

- [ ] **Add `.gitattributes`** for consistent line endings across contributors.

- [ ] **Tag a release** — the repo has 117 commits but no releases. Create `v1.0.0`
  to enable version pinning in git submodules and `npx skills add` version locks.

---

## 14. Implementation Checklist

### Phase 1 — Skill Compatibility (this repo)

- [ ] Add `metadata.openclaw` frontmatter to all 30+ SKILL.md files
- [ ] Add `## Tool Requirements` section to vendor-API-dependent skills
- [ ] Create `manifest.json` at repo root
- [ ] Create `scripts/nemonet-install.sh`
- [ ] Create `scripts/generate-egress-policy.sh`
- [ ] Remove `compass_artifact_wf-*.md` files from root
- [ ] Tag `v1.0.0` release
- [ ] Update README.md with NemoNet installation section
- [ ] Update CI to validate `manifest.json` schema

### Phase 2 — NemoNet Repo Setup (separate repo)

- [ ] Fork NVIDIA/NemoClaw → your-org/nemonet
- [ ] Add `netsec-skills-suite` as git submodule
- [ ] Create `nemonet-blueprint/` with network-specific policies
- [ ] Build custom sandbox Docker image with skills + MCP servers
- [ ] Create `launchable/` directory with Brev config
- [ ] Publish Launchable to NVIDIA Brev Explore catalog
- [ ] Add launch badge to README

### Phase 3 — ClawHub & Community (optional, high-value)

- [ ] Fork `openclaw/clawhub`
- [ ] Add all skills as ClawHub entries
- [ ] Open PR for ClawHub publication
- [ ] Post announcement to OpenClaw Discord

---

*Consolidated: 2026-03-28*
*Source: EXPANSION.md + NEMONET.md*
*Author: Vahagn Madatyan*
*License: Apache-2.0*
