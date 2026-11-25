# Instagram setup — operator guide

Updated November 25, 2026. This application implements **Instagram API with Instagram Login**, not the retired Basic Display flow or the Facebook Login integration. Meta configuration is an operator task; clients must not receive your App Secret or paste access tokens.

## 1. Prepare the app and account

- Use an Instagram Business or Creator account and a Meta developer app with the Instagram product and Instagram business login configured.
- Serve JewelAI from one public HTTPS hostname. Complete the actual privacy-policy and data-deletion requirements shown in your Meta App Dashboard.
- Add the appropriate developer/tester assets for development testing. Serving professional accounts you do not own/manage requires the access level and review approval specified by Meta; a successful tester connection is not production approval.
- Use the **Instagram App ID and Instagram App Secret** shown under the Instagram login setup, not credentials copied from an unrelated Facebook Login configuration. Dashboard labels can change; follow Meta's current business-login documentation below.

## 2. Set server-only configuration

Set these values privately in the operator's production `.env`:

| Setting | Value |
| --- | --- |
| `DOMAIN` | Dashboard hostname only, without a scheme or path |
| `INSTAGRAM_APP_ID` | Your Instagram App ID |
| `INSTAGRAM_APP_SECRET` | Your Instagram App Secret |
| `INSTAGRAM_WEBHOOK_VERIFY_TOKEN` | A private, randomly generated verification secret |
| `SECRET_KEY` | A separate private session/OAuth signing key |
| `ENCRYPTION_KEY` | A generated Fernet key, backed up securely and kept stable |
| `REGISTRATION_INVITE_CODE` | A private invitation code, at least 16 characters |

The supplied Compose file derives the following exact callback from `DOMAIN`:

```text
https://YOUR_HOSTNAME/auth/instagram/callback
```

Register that exact URI in Instagram business login's OAuth redirect settings. For a non-Compose deployment, also set `INSTAGRAM_REDIRECT_URI` to the same value and configure `CORS_ORIGINS` for the dashboard origin. Hostname, scheme, path, and trailing slash must agree. Never put these secrets in `NEXT_PUBLIC_*`, source control, screenshots, or client-facing instructions.

## 3. Permissions and webhook setup

JewelAI's authorization URL requests:

```text
instagram_business_basic
instagram_business_manage_messages
instagram_business_manage_comments
```

These cover the implemented profile/media, messaging, and comment features. The app does not request content-publishing permission.

Configure the Instagram webhook callback:

```text
https://YOUR_HOSTNAME/api/v1/webhooks/instagram
```

Use the same private `INSTAGRAM_WEBHOOK_VERIFY_TOKEN` in Meta and on the server. JewelAI answers Meta's verification challenge and verifies incoming POST signatures with the App Secret. Its per-account subscription request includes `messages`, `messaging_postbacks`, `message_reactions`, and `comments`; confirm the required subscriptions and permissions in your app's dashboard. Subscription success alone does not establish that every event type has an implemented automation handler.

## 4. Client connection flow

1. The client registers an invited workspace with email/password or signs in to an existing workspace.
2. In the connection screen, select **Sign in with Instagram**. If disabled, finish the server configuration first.
3. Authorize the correct professional account on Instagram, then return to JewelAI in the same browser.
4. JewelAI validates browser-bound state, exchanges the code server-side, encrypts the token using authenticated Fernet encryption, and saves the account only after successful webhook subscription.
5. New connections start with automatic replies **off**. Import the real catalogue, review business settings, and complete controlled DM/comment tests before enabling automation.
6. On subsequent visits, Instagram sign-in opens the linked workspace. Email login remains available. Instagram-only first-time registration is intentionally not implemented.

The service exchanges for a long-lived token and stores the expiry Meta returns. Meta documents a 60-day long-lived token and a refresh endpoint, but **automatic refresh is not implemented here**. The connection screen warns within seven days of the saved expiry; reconnect before expiry and whenever authorization is revoked or permissions change.

## 5. Acceptance and troubleshooting

- **Disabled sign-in:** confirm both Instagram credentials are configured on the backend. Do not work around this by enabling direct-token connection for clients.
- **Expired link / wrong browser:** start from JewelAI again in the same browser; do not reuse a copied callback URL or an already-used code.
- **Permissions could not be enabled:** review the granted messaging/comment permissions, app access level, account eligibility, and webhook subscription. The app intentionally does not silently mark a failed subscription as connected.
- **Already linked:** an Instagram account cannot be reassigned to a different workspace by signing in. Reconnect the original account or involve the operator; do not delete data to bypass ownership checks.
- **No replies:** check global automation, post-specific rules, human takeover, messaging policy, worker queues, live webhook delivery, and real Gemini access. Local mocked tests do not verify Meta delivery.
- Complete the live acceptance checklist in `client-handoff.md`, including canceled authorization, reconnect/disconnect, a real signed DM/comment event, and duplicate suppression.

## Official references

- [Instagram API with Instagram Login](https://developers.facebook.com/documentation/instagram-platform/instagram-api-with-instagram-login)
- [Business Login for Instagram: permissions, token exchange, expiry, and refresh](https://developers.facebook.com/documentation/instagram-platform/instagram-api-with-instagram-login/business-login)
- [Fernet encryption and key handling](https://cryptography.io/en/stable/fernet/)

References checked November 25, 2026. The current implementation and `../TEST_RESULTS.md` describe what was actually verified; external documentation does not certify this deployment.
