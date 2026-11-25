# JewelAI client handoff

Updated November 25, 2026. Local results are in `../TEST_RESULTS.md`; passing mocked tests is not live production approval.

## What the client does

1. Open the deployed HTTPS dashboard.
2. Create a workspace with their own email/password and your private invitation code, or sign in to an account already provisioned for them.
3. Select **Sign in with Instagram**, authorize their Business/Creator account on Instagram, and return to JewelAI.
4. Import their real CSV catalogue; check prices, stock, purity, photos, gold rates, store details, and reply policies.
5. Use the AI playground and a controlled Instagram test conversation before switching automatic replies on.
6. Link posts/reels to the appropriate products and enable their individual comment-to-DM rules when wanted. The global automatic-reply switch must also be on.
7. Later, sign in using Instagram directly. Email sign-in remains available, including after disconnecting Instagram.

The client never supplies a raw Instagram access token or a Gemini API key. A new workspace cannot be created with Instagram alone: first-time email registration preserves the invitation boundary and supplies an independent recovery login.

## What the operator must supply once

- A server, domain, HTTPS, PostgreSQL, Redis, running backend and Celery worker, backups, and monitoring.
- Meta Instagram App ID/Secret, webhook verification secret, exact OAuth callback, and messaging/comment permissions.
- The access level and review approval Meta requires for the client accounts being served; development-mode tests do not establish this.
- A Gemini API key with access/quota for the configured model IDs. Defaults are configuration choices, not proof of access on a particular Google project.
- Private session signing/encryption keys and invitation code. Keep the encryption key stable and backed up: losing it makes saved Instagram tokens unreadable.
- The business's actual public privacy policy, terms where applicable, and data-deletion instructions/callback required by its Meta configuration. These must describe real operations, not template promises.

The source includes public `/privacy`, `/terms` and `/data-deletion` routes with clear operator-review notices. Update the pages under `frontend/app/(policies)/` with the actual legal identity, working public contact and approved retention/deletion procedure. Until finalized, use synthetic staging data only. No automatic deletion callback is implemented. Meta's data-deletion documentation permits a deletion-instructions URL as an alternative to a callback; a draft page with no operational deletion process is not acceptance evidence.

See `instagram-setup.md` and `deployment.md`. Do not give clients your server `.env`, Meta App Secret, or operator API keys.

## Files to keep

| Keep | Reason |
| --- | --- |
| `backend/app/`, `backend/migrations/`, `backend/alembic.ini` | API, integrations, workers, and schema history |
| `backend/requirements.txt`, `backend/Dockerfile`, `backend/.dockerignore` | Backend installation and safe container build |
| `backend/tests/`, `backend/pytest.ini` | Regression checks; keep in source handoff, excluded from the runtime image |
| `frontend/app/`, `frontend/components/`, `frontend/lib/` | Application UI and API client |
| `frontend/package.json`, `frontend/package-lock.json` | Dependency declarations and reproducible `npm ci` installs |
| Frontend config/type/style files, `frontend/Dockerfile`, `frontend/.dockerignore`, `frontend/tests/` | Build, typechecking, styling, image, and regression checks |
| `infrastructure/`, `docker-compose.yml`, `.env.example`, `.gitignore`, `README.md`, `docs/`, `TEST_RESULTS.md` | Deployment and operating instructions |

Keep all three migrations, including `003_safe_business_defaults.py`. It changes defaults for future inserts without replacing existing saved settings. Existing demo-like values may have been intentionally entered: review them with the owner instead of automatically deleting or rewriting them. Gold rates must be entered and maintained by the business; this is not a live pricing feed.

## Generated files you may exclude from a source delivery

- `backend/venv/` or any `.venv/`: recreate from requirements; do not ship your machine-specific environment.
- `frontend/node_modules/`: recreate with `npm ci`.
- `frontend/.next/`, `*.tsbuildinfo`: rebuild. Keep `.next` only when deliberately shipping a tested prebuilt runtime.
- `__pycache__/`, `*.pyc`, `.pytest_cache/`, `.coverage`, `htmlcov/`, generated logs, and `.playwright-mcp/` browser artifacts.
- Old `REMEDIATION_REPORT.md`, `RELEASE_READINESS.md`, and `docs/release-readiness-report.md` may be omitted from the client package after archiving. They are historical, not current acceptance evidence.

