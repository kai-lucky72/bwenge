# Full Developer-Ready System Architecture & Sprint Plan — **Bwenge OS**

Beautiful — below is a **complete, developer-actionable system architecture** for Bwenge OS plus a concrete **sprint plan** your team can follow. This document is intended to be the single source developers use to start building, split work, and track progress. It contains:

* high-level and detailed architecture (components, responsibilities, infra)
* APIs & data models to implement first
* repository / folder structure suggestions
* sequence & data flows for main scenarios
* CI/CD, observability, security notes
* a sprint roadmap with tasks, owners, acceptance criteria

Use this as the blueprint to hand to devs and start coding.

---

# 1 Top-Level Architecture (text + components)

```
Users (Web/Mobile) 
   ↕ HTTPS / WS
Frontend (React/Next + React-Three-Fiber)
   ↕ REST / WS
API Gateway (FastAPI)  <-- Authentication, routing, rate limit
   ├─ Auth & User Service (FastAPI + Postgres)
   ├─ Knowledge Ingest Service (FastAPI + Celery workers)
   ├─ Persona / AI Engine Service (FastAPI)  ←→ LLM Orchestrator (OpenAI / Gemini / local)
   ├─ Chat Service (WebSocket sessions)
   ├─ 3D Model Service (metadata + signed URLs)
   ├─ Analytics Service (Postgres / Timescale)
   ├─ Payment & Subscription Service (Stripe/Paystack)
   └─ Automation & Scheduler (Celery beat)
Data Layer:
   ├─ PostgreSQL (meta, users, personas, conversations)
   ├─ Vector DB (Weaviate / Qdrant / Chroma) (embeddings)
   ├─ Object Storage / CDN (Supabase / S3 + Cloudflare)
   └─ Redis (cache + Celery broker)
Infra:
   ├─ Kubernetes / Managed cloud (GKE, EKS, Fly)
   ├─ CI/CD: GitHub Actions
   ├─ Observability: Prometheus + Grafana + Loki/ELK
   └─ Message Bus: Redis Streams / RabbitMQ (optional)
```

---

# 2 Component Responsibilities (developer checklist)

### API Gateway (FastAPI)

* Entrypoint for all REST and WebSocket calls.
* Tenant resolution (`X-Tenant-Id` or subdomain).
* JWT verification & refresh endpoints.
* Rate limiting, request validation, centralized logging.

### Auth & User Service

* CRUD for Users, Organizations, Roles.
* Multi-tenant logic.
* Invite / onboarding flows.
* Endpoints: `/auth/register`, `/auth/login`, `/auth/refresh`, `/users/me`, `/orgs/{id}/members`.

### Knowledge Ingestion Service

* Accept uploads (multipart + pre-signed URLs).
* Pipeline (async):

  * store raw files in object storage
  * transcribe audio/video (Whisper or OpenAI)
  * extract text from PDF/Word (PyMuPDF)
  * chunk text (smart chunking with overlap)
  * create embeddings
  * push vectors to Vector DB with metadata (persona_id, chunk_id, source)
* Endpoints: `/knowledge/upload`, `/knowledge/{id}/status`, `/knowledge/{id}/delete`.

### Vector DB (Weaviate recommended)

* Stores chunk vectors + metadata.
* Search API used by Persona Engine.
* Schema: chunk text, embedding, persona_id, org_id, source_id, timestamp.

### Persona / AI Engine Service

* Persona CRUD & configs (tone, safety rules, sample dialogs).
* RAG orchestration:

  * retrieve top-K vectors filtered by persona/org
  * assemble system prompt (persona rules) + context + session history
  * call LLM(s) via Orchestrator (supports primary & fallback)
  * produce structured response: `{text, actions, suggested_gesture, citations}`
* Session memory management (short-term + pointer to long-term vectors).
* Endpoints: `/personas`, `/ai/respond`, `/personas/{id}/settings`.

### LLM Orchestrator

* Abstracts calls to external LLMs (OpenAI, Gemini) and local LLMs (Llama).
* Handles retry, rate limits, cost control, and streaming.
* Implements prompt templates and token management.

### Chat Service

* WebSocket server for real-time messaging & streaming.
* Maintains ephemeral session context and handles message persistence.
* Integrates TTS triggers (if enabled).

