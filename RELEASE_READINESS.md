# JewelAI — Production Release Readiness & Meta Launch Guide

> Historical report — superseded November 25, 2026. Its "Ready" labels are not current production acceptance. Use `docs/client-handoff.md` and `TEST_RESULTS.md` for current functionality, limitations, and verified results.

**Product:** JewelAI — Official Meta Instagram AI Assistant for Fine Jewellery  
**Version:** 2.1.0-REMEDIATED  
**Target Environment:** Official Meta Instagram Platform (Graph API v22.0)  
**Status:** Codebase Remediated & Unit/Integration Verified • Pending Live Meta App Review & Staging  

---

## 1. Release Readiness Status Matrix

| Subsystem | Production Requirement | Implementation Status | Verification Method |
|---|---|---|---|
| **Authentication & RBAC** | Strict JWT validation, zero auto-login bypass | **Ready** | Pytest (`test_auth_bypass_prevented_without_token`, `test_invalid_jwt_token_rejected`) |
| **Registration Security** | Server-assigned roles, invite-only gating, rate limiting | **Ready** | Pytest (`test_auth_rate_limiter_blocks_excessive_attempts`, schema validation) |
| **Meta OAuth 2.0** | Instagram Login OAuth with HMAC-SHA256 state protection | **Ready** | Pytest (`test_oauth_state_generation_and_tampering_defense`, `test_instagram_connect_rejects_tampered_state`) |
| **API Version** | Official Meta Graph API v22.0 | **Ready** | Configured in `Settings` and client endpoints |
| **Data Hygiene** | No fake accounts or mock products in production | **Ready** | `/products/seed` deleted; startup auto-seeding removed |
| **AI Reliability** | No mock customer responses on AI failure | **Ready** | `AIProviderError` escalates to human staff (`pending_human`, `human_takeover=True`) |
| **AI SDK** | Supported Google GenAI SDK (`google-genai >= 1.0.0`) with async client | **Ready** | Migrated to `client.aio.models.generate_content` with candidate model fallback |
| **Catalogue Import** | Client CSV import with column mapping & preview | **Ready** | Pytest (`test_csv_preview_auto_detects_client_headers`, `test_csv_import_mapped_success`) |
| **Factual Firewall** | Strict anti-hallucination validation (prices, purity, weight, stock) | **Ready** | Pytest (`test_verified_price_passes_validation`, `test_store_24k_rate_does_not_allow_24k_claim_on_18k_item`, `test_weight_auditing_against_catalogue_specs`, `test_price_audited_when_zero_products_retrieved`) |
| **Platform Policy** | Meta 24-Hour Messaging Window enforcement | **Ready** | Pytest (`test_24_hour_messaging_window_allowed`, `test_24_hour_messaging_window_expired`, verified timestamp fix) |
| **Human Escalation** | Handover Protocol & regex word-boundary keyword triggers | **Ready** | Pytest (`test_human_takeover_blocks_ai_reply`, `test_escalation_keywords_detection`) |
| **Webhooks** | HMAC SHA256 Signature & Deduplication | **Ready** | Pytest (`test_meta_webhook_post_signature_validation`, `test_duplicate_webhook_event_prevention`) |
| **Post-to-Product Linking** | Video Post/Reel → Comments → Meta Private Reply DM | **Ready** | Pytest (`test_comments_and_post_linking.py`), Next.js Production Build (`MediaLinkingView.tsx`) |
| **Frontend UI** | Next.js 14 responsive luxury dashboard | **Ready** | Next.js 14 Production Build (`next build`), 4/4 static routes generated with strict TypeScript |

---

## 2. Still Remaining for Real Users (Production Launch Checklist)

Before real customers can interact with the system on Instagram, the following operational and platform prerequisites must be completed:

### 1. Meta App Review & Advanced Access
- In Development Mode, only registered App Roles (testers, developers, admins) can interact with the Instagram app.
- For public customers, submit for **Meta App Review** with recorded screencasts demonstrating:
  - `instagram_business_basic`: Profile and account identity.
  - `instagram_business_manage_messages`: Direct message receipt and Send API delivery.
  - `instagram_business_manage_comments`: Comment webhook ingestion and Private Reply DM dispatch.
- Complete **Meta Business Verification** in Meta Business Manager.
- Switch the Meta App from **Development Mode** to **Live Mode**.

### 2. Public Policy URLs (Meta Compliance Requirement)
Meta requires public, accessible HTTPS URLs configured in the Meta App Dashboard before review submission:
- **Privacy Policy URL**: Explaining data collection, storage duration, and customer rights.
- **Terms of Service URL**: Detailing service terms for the jewellery brand.
- **User Data Deletion Callback URL**: Endpoint confirming deletion of customer interaction data upon request.

### 3. Production Infrastructure Setup
Deploy the stack to a live production server with:
- Public domain with TLS/HTTPS certificate (managed by Caddy or Nginx reverse proxy).
- Managed PostgreSQL database with automated scheduled snapshots.
- Managed Redis instance for Celery task queuing and rate limit state.
- Celery worker background daemon running alongside FastAPI.
- Server health monitoring and error alerting (e.g. Sentry, Uptime Kuma).

### 4. Real Client Pilot & Language Verification
- Onboard an authentic jewellery client with their genuine CSV inventory (prices, purities, gross weights, photo URLs).
- Conduct a controlled pilot to verify conversational nuance and local dialect vocabulary across Gujarati, Hindi, and English customer inquiries.

### 5. Client Operational Alerts
- Implement SMS / Email / WhatsApp notifications alerting showroom managers when:
  - A Meta OAuth access token is within 7 days of expiration.
  - A message fails to deliver or human escalation is triggered.
  - A customer requests a custom bridal appointment or high-value consultation.

### 6. Usage & Billing Enforcement
- While the `UsageRecord` database model tracks input/output tokens and request types, hard quota enforcement per client subscription tier should be integrated before multi-tenant SaaS commercialization.
