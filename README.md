# NemoNet

Network automation agent platform built on [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw).

NemoNet bundles 30+ network security skills, vendor MCP servers, and sandboxed
egress policies into a single deployable package. Think
[NetClaw](https://github.com/automateyournetwork/netclaw) but on NemoClaw
instead of OpenClaw — gaining sandbox isolation, inference routing, and
declarative network policy.

## Quick Start

```bash
git clone https://github.com/vahagn-madatyan/NemoNet.git
cd NemoNet
./scripts/install.sh
```

This installs NemoClaw (if needed), configures it with NemoNet's blueprint and
workspace, and installs MCP server dependencies.

Then:

```bash
nemoclaw start    # Start the sandboxed agent
nemoclaw status   # Check sandbox health
```

## What's Inside

| Directory | Purpose |
|-----------|---------|
| `blueprint/` | NemoClaw blueprint with network egress policies |
| `workspace/` | Agent identity (SOUL.md, AGENTS.md) + skills |
| `mcp-servers/` | Vendor API integrations (Mist, PAN-OS, AWS, Meraki) |
| `scripts/` | Install, update, and policy generation scripts |
| `docker/` | Container images for production/Launchable deployments |
| `launchable/` | NVIDIA Brev one-click deploy configuration |

## Architecture

```
NemoNet (this repo)        = Blueprint + Workspace + Skills + MCP Servers
NemoClaw (npm dependency)  = Sandbox + Gateway + Inference + Policy Engine
```

NemoClaw is consumed as a runtime dependency, not forked. NemoClaw is installed
from [GitHub](https://github.com/NVIDIA/NemoClaw) (not yet on npm). When NVIDIA
ships updates, `./scripts/update-nemoclaw.sh` pulls them. NemoNet code is untouched.

## Deployment Profiles

| Profile | Use Case | Egress Policy |
|---------|----------|---------------|
| `lab` | Development and testing | Permissive (all HTTPS + SSH) |
| `production` | 24/7 operations | Strict (explicit endpoints only) |
| `govcloud` | Regulated environments | FIPS-only endpoints |
| `demo` | NVIDIA Brev Launchable | Base vendor endpoints |

## Documentation

- [NEMONET.md](NEMONET.md) — Architecture and integration design
- [EXPANSION.md](EXPANSION.md) — Detailed implementation plan
- [DESIGN.SPEC](DESIGN.SPEC) — Consolidated design specification

## License

Apache-2.0 — see [LICENSE](LICENSE)
