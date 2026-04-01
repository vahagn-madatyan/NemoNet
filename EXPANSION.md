# EXPANSION.md — NemoNet Detailed Integration Plan

> **NemoNet: Network Automation Agent Platform on NemoClaw**
>
> NemoNet configures NemoClaw for network operations. NemoClaw is a runtime
> dependency, not a fork. This document covers the detailed integration plan
> from skill consumption to production deployment.

---

## Table of Contents

1. [Context & Vision](#1-context--vision)
2. [Architecture Overview](#2-architecture-overview)
3. [NemoClaw as Runtime Dependency](#3-nemoclaw-as-runtime-dependency)
4. [Skill Consumption Strategy](#4-skill-consumption-strategy)
5. [Workspace File Design](#5-workspace-file-design)
6. [MCP Server Coordination](#6-mcp-server-coordination)
7. [Blueprint & Policy Design](#7-blueprint--policy-design)
8. [Deployment Targets](#8-deployment-targets)
9. [Security Considerations](#9-security-considerations)
10. [NemoNet vs NetClaw](#10-nemonet-vs-netclaw)
11. [Implementation Phases](#11-implementation-phases)

---

## 1. Context & Vision

NemoNet is a network automation agent platform that follows the same pattern as
[NetClaw](https://github.com/automateyournetwork/netclaw) (which builds on
OpenClaw), but uses [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw) as
its runtime to gain sandbox isolation, egress policy, and inference routing.

The goal: an operator runs `./scripts/install.sh`, and within minutes they have
a sandboxed AI agent pre-loaded with 30+ network security skills, connected to
vendor APIs via MCP servers, with every API call policy-controlled and auditable.

---

## 2. Architecture Overview

```
┌──────────────────────────────────────────┐
│  NemoNet (this repo)                     │
│  ┌────────────────────────────────────┐  │
│  │ blueprint/     → sandbox config    │  │
│  │ workspace/     → agent identity    │  │
│  │ skills/        → 30+ procedures    │  │
│  │ mcp-servers/   → vendor API tools  │  │
│  │ scripts/       → install + setup   │  │
│  └──────────────────┬─────────────────┘  │
│                     │ configures         │
│  ┌──────────────────▼─────────────────┐  │
│  │ NemoClaw (npm dependency)          │  │
│  │ ├── Sandbox orchestration          │  │
│  │ ├── Inference gateway              │  │
│  │ ├── Egress policy engine           │  │
│  │ └── Blueprint lifecycle            │  │
│  └──────────────────┬─────────────────┘  │
│                     │ runs inside        │
│  ┌──────────────────▼─────────────────┐  │
│  │ OpenShell + OpenClaw               │  │
│  │ ├── Landlock + seccomp + netns     │  │
│  │ ├── Agent loop + TUI              │  │
│  │ └── Tool execution engine          │  │
│  └────────────────────────────────────┘  │
└──────────────────────────────────────────┘
```

**Key principle:** NemoNet owns configuration. NemoClaw owns runtime.
When NVIDIA ships NemoClaw updates, `npm update -g nemoclaw` picks them up.
NemoNet code is untouched.

---

## 3. NemoClaw as Runtime Dependency

### Why Not Fork?

NemoNet's additions are entirely additive — they live in separate directories
and never modify NemoClaw source code:

| NemoNet Directory | Purpose | Touches NemoClaw? |
|---|---|---|
| `blueprint/` | Sandbox config + egress policies | No |
| `workspace/` | Agent identity + skills | No |
| `mcp-servers/` | Vendor API integrations | No |
| `docker/` | Container images | No |
| `launchable/` | Brev deployment config | No |
| `scripts/` | Install + update scripts | No |

### How NemoNet Uses NemoClaw

```bash
# NemoNet's install.sh does this:
# 1. Clone NemoClaw from GitHub and `npm link` (not yet on npm)
# 2. Configure it with NemoNet's blueprint:
nemoclaw onboard --blueprint ./blueprint/blueprint.yaml \
                 --workspace ./workspace

# Then to start:
nemoclaw start                                         # NemoClaw runs everything
```

NemoNet is to NemoClaw what NetClaw is to OpenClaw — a domain-specific
configuration package, not a fork.

### NemoClaw Install Note

NemoClaw is **not yet published to npm** (the `nemoclaw` package on npm is a
name reservation placeholder). NemoNet's install script handles this by cloning
from GitHub and installing via `npm link`. Once NVIDIA publishes the real
package, install simplifies to `npm install -g nemoclaw`.

### Update Independence

```bash
# These are independent operations:
./scripts/update-nemoclaw.sh  # runtime updates (pulls latest from GitHub)
git pull                      # NemoNet updates (new skills, MCP servers, policies)
```

---

## 4. Skill Consumption Strategy

Skills are consumed through two paths. Both draw from a single source of truth.

### Path 1: Direct in Workspace (Development)

Skills live directly in `workspace/skills/` during development.
Add your netsec-skills-suite as a git submodule:

```bash
cd nemonet/
git submodule add https://github.com/vahagn-madatyan/netsec-skills-suite.git \
    workspace/skills/netsec-skills-suite
```

### Path 2: Baked into Container Image (Production)

For production/Launchable deployments, skills are copied into the Docker image
at build time:

```dockerfile
COPY workspace/skills/ /sandbox/skills/
```

### Skill Requirements for NemoNet

Each skill needs OpenClaw-compatible frontmatter:

```yaml
---
name: palo-alto-firewall-audit
description: PAN-OS zone-based security policy audit
version: 1.0.0
metadata:
  openclaw:
    safetyTier: read-only
    requires:
      env:
        - PAN_API_KEY
    tags:
      - palo-alto
      - firewall
      - audit
    mcpDependencies:
      - palo-alto-mcp
    egressEndpoints:
      - "*.paloaltonetworks.com:443"
---
```

---

## 5. Workspace File Design

NemoNet injects these files into every sandbox session (mirrors NetClaw pattern):

| File | Purpose | Customize? |
|------|---------|-----------|
| **SOUL.md** | Core expertise, 12 operating rules, protocol knowledge | No (defines agent) |
| **AGENTS.md** | Memory system, safety guardrails, change workflows | No (defines procedures) |
| **IDENTITY.md** | Name, version, role | No |
| **USER.md** | Operator preferences, timezone, role | Yes (per operator) |
| **TOOLS.md** | Device IPs, site info, credential references | Yes (per deployment) |
| **HEARTBEAT.md** | Periodic health check procedures | Optional |

---

## 6. MCP Server Coordination

MCP servers live in `mcp-servers/` and provide typed tool interfaces to vendor APIs.
Skills declare which MCP servers they need via `mcpDependencies`.

| MCP Server | Vendor API | Transport | Skills |
|---|---|---|---|
| `juniper-mist-mcp` | api.mist.com | stdio | `wireless-security-audit` |
| `palo-alto-mcp` | Panorama REST/XML | stdio | `palo-alto-firewall-audit` |
| `aws-network-mcp` | AWS SDK (Boto3) | stdio | `aws-networking-audit`, `cloud-security-posture` |
| `meraki-mcp` | Meraki Dashboard API | stdio | (future) |
| `cno-mcp` | CNO Platform API | stdio | (future) |
| `git-netops-mcp` | Git + GitHub/GitLab | stdio | `change-verification`, `config-management` |

Skills without MCP dependencies fall back to CLI mode (SSH/exec to devices).

---

## 7. Blueprint & Policy Design

### Blueprint

`blueprint/blueprint.yaml` is NemoClaw's primary extension point. It declares:
- Sandbox base image
- Workspace path
- MCP server list and transport
- Default egress policy
- Deployment profiles

### Egress Policies

Each policy file declares which network endpoints the sandbox can reach.
All other traffic is blocked by the NemoClaw sandbox.

| Policy | Use Case | Scope |
|--------|----------|-------|
| `base.yaml` | Default — vendor API endpoints | Wildcards for major vendors |
| `production.yaml` | Strict — explicit endpoints only | No wildcards, named hosts |
| `govcloud.yaml` | FIPS-only endpoints | AWS GovCloud regions, local NIM |
| `lab.yaml` | Permissive — dev/test | All HTTPS + SSH |

---

## 8. Deployment Targets

| Target | Use Case | Skills Source | Inference |
|--------|----------|--------------|-----------|
| **NVIDIA Brev Launchable** | Demos, evaluation | `git clone` (latest) | NVIDIA Cloud |
| **AWS EC2 (production)** | 24/7 ops | Pinned release | Claude Opus/Sonnet |
| **DGX Spark** | Air-gapped demos | Container image | Local Nemotron NIM |
| **EKS / OpenShift** | Multi-tenant SaaS | Container image | Mixed |

---

## 9. Security Considerations

### Runtime Security (provided by NemoClaw)

- **Landlock LSM** — filesystem access control
- **seccomp** — syscall filtering
- **Network namespace** — isolated network stack
- **Inference gateway** — all LLM calls intercepted and auditable

### Configuration Security (provided by NemoNet)

- **Egress policies** — skills can only reach declared endpoints
- **Safety tiers** — read-write skills require operator approval
- **Credential isolation** — env vars only, never in workspace files
- **No public registry dependency** — production uses local skills, not ClawHub

---

## 10. NemoNet vs NetClaw

| | NetClaw (on OpenClaw) | NemoNet (on NemoClaw) |
|---|---|---|
| Runtime | OpenClaw (bare agent) | NemoClaw (sandboxed agent) |
| Relationship | Built on top of OpenClaw | Built on top of NemoClaw |
| Network isolation | None | Landlock + seccomp + netns |
| Egress control | None | Declarative YAML policies |
| Inference routing | Direct to provider | Gateway-routed, swappable |
| Blueprint versioning | N/A | Reproducible sandbox snapshots |
| Air-gap support | Manual | Blueprint + local NIM |
| Skills | 92 (workspace/skills/) | 30+ (workspace/skills/) |
| MCP servers | 55 | 6+ (network-focused) |
| Install | `./scripts/install.sh` | `./scripts/install.sh` |

---

## 11. Implementation Phases

### Phase 1 — Repo Structure (done)

- [x] Remove NemoClaw fork upstream remote
- [x] Remove all forked NemoClaw source code
- [x] Create NemoNet repo scaffold
- [x] Create blueprint/ with policies
- [x] Create workspace/ with identity files
- [x] Create scripts/install.sh
- [x] Create docker/Dockerfile.sandbox
- [x] Create launchable/setup.sh

### Phase 2 — Skills & MCP Servers

- [x] Add netsec-skills-suite as submodule in workspace/skills/
- [x] Add OpenClaw frontmatter to all SKILL.md files (already in upstream)
- [x] Create manifest.json with skill registry (included in submodule)
- [ ] Build juniper-mist-mcp
- [ ] Build palo-alto-mcp
- [ ] Build aws-network-mcp
- [ ] Test skills inside NemoClaw sandbox

### Phase 3 — Deployment & Testing

- [ ] Build Docker sandbox image
- [ ] Test on NVIDIA Brev Launchable
- [ ] Test on DGX Spark (air-gapped)
- [ ] Test on AWS EC2 (production profile)
- [ ] Tag v0.1.0 release

### Phase 4 — Community & ClawHub (optional)

- [ ] Publish skills to ClawHub
- [ ] Post announcement to OpenClaw Discord
- [ ] Add launch badge to README

---

*Last updated: 2026-03-30*
*Author: Vahagn Madatyan*
*License: Apache-2.0*
