# JewelAI — observed verification results

**Date:** November 25, 2026  
**Decision:** local engineering checks pass; live-production acceptance remains incomplete.  
**Scope:** Windows development machine, Python 3.13 verification environment, Node.js 26.10.0, Next.js 16.4.6 standalone frontend, disposable SQLite data. The Dockerfile's Node 22/Linux runtime was not exercised. No existing secrets or user databases were deleted or migrated.

## Results

| Check | Observed result |
| --- | --- |
| Backend full suite | **64 passed**, 0 failed, 13 deprecation warnings; **12.41 seconds** in the final root-directory confirmation run. Includes three new mock-delivery ID regressions |
| Backend dependency consistency | `pip check`: **No broken requirements found** in the fresh environment |
| Backend dependency advisory scan | Earlier November 25 baseline: `pip_audit -r backend/requirements.txt --progress-spinner off` reported **No known vulnerabilities found**. Requirements are unchanged in this follow-up; the advisory scan was not rerun |
| Frontend regression suite | **10 passed**, 0 failed in **3.84 seconds**: API/session/errors, truthful header rates, neutral business forms, preserved saved settings, and INR paise display |
| Frontend typecheck | `npm run typecheck`: passed |
| Frontend production build | Final `npm run build` passed with Next.js **16.4.6**, including TypeScript and all six emitted routes. The resulting standalone `server.js` plus copied `.next/static` served the connected checks below |
| Frontend dependency advisory scan | Final `npm audit --audit-level=low`: **0 vulnerabilities** |
| Fresh database migration / documented setup | Full suite passed; separately extracted the README development dotenv, generated temporary secrets, applied all three migrations, and started the API successfully in a temporary source copy without private `.env`/data |
| Connected browser workflows | **53 checks passed** on the final production-built standalone frontend, through the actual Next proxy and application endpoints. Provider transport was synthetic; no happy-path browser API-response stubs |
| Browser page errors / failed transports / API 5xx | **0 / 0 / 0** during the 53-check connected happy-path run |
| Connected responsive/recovery checks | **28 checks passed**: all eight screens at **375, 768, 1440 CSS pixels** without page-level horizontal overflow; catalogue/AI outage recovery, synthetic photo scenario, and no uncaught browser errors. This run deliberately injected two HTTP 503 responses |
| Earlier auth/onboarding baseline | **29 checks passed** through the same-origin proxy and isolated backend, plus login/disconnected responsive checks at **1440, 768, 375 CSS pixels**. These are earlier baseline results, not a new final rerun |
| Public policy browser checks | All three public routes opened in the final connected run. Earlier standalone policy baseline additionally verified **HTTP 200** at **1440 and 375 CSS pixels**, draft notices, links/navigation, no overflow/page errors/failed requests |
| Compose configuration | `docker compose --env-file .env.example config --quiet`: passed with synthetic required validation values |
| Docker engine/container acceptance | **Blocked**: Docker Desktop Linux engine named pipe unavailable; no container build/runtime pass claimed |
| Live Meta/Gemini, public HTTPS | **Not verified**; requires operator configuration and the live acceptance checklist |
| Source-delivery review | **120 source files** reviewed/scanned: the original 114 plus three local-only browser QA scripts, two regression-test files, and generated Next.js agent guidance. No matches for the scanned credential patterns. Assignment findings were runtime references, documented placeholders, or existing development/test literals. Pattern scanning is not a comprehensive secret-audit certification |
| Private/generated-file exclusion | `git check-ignore` confirmed environment files, private databases, virtual environments, dependencies, build output, browser artifacts, backups, uploads and key/credential files are excluded |
| GitHub source delivery | Target: `Manthan-Gohel/Jewelai` / `main`; **120 reviewed files** in this follow-up. Initial delivery `e393f47` contained 114 files, with publication recorded through `ce1045a`. Git history identifies the follow-up commits; compare local `HEAD` with the actual remote `refs/heads/main` rather than treating old hashes or local tests as proof of publication. Preserve history and use an ordinary push via native Git Credential Manager, never a chat token. Source publication is not deployment or proof of private visibility/collaborator access |

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

Earlier regressions first reproduced demo business facts in fresh connections and unvalidated negative/non-finite gold rates. Fixes ensure neutral model/database defaults, no fabricated AI store context, finite nonnegative rate inputs, and explicit clearing without modifying other rates. The migration check also verifies neutral database defaults. Existing saved business settings are not overwritten.

The connected follow-up reproduced `UNIQUE constraint failed: messages.meta_message_id` when identical mock deliveries reused deterministic IDs. Three new text/image/carousel tests failed before the fix. UUID-based synthetic IDs passed those regressions and the full 64-test suite; live Meta delivery behavior is unchanged.

The 13 warnings are Pydantic's existing class-based configuration deprecations. They do not fail these tests; migrating that configuration syntax remains maintenance work before a future Pydantic major-version upgrade.

## Frontend checks

From `frontend/`:

```bash
npm test
npm run typecheck
npm run build
npm audit --audit-level=low
```

The regression suite verifies same-origin cookie requests, readable validation/network errors, multipart CSV session-expiration handling, no-content responses, header rendering without a fictitious account/business/rate/API version, saved business values, and currency formatting. Header regressions were observed failing before their targeted fix and then passed. The new currency regression likewise failed with `₹123` instead of `₹123.45` before the fix, then passed while preserving whole-number and zero formatting.

