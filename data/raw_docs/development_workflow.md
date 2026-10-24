# Aurelia Tech — Development Workflow & Release Guide

> **Notice:** This document outlines daily engineering workflows and release practices for *Aurelia Tech*. Last updated: January 2026. Document Owner: Developer Experience Guild (`devex@aureliatech.com`).

---

## 1. Local Environment Bootstrap

1. **Clone the Repository:** Always clone repositories using SSH keys configured with GitHub Enterprise:
   ```bash
   git clone git@github.com:aurelia-tech/project-demo.git
   cd project-demo
   ```
2. **Environment Configuration:**
   Copy the provided `.env.example` file to create your local `.env`:
   ```bash
   cp .env.example .env
   ```
   *Never commit `.env` files to git. All credentials must be local or sourced from the 1Password Developer CLI.*
3. **Install Pre-Commit Hooks:**
   We enforce formatting and security scanning on every local git commit:
   ```bash
   pip install pre-commit
   pre-commit install
   ```

---

## 2. Docker Compose Local Workflows

All projects provide a standard `docker-compose.yml` defining the local developer runtime, including PostgreSQL, Redis, and mock service dependencies:

```bash
# Start all supporting services in the background
docker compose up -d postgres redis

# Check container health status
docker compose ps

# View real-time container logs
docker compose logs -f postgres

# Stop all local containers and preserve database volumes
docker compose down
```

---

## 3. Database Migrations

- **Tooling:** Python services utilize **Alembic**; Go services utilize **golang-migrate**.
- **Generating a Migration:**
  ```bash
  alembic revision --autogenerate -m "add_client_contract_status_column"
  ```
- **Reviewing Migration SQL:** Always inspect generated migration scripts in `alembic/versions/` before executing. Migrations must be backward-compatible (expand-and-contract pattern) to prevent downtime during rolling deployments.
- **Applying Migrations Locally:**
  ```bash
  alembic upgrade head
  ```

---

## 4. Running Tests Locally

Before pushing a branch to GitHub, run the full test suite locally:

```bash
# Run unit and integration tests with coverage report
pytest tests/ -v --cov=src --cov-report=term-missing

# Run code style linter and static type verification
ruff check .
mypy src/
```

---

## 5. Continuous Integration (CI) Pipeline Stages

When a pull request is opened or updated on GitHub, the automated GitHub Actions pipeline executes the following sequential stages:

1. **Lint & Security Audit:** Ruff, ESLint, Trivy container scanner, Dependabot dependency checks.
2. **Unit Test Suite:** Executes parallelized unit test matrix on Python 3.11 and 3.12.
3. **Integration Test Suite:** Boots ephemeral PostgreSQL/Redis containers and runs integration specs.
4. **Build & Image Publishing:** Builds multi-stage Docker images and pushes to Amazon ECR tagged with the Git commit SHA.
5. **Preview Environment Provisioning:** Ephemeral preview environment deployed for QA manual inspection.

---

## 6. Staging and Production Release Protocols

- **Staging Promotion:** Merges into the `main` branch automatically deploy to the Staging environment via ArgoCD. Staging mirrors production configuration and receives automated synthetic traffic.
- **Production Deployment Gates:**
  - Production deployments take place Tuesday through Thursday between 10:00 AM and 2:00 PM EST.
  - No Friday or weekend production deployments except for critical severity (P0) security hotfixes.
  - Requires approval from the owning Tech Lead and SRE on-call.
- **Canary Rollout Strategy:**
  - 10% of user traffic routed to new canary pods for 15 minutes.
  - Automated Prometheus analysis checks error rate (must be < 0.1%) and latency.
  - If metrics remain green, traffic incrementally ramps to 50%, then 100%.
  - If error spikes occur, ArgoCD initiates an automatic, instant rollback.
