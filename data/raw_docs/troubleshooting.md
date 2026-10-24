# Aurelia Tech — Troubleshooting Guide & IT FAQ

> **Notice:** This document contains common technical troubleshooting procedures for employees and developers at *Aurelia Tech*. Last updated: January 2026. Document Owner: IT Support & Developer Experience (`it-servicedesk@aureliatech.com`).

---

## 1. VPN & Network Connectivity Issues

### Symptom: Cannot Connect to Internal Wikis, Staging, or Cloud Bastions
- **Diagnosis:** Aurelia Secure VPN client (WireGuard/OpenVPN) is disconnected or DNS cache is stale.
- **Resolution Steps:**
  1. Open *Aurelia Connect* in your system tray and click **Disconnect**.
  2. Wait 10 seconds, then click **Connect** and re-authenticate via Okta MFA.
  3. Flush your local DNS cache:
     - **macOS:** `sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder`
     - **Windows:** `ipconfig /flushdns`
  4. If you still encounter `Connection Refused` on internal `.aurelia-internal.net` domains, report to `#it-support` on Slack.

---

## 2. Docker & Local Development Containers

### Symptom: "Port Already Allocated" (e.g., Port 5432 or 6379 in use)
- **Diagnosis:** A background PostgreSQL or Redis service is already bound to the local port.
- **Resolution:**
  ```bash
  # Identify process occupying port 5432 (macOS/Linux)
  lsof -i :5432
  # Terminate conflicting process
  kill -9 <PID>
  
  # Or stop all running Docker containers cleanly
  docker stop $(docker ps -q)
  ```

### Symptom: Docker Daemon Fails to Start on macOS / Windows
- **Resolution:**
  1. Restart Docker Desktop from the system menu.
  2. Increase allocated memory and CPU in Docker Desktop > Settings > Resources (minimum recommended: 4 CPUs, 8 GB RAM).
  3. If disk space is exhausted, run container prune:
     ```bash
     docker system prune -a --volumes
     ```

---

## 3. Database Migration Deadlocks (Alembic / PostgreSQL)

### Symptom: Alembic Reports "Target database is not up to date" or Migration Table Locked
- **Resolution:**
  1. Inspect the current revision in your local database:
     ```bash
     alembic current
     ```
  2. If a migration failed midway, verify the state in table `alembic_version`.
  3. To reset your local development database cleanly:
     ```bash
     docker compose down -v
     docker compose up -d postgres
     alembic upgrade head
     ```

---

## 4. GitHub SSH Access Issues

### Symptom: `git@github.com: Permission denied (publickey)`
- **Resolution:**
  1. Verify your SSH agent is running and your key is loaded:
     ```bash
     ssh-add -l
     ```
  2. If empty, add your Aurelia key:
     ```bash
     ssh-add --apple-use-keychain ~/.ssh/id_ed25519  # macOS
     ssh-add ~/.ssh/id_ed25519                       # Linux/Windows
     ```
  3. Verify connection to GitHub:
     ```bash
     ssh -T git@github.com
     # Expected: "Hi username! You've successfully authenticated..."
     ```

---

## 5. Okta MFA & Password Recovery

### Symptom: New Phone Device / Cannot Receive Okta Push Notifications
- **Resolution:**
  1. If you still have your laptop signed in, navigate to `https://aurelia.okta.com/settings` and register a secondary authentication method or backup security key.
  2. If locked out completely, request an MFA reset in `#it-urgent` on Slack or call the emergency IT support line at `+1 (800) 555-NXRA`. A live identity verification with your direct manager will be conducted before credentials are reset.

---

## 6. IT Service Desk Response SLAs & Escalation Matrix

| Priority Level | Description | Target First Response | Target Resolution | Escalation Channel |
| :--- | :--- | :--- | :--- | :--- |
| **P1 - Critical** | Company-wide system down, security breach, total work stoppage | < 15 minutes | < 2 hours | Slack `#it-urgent` & PagerDuty |
| **P2 - High** | Individual employee unable to access primary work tools (VPN, laptop lockout) | < 1 hour | < 4 hours | Jira Service Desk (High) |
| **P3 - Medium** | Software license request, non-blocking bug, hardware accessory request | < 4 business hours | < 24 business hours | Jira Service Desk (Medium) |
| **P4 - Low** | General inquiries, documentation clarification, long-term requests | < 1 business day | < 3 business days | Email `it-servicedesk@aureliatech.com` |
