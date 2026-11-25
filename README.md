# JewelAI — Instagram assistant for jewellery businesses

A Next.js/React dashboard and FastAPI backend for catalogue imports, Instagram conversations, post/product linking, and Gemini-assisted replies. The existing dark/gold interface is retained.

**Status:** local verification is recorded in `TEST_RESULTS.md`. This is not a claim of live Meta approval or production delivery. See `docs/client-handoff.md` before giving the app to a client.

## Client sign-in

1. Create an invited workspace with email and password, or sign in to an existing workspace.
2. Choose **Sign in with Instagram** and authorize a Business or Creator account on Instagram's own screen.
3. Return to JewelAI, import the real catalogue, review settings, and test replies. New connections start with automatic replies **off**.
4. On later visits, use Instagram sign-in directly or continue with email.

Clients do not paste access tokens or API keys. The operator must configure Meta and Gemini credentials on the server once. Instagram-only first-time workspace creation, password-reset email, team invitations/membership, billing, and automated token refresh are not implemented.

## Implemented safeguards

- HttpOnly session cookies, authenticated API routes, browser-bound OAuth state, invite-gated registration, and inactive-user rejection.
- Encrypted Instagram tokens, signed webhook verification, duplicate detection, messaging policy gates, and human takeover.
- Account-scoped data access and protection against moving another workspace's Instagram account.
- Actual database dashboard metrics instead of sample counts or percentage changes.
- Catalogue-grounded AI validation and human escalation on provider failures. Validation reduces risk; it is **not a guarantee that AI can never make a factual error**.
- CSV preview/mapping and a shared API error path, including session expiration.
- New workspaces do not inherit example gold rates, shop addresses, hours, phone numbers or certification claims. Rates are manually maintained; an empty/zero rate is unconfigured, not a market quote. Migration `003_safe_business_defaults` changes defaults only and preserves saved business data.

Public `/privacy`, `/terms` and `/data-deletion` routes are included and linked from sign-in and the dashboard. They are explicitly marked **operator-review drafts**: finalize the actual operator identity, public privacy/support contact and retention/deletion process before launch. They are not proof of legal compliance or Meta approval, and no automatic deletion callback is implemented.

## Local development

Use Python 3.13 and Node.js 22. Do not overwrite an existing `.env` or run migrations against valuable data without a backup.

From `backend/`, create/activate a virtual environment and install `requirements.txt`. Configure a **development** environment, not the production `.env.example` unchanged. A local configuration needs `ENVIRONMENT=development`, `DEBUG=True`, a SQLite `DATABASE_URL`, custom `SECRET_KEY`/Fernet `ENCRYPTION_KEY`, and optional real integration credentials. Mocks must be explicitly enabled only for a disposable demo.

```bash
# From backend/
python -m pip install -r requirements.txt
python -m alembic upgrade head
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

In another terminal:

```bash
# From frontend/
npm ci
npm run dev
```

Open `http://localhost:3000`. Next.js proxies `/api/v1` to `http://127.0.0.1:8000`; set server-side `BACKEND_URL` before building for a different backend. Use the same browser hostname throughout sign-in. Local OAuth still needs matching Meta redirect configuration; real webhooks need public HTTPS.

## Verification commands

```bash
# From repository root, using the configured backend virtual environment
python -m pytest -c backend/pytest.ini backend/tests -q
python -m pip check
python -m pip_audit -r backend/requirements.txt --progress-spinner off
```

```bash
# From frontend/
npm test
npm run typecheck
npm run build
npm audit
```

Tests use disposable databases and mocked external services. They do not prove live Instagram or Gemini delivery.

## Deployment and handoff

- `docs/client-handoff.md`: keep/delete guidance, client steps, limitations, and acceptance checklist.
- `docs/deployment.md`: production configuration, Compose, backup, and rollback procedure.
- `docs/instagram-setup.md`: operator-only Meta setup and permissions.
- `TEST_RESULTS.md`: actual local checks and unresolved verification gaps.
- Existing architecture, API, schema, and historical remediation reports remain for reference; the handoff and current test results take precedence over older readiness claims.
