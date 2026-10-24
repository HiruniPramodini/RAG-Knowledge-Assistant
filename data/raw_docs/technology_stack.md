# Aurelia Tech — Enterprise Technology Stack

> **Notice:** This document catalogs the approved demonstration technology stack for *Aurelia Tech*. Last updated: January 2026. Document Owner: Platform Engineering & Enterprise Architecture (`tech-stack@aureliatech.com`).

---

## 1. Overview of Technology Strategy

Aurelia's technology stack is designed around containerized microservices, strong static typing, asynchronous performance, and managed cloud-native infrastructure. We maintain an approved technology catalog to prevent tool proliferation while encouraging targeted experimentation.

---

## 2. Core Programming Languages & Frameworks

### Backend Engineering
- **Python (3.11+ / 3.12+):** Primary language for data engineering, machine learning services, and core microservices. Standard backend framework: **FastAPI** (asynchronous, Pydantic-powered validation, automatic OpenAPI generation).
- **Go (Golang 1.22+):** Utilized for high-throughput network proxies, telemetry ingestion agents, and platform tooling requiring minimal memory footprints and single-binary distribution.
- **Node.js (TypeScript / Express / Fastify):** Used selectively for specialized client integration adapters and GraphQL gateway endpoints.

### Frontend Engineering
- **React (18+) with TypeScript:** Standard framework for enterprise web portals, customer dashboards, and internal operational tools.
- **Next.js & Vite:** Modern build tools and application frameworks powering single-page applications (SPAs) and server-side rendering (SSR).
- **Styling & Design System:** Tailwind CSS paired with Aurelia's proprietary accessible component library (*Aurelia UI*).

---

## 3. Databases, Vector Stores & Caching

- **Relational Databases:** **PostgreSQL (v15+)** hosted on AWS RDS with Multi-AZ redundancy, connection pooling via PgBouncer, and JSONB capabilities for semi-structured schemas.
- **In-Memory Caching & Session Storage:** **Redis (v7+)** utilized for distributed session management, API rate limiting, pub/sub event streams, and caching hot read queries.
- **Vector Search & Embeddings Storage:** 
  - **ChromaDB:** Local and embedded vector database for fast, lightweight retrieval and on-premise AI assistants.
  - **pgvector:** Scalable vector similarity extension on managed PostgreSQL for enterprise RAG deployments.

---

## 4. Artificial Intelligence & Machine Learning Stack

- **LLM Foundation Models:** **Google Gemini API** (`gemini-2.5-flash` for high-throughput grounded synthesis and reasoning; `gemini-2.5-flash-lite` for ultra-low latency routing and intent classification).
- **Embedding Models:** `models/gemini-embedding-001` (3072-dimensional dense vector embeddings).
- **Agentic Orchestration:** **LangChain** and **LangGraph** for cyclic state graphs, multi-turn conversational agents, and deterministic tool dispatching.
- **ML Frameworks:** PyTorch, scikit-learn, and Hugging Face Transformers for custom predictive models.

---

## 5. Cloud Infrastructure & Platform Services

- **Cloud Provider:** **Amazon Web Services (AWS)** primary cloud platform.
- **Compute & Container Orchestration:**
  - **AWS Elastic Kubernetes Service (EKS):** Primary container orchestration platform for all production microservices.
  - **AWS Fargate / ECS:** Serverless container execution for asynchronous batch tasks and background workers.
  - **AWS Lambda:** Event-driven serverless executions for webhook handlers and scheduled cron triggers.
- **Infrastructure as Code (IaC):** **Terraform** for declarative provisioning of all cloud resources, modules versioned via GitHub.
- **Containerization:** **Docker** images built multi-stage with minimal Alpine/Debian-slim base images to minimize security attack surfaces.

---

## 6. CI/CD & DevOps Automation

- **Source Control & CI:** **GitHub Enterprise** and **GitHub Actions**. All test suites, security scans, Docker builds, and deployment gates run on automated runner workflows.
- **Artifact Registry:** Amazon Elastic Container Registry (ECR) for immutable Docker image tags and Helm charts.
- **Deployment Strategy:** ArgoCD GitOps operator executing blue-green and progressive canary deployments.

---

## 7. Monitoring, Logging & Observability

- **Distributed Tracing:** **OpenTelemetry (OTel)** instrumentation across HTTP services and database connections.
- **Metrics Aggregation:** **Prometheus** paired with **Grafana** dashboards for real-time infrastructure and application telemetry.
- **Log Management:** Centralized OpenSearch / CloudWatch log clusters with retention policies aligned with compliance standards.
- **Incident Alerting:** PagerDuty integration with on-call rotation schedules.