**Do not blindly delete:** `.env`, `backend/.env`, `jewelai.db`, `backend/jewelai.db`, uploads, backups, Docker volumes, or any other database. They may contain real credentials/data. Back up and identify ownership first. Exclude secrets and private databases from a source package rather than deleting the originals. No existing secrets or databases were deleted during this work.

## Safe GitHub delivery

- Revoke any personal access token pasted into chat. Never put a token in a remote URL, README, command argument, source file or client package.
- Use an authenticated integration, GitHub's browser-based Git Credential Manager, or `gh auth login` after installing GitHub CLI. Start with a private repository and deliberately grant the client's intended access.
- Review the Git candidate/staged file list and scan for credentials before uploading. `.gitignore` excludes environment files (except the example), databases, key/certificate files, uploads, backups, dependencies and generated artifacts.
- Publishing source does not deploy it, configure Meta, finalize policies or complete the live acceptance checklist. Do not transfer your operator secrets through GitHub, even in a private repository.

Source was published on November 25, 2026 to `Manthan-Gohel/Jewelai`, branch `main`, using the existing native Git Credential Manager credentials for `Manthan-Gohel`. The initial source-delivery commit is `e393f47`, containing all 114 reviewed source files. The repository's existing initial commit was preserved through a merge; no force-push was used. The earlier integration-based attempt failed with HTTP 403/404, but native Git access resolved the upload blocker. No token from chat was copied into commands, files or Git configuration. Repository visibility and collaborator access still need the owner's review; publishing does not establish that the repository is private. Do not paste another token into chat.

## Known limits to explain honestly

- No live Meta authorization, delivery, App Review, or deployed HTTPS acceptance has been established by local tests.
- Token refresh is not scheduled automatically. The connection screen warns when the saved expiry is near; reconnect through Instagram before expiry. Revocation or permission changes may require reconnecting earlier. There are no email/SMS expiry or escalation alerts.
- Logout clears this browser's cookie; copied bearer tokens remain valid until their configured expiry. There is no server-side session revocation or password-reset email workflow.
- Registration creates separate account-scoped workspaces. A `role` value does not implement shared team membership, granular RBAC, or a full multi-tenant subscription service.
- Authentication rate limiting is process-local. The supplied backend uses one API process; add a shared Redis-backed limit before scaling API instances.
- AI safeguards are heuristic. Review genuine catalogue/language examples and human escalations; do not advertise zero hallucinations.
- Queue/worker outage recovery, retry behavior, backups/restores, account deauthorization, privacy/deletion operations, and business-language quality require operator acceptance testing.
- The Compose backend healthcheck is process liveness, not end-to-end Meta/AI/queue readiness. Monitor those dependencies separately.

## Live acceptance checklist — complete before client sign-off

- [ ] Set private production values; no mock integrations or default secrets.
- [ ] Build/start the full Compose stack; verify database migrations, Redis, and the worker consuming `instagram_webhooks,celery`.
- [ ] Verify HTTPS domain, same-origin cookie login/logout, invalid credentials, expired session handling, and invitation gating.
- [ ] Complete real Instagram connect, denied/canceled authorization, reconnect, and disconnect. Confirm another workspace cannot take the account.
- [ ] Confirm Meta verification challenge and signed webhook delivery for a real incoming DM and a comment.
- [ ] Enable automation only for the test account; verify one DM reply, duplicate suppression, and a linked-post private reply/public reply.
- [ ] Turn global replies off and verify no new automatic DMs or comment replies are sent. Test human takeover and the messaging-window cutoff.
- [ ] Verify real Gemini text/image results, provider failure handling, and inventory-scoped replies in the client's languages.
- [ ] Validate imports and views with the client's real catalogue; verify no unrelated workspace data is visible.
- [ ] Verify the public privacy/deletion process, backup restore, outage alerts, and named operational owner.

**Handoff decision:** suitable for a controlled staging pilot after configuration; do not label it fully live-production-verified until the checklist is completed with real services.
