# HEARTBEAT.md — Periodic Health Check Procedures

# NemoNet runs these checks on a configurable interval.
# Each check uses read-only skills and reports status.

## Health Checks

### 1. Device Reachability
- Ping/SSH test to all devices in TOOLS.md
- Report unreachable devices immediately

### 2. BGP Peer Status
- Check established/idle/active state for all BGP neighbors
- Alert on any peer state change from established

### 3. Interface Errors
- Poll interface counters for CRC, input/output errors, discards
- Alert if error rate exceeds baseline threshold

### 4. Firewall Policy Compliance
- Compare active rulebase against last known-good baseline
- Flag any shadow rules, unused rules, or overly permissive entries

### 5. Certificate Expiry
- Check TLS certificate expiry on management interfaces
- Alert if any cert expires within 30 days

### 6. Cloud Security Posture
- Verify security group rules match expected baseline
- Check for public-facing resources that should be private
