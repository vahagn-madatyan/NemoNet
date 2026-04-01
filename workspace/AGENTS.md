# AGENTS.md — NemoNet Operating Procedures

## Memory System

NemoNet maintains session memory through workspace files:
- **SOUL.md** — Core identity and operating rules (immutable per session)
- **AGENTS.md** — This file. Operating procedures and safety guardrails.
- **IDENTITY.md** — Agent name and personality
- **USER.md** — Operator preferences, role, timezone
- **TOOLS.md** — Device inventory, site info, credential references
- **HEARTBEAT.md** — Periodic health check procedures

## Safety Guardrails

### Change Control
- All configuration changes require operator confirmation
- Read-write skills display a confirmation prompt in the TUI before execution
- Changes are logged with before/after state for rollback capability

### Network Scope
- NemoNet only operates on devices and endpoints listed in TOOLS.md
- Egress is controlled by the NemoClaw sandbox policy (blueprint/policies/)
- Attempts to reach undeclared endpoints are blocked and logged

### Credential Handling
- Credentials are injected via environment variables, never stored in workspace files
- MCP servers handle authentication — skills never see raw credentials
- API keys referenced by name only (e.g., `PAN_API_KEY`, `MIST_API_TOKEN`)

## Skill Execution

Skills are structured procedures in `workspace/skills/`. Each skill:
1. Has a safety tier: `read-only` or `read-write`
2. Declares MCP dependencies (which tool servers it needs)
3. Declares egress endpoints (which APIs it calls)
4. Operates in MCP mode (via tool servers) or CLI fallback (via SSH/exec)

## MCP Server Integration

MCP servers provide typed tool interfaces to vendor APIs:
- `juniper-mist-mcp` — Mist Cloud API
- `palo-alto-mcp` — Panorama REST/XML API
- `aws-network-mcp` — AWS SDK (Boto3)
- `meraki-mcp` — Meraki Dashboard API
- `cno-mcp` — CNO Platform API
- `git-netops-mcp` — Git + GitHub/GitLab API

Skills without MCP dependencies fall back to CLI mode using SSH/exec.
