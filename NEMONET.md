# NEMONET.md — Architecture & Integration

> NemoNet is a network automation agent platform built **on top of** NemoClaw.
> NemoClaw is consumed as a runtime dependency, not forked.

---

## Table of Contents

1. [What NemoNet Is](#1-what-nemonet-is)
2. [Architecture](#2-architecture)
3. [Relationship to NemoClaw](#3-relationship-to-nemoclaw)
4. [Repo Structure](#4-repo-structure)
5. [Install Flow](#5-install-flow)
6. [Deployment Targets](#6-deployment-targets)
7. [MCP Server Coordination](#7-mcp-server-coordination)
8. [Security Model](#8-security-model)
9. [Updating](#9-updating)
10. [Implementation Checklist](#10-implementation-checklist)

---

## 1. What NemoNet Is

NemoNet is a **network-specific configuration layer** that rides on top of
[NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw) — the open-source stack
that sandboxes [OpenClaw](https://openclaw.ai) agents inside the
[NVIDIA OpenShell](https://github.com/NVIDIA/OpenShell) runtime.

This is the same pattern as [NetClaw](https://github.com/automateyournetwork/netclaw)
(which builds on OpenClaw), but NemoNet uses NemoClaw as its runtime to gain:

- **Sandbox isolation** — Landlock LSM, seccomp filters, network namespace
- **Inference routing** — all LLM calls intercepted by OpenShell gateway
- **Declarative egress policy** — YAML-defined network allow/deny rules
- **Blueprint lifecycle** — versioned artifacts for reproducible sandbox setup

NemoNet adds:

- **Network-specific blueprint** — pre-configured egress for Mist, Panorama, AWS, etc.
- **Workspace files** — SOUL.md, AGENTS.md, IDENTITY.md defining agent expertise
- **Skills** — network and security operations procedures (netsec-skills-suite)
- **MCP servers** — vendor API integrations (Juniper, Palo Alto, AWS, Meraki, etc.)
- **Deployment profiles** — production, lab, govcloud, demo
- **NVIDIA Brev Launchable** — one-click deploy to GPU cloud

---

## 2. Architecture

```
NemoNet = Blueprint + Workspace + Skills + MCP Servers
         ↓
NemoClaw = Runtime engine (sandbox, gateway, inference, policy)
         ↓
OpenShell = Container isolation + Landlock + seccomp + netns
         ↓
OpenClaw = Agent loop (context → inference → tool exec → persist)
```

```
┌─────────────────────────────────────────────────────────────────┐
│                    NVIDIA Brev Launchable                       │
│                    (or AWS EC2 / DGX Spark)                     │
├─────────────────────────────────────────────────────────────────┤
│  NemoClaw Runtime (installed via npm, NOT forked)               │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  OpenShell Sandbox (Landlock + seccomp + netns)           │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │  OpenClaw Agent Runtime                             │  │  │
│  │  │  ┌───────────────┐  ┌────────────────────────────┐  │  │  │
│  │  │  │ Agentic Loop  │  │ NemoNet Workspace          │  │  │  │
│  │  │  │ Context →     │  │ SOUL.md / AGENTS.md        │  │  │  │
│  │  │  │ Inference →   │  │ IDENTITY.md / USER.md      │  │  │  │
│  │  │  │ Tool Exec →   │  │ TOOLS.md / HEARTBEAT.md    │  │  │  │
│  │  │  │ Persist       │  │                            │  │  │  │
│  │  │  └───────┬───────┘  └────────────────────────────┘  │  │  │
│  │  │          │                                          │  │  │
│  │  │          ▼                                          │  │  │
│  │  │  ┌─────────────────────────────────────────────┐    │  │  │
│  │  │  │ NemoNet Skills (workspace/skills/)          │    │  │  │
│  │  │  │ ├── cisco-device-health/SKILL.md            │    │  │  │
│  │  │  │ ├── palo-alto-firewall-audit/SKILL.md       │    │  │  │
│  │  │  │ ├── aws-networking-audit/SKILL.md           │    │  │  │
│  │  │  │ ├── bgp-analysis/SKILL.md                   │    │  │  │
│  │  │  │ └── ... (30+ skills)                        │    │  │  │
│  │  │  └──────────────────┬──────────────────────────┘    │  │  │
│  │  │                     │ tool calls                    │  │  │
│  │  │                     ▼                               │  │  │
│  │  │  ┌─────────────────────────────────────────────┐    │  │  │
│  │  │  │ NemoNet MCP Servers (mcp-servers/)          │    │  │  │
│  │  │  │ ├── juniper-mist-mcp                        │    │  │  │
│  │  │  │ ├── palo-alto-mcp                           │    │  │  │
│  │  │  │ ├── aws-network-mcp                         │    │  │  │
│  │  │  │ └── meraki-mcp                              │    │  │  │
│  │  │  └──────────────────┬──────────────────────────┘    │  │  │
│  │  └─────────────────────┼───────────────────────────────┘  │  │
│  │                        │ egress (policy-controlled)       │  │
│  │  ┌─────────────────────▼───────────────────────────────┐  │  │
│  │  │  NemoNet Egress Policy (blueprint/policies/)        │  │  │
│  │  │  ├── api.mist.com:443           allowed             │  │  │
│  │  │  ├── *.paloaltonetworks.com:443 allowed             │  │  │
│  │  │  ├── *.amazonaws.com:443        allowed             │  │  │
│  │  │  └── unknown-host.com           blocked → TUI       │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  Inference: Claude / Nemotron / local NIM                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Relationship to NemoClaw

**NemoNet does NOT fork NemoClaw.** NemoClaw is consumed as an npm dependency
(runtime) that NemoNet configures via blueprints and workspace files.

| Layer | Owns | Source |
|-------|------|--------|
| **NemoNet** | Blueprint, workspace, skills, MCP servers, policies | This repo |
| **NemoClaw** | CLI, sandbox orchestration, gateway, inference routing | Installed from [GitHub](https://github.com/NVIDIA/NemoClaw) (not yet on npm) |
| **OpenShell** | Container runtime, Landlock, seccomp, netns | NemoClaw dependency |
| **OpenClaw** | Agent loop, TUI, channels, tool execution | NemoClaw dependency |

NemoNet's install script calls `nemoclaw onboard` with NemoNet's blueprint path.
NemoClaw handles all the runtime complexity. NemoNet only owns the
network-specific configuration.

### Why Not Fork?

- NemoNet's additions are **entirely additive** — no NemoClaw code is modified
- Forking creates merge conflicts and drift for zero benefit
- `scripts/update-nemoclaw.sh` pulls latest upstream (will become `npm update` once published)
- Clear separation: NemoClaw = engine, NemoNet = configuration

### NemoClaw Install Method

NemoClaw is **not yet published to npm** (the `nemoclaw` package on npm is a
name reservation placeholder). NemoNet's install script clones NemoClaw from
GitHub and installs via `npm link`. Once NVIDIA publishes the real package,
the install simplifies to `npm install -g nemoclaw`.

---

## 4. Repo Structure

```
nemonet/
├── blueprint/                    # NemoClaw blueprint (extension point)
│   ├── blueprint.yaml            # Sandbox config, MCP servers, profiles
│   └── policies/
│       ├── base.yaml             # Default egress (vendor endpoints)
│       ├── production.yaml       # Strict: explicit endpoints only
│       ├── govcloud.yaml         # FIPS-only endpoints
│       └── lab.yaml              # Permissive for dev/test
│
├── workspace/                    # Injected into sandbox at session start
│   ├── skills/                   # Network skills (submodule or vendored)
│   ├── SOUL.md                   # Agent expertise and operating rules
│   ├── AGENTS.md                 # Operating procedures, safety guardrails
│   ├── IDENTITY.md               # Agent identity card
│   ├── USER.md                   # Operator customization
│   ├── TOOLS.md                  # Device inventory, credential refs
│   └── HEARTBEAT.md              # Periodic health check procedures
│
├── mcp-servers/                  # Network MCP tool servers
│   ├── juniper-mist-mcp/
│   ├── palo-alto-mcp/
│   ├── aws-network-mcp/
│   ├── meraki-mcp/
│   ├── cno-mcp/
│   └── git-netops-mcp/
│
├── docker/
│   └── Dockerfile.sandbox        # OpenShell base + skills + MCPs
│
├── launchable/                   # NVIDIA Brev one-click deploy
│   └── setup.sh
│
├── scripts/
│   ├── install.sh                # Two-phase installer
│   ├── install-mcps.sh           # MCP dependency installer
│   ├── update-nemoclaw.sh        # Update NemoClaw runtime
│   └── generate-egress-policy.sh # Auto-gen policy from manifest
│
├── manifest.json                 # Skill registry, profiles, egress mapping
├── package.json                  # NemoNet metadata
├── NEMONET.md                    # This file
├── EXPANSION.md                  # Detailed integration plan
├── DESIGN.SPEC                   # Consolidated design spec
└── LICENSE                       # Apache-2.0
```

---

## 5. Install Flow

Two-phase setup (mirrors the NetClaw pattern):

```bash
git clone https://github.com/vahagn-madatyan/NemoNet.git
cd NemoNet
./scripts/install.sh
```

**Phase 1** — Install NemoClaw runtime (cloned from GitHub, `npm link`)
**Phase 2** — Run `nemoclaw onboard` with NemoNet's blueprint and workspace
**Phase 3** — Install MCP server npm dependencies

After install:

```bash
nemoclaw start    # Start the sandboxed agent
nemoclaw status   # Check sandbox health
```

---

## 6. Deployment Targets

| Target | Use Case | Skills Source | Inference |
|--------|----------|--------------|-----------|
| **NVIDIA Brev Launchable** | Demos, evaluation | `git clone` (latest HEAD) | NVIDIA Cloud |
| **AWS EC2 (production)** | 24/7 ops | Pinned release tag | Claude Opus/Sonnet |
| **DGX Spark** | Air-gapped demos | Baked into container image | Local Nemotron NIM |
| **EKS / OpenShift** | Multi-tenant SaaS | Container image per release | Mixed |

---

## 7. MCP Server Coordination

Skills reference MCP servers by name. The MCP servers live in `mcp-servers/`.

| MCP Server | Vendor API | Skills That Use It |
|------------|-----------|-------------------|
| `juniper-mist-mcp` | api.mist.com | `wireless-security-audit` |
| `palo-alto-mcp` | Panorama REST/XML API | `palo-alto-firewall-audit` |
| `aws-network-mcp` | AWS SDK (Boto3) | `aws-networking-audit`, `cloud-security-posture` |
| `meraki-mcp` | Meraki Dashboard API | (future skills) |
| `cno-mcp` | CNO Platform API | (future skills) |
| `git-netops-mcp` | Git + GitHub/GitLab API | `change-verification`, `config-management` |

Skills without MCP dependencies operate in CLI-fallback mode using SSH/exec.

---

## 8. Security Model

NemoClaw provides the runtime security. NemoNet configures it:

- **Sandbox isolation** — Landlock LSM, seccomp, network namespace (NemoClaw)
- **Egress policy** — `blueprint/policies/*.yaml` declare allowed endpoints (NemoNet)
- **Safety tiers** — `read-write` skills require operator approval in TUI (NemoNet)
- **Inference routing** — all LLM calls routed through OpenShell gateway (NemoClaw)
- **Credential isolation** — env vars only, never in workspace files (NemoNet)

---

## 9. Updating

NemoClaw and NemoNet update independently:

```bash
# Update NemoClaw runtime (upstream improvements)
./scripts/update-nemoclaw.sh
# (will become `npm update -g nemoclaw` once NemoClaw is published to npm)

# Update NemoNet (your skills, MCPs, blueprints)
cd nemonet && git pull
```

---

## 10. Implementation Checklist

### Phase 1 — NemoNet Repo (this repo)

- [x] Remove NemoClaw fork (disconnect upstream, delete forked files)
- [x] Create blueprint/ with network-specific policies
- [x] Create workspace/ with SOUL.md, AGENTS.md, IDENTITY.md, etc.
- [x] Create scripts/install.sh (two-phase, mirrors NetClaw)
- [x] Create docker/Dockerfile.sandbox
- [x] Create launchable/setup.sh
- [x] Add netsec-skills-suite to workspace/skills/ (git submodule)
- [x] Wire manifest.json from submodule into blueprint
- [ ] Build MCP servers in mcp-servers/
- [ ] Tag v0.1.0 release

### Phase 2 — Skills Integration

- [x] Add OpenClaw-native frontmatter to all SKILL.md files (already in upstream)
- [x] Add MCP tool references to vendor-dependent skills (in manifest.json)
- [ ] Validate skills work inside NemoClaw sandbox

### Phase 3 — Deployment

- [ ] Build and test Docker sandbox image
- [ ] Publish NVIDIA Brev Launchable
- [ ] Test DGX Spark air-gapped deployment
- [ ] Test AWS EC2 production deployment

---

*Last updated: 2026-03-30*
*License: Apache-2.0*
