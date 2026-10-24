# Aurelia Tech — Engineering Standards & Practices

> **Notice:** This document contains illustrative demonstration engineering guidelines for *Aurelia Tech*. Last updated: January 2026. Document Owner: Technical Architecture Board (`architecture-board@aureliatech.com`).

---

## 1. Core Engineering Philosophy

Engineering at Aurelia is centered around three tenets:
1. **Maintainability over Cleverness:** Code is read significantly more often than it is written. Simple, expressive patterns with clear typing are preferred over obscure abstractions.
2. **Automated Quality Verification:** If a behavior is not covered by an automated test in CI, it cannot be considered reliable.
3. **Continuous Deployment with Safety Guards:** Fast, small releases accompanied by comprehensive telemetry, automated canary rollouts, and instant rollback mechanisms.

---

## 2. Git Workflow & Branching Strategy

Aurelia follows a trunk-based branching workflow with lightweight feature branches:

- **Branch Naming Conventions:**
  - `feat/JIRA-123-short-description`: New functional capabilities.
  - `fix/JIRA-456-bug-summary`: Bug fixes and remediations.
  - `refactor/component-name`: Architectural or code health improvements without behavioral changes.
  - `docs/section-update`: Documentation or diagram updates.
  - `chore/dependency-upgrade`: Routine dependency updates or tooling maintenance.
- **Trunk Protection:** The `main` branch is protected. Direct commits and force pushes are blocked.
- **Commit Messages:** Follow the Conventional Commits specification:
  ```text
  feat(auth): implement JWT refresh token rotation mechanism [JIRA-102]
  fix(billing): correct stripe webhook idempotency key check [JIRA-205]
  ```

---

## 3. Pull Request (PR) Requirements & Code Reviews

Every change proposed to `main` must meet the following criteria before merging:
1. **Peer Approvals:** Minimum of **two positive code reviews** (`LGTM` approvals) from senior or peer engineers on the owning team.
2. **Automated CI Checks:**
   - Unit and integration test suites must pass 100%.
   - Code coverage must not drop below **80%** on changed lines.
   - Static analysis, linting (`ruff`, `eslint`), and type checking (`mypy`, `tsc`) must report zero errors.
   - Vulnerability scanners (`trivy`, `dependabot`) must report zero High or Critical vulnerabilities.
3. **PR Size Limit:** Pull requests should aim for fewer than **400 lines of modified code** to ensure reviewers can perform a thorough analysis. Large features should be decomposed into smaller, incrementally deployable PRs behind feature flags.
4. **Description Template:** Every PR must articulate:
   - What problem is being solved.
   - Architecture or design decisions made.
   - How the change was tested manually and automatically.
   - Screenshots or terminal logs for UI or CLI changes.

---

## 4. Testing Pyramid & Verification Guidelines

- **Unit Tests:** Fast, isolated tests executing in milliseconds. Mock external networks, third-party APIs, and databases.
- **Integration Tests:** Verify interactions between application components, databases, and message queues using ephemeral Docker containers (`testcontainers`).
- **End-to-End (E2E) & Smoke Tests:** High-value user journey tests executed against staging environments before production promotion.
- **Contract Testing:** Microservices communicate using OpenAPI schemas or Protocol Buffers, verified in CI using consumer-driven contract tests.

---

## 5. Coding Standards by Language

### Python (Backend & ML)
- Follow **PEP 8** style guidelines, enforced automatically via **Ruff** for linting and formatting.
- Strict typing with **Mypy** on all public functions, classes, and Pydantic schemas.
- Use explicit docstrings following Google Python Style Guide for public APIs.
- Handle exceptions deliberately; never use bare `except:` clauses.

### TypeScript / JavaScript (Frontend)
- Enforce strict mode in `tsconfig.json`.
- Functional React components with custom hooks; avoid class components.
- State management via Zustand or React Query; avoid prop drilling.
- ESLint with Airbnb / TypeScript recommended ruleset.

---

## 6. Observability, Logging & Telemetry

- **Structured Logging:** All services must output logs in structured JSON format with standard fields:
  - `timestamp`: ISO-8601 UTC.
  - `level`: DEBUG, INFO, WARNING, ERROR, CRITICAL.
  - `trace_id` & `span_id`: Injected automatically via OpenTelemetry context propagation.
  - `message`: Clear, human-readable description.
  - `service_name`: Identifier of the microservice.
- **PII Scrubbing:** Personally Identifiable Information (passwords, credit cards, emails, social security numbers) must never be written to application logs.
- **Metrics & Alerting:** Services must expose Prometheus metrics endpoints (`/metrics`) tracking HTTP request rates, error rates (5xx), and P95/P99 latency.

---

## 7. Architecture Decision Records (ADRs)

Substantial technical changes—such as adopting a new database, altering an authentication mechanism, or introducing a major framework—must be proposed via an **Architecture Decision Record (ADR)** submitted to `docs/adr/`. The ADR is reviewed by the Technical Architecture Board before implementation begins.