The production build emits a warning about an unrelated `pnpm-workspace.yaml` in the Windows home directory, which Next.js ignores. The standalone output was started with `node .next/standalone/server.js` after copying `.next/static` into the standalone package, matching the image's standalone runtime pattern. No Docker image execution is implied.

## Final connected browser journeys and evidence

The final connected run used a fresh QA database, `scripts/browser-qa-server.py` on **127.0.0.1:8002**, and the final Next.js standalone build on **127.0.0.1:3013**, compiled with `BACKEND_URL=http://127.0.0.1:8002`. `.next/static` was copied into the standalone package as the Dockerfile does. No Docker image was run. The unrelated listener on port 3000 was not stopped or replaced by this follow-up.

Start the disposable QA backend and matching frontend using the connected-dashboard instructions in `README.md`, then execute `scripts/browser-workflow-check.js` followed by `scripts/browser-layout-check.js` using Playwright MCP's `browser_run_code` filename input. They are Playwright function scripts, not standalone Node programs or `npm test` files. Create `.playwright-mcp/` first. On a fresh QA database the workflow returns **53 checks**; reruns against an already-connected fixture skip the initial connection and return one fewer check.

Verified local journeys include:

- First Instagram connection with the application's callback, browser-bound state, and session handling; returning direct Instagram sign-in without email/password; refresh/reconnect/disconnect and reconnect with auto-replies off. Instagram transport is synthetic, not Meta-hosted authentication.
- Saved public-reply switches/text/custom templates survive reopening Manage Link; native product checkboxes, linking/unlinking, post search/refresh, and persisted activity fixtures work. Loaded activity counts no longer pretend to be a complete daily quota.
- Add/search/category selection/delete, decimal price/zero-stock persistence and displayed paise, and CSV preview → Back → preview → mapping/import → refreshed catalogue. The remounted required file input reproduced a blocked second preview before the fix.
- Store rates/details, FAQ creation, business/tone/contact saves, and explicit audit refresh.
- Needs Staff includes pending-human threads without a takeover flag; the pending badge is not labeled AI; expired/recent standard messaging-window labels differ; takeover/manual send/resume and inbox search/filter operations complete through actual endpoints with mock message delivery.
- English/Hindi/Gujarati/custom AI UI scenarios render synthetic results. The responsive run injects a catalogue outage and an AI outage, verifies visible errors/retry recovery, and exercises a synthetic photo response. No claim is made about actual language quality or image matching.
- All eight screens fit at 375/768/1440 CSS pixels. Final screenshots use `.playwright-mcp/workflow-*`; mobile inbox and post-linking pages were visually inspected. No prior committed visual baseline exists, so pixel-regression comparison is inconclusive, not passed.

Meta media/OAuth/message transport and Gemini are deliberately synthetic, and the image fixture is local. Backend authentication, authorization, browser state, persistence, and same-origin proxy requests remain real application behavior. The local-only harness creates a new temporary database instead of opening user data and must never be deployed. These targeted checks are not an exhaustive every-button/every-browser/accessibility audit or live-provider acceptance.

## Earlier auth/onboarding and public-policy baseline

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

Earlier screenshots and the local auth browser harness are under `.playwright-mcp/` with the `handoff-` prefix. They contain synthetic accounts only and can be excluded from source delivery. The committed `scripts/` harness adds connected synthetic-provider checks as described above; real-provider connected behavior still requires live/staging acceptance.

The earlier policy-only standalone build on `http://127.0.0.1:3012` served `/privacy`, `/terms` and `/data-deletion` without authentication. All six route/viewport combinations passed at 1440 and 375 CSS pixels, with HTTP 200, correct headings, visible operator-review warnings, policy navigation and no page-level horizontal overflow. Cross-page link navigation also passed; no page errors or failed transports were observed. Screenshots are under `.playwright-mcp/final-policy-*`; mobile privacy and desktop deletion screenshots were visually inspected. These checks do not establish deployed public reachability or legal acceptance.

## Remaining release gates

1. Start a working Docker engine; build/run the complete Linux Compose stack, verify PostgreSQL migrations, both worker queues, container health, and restart/outage behavior.
2. Configure the real domain, HTTPS, Meta app permissions/access, exact redirect/webhook, and Gemini model access/quota. Complete actual Instagram connect/reconnect/disconnect and DM/comment delivery.
3. Finalize and test the operator's real public policy/support/deletion process. Public policy/deletion routes now exist but are clearly marked operator-review drafts; the legal identity, public contact and retention/deletion schedule must be finalized before real customer data is used. No automatic data-deletion callback is implemented.
4. Validate the client's real catalogue/languages, human takeover, global pause, duplicate handling, provider errors, backup restore, and operational monitoring.
5. Explain remaining limits: no automatic Instagram token refresh, no password-reset email, no server-side bearer-token revocation, process-local login limits, and no shared-team/RBAC/subscription implementation.

Use `docs/client-handoff.md` for exact keep/exclude guidance and the full live checklist. Historical readiness/remediation reports do not override these results. Source-control preparation or GitHub publishing is separate from deployment, Meta review submission and production approval; none of those live operations is established by this report.
