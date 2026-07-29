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

On Kubernetes you set the same values in the Helm values. They sit on `backend`, `celery-worker`, `celery-beat`, `inference-service` and — twice — on `frontend`: once in the init container that writes `runtime-config.js`, and once on the nginx container that derives the Content-Security-Policy from it.

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
- **Query parameters, stack-frame locals and context fields** are redacted by *name* (`token`, `password`, `email`, `secret`, …). The key stays visible, the value does not — so a reader can tell a credential was present there.
- **Of the user**, only `id` and tenant survive. They make an issue actionable; name, email and IP address do not.
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
| Frontend | Uncaught errors, rejected promises, and every render failure an error boundary catches |

The frontend's error boundaries report explicitly: a boundary that renders a fallback has, from every global handler's point of view, made the error disappear — the user sees a tidy card and nobody is told the widget is broken.

## Verifying it works

There is no test button. The reliable path:

1. Set `SENTRY_DSN` and restart the containers.
2. Backend: the logs contain `error_tracking: enabled for backend (environment=…, release=…)`.
3. Frontend: the browser's network tab shows an additional JavaScript bundle — that is the lazily loaded SDK. If it does not appear, the DSN never reached `runtime-config.js`.
4. Provoke a failure and check that it arrives. If it does not, look at the NetworkPolicy first (backend) or the Content-Security-Policy (frontend, visible as a CSP violation in the browser console).
