# JewelAI — Instagram assistant for jewellery businesses

A Next.js/React dashboard and FastAPI backend for catalogue imports, Instagram conversations, post/product linking, and Gemini-assisted replies. The existing dark/gold interface is retained.

**Status:** local verification is recorded in `TEST_RESULTS.md`. This is not a claim of live Meta approval or production delivery. See `docs/client-handoff.md` before giving the app to a client.

## Connect and sign in with Instagram

**Clients use the “Sign in with Instagram” button, not pasted API keys or access tokens.** The operator configures the Instagram app and Gemini credentials privately on the server once. JewelAI never asks the client for their Instagram password; any Instagram authentication happens on Instagram's own screen.

### First visit: create a workspace and link it once

1. Get the dashboard address and private invitation code from the operator.
2. Open the dashboard, choose **New to JewelAI? Create your workspace**, and enter your name, workspace email, password, and invitation code. Existing users can choose **Sign in** instead.
3. Open **Meta Integration** and select **Sign in with Instagram**.
4. On Instagram's authorization screen, sign in to the **Business or Creator account** you manage and approve the requested profile, messaging, and comment access. A personal account must be made eligible for the professional-account integration first.
5. Return automatically to JewelAI in the **same browser**. Confirm that the expected username and notification-subscription status appear.
6. Leave **AI Paused** while importing your real catalogue, entering store details/policies, and testing replies in **AI Playground**. New connections and reconnections start with automatic replies off.

### Later visits: sign in directly with Instagram

1. Open JewelAI's login screen and click **Sign in with Instagram**.
2. Authorize the **same previously linked account**.
3. JewelAI opens its existing workspace without asking for the workspace email/password. Email sign-in remains available as an alternative.

**Important:** Instagram-only creation of a brand-new workspace is not implemented. The first email/invitation step is required once. A different Instagram account does not automatically gain access to an existing workspace, and an already-owned account cannot be moved between workspaces by signing in.

Use **Reconnect Instagram** if authorization expires or permissions change. **Disconnect** stops automation and clears the saved token but keeps catalogue and conversation history; it is not account/data deletion. After disconnecting, use workspace email sign-in to reconnect. Automatic token refresh and password-reset email are not implemented.

If Instagram sign-in is disabled, the **operator** must complete `docs/instagram-setup.md`; asking clients to paste tokens is not a workaround.

## Implemented safeguards

- HttpOnly session cookies, authenticated API routes, browser-bound OAuth state, invite-gated registration, and inactive-user rejection.
- Encrypted Instagram tokens, signed webhook verification, duplicate detection, messaging policy gates, and human takeover.
- Account-scoped data access and protection against moving another workspace's Instagram account.
- Actual database dashboard metrics instead of sample counts or percentage changes.
- Catalogue-grounded AI validation and human escalation on provider failures. Validation reduces risk; it is **not a guarantee that AI can never make a factual error**.
- CSV preview/mapping and a shared API error path, including session expiration.
- New workspaces do not inherit example gold rates, shop addresses, hours, phone numbers or certification claims. Rates are manually maintained; an empty/zero rate is unconfigured, not a market quote. Migration `003_safe_business_defaults` changes defaults only and preserves saved business data.

Public `/privacy`, `/terms` and `/data-deletion` routes are included and linked from sign-in and the dashboard. They are explicitly marked **operator-review drafts**: finalize the actual operator identity, public privacy/support contact and retention/deletion process before launch. They are not proof of legal compliance or Meta approval, and no automatic deletion callback is implemented.

## Run locally from a fresh checkout

### 1. Prerequisites and source

- Python **3.13**, Node.js/npm, and Git. The supplied Dockerfile targets **Node.js 22**; current local checks used **Node.js 26.10.0**. The Node 22 container runtime still needs validation.
- Two terminals: one for FastAPI, one for Next.js.
- Real Instagram/Gemini credentials are needed for live integrations, **not** for unit tests or the disposable QA setup below.
- Docker is optional for local SQLite development; it is required for the supplied production stack.

```bash
git clone https://github.com/Manthan-Gohel/Jewelai.git
cd Jewelai
```

Already have the project? Use that checkout. **Do not overwrite existing `.env` files, signing/encryption keys, databases, or saved settings.** Back up valuable data before migrations. There are no production default login credentials.

### 2. Create and activate a backend environment

Windows PowerShell, from the repository root:

```powershell
py -3.13 -m venv backend/.venv
.\backend\.venv\Scripts\Activate.ps1
cd backend
python -m pip install -r requirements.txt
```

macOS/Linux equivalent:

```bash
python3.13 -m venv backend/.venv
source backend/.venv/bin/activate
cd backend
python -m pip install -r requirements.txt
```

