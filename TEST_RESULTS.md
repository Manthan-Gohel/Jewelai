# JewelAI — observed verification results

**Date:** November 25, 2026  
**Decision:** local engineering checks pass; live-production acceptance remains incomplete.  
**Scope:** Windows development machine, fresh backend verification environment, production-built frontend, disposable SQLite data. No existing secrets or user databases were deleted or migrated.

## Results

| Check | Observed result |
| --- | --- |
| Backend full suite | **61 passed**, 0 failed, 13 deprecation warnings; 37.92 seconds in the final confirmation run |
| Backend dependency consistency | `pip check`: **No broken requirements found** in the fresh environment |
| Backend dependency advisory scan | `pip_audit -r backend/requirements.txt --progress-spinner off`: **No known vulnerabilities found** |
| Frontend regression suite | **9 passed**, 0 failed in the final run: API/session/errors, truthful header rates, neutral business forms and preserved saved settings |
| Frontend typecheck | `npm run typecheck`: passed |
| Frontend production build | `npm run build`: passed with Next.js **16.4.6**, including the final Navbar changes, TypeScript, `/auth/instagram/callback`, `/privacy`, `/terms` and `/data-deletion` |
| Frontend dependency advisory scan | `npm audit`: **0 vulnerabilities** |
| Fresh database migration | Passed in the backend regression suite and again before the isolated browser-test API started |
| Browser auth/onboarding checks | **29 checks passed** through the real same-origin Next.js proxy and isolated backend; no browser API-response mocks |
| Browser page errors / failed transports / API 5xx | **0 / 0 / 0** during those journeys |
| Responsive checks | Login and disconnected onboarding at **1440, 768, and 375 CSS pixels**: no page-level horizontal overflow; screenshots captured and desktop/mobile onboarding inspected |
| Final public policy browser checks | All three routes returned **HTTP 200** at **1440 and 375 CSS pixels** (six route/viewport checks); correct headings, visible draft notices, three policy links, working cross-page navigation, no horizontal overflow, page errors or failed requests |
| Compose configuration | `docker compose --env-file .env.example config --quiet`: passed with synthetic required validation values |
| Docker engine/container acceptance | **Blocked**: Docker Desktop Linux engine named pipe unavailable; no container build/runtime pass claimed |
| Live Meta/Gemini, public HTTPS | **Not verified**; requires operator configuration and the live acceptance checklist |
| Source-delivery review | **114 candidate source files**; no matches for the scanned GitHub/Google/provider/Meta/AWS token, JWT, private-key or embedded-password URL patterns. Development/test literals and empty example secret fields were reviewed; this is not a comprehensive secret-audit certification |
| Private/generated-file exclusion | `git check-ignore` confirmed environment files, private databases, virtual environments, dependencies, build output, browser artifacts, backups, uploads and key/credential files are excluded |
| GitHub publication | **Blocked**: authenticated integration repository creation returned **HTTP 403 — Resource not accessible by personal access token**. No repository was created, no source was uploaded and no exposed chat token was used. Reauthorize the integration or supply an authorized existing destination before publishing |

Advisory scans report known advisories at scan time; they are not a security certification. No coverage percentage, load benchmark, screen-reader audit, or comprehensive accessibility pass is claimed. There is no configured standalone frontend lint command, so no separate lint pass is claimed.

## Backend checks and environment

The current requirements were installed successfully in a new virtual environment at:

```text
C:\Users\manth\AppData\Local\Temp\opencode\jewelai-verify-20261125
```

The application's existing `backend/venv` was not used to establish the final runtime results; it still needs to be recreated or updated before use with the current requirements. Do not ship either local virtual environment. Direct requirements are version-constrained, but this project does not include a complete cross-platform transitive Python dependency lock; verify fresh deployments rather than treating one Windows installation as a Linux runtime test.

Commands, from the project root with the fresh environment active:

```bash
python -m pytest -c backend/pytest.ini backend/tests -q
python -m pip check
```

The advisory scanner was installed separately in the original environment and run against the **current requirements file**, not used as proof that the old environment was upgraded:

```bash
python -m pip_audit -r backend/requirements.txt --progress-spinner off
```

Coverage includes authentication, browser-bound OAuth state, inactive-user rejection, invitation gating, session-cookie/CSRF behavior, JWT expiry requirements, token encryption, signed webhook handling, account isolation, catalogue/CSV validation, mocked AI/reply pipeline behavior, messaging policy, post/comment processing, and the global automatic-reply pause. The migration regression creates a new disposable database from a different working directory and checks required tables and token-expiry schema.