### 3D Model Service

* Stores metadata for avatars and objects: model_url, animations, default_mappings.
* Provides signed URLs (short lived) for asset download.
* Endpoint: `/3d/persona/{persona_id}` → `{model_url, animations, scale, bounding_box}`.

### Analytics Service

* Event ingestion (message events, quiz results, usage).
* Aggregations and report generation.
* Dashboard endpoints for orgs: `/orgs/{id}/reports`, `/orgs/{id}/student/{id}/progress`.

### Automation & Scheduler (Celery + Redis)

* Handles ingestion tasks, scheduled retraining, weekly reports, reminders.
* Celery Beat for periodic tasks.

### Payment & Subscription Service

* Integrate Stripe / Paystack.
* Webhook handling for payment events.
* Plan enforcement for usage quotas, storage.

---

# 3 Key APIs & sample payloads (implement first)

Implement these first so front-end and backend teams can start parallel:

Auth & Users

* `POST /auth/register`

  * body: `{name, email, password, orgName (opt)}`
* `POST /auth/login`

  * body: `{email, password}`
* `GET /users/me`
* `POST /orgs/{orgId}/invite`

Knowledge

* `POST /knowledge/upload` (multipart returning uploadId)
* `GET /knowledge/{uploadId}/status`
* `DELETE /knowledge/{id}`

Persona & AI

* `POST /personas` — create persona (body: `{name, orgId, tone, samplePrompts, safetyRules}`)
* `GET /personas/{id}`
* `POST /ai/respond` — sync mode (body: `{personaId, sessionId, userId, userMessage}`)

  * returns: `{responseText, actions:[{type, payload}], citations:[]}`
* `WS /ws/chat?persona={id}&session={s}` — streaming chat

3D

* `GET /3d/persona/{personaId}` → `{modelUrl, animations, version, mime}`

Analytics

* `GET /orgs/{orgId}/reports/weekly`
* `GET /orgs/{orgId}/students/{id}/progress`

Payment

* `POST /payments/subscribe` — returns checkout link
* `POST /webhooks/payment` — handle events

---

# 4 Database basic schema (starter)

Use PostgreSQL with these core tables. Extend as needed.

`organizations (org_id pk, name, plan, created_at)`
`users (user_id pk, org_id fk, name, email, role, password_hash, created_at)`
`personas (persona_id pk, org_id fk, name, tone jsonb, rules jsonb, created_at)`
`knowledge_sources (source_id pk, org_id fk, persona_id fk, title, type, status, storage_path)`
`conversations (conv_id, persona_id, user_id, messages jsonb, created_at, updated_at)`
`analytics_events (event_id, org_id, user_id, type, payload jsonb, timestamp)`

Vectors stored in vector DB with metadata referencing `source_id` and `persona_id`.

---

# 5 Repository & folder structure (recommended)

```
/bwenge
  /docs                  # architecture docs, sequence diagrams
  /deploy                # k8s manifests, helm charts, terraform (optional)
  /services
    /api-gateway         # FastAPI gateway (routes, auth middlewares)
    /auth-service        # FastAPI microservice + migrations
    /ingest-service      # FastAPI + Celery workers
    /persona-service     # FastAPI (RAG + orchestration)
    /chat-service        # WS server (FastAPI or Socket.IO)
    /3d-service          # metadata, signed-url generator
    /analytics-service   # aggregator, reports
    /payments-service    # stripe integration
  /libs
    /common              # shared DTOs, auth utils, logging
  /infra
  /scripts
  README.md
```

Each service should be containerized with a `Dockerfile` and have its own `requirements.txt` (Python) or `package.json` if Node is used.

---

# 6 Sequence / Data Flows (developer diagrams in words)

### Flow: Upload → Teach (example Gabriel)