If PowerShell activation is restricted, use `backend/.venv/Scripts/python.exe` directly for the Python commands instead of changing machine-wide execution policy.

### 3. Configure development privately

From the activated environment, generate **separate** random secrets for signing, invitation, and webhook verification. Run the first command once per secret; store the outputs only in your private configuration:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Create `backend/.env` **only if it does not already exist**, using this development configuration and replacing the angle-bracket placeholders. Do not copy the root production template unchanged for SQLite development.

```dotenv
ENVIRONMENT=development
DEBUG=True
DATABASE_URL=sqlite:///./jewelai-local.db
SECRET_KEY=<your-generated-signing-secret>
ENCRYPTION_KEY=<your-generated-Fernet-key>
REGISTRATION_INVITE_CODE=<your-generated-private-invitation>
ENABLE_OPEN_REGISTRATION=False
ENABLE_DIRECT_TOKEN_CONNECT=False
MOCK_INSTAGRAM_API=False
MOCK_AI_PROVIDER=False
CORS_ORIGINS=["http://localhost:3000"]
INSTAGRAM_APP_ID=
INSTAGRAM_APP_SECRET=
INSTAGRAM_WEBHOOK_VERIFY_TOKEN=<your-generated-webhook-secret>
INSTAGRAM_REDIRECT_URI=http://localhost:3000/auth/instagram/callback
GEMINI_API_KEY=
```

Empty integration credentials intentionally leave live features unavailable. For real use, set the Instagram credentials and Gemini key, plus `GEMINI_TEXT_MODEL`, `GEMINI_VISION_MODEL`, and `GEMINI_EMBEDDING_MODEL` to IDs actually available to your project. Do not assume the example/default model names establish current access or quota. Never put secrets into `NEXT_PUBLIC_*` variables or the browser.

The backend reads `.env` relative to its **working directory**. Run the following commands from `backend/`, not the repository root:

```bash
python -m alembic upgrade head
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Alembic creates/upgrades the schema. Ordinary API startup does **not** create tables. The example SQLite path creates `backend/jewelai-local.db`; do not point it at an existing valuable database for experimentation.

### 4. Start the frontend

In a second terminal, from the repository root:

```bash
cd frontend
npm ci
npm run dev
```

Open `http://localhost:3000`. Next.js proxies `/api/v1` to `http://127.0.0.1:8000` so browser requests stay same-origin. To change the backend, set the server-only `BACKEND_URL` before starting/building Next.js. Restart after configuration changes; production proxy changes require rebuilding.

Use **one browser hostname consistently**. Switching between `localhost` and `127.0.0.1` during OAuth loses browser-bound state/cookies. Real OAuth requires an exactly matching redirect URI in the Meta app; real webhooks require a reachable HTTPS deployment. Do not assume a local URL is approved by Meta.

Create the invited workspace using the code from `backend/.env`, then follow the Instagram walkthrough above. Without configured Meta access, use the disposable QA setup for a simulated connected dashboard instead.

In development/tests, Celery runs tasks **in-process/eagerly using a memory broker**. No separate local Redis/worker is required for this path, but it does not exercise the production queue.

## Use the dashboard

| Screen | What to do |
| --- | --- |
| Overview | Review database metrics; use the inbox/playground shortcuts. |
| Catalogue | Add a product, search by SKU/name, filter categories, import a CSV, or delete a selected item after confirmation. Stock can be zero; INR prices retain paise. |
| Reels & Post Linking | Refresh posts, select **Link Products / Manage Link**, select products, configure reply options/templates, then **Save Link**. Saving an empty selection unlinks products. Inspect the activity tab for recorded comment processing. |
| Live Inbox | Search customers, use **Needs Staff / AI Handled**, select a thread, take over, send a manual reply, or resume AI. The displayed standard 24-hour window is informational; the backend enforces configured sending policy. |
| Knowledge & FAQs | Save real store hours/address and manually maintained INR-per-10g rates; add factual FAQ/policy documents. Empty/zero rates mean unconfigured, not a live market price. |
| Settings & Logs | Save business name, tone, tagline, and contact; use **Refresh audit logs** to reload records. This is not a push-based live stream. |
| AI Playground | Try English/Hindi/Gujarati, photo matching, and staff-escalation examples or a custom question before enabling automation. An automated validation pass is not a factual guarantee. |
| Meta Integration | Connect, refresh status, reconnect, or disconnect your professional account. |

CSV example (synthetic data, not a business claim):

```csv
sku,name,price,category,stock
DEMO-RING-001,Example Ring,12500.50,Rings,0
```

Choose **Import Client CSV → Preview & Map Columns**, review/map at least SKU, Name, and Price, select **Execute Verified Import**, inspect row-level results, then **Done & Refresh Catalogue**. Existing SKUs are updated; back up important catalogues before bulk changes.

