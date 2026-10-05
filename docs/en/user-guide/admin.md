# Platform Admin Area

The platform admin area is exclusively accessible to users with the platform role **admin**. It enables platform-wide management of all tenants and users — independent of the tenant-scoped tenant-admin role.

---

## Prerequisites

- Platform role **admin** (distinct from the tenant-admin role)
- Access via `/admin/platform` (in full mode)

!!! warning "Do not confuse with tenant-admin"
    The platform-admin role is a **platform-wide** special role. It grants access to data across all tenants. The tenant-admin role, by contrast, is limited to a single tenant and is assigned via **Settings > Tenants > Members**.

---

## Distinction: Platform-Admin vs. Tenant-Admin

| Function | Platform Admin | Tenant Admin |
|---------|---------------|-------------|
| Manage all tenants | Yes | No |
| Platform-wide user management | Yes | No |
| View tenant statistics | Yes | No |
| Configure OIDC providers | Yes | No |
| Manage own tenant's members | Yes | Yes |
| Tenant locations and plant data | Yes | Yes |

---

## Tenant Management

In the **Admin > Tenants** section you can:

- View all platform tenants (name, slug, member count, creation date)
- Deactivate or delete individual tenants
- View tenant quotas and limits
- Manage a tenant's members on their behalf

!!! info "A deactivated tenant locks every member out"
    When you deactivate a tenant, no member can reach it any more — not in the app, not with an API key, not from an MCP client. To its members it then looks like a tenant that does not exist. If it was their personal garden, they only see the shared plant catalogue. The memberships and all data are kept: when you reactivate the tenant, every member immediately has their previous access with the same role again. You yourself keep administering a deactivated tenant here in the admin area. <!-- Issue #2105 -->

!!! danger "Deleting a tenant is irreversible"
    Deleting a tenant first deactivates every membership immediately, then removes its contributed recognition vectors, its object storage (photos, attachments) and every domain record it holds — sites, plants, planting runs, diary entries, tasks, tanks, sensors and every other location-bound record — and finally the tenant record itself. Harvest and treatment documentation is exempt because it must be kept for several years under statutory law (CanG, German Plant Protection Act): those records are retained but pseudonymized. This action cannot be undone. Create a data export for the affected tenant beforehand. <!-- Issue #1769 -->

    A confirmation dialog additionally requires you to re-confirm before the deletion runs: enter the tenant's slug and, if your account has a local password, your current password — if it has none and you sign in through Google or a generic OIDC provider, you instead click **Sign in again**; only for an account signed in exclusively through GitHub/Apple, click **Send code by email** and enter the confirmation code it mails you. If the entered slug does not match, the action reports `422`; if the password, fresh sign-in, or code is missing or wrong, it reports `401` — in all cases the tenant stays unchanged. A service account cannot perform this action, and neither can signing in with a personal API key instead of a signed-in session. After five wrong confirmations the system locks the confirmation for 15 minutes — repeated failures double the wait time up to 4 hours (`429`, the message states the wait time); the same budget applies account-wide to confirming an account deletion, an email change, and a password change too. <!-- Issue #1791, #1813, #1814, #1816, #1815, #1841 -->

    The action answers `202 Accepted` (formerly `200` or `204`): it only accepts the deletion, creates the deletion record and deactivates every membership — the deletion itself then runs in the background in a worker, in small batches with a continuous heartbeat. When the response arrives, nothing is deleted yet; the interface reports "Deletion accepted". If a step fails or something is left over, you no longer see it as an error (`500`/`502`) on the action: the deletion stays recorded, the daily retry run resumes it automatically, and after the third unsuccessful attempt the system raises an operator alert (log event `tenant_erasure.escalated`). If a deletion is already running for the tenant, a second attempt reports a conflict (`409`). <!-- Issue #1792 --> If the instance is not correctly configured for tenant deletion, it reports `503` — in this case nothing was changed.

---

## User Management

In the **Admin > Users** section you can:

- View all user accounts on the platform
- Lock or deactivate user accounts
- Assign platform roles (`admin`, `viewer`)
- Trigger password resets for users
- Process GDPR requests (data deletion, data access)

!!! note "GDPR requests"
    Data subject rights under GDPR Art. 15–21 are available to users via the self-service API at `/api/v1/privacy/`. As a platform admin, you can view and process requests in the admin area. See [Privacy (GDPR)](privacy.md) for details.