1. Teacher uploads `POST /knowledge/upload` → file stored in Object Storage and uploadId returned.
2. API enqueues Celery job `process_upload(uploadId)`.
3. Worker downloads file → if audio/video: transcribe via Whisper → extract text.
4. Worker chunks text → requests embeddings from embedding service → writes vectors to Vector DB with metadata `{org_id, persona_id, source_id, chunk_id}`.
5. Knowledge status set to `ready`.
6. Student asks: open WebSocket `WS /ws/chat?persona=gabriel`.
7. Chat Service forwards message to Persona Service: `POST /personas/{id}/respond` with session context.
8. Persona Service queries Vector DB (top K), assembles prompt (system persona + retrieved chunks + last N messages), calls LLM via Orchestrator.
9. LLM returns response → Persona Service optionally adds `animation_hint`.
10. Chat Service streams response back to frontend; front-end fetches avatar model from 3D Service and triggers animation.

---

# 7 Non-functional requirements & infra details

* **Latency:** Aim ≤ 2s for simple queries (cached), 2–6s for RAG+LLM (depends on LLM).
* **Throughput:** Use autoscaling for API & workers; implement queue limits and backpressure.
* **Storage:** Use CDN for GLTF, S3/Supabase for files; sign URLs for access control.
* **Observability:** Instrument each service with metrics + logs. Central tracing with OpenTelemetry.
* **Security:** TLS everywhere, signed URLs, tenant isolation filters on Vector DB queries, RBAC checks per API.
* **Backups:** DB daily snapshots; vector DB export periodically.

---

# 8 Sprint Roadmap (8 sprints, 2 weeks each — 16 weeks total)

Each sprint includes owner(s), tasks, deliverables, acceptance criteria.

---

## Sprint 0 — Prep & Infra (1 week; optional pre-sprint)

**Goal:** Project kickoff, repo setup, infra basics
**Owners:** Both
**Tasks:**

* Create repo structure + CI skeleton (GitHub Actions)
* Create cloud accounts, object storage, basic Postgres, Redis
* Define subdomain / tenant strategy
  **Deliverables:**
* Repo + CI created
* Minimal infra accessible
  **Acceptance:** Can run `docker-compose up` locally with Postgres & Redis.

---

## Sprint 1 — Auth, API Gateway, and User model (2 weeks)

**Goal:** Implement auth flow, org & user CRUD, API gateway skeleton
**Owners:** You (Auth/API), Friend (help design tokens)
**Tasks:**

* Auth service + DB migrations
* JWT + refresh tokens
* User & Org CRUD endpoints
* API Gateway basic routing & tenant middleware
* Basic frontend auth pages (login/register)
  **Deliverables:**
* `POST /auth/register`, `POST /auth/login`, `GET /users/me`
* Integration tests
  **Acceptance:** Manual sign-up/login flow works; tokens validate across services.

---

## Sprint 2 — Storage + Knowledge Upload + Worker (2 weeks)

**Goal:** Upload flow + async processing scaffold
**Owners:** You (storage + Celery), Friend (transcription pipeline prototype)
**Tasks:**

* Implement `/knowledge/upload` endpoint (presigned/upload strategy)
* Setup Celery + Redis broker
* Worker job skeleton to download file and store metadata
* Add simple PDF/Text extraction (PyMuPDF)
  **Deliverables:**
* Upload -> job enqueued -> job stores `knowledge_sources` record
  **Acceptance:** Upload a PDF → job runs → `knowledge_sources.status` = `processing`.

---

## Sprint 3 — Transcription, Chunking & Embeddings (2 weeks)

**Goal:** Build ingestion pipeline: transcription (Whisper), chunking, embedding push to Vector DB
**Owners:** Friend (embedding & vector DB), You (worker orchestration)
**Tasks:**

* Integrate Whisper or OpenAI audio for transcription
* Implement chunking algorithm with overlap
* Integrate embedding API (OpenAI embeddings or local)
* Write vectors to Weaviate with metadata
  **Deliverables:**
* `knowledge_sources` status = `ready` and vector count stored
  **Acceptance:** Uploaded document is searchable via vector DB (test query returns chunks).

---

## Sprint 4 — Persona CRUD & RAG prototype (2 weeks)

**Goal:** Persona creation + retrieval + basic RAG
**Owners:** Friend (Persona & RAG), You (DB & APIs)
**Tasks:**

* Persona create/read/update endpoints
* Implement a basic Persona template (system prompt)
* Implement RAG query: retrieve top-K chunks from vector DB given user prompt
* Build LLM Orchestrator stub + call OpenAI/Gemini (dev keys)
  **Deliverables:**
