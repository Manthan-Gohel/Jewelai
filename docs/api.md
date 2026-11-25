# JewelAI — REST API Reference

Base URL: `/api/v1`

Updated November 25, 2026. Use the running API's `/docs` or `/openapi.json` for authoritative request/response schemas. Local regression results and live-service gaps are in `../TEST_RESULTS.md`.

Browser requests use an HttpOnly session cookie. Mutating browser requests must include `X-JewelAI-Request: 1` and come from an allowed origin; signed Meta webhooks use their separate signature check. Bearer authentication remains available for API clients. Business-data endpoints require the authenticated user's connected Instagram account.

## 1. Authentication & Instagram OAuth
- `GET /auth/setup`: Report whether registration needs an invitation and whether Instagram login is configured.
- `POST /auth/register`: Create an account-scoped workspace; invite-gated in production, including the first user. Server assigns the role. Sets a session cookie and returns a bearer token/user.
- `POST /auth/login`: Authenticate with email/password, set a session cookie, and return a bearer token/user. Inactive users cannot sign in.
- `POST /auth/logout`: Clear this browser's session/OAuth cookies. Does not invalidate previously copied bearer tokens.
- `GET /auth/me`: Get current authenticated user details.
- `GET /auth/instagram/status`: Read the workspace's connection and operator configuration status.
- `GET /auth/instagram/oauth-url`: Start an authenticated account connection and set a browser-bound OAuth-state cookie.
- `POST /auth/instagram/connect`: Validate the code/state, exchange tokens, subscribe webhooks, and save the encrypted connection. New connections start with automatic replies off.
- `GET /auth/instagram/login`: Start Instagram sign-in for an already-linked workspace.
- `POST /auth/instagram/session`: Finish Instagram sign-in after validating browser-bound state; does not create an uninvited workspace.
- `POST /auth/instagram/disconnect`: Clear the locally saved token, mark disconnected, and pause automatic replies while retaining business data. This is not a Meta account-wide grant revocation endpoint.
- `POST /auth/instagram/connect-token`: Disabled by default; only for explicitly enabled operator recovery or isolated tests, not the client onboarding UI.

## 2. Meta Webhooks
- `GET /webhooks/instagram`: Official Meta verification endpoint. Validates `hub.mode == 'subscribe'` and `hub.verify_token`, returning integer challenge.
- `POST /webhooks/instagram`: Ingests real-time events. Verifies `X-Hub-Signature-256` HMAC-SHA256 signature, stores payload, deduplicates, and enqueues worker task.

## 3. Conversations & Live Inbox
- `GET /conversations`: List customer threads with unread counts and latest messages. Supports `?status=active|pending_human` and `?search=...`.
- `GET /conversations/{id}`: Full message history, customer details, and delivery receipts.
- `POST /conversations/{id}/reply`: Staff manual reply. Automatically engages Human Takeover mode and dispatches message via Meta Send API.
- `PATCH /conversations/{id}/ai`: Toggle `ai_enabled` (true/false) and `human_takeover` (true/false).

## 4. Jewellery Catalogue
- `GET /products`: List products with pagination, category filter, and search.
- `POST /products`: Add jewellery item (SKU, name, category, price, purity, weight, stock, image URLs).
- `GET /products/{id}`: Get product detail.
- `PATCH /products/{id}`: Update product fields.
- `DELETE /products/{id}`: Delete product.
- `POST /products/import-csv`: Multipart file upload for bulk catalogue import.
- `POST /products/csv-preview`: Preview uploaded CSV columns and sample rows.
- `POST /products/csv-import-mapped`: Import the uploaded CSV using the selected column mapping.

There is no sample-product seeding endpoint.

## 5. Knowledge & Store FAQs
- `GET /knowledge`: List store FAQs, return policies, gold rate guidance, and shipping info.
- `POST /knowledge`: Add new FAQ item.
- `PATCH /knowledge/{id}`: Update document.
- `DELETE /knowledge/{id}`: Delete document.

## 6. AI Testing Playground
- `POST /ai/test`: Run simulation without sending an Instagram message.
  - Request: `{ message: string, image_url?: string, language_override?: string }`
  - Response: `{ language_detected, intent_detected, extracted_entities, retrieved_products, generated_reply, fact_validation_passed, validation_flags, latency_ms }`

## 7. Business Settings & Analytics
- `GET /settings`: Get brand persona, operator-entered gold rates (24K, 22K, 18K), timings, and address. Rates are not a live market feed.
- `PATCH /settings`: Update business settings and daily gold rates.
- `GET /analytics/overview`: Database-backed rolling-24-hour message/reply metrics, validation-pass rate, average recorded latency, and current account/product/conversation counts. The pass rate is a heuristic validation metric, not measured factual accuracy.
- `GET /analytics/logs`: Automation audit trail with intent and validation status.
- `GET /health`: Process liveness/configuration summary only; does not check database, worker, Meta, or Gemini readiness.
