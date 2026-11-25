# JewelAI deployment — operator runbook

Updated November 25, 2026. **The supplied container stack has not been built or run in this verification environment because Docker Desktop's Linux engine is unavailable.** Compose configuration validation passed; that is not container or production acceptance. Complete `client-handoff.md` before client sign-off.

## 1. Prepare a private deployment

Use a Linux host with Docker Engine/Compose, persistent storage, a public hostname, and inbound ports 80/443. Size and load-test the host for the client's actual catalogue and message volume; no capacity benchmark is supplied.

Copy or clone the reviewed application source into your deployment directory. Keep source-repository access private and transfer deployment secrets separately. Exclude local virtual environments, `node_modules`, `.next`, caches, secrets, and private SQLite files; see `client-handoff.md`.

Create `.env` from `.env.example` **only when it does not already exist**. Never replace working secrets with the template. Keep the file private and out of source control. Set:

| Setting | Required operator action |
| --- | --- |
| `DOMAIN` | Public hostname only; no `https://` prefix or path |
| `POSTGRES_PASSWORD` | Unique random password; a hex-generated value avoids URL delimiters in the connection URL |
| `SECRET_KEY` | Unique random signing key, at least 32 characters |
| `ENCRYPTION_KEY` | Valid generated Fernet key; securely back it up and keep it stable |
| `REGISTRATION_INVITE_CODE` | Private invitation secret, at least 16 characters |
| `INSTAGRAM_APP_ID`, `INSTAGRAM_APP_SECRET` | Credentials from Instagram business login setup |
| `INSTAGRAM_WEBHOOK_VERIFY_TOKEN` | Separate random webhook verification secret |
| `GEMINI_API_KEY` | Operator key with access and quota for each configured model |
| `GEMINI_TEXT_MODEL`, `GEMINI_VISION_MODEL`, `GEMINI_EMBEDDING_MODEL` | Verify the configured model IDs against your project's actual access |

Generate signing, database, invitation, and webhook secrets separately with `python -c "import secrets; print(secrets.token_hex(32))"`. Generate a Fernet key from a Python environment with backend dependencies using `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`. Store generated values privately; never paste them into support transcripts or client handoff material.

Compose explicitly sets production mode, `DEBUG=False`, both integration mocks off, invitation-only registration, and direct-token connection off. It derives the HTTPS OAuth callback and CORS origin from `DOMAIN`. For manual deployments, provide those settings yourself. Production validation rejects insecure defaults, missing integration credentials, mock integrations, and non-PostgreSQL databases.

## 2. Configure Meta and start the stack

Complete `instagram-setup.md`, including exact redirect URI, public webhook, permissions, and required access/review. Confirm DNS points to the deployment host and TLS can be provisioned. The existing Caddyfile reads `DOMAIN`; do not replace it with an unrelated example.

From the directory containing `docker-compose.yml`:

```bash
docker compose config --quiet
docker compose up -d --build
docker compose ps
docker compose logs --tail=100 backend celery_worker frontend caddy
```

Use `--quiet` for configuration validation so interpolated secrets are not printed. Logs may contain customer data or authorization parameters; restrict access and redact before sharing.

The stack contains PostgreSQL, Redis, the backend, a Celery worker, the standalone Next.js frontend, and Caddy. Only Caddy publishes host ports. Do not expose PostgreSQL, Redis, or the backend directly. Worker queues are **`instagram_webhooks,celery`**; omitting either can leave work unprocessed.

The backend runs `alembic upgrade head` before starting the API; application startup does not create tables automatically. Back up existing data before an upgrade. The worker waits for backend liveness. This does not prove Meta, Gemini, queue processing, or recovery behavior; monitor and test those separately.

The frontend image builds with Node.js 22, a same-origin `/api/v1` proxy, and Next.js standalone output. `BACKEND_URL` is a build argument; changing it requires a rebuild. Compose supplies the internal backend URL. Its runtime image starts with `node server.js`, not a development server.

## 3. Validate before enabling replies

1. Open the HTTPS dashboard and confirm session login/logout, invitation gating, and reconnect flows. A production session cookie must be Secure and HttpOnly.
2. Create the client's workspace and complete real Instagram authorization. New connections must show automatic replies off.
3. Import the real catalogue, configure store policies and current gold rates, and verify account-scoped views.
4. Confirm a real webhook reaches the backend and the worker processes it. Exercise text/image AI calls with the actual configured Gemini project.
5. Run controlled DM/comment, duplicate, messaging-window, human-takeover, and global-pause tests. Enable automation only after the client approves the results.
6. Complete every item in `client-handoff.md`. Local tests use mocked external services and cannot sign off production delivery.

The backend healthcheck calls `/` inside its container: it reports process liveness, not database/worker/integration readiness. The public site's `/` is the frontend. Do not substitute the landing page for operational monitoring.

## 4. Backups and restore drills

Back up PostgreSQL, any operational file storage, and the required encryption/signing configuration using your organization's retention and access policy. Keep database backups encrypted off-host and store recoverable encryption keys separately. Losing the Fernet key makes saved Instagram tokens unreadable; changing it does not automatically re-encrypt existing rows.

Example PostgreSQL backup from the deployment directory, in Bash:

```bash
set -euo pipefail
mkdir -p /var/backups/jewelai
backup="/var/backups/jewelai/jewelai-$(date +%Y%m%d-%H%M%S).sql.gz"
docker compose exec -T postgres sh -c 'pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB"' | gzip > "$backup"
gzip -t "$backup"
```

Record command success and copy the backup off-host. A valid gzip stream is not proof of a restorable database. Schedule an actual restore drill into a **new, isolated PostgreSQL database**, run migrations as appropriate, verify record counts and application access, and confirm encrypted-token recovery using the correct key. Do not restore over a client's production database as a test. The backup/restore drill remains an outstanding acceptance item.

## 5. Upgrades, rollback, and operations

- Retain the previously tested application/container version and a pre-upgrade database backup. This project does not include an automated release pipeline or migration rollback guarantee.
- Test upgrades and migrations on a copy first. If a schema change is not backward compatible, rolling back only the app image is insufficient; use the reviewed database recovery plan.
- Never use `docker compose down -v` as a normal update or troubleshooting step: it deletes named volumes containing persistent data.
- Use one API process with the current process-local login limiter. Add a shared limiter before scaling API instances; roles alone do not implement shared teams or granular RBAC.
- Document a named operator, incident contacts, worker/backlog alerts, failed webhook/AI delivery monitoring, privacy/deletion handling, and reconnect reminders. Automatic token refresh and email/SMS alerts are not implemented.
- Rotate credentials only with a tested recovery plan. Session logout clears one browser cookie; copied bearer tokens remain valid until expiry.

See `../TEST_RESULTS.md` for observed checks and explicit gaps. Do not call this deployment production-verified until the full stack and live services have passed acceptance.