Post-level switches do not override **AI Paused**. Do not enable **AI Auto-Reply Active** until the real catalogue, permissions, policies, workers, and controlled delivery tests are approved. Provider failures, quota/policy limits, and human takeover can still prevent a reply. Recent activity counts are not a complete daily-quota counter.

## Production: supplied Docker Compose stack

**Not yet runtime-verified:** Docker Desktop's Linux engine was unavailable on the verification machine. A valid Compose file is not proof that containers or live delivery work.

1. Prepare a Linux Docker/Compose host, persistent storage, public DNS, and ports 80/443.
2. At the repository root, create `.env` from `.env.example` **only if absent**. This root file is for Compose; it is separate from `backend/.env` used above.
3. Set `DOMAIN` to the hostname only (no scheme/path), `POSTGRES_PASSWORD`, generated signing/Fernet/invitation/webhook secrets, the Instagram app credentials, Gemini key, and accessible model IDs. Keep the encryption key stable and backed up.
4. Complete operator setup in `docs/instagram-setup.md`. Register the exact URLs below and finalize the public privacy/support/deletion information.

```text
OAuth redirect: https://YOUR_HOSTNAME/auth/instagram/callback
Webhook:       https://YOUR_HOSTNAME/api/v1/webhooks/instagram
```

The implementation requests `instagram_business_basic`, `instagram_business_manage_messages`, and `instagram_business_manage_comments`. Complete the permissions, tester/access, and app-review steps required in your Meta dashboard; a synthetic or tester sign-in is not public-service approval.

From the repository root:

```bash
docker compose config --quiet
docker compose up -d --build
docker compose ps
docker compose logs --tail=100 backend celery_worker frontend caddy
```

`--quiet` avoids printing interpolated secrets. Restrict/redact logs. The stack includes PostgreSQL, Redis, API, Celery, Next.js standalone, and Caddy; only Caddy publishes ports. It enforces production mode, mocks/debug off, private registration, and PostgreSQL. The API runs migrations before starting. Both worker queues, **`instagram_webhooks,celery`**, must be consumed.

For a separately managed worker, the command is:

```bash
celery -A app.workers.celery_app.celery_app worker --loglevel=info -c 4 -Q instagram_webhooks,celery
```

For the supported production frontend packaging, use the supplied Dockerfile: it runs generated standalone `server.js` with `.next/static` copied into place. `npm run build` alone is a build check, not a deployment; do not substitute the repository's `npm start` for that standalone packaging.

Follow `docs/deployment.md` for backups, restore drills, upgrades, and rollback. Never troubleshoot by deleting private SQLite files or using `docker compose down -v`; that removes persistent volumes. Verify real OAuth, signed webhooks, worker processing, DM/comment delivery, and Gemini calls before enabling automation.

## Verification commands

The advisory scan requires the separate optional `pip-audit` tool (`python -m pip install pip-audit`); it is not an application runtime dependency.

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

### Connected-dashboard browser regression checks

For an isolated local demo/test **instead of** your real backend, use the installed backend environment from the repository root:

```bash
python scripts/browser-qa-server.py
```

In a separate PowerShell terminal:

```powershell
cd frontend
$env:BACKEND_URL="http://127.0.0.1:8002"
npm run dev -- --hostname 127.0.0.1 --port 3013
```

In Bash, use `BACKEND_URL=http://127.0.0.1:8002 npm run dev -- --hostname 127.0.0.1 --port 3013` from `frontend/`.

Open `http://127.0.0.1:3013`, sign in with the **synthetic local fixture** `buttons-client@example.com` / `Buttons-qa-only-2026!`, then connect Instagram to exercise the synthetic callback. These credentials exist only in the temporary QA database, never in normal deployments. The QA server binds to loopback, creates a fresh temporary SQLite database on each start, and avoids existing `.env`/database files. **Never expose or deploy it.**

With Playwright MCP available, run `scripts/browser-workflow-check.js` through its `browser_run_code` filename input, then `scripts/browser-layout-check.js`. These files are Playwright functions, not `npm test` files or standalone Node executables. Run from the repository root and create an ignored `.playwright-mcp/` directory first for layout screenshots. The workflow script seeds synthetic conversation fixtures; manual sign-in alone does not seed those threads.

