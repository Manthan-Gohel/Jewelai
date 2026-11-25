# JewelAI — System Architecture Specification

## 1. Executive Summary
JewelAI is a production-grade, asynchronous AI sales assistant built specifically for luxury jewellery retailers on the official Meta Instagram Platform. It bridges customer Instagram DMs to verified inventory, certified diamond/gold specifications, and multilingual customer service (English, Hindi, Gujarati).

---

## 2. Architecture & Data Flow

```
[ Instagram Customer ]
        │  (Text / Reference Photo DM)
        ▼
[ Meta Instagram Platform ]
        │  (POST /api/v1/webhooks/instagram with X-Hub-Signature-256)
        ▼
[ Caddy / Nginx Reverse Proxy ]
        │  (Reverse proxy to :8000)
        ▼
[ FastAPI Ingress Handler ]
        ├── 1. Validates HMAC-SHA256 signature
        ├── 2. Stores event in `webhook_events` table
        ├── 3. Deduplicates event (`mid` in Redis / DB)
        ├── 4. Enqueues background task (Celery / BackgroundWorker)
        └── 5. Responds HTTP 200 OK (< 200ms) to Meta
                   │
                   ▼
       [ Celery Background Worker ]
                   ├── 1. Verifies 24-Hour Messaging Window
                   ├── 2. Checks Human Takeover & AI Enabled Status
                   │
                   ▼ (If Authorized)
       [ AI Orchestrator Pipeline ]
                   ├── Step A: Intent & Language Classifier (En / Hi / Gu)
                   ├── Step B: Vision Reference Analyzer (Attributes, Gemstone, Style)
                   ├── Step C: Knowledge & Catalogue Retrieval (PostgreSQL)
                   ├── Step D: Grounded Response Generation (Gemini 2.5 Flash)
                   └── Step E: Factual Anti-Hallucination Firewall (Price & Purity Verifier)
                                   │
                                   ▼
                   [ Meta Send API ] ──► Delivered to Customer on Instagram
                                   │
                                   ▼
                   [ PostgreSQL DB ] ──► Real-Time Next.js Admin Dashboard
```

---

## 3. Core Architectural Modules

### 3.1 Webhook Ingestion & Deduplication
- **Asynchronous Decoupling**: Meta requires webhook responses within a few seconds, or it retries exponentially. FastAPI validates the event signature, persists the payload, enqueues the worker, and immediately responds with HTTP 200.
- **Deduplication Engine**: Meta events can be delivered multiple times. The system enforces idempotency by indexing the Meta Message ID (`mid`). Retried webhooks are logged and dropped before queuing any AI response.

### 3.2 Policy & Human Takeover Gate
- **24-Hour Messaging Window**: Checks `last_customer_message_at`. Automated responses older than 24 hours are blocked per Meta policy.
- **Human Takeover Priority**: Staff can toggle "Take Over Thread" at any time from the dashboard. Any manual staff reply automatically halts AI auto-replies for that thread.

### 3.3 Multilingual AI Reasoning Layer
- **Provider-Independent Abstraction**: All AI calls operate behind the `AIProvider` interface, allowing hot-swapping between Google Gemini, Mock provider, and alternative models.
- **Multilingual Support**: Tailored system instructions accurately classify natural English, Hindi (Devanagari & Romanized Hinglish), and Gujarati (Gujarati script & Gujlish).
- **Vision Reference Understanding**: Extracts jewellery category, metal color, estimated purity, gemstone types, and design styles from customer-uploaded screenshots.

### 3.4 Factual Anti-Hallucination Firewall
- **Zero Hallucination Guarantee**: The validator analyzes the synthesized reply text against verified catalogue records and store gold rates.
- **Safe Fallback**: If an unverified price or unsupported claim is detected, the message is sanitized and replaced with a polite response connecting the customer to a human jewellery specialist.