!!! note "Verifying an email or reactivating an account requires your own confirmation"
    If you change whether a user's email address counts as verified, or whether the account is active (marking it verified, withdrawing the verification, reactivating or deactivating it) in the edit-user dialog, you additionally confirm with your **own** current password — if you don't have one, you instead sign in again with your sign-in provider, or, only if you sign in exclusively through GitHub or Apple, have a code sent by email. Reason: a verified email address lets sign-in providers link to this account automatically (see [Account & Sign-In](account.md#signing-in-with-google-github-or-another-provider)) — a hijacked admin session could otherwise mark someone else's account as verified under a victim's address. Withdrawing the verification matters just as much: an unverified account is what the daily clean-up removes, and a deactivated one cannot sign in — so these changes are step-up acts too, and an API key is refused (`403`). An account whose verification an administrator withdrew is **never** removed by the clean-up of unconfirmed accounts. Renaming and re-saving unchanged values require no additional confirmation. After too many failed attempts, the same lockout as described below for account deletion applies (15 minutes, doubling up to 4 hours, `429`). <!-- Issue #1857, #1992 -->

!!! note "Deactivating a tenant, changing a role and removing a member ask for your own confirmation"
    When you deactivate or reactivate a tenant, change a member's role (also from a user's tenant section) or remove a member, you confirm with **your own** current password — if you have none, you sign in again at your identity provider instead, or, only when you sign in exclusively through GitHub or Apple, have a code e-mailed. Reason: each of these can lock members out of a tenant or take their lead role away. Renaming and re-sending an unchanged value need no confirmation.

!!! note "Adding a user to a tenant asks for your own confirmation"
    When you add a user to a tenant — from the tenant view as well as the user view — you confirm with **your own** current password (without a local password: a fresh sign-in at your provider, or, for GitHub/Apple only, a code by email). Reason: whoever receives the lead role in the `platform` tenant is a platform admin, and in any other tenant the membership gives access to its data. You cannot add yourself to the `platform` tenant. Every add is written to the security audit (`GET /api/v1/admin/platform/security-audit`; kept two years) — as is every role, scope and removal change. <!-- Issue #2106, #2111 -->

!!! note "Who may register"
    Whether anybody can register, only with an invitation or nobody, you decide as the operator with `REGISTRATION_MODE` (`open` is the default; see [Environment variables](../reference/environment-variables.md)); `REGISTRATION_ALLOWED_DOMAINS` additionally limits registration to certain email domains. A pending email invitation for exactly the address opens registration for `invite_only` and despite the domain list — not for `closed`. Existing accounts sign in in every mode. <!-- Issue #2132 -->

!!! note "Member limit and platform ceiling"
    Every tenant has a member limit (`max_members`). It can be at most the platform ceiling `TENANT_MAX_MEMBERS_CEILING` (default 50, see [Environment variables](../reference/environment-variables.md)) — for you as a platform admin too. Once a tenant is full, adding a member is refused before you are asked for your confirmation. If you lower the ceiling, tenants holding more members keep all of them; only new joins are refused. The platform tenant is not exempt. <!-- Issue #2133 -->

!!! danger "Deleting a user account is immediate and complete"
    A confirmation dialog requires you to re-confirm before the deletion runs: enter the **target account's email address** and your **own** current password, if your admin account has a local password — if it doesn't and you sign in through Google or a generic OIDC provider, you instead click **Sign in again**; only if you sign in exclusively through GitHub/Apple, click **Send code by email** and enter your own confirmation code; never the password of the account being deleted. If the entered email address does not match, the action reports `422`; if your password, fresh sign-in, or code is missing or wrong, it reports `401`. You cannot delete your own account this way (`403`). After five wrong confirmations the system locks the confirmation for 15 minutes — repeated failures double the wait time up to 4 hours (`429`, the message states the wait time); the same budget applies account-wide to tenant deletion, email changes, and password changes too. <!-- Issue #1813, #1814, #1816, #1815, #1841 -->

    Once confirmed successfully, the action answers `202 Accepted` (formerly `204`): the deletion is accepted, the user account is deactivated at once, all sessions end, the other members of its personal gardens are told right away (no grace period), and the full account erasure then runs in the background in a worker (see [Data Retention & Anonymization](../guides/data-retention.md)). When the response arrives, nothing is erased yet; the body names the erasure request (`erasure_key`), whose status you read from `GET /api/v1/admin/platform/erasures/{erasure_key}` (`completed` once everything is done). <!-- Issue #1949 --> An erasure request is persisted as proof — the same as when a user deletes their own account; it additionally carries a salted reference to you as the confirming admin, never your account key in the clear.

    If the erasure could not be fully completed — or a single external service could not be reached — the erasure request shows `partially_completed` and is automatically resumed by the daily retry run; you do not need to redo anything manually (the action no longer answers `500` or `502` for this). A second deletion attempt for the same account resumes the open request at once instead of waiting for the next run, and answers `202` again; while a run is still working on it, the action answers `409`.

    If a deletion for that account is already running (for example, through the daily cleanup for never-confirmed accounts), the action reports a conflict (`409`). If the instance is not configured correctly for account erasure, it reports `503` — in that case nothing was changed.

---

## Statistics

The **Admin > Statistics** section provides an overview of:

- Number of active tenants and users
- Active planting runs platform-wide
- Celery task queue status
- Storage usage (ArangoDB, TimescaleDB, Redis)

---

## OIDC Providers

Here you configure federated authentication providers (e.g. Google, GitHub, corporate OIDC instances). These settings apply platform-wide to all tenants.

You manage them on a page of their own: open **Settings > Platform Mode** and click **Manage OIDC providers** in the "Sign-in providers (OIDC)" card (address `/admin/oidc-providers`). The card only appears for platform admins. On the page you can:

- see every provider with its type, issuer URL, client ID, scopes, whether it is active and when its discovery document was last fetched
- **add** a provider (**Add provider**)
- **edit** a provider (pencil icon)
- **test** a provider (**Test**): it fetches the discovery document and reports four findings — scopes, provider type, signing keys and issuer — each as "OK", "Failed" or "Not applicable", with the reason the server names. The test needs no confirmation.
- **delete** a provider (trash icon)

A new provider starts **switched off**. It only shows up on the sign-in page once you switch it on.

!!! warning "Anything that affects who may sign in asks you to confirm again"
    A provider decides whom a sign-in belongs to: whoever can point a provider at a server of their own can sign in as any account whose address that server claims. So adding, deleting and every change except the display name and the icon asks you to confirm with your own credentials: your current password — or, without a local password, a fresh sign-in at your provider or the confirmation code that arrives by e-mail. When deleting, you also type the provider's short name. Switching a provider on **or off** needs the confirmation too: a disabled provider can no longer re-authenticate anyone, and the accounts linked only through it would fall back to the weaker e-mailed code. The form tells you before you submit whether your change needs the confirmation. A signed-in session with a personal API key cannot change providers at all.

    Known edge case: if you sign in **only** through the very provider you want to repair, and it is broken right now, you cannot sign in there again. Set yourself a local password beforehand. <!-- #1883, #1906 -->

!!! info "The client secret is write-only"
    The client secret is stored encrypted and never shown again — not in the list, not in the edit form. When you edit a provider, leave **New client secret** empty to keep the stored one; a new secret needs your confirmation. <!-- #1906 -->

!!! info "Fixed endpoints and the default tenant are set when you add the provider"
    **Advanced** in the add form takes fixed addresses for authorization, token, userinfo and key set, and the default tenant that new federated accounts join. The interface does not show them afterwards because the interface to the server does not return them; to change them later, use the REST API under `/api/v1/admin/oidc-providers` (`PUT`). The short name (slug) cannot be changed after adding either: it is part of the callback URL. <!-- #1906 -->

!!! info "Register the callback URL with the provider"
    Register exactly `{APP_BASE_URL}/api/v1/auth/oauth/{slug}/callback` as the provider's callback URL (redirect URI) — with the public address from `APP_BASE_URL` and the provider's short name (slug), e.g. `https://garden.example/api/v1/auth/oauth/google/callback`. Sign-in and the fresh sign-in that confirms an action use the same URL. While `APP_BASE_URL` is still the default `http://localhost:5173`, the provider refuses the sign-in. <!-- #1865 -->

!!! info "Two providers, the same identifier"
    A link belongs to exactly the provider it was made through. If another provider reports the same user identifier (`sub`), that is a different person — it is never signed in to the linked account. The update assigned older links to their provider where exactly one provider of their type existed. If two generic OIDC providers were already set up at that point, the assignment is open: the people concerned sign in once more through their verified e-mail address (or with their password). <!-- #1869 -->

!!! info "Deleting, re-creating and repointing a provider"
    **Deleting** a provider also deletes every link made through it (and its encrypted provider tokens) — otherwise a provider created later under the same short name (slug), possibly at another identity provider, would inherit them. The affected accounts keep their other ways in; whoever was signed in only through this provider signs in once through their verified e-mail address (or with the password) after the provider is re-created. The log event `oidc_provider.deleted` carries the count (`links_deleted`), no accounts. **Creating** a provider likewise removes links an earlier deletion left behind under that slug. **Repointing** `issuer_url` or `provider_type` deletes the stored discovery document in the same step: it belonged to the old issuer. Until the next fetch (every 6 hours, or `POST /api/v1/admin/oidc-providers/{key}/test`) the new issuer's endpoints are unknown — unless you set them yourself, run the test right after repointing. A fetched discovery document is accepted only if its `issuer` is the configured issuer and it contains `authorization_endpoint`, `token_endpoint` and `jwks_uri`. <!-- #1935, #1969 -->

!!! info "Sign-in checks the ID token"
    Signing in through a provider that issues an ID token checks the signature (keys from `jwks_url` or the discovery document), issuer, audience (`aud`), `nonce` and validity, and the `sub` must be non-empty and match the userinfo result. If the sign-in of a previously working provider fails with `provider_error` afterwards, look for the log event `oauth_login_refused` — its `reason` field names the failed check (`signature` or `jwks_unavailable`: keys unreachable or wrong; `iss`: `issuer_url` does not equal the provider's `iss`; `sub_mismatch`: userinfo and ID token name different people). The key set must be reachable over `https`. <!-- #1936 -->


!!! info "`https` addresses only; key fetch with a cache and limits"
    The form and the API accept `issuer_url`, `authorization_url`, `token_url`, `userinfo_url` and `jwks_url` (optional: pins the provider's key endpoint) only as `https` addresses and answers anything else with `422`. Only with `DEBUG=true` is `http` to `localhost`, `127.0.0.1` or `::1` allowed (local development against a provider on the same machine). A configuration you stored with `http` before this rule stays stored but is no longer contacted at sign-in: the sign-in ends with `provider_error` until you change the address to `https` — the test (`POST /api/v1/admin/oidc-providers/{key}/test`) names the reason. An update that repeats the old `http` field unchanged is answered with `422` too.

    The server does not fetch the provider's keys on every sign-in: it keeps them per provider for ten minutes in the memory of each worker and fetches them again when an ID token names an unknown key (`kid`) — at most once every ten seconds per provider. A fetch failure is remembered for 30 seconds only; after that the server tries again. Responses over 256 KiB are discarded, and a single unusable key in the set is skipped. If the provider's discovery document names a `jwks_uri` on an internal address (metadata service, private network), the server does not fetch it; a provider on your own network may publish its key set only on its own host — otherwise enter it yourself as `jwks_url`. In addition, sign-in refuses an ID token that is not valid yet (`nbf`, 30 seconds of tolerance, reason `nbf`) or was issued more than ten minutes ago (`iat`). <!-- #1987 -->

    The same rule applies to the token and userinfo endpoints, which receive the client secret, the authorization code and the access token: when they come from the discovery document, the server never dials them on a metadata or link-local address, and on a private address only on the issuer's own host; if you enter `token_url` or `userinfo_url` yourself, a private address is your choice, the metadata address never. The address of `issuer_url` is checked the same way before the discovery document is fetched. Their responses are capped at 256 KiB like the key set. A refused sign-in shows up in the log as `oauth_endpoint_refused` (reason e.g. `The token endpoint resolves to a blocked address.`); the browser sees `provider_error`. <!-- #2007 -->

!!! info "The test reports keys and issuer"
    Besides `scope_check` and `provider_type_check`, `POST /api/v1/admin/oidc-providers/{key}/test` returns two more findings so that you see a failing sign-in check before users meet it: `jwks_check` (`ok`, `jwks_url`, `key_count`, `skipped_key_count`, `key_ids`, `detail`) fetches the key set the way sign-in does and says whether that worked; `issuer_check` (`ok`, `configured_issuer`, `accepted_issuers`, `discovery_issuer`, `detail`) says whether the `iss` the provider announces is the one sign-in accepts. If it differs, `detail` names the announced value, which is the one to set as `issuer_url`. Both findings carry `applicable: false` when the provider issues no ID token (GitHub, or a provider without the `openid` scope). The test does not fill the sign-in's cache. When you **repoint** `issuer_url`, the API also clears the stored `authorization_url`, `token_url`, `userinfo_url` and `jwks_url` that the request does not name again — they belonged to the old issuer.

!!! info "Deleting and re-creating at the same time"
    A sign-in that is running while you delete a provider and create another under the same slug no longer writes a link or an account into the new provider: it ends with `provider_error` (`reason=configuration_changed`). Links now also carry the key of their configuration; older ones without a key are matched by slug as before. Creating a provider stores it switched off first, removes the slug's orphans and then switches it on; if two admins create the same slug at the same time, the second fails with `409` without deleting any of the first's links. <!-- #1987 -->

!!! warning "The provider type is limited to four values"
    Only `google`, `github`, `apple` and `oidc` are valid — lower-case. Anything else, including `GitHub` or `GITHUB`, is rejected with `422` on create and on update.

    The reason: sign-in reads the type character by character. A provider registered as `GitHub` used to be stored and was then served by the **generic OIDC branch** — GitHub's well-known endpoints were not used, the GitHub address lookup never happened, and nothing complained.

    `oidc` is the right value for any provider without special handling of its own (Keycloak, Authentik, Azure AD, Okta); its endpoints then come from the discovery document.

    For providers stored before this check existed, `POST /api/v1/admin/oidc-providers/{key}/test` reports the finding in its `provider_type_check` field (`ok`, `provider_type`, `known_provider_types`, `detail`). Existing entries are **not** rewritten automatically — correct them in the edit form (or with `PUT`).

!!! warning "GitHub requires the `user:email` scope"
    A provider of type `github` whose scope list contains neither `user:email` nor the parent scope `user` is rejected with `422` on create and on update.

    The reason: GitHub exposes whether an address is verified only through `GET /user/emails`, and that endpoint answers `403` without the scope. Without it **every** sign-in through this provider treats the address as unverified and an existing account is never linked automatically — until now the only trace was one log line per sign-in.

    Spelling matters: GitHub scope names are lower-case, so `USER:EMAIL` is rejected. Several scopes may share one entry (`"read:user user:email"`).

    For providers stored before this check existed, `POST /api/v1/admin/oidc-providers/{key}/test` reports the same finding in its `scope_check` field (`ok`, `missing_scopes`, `detail`). The test does not need a valid discovery document — GitHub publishes none, and the scope verdict is reported anyway.

See [Authentication](../api/authentication.md) for details.

---

## Enabling Plant Photo Identification

[Photo identification](plant-identification.md) is an optional feature that requires API credentials from a third-party service. As long as no key is configured, the backend reports `available: false` and the entire camera/upload UI remains hidden for all users.

The Pl@ntNet API key is an **instance-wide setting** — a single key applies to all users of the instance. The free tier allows 500 identifications per day across the entire instance.

!!! note "Platform admin required"
    Only users with the platform role **admin** can manage the API key. The setting applies platform-wide.

### Step 1: Obtain a free Pl@ntNet key

1. Open [my.plantnet.org](https://my.plantnet.org) in a browser
2. Create an account or sign in
3. Navigate to **Account** > **API key**
4. Copy the displayed API key

!!! warning "Non-commercial use only"
    The Pl@ntNet free tier is explicitly licensed for non-commercial use. For commercial instances review the terms of use at [my.plantnet.org](https://my.plantnet.org).

### Step 2: Enter the key via the Admin UI (recommended)

This is the **preferred method** — no pod restart required, no file changes, takes effect immediately.

1. Sign in as a platform admin
2. Open **Account Settings** (click your profile picture in the top right)
3. Select the **Integrations** tab
4. Scroll to the **Plant Identification** section
5. Enter the copied API key in the **Pl@ntNet API Key** field
6. Click **Save**

The key is stored in masked form — it is never visible in plain text in API responses or logs. The field indicates whether the key is sourced from the database (UI entry), from an environment variable, or is not set at all.

**Optional: Test the key immediately**

After saving, click **Test Connection**. The backend sends a test request to Pl@ntNet and reports whether the key is valid and how many requests remain for today.

!!! info "Stored encrypted"
    Kamerplanter stores the Pl@ntNet key and the Home Assistant token encrypted with the instance's `FERNET_KEY`; the interface shows only the last four characters. Without a `FERNET_KEY` — possible only with `DEBUG=true` — they stay plaintext and the log reports `encryption_disabled`. <!-- #2113 -->

**Optional: Remove the key**

Click **Remove** to delete the database-stored key. If no environment variable is set either, photo identification is deactivated immediately.

---

### Alternative: Set the key as an environment variable

The environment variable `PLANTNET_API_KEY` remains fully supported — it is suitable for automated deployments, GitOps workflows, or when UI access is not used.

!!! warning "Priority: UI value takes precedence"
    If a key is stored in the database via the Admin UI, it **overrides the `PLANTNET_API_KEY` environment variable**. A key set via the UI takes effect immediately without a pod restart. The environment variable is only used when no database entry exists.

=== "Production / Kubernetes"

    Create a Kubernetes Secret and load it into the backend via `envFrom`. **Never** commit the key in plain text in `values.yaml`.

    ```bash
    kubectl create secret generic kamerplanter-secrets \
      --from-literal=PLANTNET_API_KEY="your-api-key" \
      --namespace kamerplanter
    ```

    Reference the secret in Helm values:

    ```yaml
    # helm/kamerplanter/values.yaml (excerpt)
    backend:
      envFrom:
        - secretRef:
            name: kamerplanter-secrets
    ```

    After the next rollout the backend automatically reads the key from the secret environment variable.

=== "Local dev (kind / Skaffold)"

    For quick testing without a Kubernetes Secret: add the variable directly to the `env:` block of the backend container in `helm/kamerplanter/values.yaml`. **Do not commit.**

    ```yaml
    # helm/kamerplanter/values.yaml (local only, do not commit)
    backend:
      env:
        PLANTNET_API_KEY: "your-api-key"
    ```

    Skaffold redeploys the change automatically.

=== "Docker Compose"

    Add the key to the `.env` file in the repository root:

    ```bash
    # .env (do not commit)
    PLANTNET_API_KEY=your-api-key
    ```

    Restart the stack:

    ```bash
    docker compose up -d
    ```

### Step 3: Verify activation via API

Call the status endpoint:

```bash
curl -s http://localhost:8000/api/v1/recognition/status | python3 -m json.tool
```

Expected response when the key is correctly set:

```json
{
  "available": true,
  "adapter": "plantnet",
  "daily_limit": 500,
  "remaining_today": 498
}
```

After successful configuration, the camera/upload function and the **Add by Photo** button in the species overview appear automatically in the UI. Users see the consent dialog the first time they use the feature — from that point on it is fully functional.

### Optional fine-tuning

The following variables do not usually need to be changed. They have sensible default values. A full description is available in the [Environment Variables reference](../reference/environment-variables.md#photo-identification-req-029):

| Variable | Default | Purpose |
|----------|---------|---------|
| `IDENTIFICATION_PRIMARY_ADAPTER` | `plantnet` | Preferred adapter (extensible) |
| `IDENTIFICATION_CONFIDENCE_AUTO_ACCEPT` | `0.85` | Threshold for "very certain" highlighting |
| `IDENTIFICATION_CONFIDENCE_MIN_SHOW` | `0.10` | Minimum confidence required to show a result |
| `IDENTIFICATION_MAX_IMAGE_SIZE_MB` | `10` | Maximum image size in megabytes |
| `IDENTIFICATION_RATE_LIMIT_PER_USER_DAY` | `0` | Max requests per user per day (`0` = adapter limit) |

### Privacy note

Photos are **not** stored on the Kamerplanter server — they are transmitted to Pl@ntNet (CIRAD/INRIA, France/EU) for analysis only and discarded immediately afterwards. EXIF metadata (GPS, camera model) is stripped before transmission. Each user must consent to image transfer once. Full details: [Privacy (GDPR) — Photo Identification](privacy.md#photo-identification-plant_identification).

---

## Enabling Pest Detection {#enabling-pest-detection}

[Pest detection](pest-detection.md) is disabled by default (`PEST_DETECTION_ENABLED=false`). As long as no adapter is configured, the backend reports `adapter: null` and the "Check for Pests" button remains hidden for all users.

!!! note "Platform admin required"
    Only users with the platform role **admin** can configure pest detection. The settings apply platform-wide.

!!! note "Phase 1 — Self-Hosted-First"
    In the current phase (Phase 1) two adapters are available: the local **symptom adapter** (`local_pest_symptom`, requires no external services or user consent) and the optional **cloud adapter** (Kindwise, requires user consent). A self-hosted direct detector using ONNX is being prepared for Phase 2.

### Adapter 1: Local symptom adapter (self-hosted, recommended)

The local adapter detects damage patterns and symptoms (webbing, honeydew, suction damage) directly on the instance — no third-party service, no privacy consent required from users.

**Enable via environment variables:**

```bash
PEST_DETECTION_ENABLED=true
PEST_DETECTION_SYMPTOM_ENABLED=true
PEST_DETECTION_PRIMARY_ADAPTER=local_pest_symptom
```

=== "Kubernetes / Helm"

    ```bash
    kubectl create secret generic kamerplanter-secrets \
      --from-literal=PEST_DETECTION_ENABLED="true" \
      --from-literal=PEST_DETECTION_SYMPTOM_ENABLED="true" \
      --from-literal=PEST_DETECTION_PRIMARY_ADAPTER="local_pest_symptom" \
      --namespace kamerplanter
    ```

    Reference the secret in Helm values:

    ```yaml
    # helm/kamerplanter/values.yaml (excerpt)
    backend:
      envFrom:
        - secretRef:
            name: kamerplanter-secrets
    ```

=== "Docker Compose"

    ```bash
    # .env (do not commit)
    PEST_DETECTION_ENABLED=true
    PEST_DETECTION_SYMPTOM_ENABLED=true
    PEST_DETECTION_PRIMARY_ADAPTER=local_pest_symptom
    ```

    Restart the stack:

    ```bash
    docker compose up -d
    ```

=== "Local dev (kind / Skaffold)"

    ```yaml
    # helm/kamerplanter/values.yaml (local only, do not commit)
    backend:
      env:
        PEST_DETECTION_ENABLED: "true"
        PEST_DETECTION_SYMPTOM_ENABLED: "true"
        PEST_DETECTION_PRIMARY_ADAPTER: "local_pest_symptom"
    ```

!!! warning "Prerequisite: inference service + few-shot index"
    The local symptom adapter classifies via **few-shot classification on a frozen DINOv2 model** (no separate, license-critical model). For the button to appear and return real findings, **two** steps are required:

    1. **Deploy the inference service** (the same service used for plant identification). Once reachable it answers `GET /pest/ready`. <!-- REQ-029-A -->
    2. **Build the few-shot index** — a one-time cold start that pulls ~30 CC0/CC-BY images per class from GBIF and indexes them as prototypes. **No GBIF credentials required** (public occurrence search):

        ```bash
        # in the backend container/environment, with the inference service reachable
        python -m app.migrations.acquire_pest_dataset --manifest pest_reference_manifest.json
        ```

        The script fetches images, filters each to CC0/CC-BY, indexes the DINOv2 prototypes in the inference service, and writes an **attribution manifest** (CC-BY compliance). **No images are persisted.** Also available as the Celery task `acquire_pest_dataset_task`.

    While the index is empty, `/pest/detect` returns "no findings" (not an error). The **direct detector with bounding boxes** (mode 1) is in preparation for phase 2 (externally blocked: model license sign-off + benchmark).

!!! tip "Preview only, without the inference service"
    To just preview the UI without an inference service, enable the demo adapter: `PEST_DETECTION_ENABLED=true` + `PEST_DETECTION_DEMO_ENABLED=true`. It returns clearly-labelled placeholder findings — never for real decisions.

### Adapter 2: Cloud detection (Kindwise — optional, requires consent)

The Kindwise cloud adapter transmits photos to the Kindwise service (Brno, Czech Republic — EU) for analysis. It is disabled by default and requires explicit user consent (consent purpose `pest_detection_cloud`).

!!! warning "Verify contractual requirements before activation"
    Before activating the cloud adapter, the following points must be clarified:
    - Sign a data processing agreement (DPA under GDPR Art. 28) with Kindwise
    - Confirm EU hosting guarantee and data retention period contractually
    - Empirically test the suitability of the `plant.health` product for your target pest classes (indoor)
    Detailed checklist: `spec/analysis/pest-detection-implementation-prep.md` §5.

**Enable via environment variables:**

```bash
PEST_DETECTION_ENABLED=true
PEST_DETECTION_CLOUD_ENABLED=true
PEST_DETECTION_CLOUD_API_KEY=your-kindwise-api-key
PEST_DETECTION_PRIMARY_ADAPTER=local_pest_symptom   # local remains default; cloud selectable as fallback or primary
```

The button appears automatically in the UI after the next backend restart. Users who want to use the cloud adapter are prompted for consent on first use.

### Checking the status

Call the status endpoint (tenant-scoped, JWT required):

```bash
curl -H "Authorization: Bearer <JWT>" \
  http://localhost:8000/api/v1/t/{tenant_slug}/pests/status | python3 -m json.tool
```

Expected response when an adapter is active:

```json
{
  "adapter": "local_pest_symptom",
  "pest_detection_enabled": true,
  "symptom_enabled": true,
  "detector_enabled": false,
  "cloud_enabled": false
}
```

If `pest_detection_enabled: false` or `adapter: null`, the button remains hidden in the UI.

### Optional fine-tuning

The following variables do not usually need to be changed. A full description is available in the [Environment Variables reference](../reference/environment-variables.md#pest-detection-req-044):

| Variable | Default | Purpose |
|----------|---------|---------|
| `PEST_DETECTION_ENABLED` | `false` | Master switch — feature on/off |
| `PEST_DETECTION_SYMPTOM_ENABLED` | `true` | Damage pattern detection (mode 2) on/off |
| `PEST_DETECTION_DETECTOR_ENABLED` | `false` | Direct detector (mode 1, Phase 2) on/off |
| `PEST_DETECTION_CLOUD_ENABLED` | `false` | Cloud adapter on/off |
| `PEST_DETECTION_CLOUD_API_KEY` | — | API key for the cloud adapter (Kindwise) |
| `PEST_DETECTION_PRIMARY_ADAPTER` | `local_pest_symptom` | Preferred adapter |
| `PEST_DETECTION_MAX_IMAGE_SIZE_MB` | `8` | Maximum image size in megabytes |

### Privacy note

- **Local adapter:** Photos do not leave the instance; no consent required; EXIF is removed before any processing.
- **Cloud adapter:** Photos are sent to Kindwise (EU); users must consent once for the purpose `pest_detection_cloud`; DPA contractually required; EXIF stripped twice (frontend + backend).
- Photos are never stored permanently — only the detection result and an anonymous image hash are retained.

See [Privacy (GDPR)](privacy.md) for details.

---

## Curating Reference Images for Plant Identification

The self-hosted plant identification (DINOv2) compares user photos against a stored **reference index**. If that index contains blurry, misidentified, or otherwise unsuitable images, recognition accuracy for the affected species deteriorates.

As a platform admin you can **deselect individual reference images** after a visual inspection — they are then excluded from recognition but remain in the system (soft delete, reactivatable at any time). The full guide including the coverage threshold (< 5 active images), API endpoints, and FAQ is available at:

**[Curating Reference Images](reference-image-curation.md)**

---

## Approving user pest photos (moderation)

On the [pest detail page](pest-detail.md), users can contribute their own photos for a pest. These images are **private** at first (visible only to that user's garden/tenant). As a platform admin you can **promote** especially good shots to be globally visible.

Moderation lives in the admin area, in the **"Contributed pest images"** card:

1. Select the pest in question.
2. You see all contributed images **across all tenants** with a preview, provenance (user/tenant/date) and status (private/global).
3. **Promote** sets an image to `global` — it then appears in the gallery for all users (served through a global, read-only delivery path that exposes promoted images only). **Demote** reverts it (with confirmation).

!!! tip "Deselect directly on the detail page"
    As a platform admin you can also curate images **directly on the [pest detail page](pest-detail.md)**: the **"Show deselected"** switch reveals deactivated images too, and per image you can **deselect** it (deactivate instead of delete) or **re-include** it. This applies to recognition reference images and to contributed images. Regular users only ever see active images. Deselecting is reversible; a pure gallery deselection leaves the recognition index untouched.

!!! note "Effect on AI recognition"
    When [pest recognition](#enabling-pest-detection) is active (`PEST_DETECTION_ENABLED=true`), a promoted image is additionally fed into the recognition index as a few-shot reference (`source=user_contributed`) — provided the pest has a recognition class (`detection_slug`). Only the embedding and its provenance are stored, **never the original image**. Demoting retracts the reference.

!!! warning "Data protection"
    Contributed images are removed completely when a user or tenant is deleted (document, image file, and its preview images). Location data (EXIF) is stripped on upload. If an image was ever promoted, the same deletion also removes the recognition vector computed from it from the recognition base — regardless of whether the promotion was still active or had already been reverted at the time of deletion. If the inference-service is unreachable or not configured on the celery-worker at that point, the deletion stays open, or a tenant deletion is refused, rather than leaving vectors behind — see [Setting Up Plant Identification](../deployment/inference-service.md).

---

## Frequently Asked Questions

??? question "Who can assign the platform-admin role?"
    The platform-admin role can only be assigned by an existing platform admin — directly via the API or in the admin area. During initial setup, the first registered user is automatically configured as platform admin.

??? question "Can a platform admin view tenant data?"
    Yes. Platform admins have read access to all tenant-scoped data. This permission should be restricted to trusted individuals and accompanied by an audit log. <!-- REQ-024 -->

??? question "Is there a viewer role for the admin area?"
    Yes. The platform role `viewer` grants read access to all admin statistics and tenant overviews, but no write permissions.

??? question "Where exactly in the UI do I find the Pl@ntNet key setting?"
    Open **Account Settings** (click your profile picture in the top right) → **Integrations** tab → **Plant Identification** section. There you can enter, test, and remove the key. The setting is only visible to users with the platform role **admin**.

??? question "Can I also set the key as an environment variable instead of using the UI?"
    Yes. The environment variable `PLANTNET_API_KEY` remains fully supported and is suitable for GitOps workflows or automated deployments. Important: a key stored in the database via the Admin UI takes **precedence** over the environment variable and takes effect immediately without a pod restart.

??? question "What happens when the daily limit is exhausted?"
    The backend reports `remaining_today: 0`. The UI shows the message "Daily identification limit reached. Available again tomorrow." The limit resets daily at midnight UTC. All other features remain fully available.

??? question "Can I use a different recognition service instead of Pl@ntNet?"
    Currently Pl@ntNet is the only implemented adapter (`IDENTIFICATION_PRIMARY_ADAPTER=plantnet`). A phase-2 extension for local offline recognition (without a third-party service) is planned.

---

## See Also

- [Tenants & Gardens](tenants.md) — Tenant management as tenant-admin <!-- REQ-024 -->
- [Roles, Tenants & Visibility](../reference/roles-and-permissions.md) — Platform role versus garden role
- [Privacy (GDPR)](privacy.md) — Data subject rights and GDPR compliance
- [Authentication](../api/authentication.md) — JWT, OAuth2/OIDC, service accounts
- [Identify Plant by Photo](plant-identification.md) — End-user guide
- [Environment Variables](../reference/environment-variables.md) — Full variable reference