The workflow checks exercise actual application routes/state/session handling through the Next proxy, but Instagram/OAuth transport, message delivery, image fixture, and Gemini responses are synthetic. Responsive checks cover 375/768/1440px plus injected catalogue/AI failure recovery. See `TEST_RESULTS.md` for observed results, not a blanket promise that every browser/provider/edge case works.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| Cannot create a workspace | Use the private invitation configured on that backend and meet the form's password requirements. No default account is created by normal startup. |
| Instagram button disabled | Configure the Instagram App ID and Secret server-side and restart; keep direct-token connection disabled. |
| OAuth state/redirect failure | Start again from JewelAI in the same browser/hostname; match the exact scheme, host, port, path, and trailing slash configured in Meta. Never reuse a copied callback/code. |
| Instagram account already linked | Sign into its original workspace. Do not delete data or bypass ownership checks. |
| API/proxy errors | Ensure FastAPI is running, `BACKEND_URL` is correct, migrations ran against the intended database, and the frontend was restarted/rebuilt. |
| Production rejects SQLite/mocks/defaults | This is intentional validation. Use the development settings locally or fully configure PostgreSQL and real integrations for production. |
| Connected but no replies | Check global pause, post options, thread takeover, actual granted permissions/webhook subscription, both worker queues, messaging-window/quota gates, and provider errors. |
| Gemini request fails | Verify actual model access, quota/billing, API key, and the configured text/vision/embedding IDs. Mock success does not verify them. |
| CSV Back button / validation notices | Review column mapping and row errors. Required price/SKU/name fields must be present; importing can update existing SKUs. |
| Token expired/revoked | Reconnect via Instagram and retest. No automatic refresh job exists. |
| Policy pages have draft notices | Finalize operator identity, public contact, retention, and a tested deletion process before launch; do not merely remove the notice. |

## Keep, exclude, and protect

- **Keep in source:** `backend/app`, migrations/Alembic configuration, requirements/tests, `frontend/app`, components/lib/public/tests, package lock/configuration, `frontend/AGENTS.md`, `infrastructure/`, `docs/`, `scripts/`, Compose/Dockerfiles, `.env.example`, and verification reports.
- **Recreate, do not publish:** `.venv`/`venv`, `node_modules`, `.next`, Python/test caches, logs, generated screenshots, and TypeScript build caches. `scripts/browser-qa-server.py` is a local-only test tool, not a deployment service.
- **Keep private and back up:** real `.env` files, signing/Fernet/provider credentials, SQLite/PostgreSQL data, uploads, and backups. “Exclude from Git” does **not** mean safe to delete.
- The `.git` folder holds repository history and is not a runtime dependency. Preserve it in the development checkout; never deploy its local-only delivery/review scripts as public endpoints.
- If a credential has been exposed in a chat or commit, revoke/rotate it with its provider and a recovery plan. Removing it from the current file does not revoke it. Revocation of any previously exposed GitHub token has not been verified here.

## What remains before a real launch

### Deployment and acceptance gates

- [ ] Build/run the complete Linux container stack, including PostgreSQL and Redis/Celery; test queue retries, restart recovery, migrations, monitoring, and an isolated backup restore.
- [ ] Configure public HTTPS/DNS and real Meta app access/review; verify client-owned Business/Creator OAuth, cancellation, reconnect/disconnect, and permission revocation.
- [ ] Observe real signed DM/comment webhooks, duplicates, queue processing, catalogue-grounded text/photo replies, public/private replies, policy windows/caps, global pause, and staff takeover.
- [ ] Verify Gemini text/vision/embedding calls against the operator's actual model access and quota. Load-test the intended catalogue/message volume.
- [ ] Finalize operator identity, a functioning public privacy/support contact, retention schedule, deletion handling, and reviewed policy pages. Existing pages are drafts, not legal sign-off.
- [ ] Complete browser/accessibility/security review for the target environment, dependency maintenance, operational alerts, incident ownership, and `docs/client-handoff.md` sign-off.

### Capabilities not implemented

- Instagram-only first-time workspace registration; email password-reset delivery.
- Scheduled Instagram token refresh and automatic Meta data-deletion callback.
- Shared-team membership, granular role-based permissions, subscriptions/billing.
- Server-side revocation of already-issued bearer tokens; logout clears the browser cookie only.
- Redis-backed/shared authentication rate limiting before multi-instance scaling.
- Automated release/rollback pipelines, production monitoring/alert delivery, and a live gold-rate feed.

The inbox uses periodic fetching, audit logs use explicit refresh, and local tests do not certify live AI accuracy or provider delivery. Existing Pydantic deprecation warnings and the absence of a dedicated frontend lint command are recorded in `TEST_RESULTS.md`.

## Deployment and handoff

- `docs/client-handoff.md`: keep/delete guidance, client steps, limitations, and acceptance checklist.
- `docs/deployment.md`: production configuration, Compose, backup, and rollback procedure.
- `docs/instagram-setup.md`: operator-only Meta setup and permissions.
- `TEST_RESULTS.md`: actual local checks and unresolved verification gaps.
- Existing architecture, API, schema, and historical remediation reports remain for reference; the handoff and current test results take precedence over older readiness claims.
