# Aurelia Tech — Current Projects & Strategic Initiatives

> **Notice:** This document catalogs active demonstration engineering projects and strategic initiatives for *Aurelia Tech*. Last updated: January 2026. Document Owner: Project Management Office & Engineering Leadership (`pmo@aureliatech.com`).

---

## 1. Project Atlas — Unified Client Success Platform

- **Objective & Business Problem:** Consolidate client account health monitoring, contract renewal schedules, support escalation telemetry, and usage analytics into a single real-time portal. It replaces three fragmented legacy CRM tools.
- **Owning Team:** Product Engineering Squad (*Team Atlas*), comprising 6 software engineers, 1 product manager, 1 UX designer, and 1 QA lead.
- **Technology Architecture:**
  - **Frontend:** React 18, TypeScript, Tailwind CSS, Vite.
  - **Backend:** Python 3.11, FastAPI, SQLAlchemy async ORM.
  - **Data Tier:** AWS Aurora PostgreSQL, Redis cache.
  - **Telemetry:** OpenTelemetry with Grafana dashboard.
- **Deployment & Status:** Currently in **Production Release v2.4**. Serving 85 internal Client Success Managers across Austin and Lisbon hubs.
- **Repository Reference:** `github.com/aurelia-tech/atlas-platform-demo` (internal).

---

## 2. Project Horizon — Enterprise Data & AI Initiative

- **Objective & Business Problem:** Introduce applied AI and intelligent automation across client deliverables and internal knowledge discovery. Core sub-initiatives:
  1. *Client Churn Predictor:* An XGBoost and neural ranking model forecasting client churn risk 90 days prior to contract expiration.
  2. *Enterprise Knowledge Assistant (RAG):* An internal AI knowledge assistant enabling employees to query HR, IT, and engineering documentation with verified citations and agentic tool routing.
- **Owning Team:** Data & AI Team, comprising 4 Machine Learning Engineers, 2 Data Platform Engineers, and 1 MLOps Specialist, reporting jointly to the CTO and CPO.
- **Technology Architecture:**
  - **Core Frameworks:** Python 3.11, LangChain, LangGraph state machine.
  - **LLM Foundation:** Google Gemini API (`gemini-2.5-flash` synthesis, `gemini-2.5-flash-lite` router).
  - **Vector Database:** ChromaDB with dense embeddings (`gemini-embedding-001`).
  - **Frontend:** Streamlit enterprise chat application.
- **Deployment & Status:** Currently in **Beta Phase / Pilot Rollout**. Under evaluation by 60 pilot employees across all departments.

---

## 3. Project Beacon — Platform Reliability & Cloud Modernization

- **Objective & Business Problem:** Enhance infrastructure resilience, eliminate single points of failure, migrate lingering legacy VMs into containerized Kubernetes pods, and institute zero-downtime automated deployment pipelines.
- **Owning Team:** Platform Engineering & SRE Team (5 site reliability engineers) reporting to the VP of Platform.
- **Key Milestones Achieved:**
  - Containerized 100% of core customer-facing backend APIs on AWS EKS.
  - Implemented automated canary deployment rollouts via ArgoCD with automated rollback on error spikes (>0.5% 5xx).
  - Reduced mean time to recovery (MTTR) by 42% across Q3-Q4.
- **Deployment & Status:** **Active Multi-Quarter Initiative**. Next phase focuses on multi-region failover and cross-cloud disaster recovery drills.

---

## 4. Retail Client Onboarding Revamp

- **Objective & Business Problem:** Streamline implementation workflows for enterprise retail customers, shortening onboarding time from 6 weeks down to 3 weeks through self-service schema mapping tools and automated data validation scripts.
- **Owning Team:** Cross-functional initiative co-led by Product and Client Success.
- **Deployment & Status:** **Scheduled for Q2 2026 completion**. Currently in pilot testing with two enterprise retail partner accounts.

---

## 5. Quarterly Innovation Time & Employee Hackathons

- **Policy:** Aurelia allocates **10% of engineering bandwidth** (roughly 1 day every two weeks or a concentrated 3-day sprint per quarter) to *Innovation Time*.
- **Eligibility:** All engineers, data scientists, and technical product managers who are on schedule with core deliverables.
- **Process:** Employees pitch internal tooling improvements, open-source bug fixes, or prototype experimental machine learning models. Selected projects often graduate to official company roadmap items (as Project Horizon originated).