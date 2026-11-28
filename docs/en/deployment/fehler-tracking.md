# Error tracking (optional)

Without error tracking you only learn about a runtime failure if someone opens the container logs, knows what to search for, and reconstructs the failure from scattered lines. An error tracker inverts that: the application reports every uncaught failure with its stack trace, request context, release and environment, groups recurring events into one issue, and tells you when a fixed error comes back in a later release.

Kamerplanter is **prepared for this but switched off by default**. With no DSN configured, nothing happens at all: the Python SDK is never initialised and the frontend does not even download its SDK bundle. So there is nothing to turn off if you do not run a tracker.

!!! warning "Not implemented yet"
    This page covers the **application side**. Provisioning and operating a GlitchTip instance is not part of this project and is not documented yet.

---

## What you need

A tracker that speaks the Sentry protocol. The reference is [GlitchTip](https://glitchtip.com/) (open source, self-hostable), but nothing in the code binds to it — Sentry itself or any compatible tracker works the same way. Switching is a DSN change, never a code change.

## Turning it on

All four values come from the environment; in Docker Compose from your `.env`:

```bash
SENTRY_DSN=https://<public-key>@glitchtip.example.org/1
SENTRY_ENVIRONMENT=production
SENTRY_RELEASE=v1.4.2
SENTRY_SAMPLE_RATE=1.0
```

The DSN carries only a public ingest key, not a secret — it is meant to reach the frontend, because that is exactly where it is needed.

On Kubernetes you set the same values in the Helm values. They sit on `backend`, `celery-worker`, `celery-beat`, `inference-service` and on `frontend` in the init container `init-runtime-config`. It writes `runtime-config.js` and also adds exactly the origin of your DSN (scheme, host and port) to the Content-Security-Policy's `connect-src`, so the browser may send its error reports there. You do not set the DSN on the nginx container. <!-- #3025 -->

!!! danger "NetworkPolicy: a self-hosted tracker is unreachable at first"
    The backend's egress rule permits outbound traffic to the internet but **deliberately excludes the private address ranges** (RFC 1918, plus link-local). If your tracker runs in the same cluster or on the LAN, it needs an additional egress rule. Without it, events are dropped with no error surfacing anywhere — the SDK does not report a blocked connection. Enabling this is therefore two changes, not one.

---

## The environments

`SENTRY_ENVIRONMENT` comes from a **closed vocabulary**. Alert rules filter on these exact strings, and the value must be the same across every component:

| Value | For |
|-------|-----|
| `development` | Local development. The default when nothing is set. Nobody may ever be paged from this environment. |
| `e2e` | The end-to-end test runs. Deliberately provoked failures belong here, not in the alert channel. |
| `staging` | The pre-production stage. A new issue here is a release-readiness input for the candidate. |
| `production` | Live operation. The only environment that pages. |

A typo (`producton`) does **not** prevent initialisation — the application logs a warning and reports anyway. That is deliberate: refusing quietly would look exactly like a healthy, quiet instance, whereas a stray value in the tracker's environment list is noticed immediately.

## The release identifier

`SENTRY_RELEASE` should be the image tag or the commit SHA. Without it the tracker cannot say which deployment introduced a failure, and it cannot tell a **regression** — an issue marked resolved that reappears — from a new issue. That distinction is the point at which an error tracker becomes more than a list of errors.

With nothing set, each component reports a coarse fallback (`kamerplanter-backend@1.0.0`, and `kamerplanter-frontend@dev` in the browser). It is deliberately recognisable as useless.

## The sample rate

`SENTRY_SAMPLE_RATE=1.0` — **every** event is reported.

This is a decision, not a default nobody touched: at the volume a Kamerplanter instance produces, sampling is just a way to miss the one failure that happens once a day. As soon as event volume becomes noticeable — particularly on a hosted plan with a quota — the rate should be re-evaluated and recorded here. An unparseable value falls back to `1.0` and logs that it did.

---

## What is never transmitted

Error events can contain personal data, so filtering happens at the SDK boundary before anything leaves the process:

- **Request bodies and cookies** are dropped wholesale. A request body is the richest source of personal data this application has — plant notes, harvest records, invitations.
- **Headers** follow an allow-list (`Content-Type`, `User-Agent` and a few more). A header some future proxy adds is therefore withheld by default, instead of leaking until someone remembers to block it.
- **The request address** is the route pattern, never the requested path: the event URL and transaction name read `/api/v1/t/{tenant_slug}/attachments/{key}/…`, not the path with tenant slug and download token (the token *is* the authorisation). When the framework supplied no pattern (a 404, an error before routing), the backend reduces the path to fixed route segments as in its access logs. Method, host and status code stay.
- **Query parameters** keep only their name, every value is redacted — also the raw query of outbound requests in breadcrumbs (`http.query`). **Context fields** are redacted by *name* (`token`, `password`, `email`, `secret`, …), in nested structures too. The key stays visible, the value does not — so a reader can tell a credential was present there.
- **Stack-frame locals** are not sent. A variable's name does not say what it holds — `url` or `html` in a mail adapter hold the password-reset link. An event therefore shows files, functions and lines, but no runtime values.
- **Exception texts and log messages** go through the same cleanup as the log lines, in the backend and the Celery worker: an error message from the application's own domain logic appears only as its error code, email addresses become digests, query strings and credentials in URLs (in the path too, such as a Telegram bot token) become `<redacted>`. The same holds for breadcrumbs. The two side services (inference-service, knowledge-service) apply a simpler cleanup that recognises shapes only: credentials and query strings in URLs, a Telegram-style token in a path, email addresses (as `<email>`). Free text such as a search question has no shape and is not hidden there. Uncaught tracebacks that these services print to stderr go through the same cleanup, and dictionary keys, tags and contexts of an event are cleaned like values.
- **Of the user**, the backend sends pseudonyms only, and only with that person's `error_tracking` consent (privacy settings): `user.id` is the account reference `sub_…`, `user.tenant` the tenant reference `ten_…` of the request — the same values as in the log lines, never the keys. Without consent, or when it cannot be read, the event leaves without a user block. They make an issue actionable and attributable to a tenant; name, email and IP address do not. Whatever the SDK or an integration writes into the user block itself is dropped. Events of the Celery worker and of the side services carry no user block.
- **Input breadcrumbs** (`ui.input`) are discarded entirely in the browser.

The rules run in **every** environment, including locally. A filter that is only switched on at go-live is an untested filter.

## What the tracker is not

A log sink. Only errors and deliberately captured events belong there; INFO and DEBUG messages stay in the logging pipeline. Anything else destroys grouping quality and the event budget.

---

## What gets reported

| Component | What the SDK covers |
|-----------|--------------------|
| Backend (FastAPI) | Uncaught exceptions in any request, plus startup failures |
| Celery worker and beat | Failed background jobs — the least visible failure class there is, because nobody is waiting on a response |
| Inference and knowledge service | The same, each with its own `component` tag |
| Frontend | Uncaught errors, rejected promises, and every render failure an error boundary catches — only once the person in the browser has consented to error analysis (see below) |

The frontend's error boundaries report explicitly: a boundary that renders a fallback has, from every global handler's point of view, made the error disappear — the user sees a tidy card and nobody is told the widget is broken.

## Consent in the frontend

In the browser the DSN alone is not enough: the frontend loads and starts its SDK only when the consent **Send error reports from the browser** (`browser_error_reports`) allows it. It is a purpose of its own; the server-side consent `error_tracking` still only decides whether a backend event carries the account and garden pseudonyms. As long as there is no valid consent, the browser does not download the SDK bundle and no error report leaves it.

- **Where it is asked:** with a DSN set, a consent banner appears at the bottom offering "Accept all", "Necessary only" and "Settings" — for this browser when signed out, for the account after signing in. Its text names the host from the DSN as the recipient. Without a DSN there is no banner.
- **Whose decision counts:** signed out, the browser's (`localStorage`, `kamerplanter:consent:v1`). Signed in, only the account's (`POST`/`DELETE /api/v1/privacy/consents`, with text version, IP address and user agent as evidence) — and only if sending was not declined in this browser without signing in. A browser grant is never taken over into the account. Before the sign-in check has finished, the frontend sends nothing; errors from the first moments of a page view are therefore missing in the tracker.
- **After the update:** people who had only consented in the browser are asked once more by the banner; earlier declines stay in place. Frontend errors therefore arrive less often at first after the update.
- **Errors only, without identifiers:** the frontend sends no sessions (release-health figures such as "crash-free sessions" therefore stay empty for the frontend) and no client reports. In addresses of events and breadcrumbs it replaces the tenant short name with `:tenant`, record keys with `:key`/`:id` and tokens with `:token` — grouping by route still works.
- **Sync:** a signed-in tab reads the account consent on sign-in, when the tab becomes visible again, when the network comes back, and every ten minutes; without a sync a confirmation expires after 30 minutes. A failed sync means "no consent".
- **Light mode:** no banner appears here (the GDPR household exemption), and in Light mode the frontend reports no errors — not even when the browser still holds a consent from before the switch to Light mode. The backend keeps reporting.
- **Revoking:** under **Privacy → Consents**, section "Error reports from the browser", there is the switch "Allow for my account". Turning it off stops reporting at once, without a reload, also in other open tabs.

For you as the operator this means: after setting the DSN, frontend errors only arrive from people who consented. A quiet frontend area in the tracker can therefore also mean "nobody consented".

## Verifying it works

There is no test button. The reliable path:

1. Set `SENTRY_DSN` and restart the containers.
2. Backend: the logs contain `error_tracking: enabled for backend (environment=…, release=…)`.
3. Frontend: open the application in a private window. The consent banner appears — if it does not, the DSN never reached `runtime-config.js`. Click "Accept all": only now does the browser's network tab show an additional JavaScript bundle, the lazily loaded SDK.
4. Provoke a failure and check that it arrives. If it does not, look at the NetworkPolicy first (backend) or the Content-Security-Policy (frontend, visible as a CSP violation in the browser console).