New regressions first reproduced demo business facts in fresh connections and unvalidated negative/non-finite gold rates. Fixes ensure neutral model/database defaults, no fabricated AI store context, finite nonnegative rate inputs, and explicit clearing without modifying other rates. The migration check also verifies neutral database defaults. Existing saved business settings are not overwritten.

The 13 warnings are Pydantic's existing class-based configuration deprecations. They do not fail these tests; migrating that configuration syntax remains maintenance work before a future Pydantic major-version upgrade.

## Frontend checks

From `frontend/`:

```bash
npm test
npm run typecheck
npm run build
npm audit --audit-level=low
```

The regression suite verifies same-origin cookie requests, readable validation/network errors, multipart CSV session-expiration handling, no-content responses, and header rendering without a fictitious account/business/rate/API version. Header regressions were observed failing before the targeted fix and then passed.

The production build emits a warning about an unrelated `pnpm-workspace.yaml` in the Windows home directory, which Next.js ignores. The standalone output was started with `node .next/standalone/server.js` after copying `.next/static` into the standalone package, matching the image's standalone runtime pattern. No Docker image execution is implied.

## Browser journeys and evidence

The auth/onboarding browser run used a fresh context at `http://127.0.0.1:3000`, a production build compiled with `BACKEND_URL=http://127.0.0.1:8001`, and a fresh API/database on port 8001. The backend had no Instagram/Gemini credentials or integration mocks enabled. The existing process on port 8000 and existing private databases were left alone. Rebuild with the correct backend URL for your own deployment; generated `.next` output is not source handoff material.

Observed journeys:

- Initial email sign-in and disabled/unconfigured Instagram sign-in with operator guidance.
- Invalid invitation rejected with HTTP 403; valid invited registration enters disconnected onboarding.
- All eight navigation choices retain safe onboarding until an account is connected.
- No invented business name, Instagram handle, gold rate, or API version in the disconnected header; AI toggle disabled.
- Logout clears the session; invalid credentials return a readable error; valid email login persists after reload.
- Session cookie is HttpOnly and SameSite=Lax. Secure is false on this development HTTP instance; production HTTPS-cookie behavior still requires deployed verification.
- Missing/expired browser session returns to sign-in.
- Canceled OAuth and missing/mismatched browser state produce readable recovery screens; callback query parameters are removed.
- No uncaught JavaScript errors, failed network transports, or API 5xx during these journeys. Expected authentication/invitation failures were HTTP 401/403, not treated as application outages.

Screenshots and the local browser harness are under `.playwright-mcp/` with the `handoff-` prefix. They contain synthetic accounts only and can be excluded from source delivery. There is no prior committed visual baseline, so visual regression comparison is **inconclusive**, not a claimed pass. Connected-account interactions beyond backend tests still require live/staging acceptance.

After the final build, the standalone frontend on `http://127.0.0.1:3012` served `/privacy`, `/terms` and `/data-deletion` without authentication. All six route/viewport combinations passed at 1440 and 375 CSS pixels, with HTTP 200, correct headings, visible operator-review warnings, policy navigation and no page-level horizontal overflow. Cross-page link navigation also passed; no page errors or failed transports were observed. Screenshots are under `.playwright-mcp/final-policy-*`; mobile privacy and desktop deletion screenshots were visually inspected. These checks do not establish deployed public reachability or legal acceptance.

## Remaining release gates

1. Start a working Docker engine; build/run the complete Linux Compose stack, verify PostgreSQL migrations, both worker queues, container health, and restart/outage behavior.
2. Configure the real domain, HTTPS, Meta app permissions/access, exact redirect/webhook, and Gemini model access/quota. Complete actual Instagram connect/reconnect/disconnect and DM/comment delivery.
3. Finalize and test the operator's real public policy/support/deletion process. Public policy/deletion routes now exist but are clearly marked operator-review drafts; the legal identity, public contact and retention/deletion schedule must be finalized before real customer data is used. No automatic data-deletion callback is implemented.
4. Validate the client's real catalogue/languages, human takeover, global pause, duplicate handling, provider errors, backup restore, and operational monitoring.
5. Explain remaining limits: no automatic Instagram token refresh, no password-reset email, no server-side bearer-token revocation, process-local login limits, and no shared-team/RBAC/subscription implementation.

Use `docs/client-handoff.md` for exact keep/exclude guidance and the full live checklist. Historical readiness/remediation reports do not override these results. Source-control preparation or GitHub publishing is separate from deployment, Meta review submission and production approval; none of those live operations is established by this report.
