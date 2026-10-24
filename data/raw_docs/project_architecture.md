# Aurelia Tech — System Architecture & Design Guidelines

> **Notice:** This document illustrates system architecture and integration patterns for *Aurelia Tech*. Last updated: January 2026. Document Owner: Enterprise Architecture Guild (`ea-guild@aureliatech.com`).

---

## 1. Architectural Principles

All systems engineered at Aurelia conform to five architectural tenets:
1. **Decoupled Microservices:** Services own their database schemas; no direct cross-database queries. Inter-service data sharing occurs via RESTful APIs, gRPC, or asynchronous message events.
2. **Stateless Compute:** Backend service containers maintain no local state between requests, allowing horizontal autoscaling (HPA) in response to CPU/memory metrics.
3. **Defense in Depth & Zero Trust:** Every network connection is authenticated using mTLS. Service-to-service calls carry signed JWT authentication headers.
4. **Resilience & Fault Tolerance:** Circuit breakers, exponential backoff with jitter on network retries, and fallback degradation strategies prevent cascading service failures.
5. **API-First Design:** OpenAPI 3.1 specifications must be written, reviewed, and approved before backend API code is authored.

---

## 2. Standard Service Architecture Pattern

A typical Aurelia backend service follows the Clean/Hexagonal Architecture pattern:

```text
┌────────────────────────────────────────────────────────┐
│                   API Transport Layer                  │
│       FastAPI Routers, Input Validation, Rate Limiter  │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│                    Domain Core Layer                   │
│        Business Logic, Entity Validation, Policies      │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│                  Infrastructure Layer                  │
│     PostgreSQL Adapters, Redis Cache, S3 Storage, OTel │
└────────────────────────────────────────────────────────┘
```

---

## 3. Communication Patterns & Message Bus

- **Synchronous Communication:** REST over HTTP/2 for user-facing client requests. Internal low-latency inter-service calls utilize **gRPC** with Protocol Buffers.
- **Asynchronous Event Streaming:** Utilizes Apache Kafka / AWS Kinesis for streaming events (such as `client.account.created`, `invoice.paid`, `support.ticket.escalated`). Consumers guarantee idempotent event processing using deduplication keys.

---

## 4. Security & Identity Management Architecture

- **User Authentication:** OAuth 2.0 with OpenID Connect (OIDC) orchestrated by Okta.
- **Token Format:** Short-lived JSON Web Tokens (JWT) with a 15-minute expiration, paired with secure HTTP-only refresh cookies.
- **Role-Based Access Control (RBAC):** Permissions are encapsulated in JWT claims and enforced at the API gateway layer using fine-grained scopes (e.g., `atlas:clients:read`, `atlas:clients:write`).
- **Secrets Management:** AWS Secrets Manager and HashiCorp Vault. No plain text secrets or passwords exist in configuration files or Git repositories.

---

## 5. Storage Tier Architecture

- **Primary Relational Store:** AWS Aurora PostgreSQL in Multi-AZ clusters with automated failover (< 30 seconds) and read replicas.
- **Object Storage:** Amazon S3 with server-side encryption (SSE-KMS) and lifecycle policies transitioning documents older than 90 days to Glacier Instant Retrieval.
- **Vector Embeddings Store:** Local ChromaDB instances for lightweight indexing and pgvector on Aurora PostgreSQL for large-scale enterprise semantic vector searches.