* `POST /personas`, `POST /ai/respond` returns response using retrieved chunks
  **Acceptance:** A test prompt with persona returns coherent response including citations to chunks.

---

## Sprint 5 — Chat Service (WebSocket), Conversation persistence (2 weeks)

**Goal:** Real-time chat with session context and streaming
**Owners:** Friend (chat & streaming), You (persistence)
**Tasks:**

* Implement WebSocket server for chat sessions
* Stream LLM responses over WS (chunked)
* Persist conversations to DB
* Simple frontend chat UI
  **Deliverables:**
* Live chat between frontend and Persona service
  **Acceptance:** Conversation flows through WS, stored in `conversations` table.

---

## Sprint 6 — 3D Service + Frontend Integration (2 weeks)

**Goal:** 3D model metadata service + basic avatar rendering in frontend
**Owners:** You (3D service API), Frontend contractor (rendering), Friend (mapping)
**Tasks:**

* Implement 3D model service endpoints and storage references
* Provide `animation_hint` field in AI response
* Frontend loads GLTF and plays default animation
  **Deliverables:**
* 3D Avatar appears in chat, reacts with `animation_hint`
  **Acceptance:** When LLM returns animation hint, the avatar plays corresponding clip.

---

## Sprint 7 — Analytics, Automation, & Reports (2 weeks)

**Goal:** Event ingestion, weekly reports, scheduled tasks
**Owners:** You (automation), Friend (analytics integration)
**Tasks:**

* Event tracking & analytics store
* Celery Beat scheduled jobs for weekly report generation
* Implement `/orgs/{id}/reports/weekly`
  **Deliverables:**
* Weekly report email or dashboard generation
  **Acceptance:** Reports reflect interactions from the week.

---

## Sprint 8 — Payments, Hardening, Tests & Pilot (2 weeks)

**Goal:** Payment integration, quotas, security hardening, pilot readiness
**Owners:** You (payments + infra), Friend (model cost control + safety)
**Tasks:**

* Integrate Stripe/Paystack + webhook handling
* Implement quotas & usage enforcement per org
* Add logging, metrics, and alerting
* End-to-end tests, security review
* Pilot deployment for 1–2 schools
  **Deliverables:**
* Billing flow, quotas enforced, pilot usage
  **Acceptance:** Pilot users can sign up, upload content, chat, and receive invoices; no major security issues.

---

# 9 Acceptance Criteria per Sprint (short list)

* Unit & integration tests pass (CI)
* Endpoints documented (OpenAPI)
* Basic front-end workflow demonstrated
* Security checks (auth flows) verified
* Vector DB queries return expected results

---

# 10 Who does what — two-person split (detailed)

**You (Kagabo)** — Backend, infra, infra-as-code, storage, auth, payments, deployment, monitoring.

* Sprint leads: 1 (Auth), 2 (Upload/Workers), 6 (3D storage), 7 (Automation), 8 (Payments/Infra).

**Friend (AI Expert)** — Persona engine, embeddings, vector DB, RAG, LLM orchestration, chat streaming.

* Sprint leads: 3 (embeddings), 4 (persona & RAG), 5 (Chat + streaming), 6 (3D mapping).

Shared responsibilities: prompt design, safety rules, end-to-end tests, pilot engagement.

---

# 11 CI/CD, testing & observability (must implement early)

* CI pipeline:

  * Unit tests → Lint → Build Docker images → Push to registry
  * Deploy to staging on merge to `main`
* CD: GitHub Actions with approval for prod deploys.
* Tests:

  * Unit tests per service
  * Integration tests for ingest→embed→retrieve flow
  * E2E tests with Playwright for basic frontend flows
* Observability:

  * Prometheus metrics per service; Grafana dashboards (request rate/latency, queue length)
  * Centralized logs: Loki/ELK
  * SLOs & Alerts: error rate > 2% triggers alert

---

# 12 Security & privacy (must implement before pilot)

* Tenant isolation on queries (always include `org_id` filter)
* Signed URLs for asset downloads (short TTL)
* Encrypt sensitive data in DB (PHI if required)
* Audit logs for admin actions & downloads
* Data retention & export features for compliance

---

