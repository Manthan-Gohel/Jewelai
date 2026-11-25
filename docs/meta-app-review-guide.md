# Meta App Review preparation — not submission evidence

Updated November 25, 2026. **No review submission, approval, public policy URL, deletion callback, or live delivery has been verified for this deployment.** The previous pre-checked checklist and example performance guarantees were inaccurate and have been removed.

Use `instagram-setup.md` for the implemented Instagram Login flow and official references. Follow the current requirements in your own Meta App Dashboard; do not assume an app mode switch alone authorizes every client account.

## Describe only implemented uses

JewelAI requests three permissions:

- `instagram_business_basic`: identify the professional account and retrieve profile/media used by the dashboard and post linking.
- `instagram_business_manage_messages`: receive customer message events, send permitted automated replies, and support manual replies from the inbox.
- `instagram_business_manage_comments`: receive comment events and support the configured comment/private-reply workflows.

Explain the actual business use and data handling in your own words. Do not claim publishing, analytics permissions, an automatic live gold-price feed, guaranteed response times, or error-free AI. Gold rates are operator-entered, and AI validation is heuristic.

## Public policy and deletion work is still required

The source includes `/privacy`, `/terms` and `/data-deletion` pages, verified locally and clearly marked **operator-review drafts**. Finalize the actual operator identity, public privacy/support contact, retention schedule and tested deletion procedure before publishing them for real users or supplying their HTTPS URLs to Meta. Local pages are not deployed public-policy evidence. No automatic data-deletion callback is implemented; do not advertise a nonexistent API route.

The operator must supply the policy/support/deletion surfaces required by its Meta configuration and an actual process for handling deletion requests, retained records, backups, and external processing. Any callback advertised to Meta must first be implemented and tested. Match policy statements to real operations, and have the responsible business/privacy owner approve them.

Disconnecting Instagram clears JewelAI's local saved token and pauses automation. It does not delete all workspace records or implement an account-wide Meta authorization revocation flow.

## Record a real, controlled demonstration

Use an HTTPS staging deployment, approved test accounts, and synthetic customer/catalogue data. Redact secrets and unrelated customer information. Follow the submission format requested by your dashboard rather than an invented fixed video length.

1. Show invited email registration/sign-in, then the official Instagram connection and the permissions requested.
2. Return to the connected workspace and show automation initially off. Show the real linked professional account, not a hardcoded demo badge.
3. Upload a small accurate catalogue and set the business's rates/policies. Enable automatic replies only for the controlled test.
4. Send an actual incoming customer DM and demonstrate a delivered reply. Measure what occurs; do not promise a two-second response time.
5. If requesting comment permission, show a linked post, an actual comment event, and the supported private/public reply behavior.
6. Show manual takeover and the global pause preventing further automated replies. Demonstrate disconnect/reconnect and how the operator handles failures/deletion requests.

Mocked tests, static screenshots, and local pipeline tests are useful engineering checks but are not proof of live Meta authorization or delivery.

## Operator completion checklist

- [ ] Confirm app/account eligibility and the access level required for the actual clients.
- [ ] Configure exact OAuth redirect, requested permissions, webhook verification, and subscriptions.
- [ ] Supply the actual public policy/support/deletion surfaces required by the app configuration.
- [ ] Test the implemented deletion process; do not advertise a nonexistent callback.
- [ ] Prepare reviewer access and instructions according to Meta's current requirements, without sharing operator secrets.
- [ ] Record a real end-to-end demonstration with controlled test accounts/data.
- [ ] Submit accurate app/business details and permission-use explanations.
- [ ] Record Meta's actual decision and complete `client-handoff.md` live acceptance before client sign-off.
