# Aurelia Tech — IT Onboarding & Workplace Technology Guide

> **Notice:** This document contains illustrative demonstration IT procedures for *Aurelia Tech*. Last updated: January 2026. Document Owner: Information Technology & Security Operations (`it-servicedesk@aureliatech.com`).

---

## 1. First Day Hardware & Equipment Setup

- **Standard Hardware Provisioning:**
  - **Engineering & Product:** Apple MacBook Pro 14" or 16" (M-series, 32GB Unified Memory, 1TB SSD).
  - **Operations, Finance & Client Success:** Dell XPS 15 or Lenovo ThinkPad X1 Carbon (Intel Core i7, 32GB RAM, 512GB SSD) running Windows 11 Enterprise.
- **Shipment:** Laptops are pre-configured with Jamf/Intune mobile device management (MDM) and shipped to your home address to arrive 2-3 business days prior to your start date.
- **Initial Boot & Zero-Touch Deployment:** Power on the laptop, connect to Wi-Fi, and log in using the temporary credentials sent to your personal email. The device will automatically install Aurelia security profiles and required software agents.

---

## 2. Core Accounts & Collaboration Suite

Your primary accounts are provisioned 48 hours prior to your start date:
- **Email & Calendar:** Google Workspace (`firstname.lastname@aureliatech.com`).
- **Team Communication:** **Slack** — primary internal messaging platform. Key default channels:
  - `#announcements`: Company-wide news and updates.
  - `#general`: General discussion and social interaction.
  - `#it-support`: Everyday IT questions and help requests.
  - `#it-urgent`: Critical production or access blockers (monitored 24/7).
- **Project Tracking:** **Jira Software & Confluence** (Engineering, Product, Operations).
- **Source Code Management:** **GitHub Enterprise** (Engineering team members are invited to the `@aurelia-tech` organization).
- **Identity & Password Management:** **Okta Single Sign-On (SSO)** and **1Password Business** for secure password storage.

---

## 3. Password Standards & Multi-Factor Authentication (MFA)

- **Password Complexity Rules:**
  - Minimum length: **12 characters**.
  - Must include uppercase letters, lowercase letters, numbers, and special symbols (`!@#$%^&*`).
  - Passwords expire and must be rotated every **90 days** via Okta.
  - Password reuse is restricted across the previous 10 passwords.
- **Multi-Factor Authentication (MFA):**
  - Mandatory for all company accounts using **Okta Verify** with push notifications or hardware FIDO2 keys (YubiKey).
  - SMS-based MFA is strictly prohibited due to SIM-swapping vulnerabilities.
- **Credential Sharing Prohibition:** Sharing login credentials, API tokens, or SSH keys with other employees or external contractors is a direct violation of company policy.

---

## 4. VPN and Remote Access Guidelines

- **Access Requirement:** All connections to Aurelia internal resources, staging environments, internal wikis, and cloud bastions require an active **Aurelia Secure VPN** connection, even when working from an office hub.
- **Client Configuration:** Pre-installed on your laptop as *Aurelia Connect* (OpenVPN/WireGuard protocol). Authenticate via Okta SSO and complete MFA.
- **Troubleshooting VPN Connections:**
  1. Verify your local internet connection is functional.
  2. Disconnect and restart the VPN client.
  3. If connection errors persist after two attempts, submit an urgent ticket to `#it-support`. Do not disable security agents or attempt manual network overrides.

---

## 5. Software Request & Approval Workflow

- **Pre-Approved Standard Software Catalog:** Available directly via the self-service portal (Self Service on macOS / Company Portal on Windows), including VS Code, Docker Desktop, Postman, Slack, and Zoom.
- **Purchased Software Requests:**
  - **Under $50 USD / month:** Auto-approved within 1 business day via the IT Service Desk.
  - **Over $50 USD / month:** Requires formal written approval from your direct manager in the Jira Service Management portal.

---

## 6. Engineering Development Environment Setup

New software engineers must complete the following baseline local configuration:
1. **Xcode Command Line Tools / Windows Subsystem for Linux (WSL2):**
   ```bash
   xcode-select --install  # macOS
   ```
2. **Package Management:** Install Homebrew (macOS) or Chocolatey (Windows).
3. **Runtime Environments:**
   - **Python:** Managed via `pyenv` (recommended version: Python 3.11.x).
   - **Node.js:** Managed via `nvm` (recommended LTS version: Node 20.x).
   - **Go:** Go 1.22+ for microservices.
4. **Containerization:** Install **Docker Desktop** through the company Self-Service catalog to ensure compliance with enterprise licensing.
5. **SSH Key Registration:** Generate an `ed25519` SSH key pair and register the public key in GitHub Enterprise:
   ```bash
   ssh-keygen -t ed25519 -C "firstname.lastname@aureliatech.com"
   ```

---

## 7. Reporting IT Incidents & Getting Support

- **Standard Help Desk Tickets:** Submit requests via the Jira Service Management portal or email `it-servicedesk@aureliatech.com` (SLA: First response within 4 business hours).
- **Urgent / P1 Blocker Issues:** Post directly in the `#it-urgent` Slack channel with:
  - Brief description of the issue.
  - System or service affected.
  - Impact on deliverables.
- **Account Lockouts & Recovery:** Contact the on-call IT administrator via the automated self-service phone helpline or reach out to your manager for identity verification.

---

## 8. Offboarding and Equipment Return

Upon departure from Aurelia Tech:
- All system access, SSO tokens, and VPN credentials are automatically decommissioned at 5:00 PM on the employee's final working day.
- Company hardware must be returned using the prepaid shipping container provided by IT within **5 business days** of departure.