<!-- REQ-023 — Source: src/frontend/src/pages/auth/{LoginPage,RegisterPage,EmailVerificationPage,PasswordResetRequestPage,PasswordResetConfirmPage,OAuthCallbackPage,AccountSettingsPage,EmailChangeCard,EmailChangeConfirmPage,EmailChangeRevertPage}.tsx, src/backend/app/domain/services/auth_service.py, src/backend/app/domain/engines/login_throttle_engine.py, src/backend/app/config/settings.py — REQ-025 (Art. 16) for the email change itself, see privacy.md -->

# Account & Sign-In

This page explains how to create a Kamerplanter account, sign in, and manage your personal settings such as profile, language and active sessions.

!!! info "Applies to Full Mode"
    This page describes multi-user operation (Full Mode) with registration and login. If your instance runs in **Light Mode**, there is no sign-in at all — see [Light Mode](light-mode.md).

---

## Prerequisites

- Your Kamerplanter instance runs in Full Mode
- A valid email address you have access to

## Creating an Account (Registration)

1. Open the sign-in page and click **Don't have an account? Register**
2. Fill in the form:

    | Field | Description |
    |-------|-------------|
    | **Display Name** | Your name as shown in the app |
    | **Email** | Your sign-in email address |
    | **Password** | At least 10 characters |
    | **Confirm Password** | Must match the password |

3. Click **Register**

Registration automatically creates your **personal tenant** (see [Tenants & Gardens](tenants.md)) — your private space for plants, locations and tasks.

### Confirming Your Email Address

After registering, you receive an email with a confirmation link.

1. Open the email and click the confirmation link
2. The page shows **Email successfully verified** — you can now sign in
3. Click **Log in** to go straight to the sign-in page

!!! warning "Sign-in only works after confirmation"
    As long as your email address is unconfirmed, the system rejects sign-in attempts. The confirmation link is valid for **24 hours**. If the email doesn't arrive, check your spam folder.

#### When the Confirmation Link No Longer Works

If the link is older than 24 hours or was copied incompletely, the page shows a red notice instead of the success message — for example **Invalid or expired token**. Below it you will find the same **Log in** button, which takes you back to the sign-in page. From there you can sign in (if your address was already confirmed via an earlier link) or use **Forgot password?** to have another email sent to you.

!!! note "Changed behaviour"
    Up to this version this error page was a dead end: it showed only the error message and no way back into the application — you had to type the sign-in page's address yourself. <!-- REQ-023 -->

---

## Signing In

### With Email and Password

1. Enter your email address and password
2. Optionally enable **Remember me**
3. Click **Log in**

!!! tip "Only use \"Remember me\" on private devices"
    Without **Remember me**, your session expires after 24 hours. With it enabled, it stays active for up to 30 days. Only use this option on devices no one else can access.

### Signing In with Google, GitHub or Another Provider

If your administrator has configured external sign-in providers, additional buttons such as **Log in with Google** appear below the sign-in form. Under the hood, Kamerplanter uses **OpenID Connect (OIDC)**, an open standard that connects providers such as Google, GitHub or Apple.

1. Click the button for the provider you want to use
2. Sign in with the provider and confirm access
3. You are redirected back to Kamerplanter and signed in

Kamerplanter links the provider to an existing local account only when **both sides** confirm the email address: your local account and the provider. If sign-in fails, you land back on the sign-in page with an error message. Try again, or sign in with email and password instead.

!!! info "When the provider says nothing about the address"
    Some providers never say whether they have confirmed an email address. Kamerplanter treats that silence as "unconfirmed" and skips the automatic link. Sign in with your email and password instead — the sign-in page tells you so when this happens.

!!! note "Alternative sign-in options not showing?"
    If the list of external providers fails to load, the sign-in page shows a message. You can still sign in with email and password in this case.

### Temporary Account Lock

After several failed sign-in attempts in a row, the system temporarily locks your account to protect it from automated attacks. The lockout starts at a few minutes and increases with further failed attempts — the sign-in form shows how much longer the lock lasts. Wait until the lock expires or reset your password (see below).

---

## Forgot and Reset Your Password

1. On the sign-in page, click **Forgot password?**
2. Enter your email address and click **Send Reset Link**
3. You see the confirmation **If an account with this email exists, a reset link has been sent**

!!! note "Why this message always appears"
    This message is shown regardless of whether an account with the entered address exists. It prevents outsiders from using the reset feature to discover which email addresses are registered with Kamerplanter.

4. Open the reset link from the email (valid for **1 hour**)
5. Choose a new password (at least 10 characters) and confirm it
6. Click **Save Password** — you are redirected to the sign-in page

---

## Managing Profile, Language and Timezone

Open your account settings via your profile picture or initials in the top right of the navigation bar.

In the **Profile** tab you can change:

| Setting | Description |
|---------|-------------|
| **Display Name** | Shown throughout the app |
| **Email** | Display only here — change your sign-in address in the **Change Email Address** section right below (see next section) |
| **Language** | German or English — switches the interface language immediately |
| **Timezone** | Used for all date and time displays, e.g. `Europe/Berlin` |

