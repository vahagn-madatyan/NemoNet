# NemoNet

[![Deploy on Brev](https://brev-assets.s3.us-west-1.amazonaws.com/nv-lb-dark.svg)](https://brev.nvidia.com/launchable/deploy/now?launchableID=env-YOUR_ID_HERE)

Network automation agent platform built on [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw).

NemoNet bundles 37 network security skills, vendor MCP servers, and sandboxed
egress policies into a single deployable package. Think
[NetClaw](https://github.com/automateyournetwork/netclaw) but on NemoClaw
instead of OpenClaw -- gaining sandbox isolation, inference routing, and
declarative network policy.

## Quick Start

```bash
git clone --recurse-submodules https://github.com/vahagn-madatyan/NemoNet.git
cd NemoNet
./scripts/install.sh
```

This installs NemoClaw (if needed), deploys MCP server configuration, configures
the sandbox with NemoNet's blueprint and workspace, and loads 37 skills.

Then:

```bash
nemoclaw start    # Start the sandboxed agent
nemoclaw status   # Check sandbox health
```

## What's Inside

| Directory | Purpose |
|-----------|---------|
| `blueprint/` | NemoClaw blueprint with network egress policies |
| `workspace/` | Agent identity (SOUL.md, AGENTS.md) + 37 skills |
| `config/` | `openclaw.json` -- MCP server declarations |
| `scripts/` | Install, update, and setup scripts |
| `docker/` | Container images for production deployments |
| `launchable/` | NVIDIA Brev one-click deploy configuration |

## Architecture

```
NemoNet (this repo)        = Blueprint + Workspace + Skills + MCP Config
NemoClaw (runtime dep)     = Sandbox + Gateway + Inference + Policy Engine
OpenShell                  = Landlock + seccomp + netns container runtime
OpenClaw                   = Agent loop + TUI + tool execution
```

NemoClaw is consumed as a runtime dependency, not forked. When NVIDIA ships
updates, `./scripts/update-nemoclaw.sh` pulls them. NemoNet code is untouched.

## MCP Servers

MCP servers are external packages configured in `config/openclaw.json`, deployed
to `~/.openclaw/openclaw.json` at install time. No in-repo server code.

| Server | Source | Transport | Auth |
|--------|--------|-----------|------|
| **Zscaler** (ZIA/ZPA/ZDX) | `uvx zscaler-mcp` | stdio | Client ID + Secret |
| **Juniper Mist** | `mcp.ai.juniper.net` (cloud) | remote via mcp-remote | Bearer token |
| **Cloudflare API** | `mcp.cloudflare.com` (cloud) | remote via mcp-remote | OAuth |
| **Cloudflare Radar** | `radar.mcp.cloudflare.com` (cloud) | remote via mcp-remote | OAuth |
| **Cloudflare DNS** | `dns-analytics.mcp.cloudflare.com` (cloud) | remote via mcp-remote | OAuth |
| **Palo Alto PAN-OS** | `uvx pan-os-mcp` | stdio | API key |
| **AWS Networking** | `uvx awslabs.aws-network-mcp-server` | stdio | AWS profile |
| **nmap** | `uvx nmap-mcp` | stdio | None |
| **NetBox** | `uvx netbox-mcp` | stdio | API token |
| **GitHub** | `ghcr.io/github/github-mcp-server` | Docker/stdio | PAT |

## Skills (37)

From [netsec-skills-suite](https://github.com/vahagn-madatyan/netsec-skills-suite)
(git submodule):

- **Device Health** -- Cisco, Juniper, Arista
- **Routing** -- BGP, OSPF, EIGRP, IS-IS analysis
- **Firewalls** -- Palo Alto, FortiGate, Check Point, Cisco ASA audits
- **Compliance** -- CIS benchmarks, NIST assessment
- **Cloud** -- AWS, Azure, GCP networking audits
- **SASE** -- Zscaler ZIA/ZPA, Prisma Access, FortiSASE
- **Security** -- ACL analysis, vulnerability assessment, zero-trust
- **Operations** -- Change verification, config management, incident response

## Deployment Profiles

| Profile | Use Case | Egress Policy |
|---------|----------|---------------|
| `lab` | Development and testing | Permissive (all HTTPS + SSH) |
| `production` | 24/7 operations | Strict (explicit endpoints only) |
| `govcloud` | Regulated environments | FIPS-only endpoints |
| `demo` | NVIDIA Brev Launchable | Base vendor endpoints |

## Documentation

- [NEMONET.md](NEMONET.md) -- Architecture and integration design
- [EXPANSION.md](EXPANSION.md) -- Detailed implementation plan
- [DESIGN.SPEC](DESIGN.SPEC) -- Consolidated design specification

## License

Apache-2.0 -- see [LICENSE](LICENSE)