Click **Save** after making changes.

---

## Changing Your Email Address

In the **Profile** tab of your account settings, below your profile data, you'll find the **Change Email Address** section. This is the correction path under GDPR Art. 16 — for the full breakdown of what happens to your data, see [Changing Your Email Address (GDPR Art. 16)](privacy.md#changing-your-email-address-gdpr-art-16).

1. Enter the **new email address** and click **Request Change**
2. Confirm yourself in the dialog that opens — with your **current password**, if your account has one, otherwise via **Sign in again** (Google, generic OIDC provider) or, only for accounts linked exclusively to GitHub/Apple, via **Send code by email**
3. The interface confirms: a confirmation link was sent to the new address; your **current** address is notified about the requested change immediately

Until confirmed, you keep signing in with your previous address.

!!! tip "Confirming via the new address"
    Open the email at the **new** address and click **Confirm New Address**. Only that click makes the new address your sign-in address — merely opening the email is not enough. All your sessions are then signed out; you sign in again with the new address afterwards.

!!! warning "Wrong recipient? Undo it"
    Your **previous** address also receives an email after confirmation — with a link that lets you undo the change once, within 7 days. This also unlinks sign-in providers newly linked since the change and revokes API keys created since then. For the full breakdown of what the restore does, see [Changing Your Email Address (GDPR Art. 16)](privacy.md#changing-your-email-address-gdpr-art-16).

---

## Changing Your Password and Managing Sign-In Providers

In the **Security** tab of your account settings you manage how you sign in.

### Changing or Setting Your Password

- If you already have a local password, enter your current password and choose a new one
- If you have only ever signed in via an external provider, you can **set** a local password here as well — instead of a current password (which doesn't exist yet), click **Sign in again** for Google or a generic OIDC provider and confirm with a fresh sign-in at that provider; only if you sign in exclusively through GitHub or Apple, click **Send code by email** instead and enter the code from the mail. Afterwards you can sign in either with email/password or via the provider.

!!! warning "Changing your password ends all sessions"
    As soon as you change your password, all active sessions are terminated — including on other devices. You will need to sign in again there.

!!! note "Locked out after too many attempts"
    Entering your current password correctly is itself a re-confirmation step (just like account or tenant deletion, see below). If you enter it wrong repeatedly, the system locks the confirmation for 15 minutes — repeated failures double the wait time up to 4 hours; the error message shows the remaining time. This lock only affects the confirmation, not signing in itself.

### Linked Sign-In Providers

The list shows all sign-in methods linked to your account (local password, Google, GitHub, …). You can unlink a provider as long as at least one other sign-in method remains. Your last remaining sign-in method cannot be removed, so you can never be locked out of your account.

To unlink one, you additionally confirm with your current password — if you don't have one, you instead sign in again with that provider (**Sign in again**), or, only if you sign in exclusively through GitHub or Apple, have a code sent by email. This is the same confirmation path as changing your password above, with the same lockout behaviour after too many failed attempts. <!-- REQ-023 -->

!!! note "Couldn't load the list?"
    If the list fails to load, the card shows a warning. As long as it is unclear whether your account has a local password, the password form above keeps showing the current-password field as a precaution — reload the page to try again.

---

## Viewing and Ending Active Sessions

The **Sessions** tab shows all devices and browsers you are currently signed in on:

| Column | Meaning |
|--------|---------|
| **Device** | Browser/device information; your current session is marked |
| **Session Type** | **Persistent** (created with "Remember me", up to 30 days) or **Session** (without it, up to 24 hours) |
| **IP** | IP address the session was created from |
| **Expires** | Expiry date of the session |

To end a session you don't recognize or no longer need, click the trash icon on that row. You cannot end your current session here — for that, use **Log out** in the account menu.

!!! tip "Found a suspicious session?"
    End it immediately, then change your password — that automatically ends all remaining sessions (see above).

### Connecting a Mobile Device by QR Code

In the same **Sessions** tab, click **Connect mobile device** to connect a phone or tablet to your account without typing your password on that device.

1. Click **Connect mobile device**
2. Confirm with your current password — if you don't have one, sign in again with your sign-in provider, or, only if you sign in exclusively through GitHub or Apple, have a code sent by email
3. Open the Kamerplanter app on your phone, choose **Connect device** there, and scan the displayed QR code
4. The device then appears in the session list above and can be signed out there at any time

!!! warning "Never share the QR code"
    The QR code signs a device in to your account fully and permanently. Never show it to anyone, and only scan a code you just generated yourself — it is valid for a few seconds only.

!!! note "Why a re-confirmation?"
    Because the QR code fully signs in a new device, you first confirm it is you — so nobody can connect a device of their own from a browser you left open. <!-- REQ-023 -->

---

## Managing API Keys

In the **API Keys** tab, you create and revoke personal access keys for programmatic access — for example your own scripts, the MCP server, or a Home Assistant integration that cannot sign in interactively.

### Creating an API Key

1. Click **Create API key**
2. Give it a **label** that will help you recognize it later (e.g. "MCP server" or "Home Assistant")
3. Confirm with your current password — if you don't have one, sign in again with your sign-in provider, or, only if you sign in exclusively through GitHub or Apple, have a code sent by email
4. Copy the displayed key to a safe place right away

!!! danger "The key is shown only once"
    For security reasons, Kamerplanter shows the full key only right after creation. If you close the dialog without copying it, you need to create a new key.

!!! note "Why a re-confirmation?"
    An API key signs applications in to your account permanently — it stays valid even if you change your password (see below). That is why you confirm creating one, so nobody can quietly set up access from a browser you left open. <!-- REQ-023 -->

### Revoking an API Key

The list shows all your keys with their label, creation date, and last used time. Click **Revoke API key** to invalidate a key you no longer need or don't recognize, immediately.

!!! warning "Changing your password does not revoke API keys"
    Unlike sessions, changing your password, resetting it, or "sign out everywhere" do **not** end existing API keys — a key represents a deliberately set-up integration that would otherwise fail without warning. If you suspect your account was compromised: change your password, sign out everywhere, **and** additionally revoke any API key you don't recognize.

For further technical details (endpoints, IP allowlist, rate limits), see the [API documentation](../api/authentication.md).

---

## Experience Level and Other Settings

In the **Experience** tab of your account settings you can also:

- adjust your experience level (Beginner, Intermediate, Expert) — see [Getting Started — Onboarding](onboarding.md) for details on the three levels
- set your **watering can size**, which is used as a default in dosing calculators
- restart the **setup wizard**, for example to add another scenario

Which functional areas you show or hide independently of your experience level is controlled in the **Modules & Features** tab — see [Modules & Features](module-visibility.md).

Personal API keys are managed in the **API Keys** tab — see [Managing API Keys](#managing-api-keys) above.

---

## Deleting Your Account

In the **Account** tab of your account settings, the red-highlighted area contains the **Delete Account** button. This is the same erasure path as the Privacy area (see [Deleting Your Account (GDPR Art. 17)](privacy.md#deleting-your-account-gdpr-art-17)): your account is closed immediately — you can no longer sign in afterwards — and your personal data is permanently erased after the grace period (90 days by default). Legally protected data (harvest and treatment documentation) is anonymized instead of deleted.

The confirmation dialog asks you to type your **own email address** back in. If your account has a local password, you also enter your **current password**. If you sign in through Google or a generic OIDC provider instead, you click **Sign in again** in the dialog and confirm with a fresh sign-in at that provider; only if you sign in exclusively through GitHub or Apple — which cannot do that — you click **Send code by email** and enter the confirmation code it mails you.

!!! danger "Account deletion is permanent"
    Once you confirm, the deletion cannot be undone. Download your data export first if you want to keep a copy of your data (see [Privacy & GDPR](privacy.md)). For the full breakdown of what is deleted immediately, what is deleted after 90 days, and what is only anonymized, see [Deleting Your Account (GDPR Art. 17)](privacy.md#deleting-your-account-gdpr-art-17).

!!! note "Locked out after too many attempts"
    If you enter the password wrong repeatedly, the system locks the confirmation for 15 minutes — repeated failures double the wait time up to 4 hours; the dialog shows the remaining wait time. This lock only affects the deletion confirmation, not signing in: you can still sign in normally, end individual sessions in the **Sessions** tab, or reset your password via **Forgot password?**.

---

## Frequently Asked Questions

??? question "I didn't receive a confirmation email. What can I do?"
    Check your spam folder first. The confirmation link is valid for 24 hours; after that, you need to register again to receive a new email.

??? question "Can I change my email address?"
    Yes, in the **Profile** tab of your account settings, in the **Change Email Address** section (see above). The new address must be confirmed via a confirmation link; your previous address can then undo the change for 7 days. Details: [Changing Your Email Address (GDPR Art. 16)](privacy.md#changing-your-email-address-gdpr-art-16).

??? question "What happens if I unlink a sign-in provider like Google?"
    You will no longer be able to sign in through that provider. As long as at least one other sign-in method (password or another provider) remains, sign-in continues to work through that method.

??? question "Why were all my sessions ended when I only changed my password?"
    This is a security measure: after a password change, all sessions are ended as a precaution so a potentially compromised device no longer has access. You will need to sign in again everywhere.

??? question "Why does creating an API key or connecting a mobile device require re-confirmation?"
    An API key or a device paired by QR code signs an application in to your account permanently — both survive a later password change. The re-confirmation makes sure it is really you triggering the step, not someone who briefly had access to a browser you left open.

??? question "I suspect my account was compromised — what do I do?"
    Change your password (this automatically ends all sessions), or additionally use **Sign out everywhere**. Then revoke any key you don't recognize in the **API Keys** tab — a password change does **not** automatically revoke API keys.

---

## See Also

- [Getting Started — Onboarding](onboarding.md)
- [Tenants & Gardens](tenants.md)
- [Roles, Tenants & Visibility](../reference/roles-and-permissions.md)
- [Modules & Features](module-visibility.md)
- [Privacy & GDPR](privacy.md)
- [API Documentation: Authentication](../api/authentication.md)
