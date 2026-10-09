# Tenants & Gardens

Kamerplanter is a multi-tenant platform: your data is organised in **tenants** — isolated containers, each mapped to a single type of organization. You can be a member of multiple tenants at the same time, for example your private balcony garden and the community garden of your association.

---

## What Is a Tenant?

A tenant is the central isolation container for all resources: plants, locations, tasks, harvests and care data always belong to exactly one tenant. Other tenants cannot see this data.

| Tenant type | Use case | Example |
|-------------|---------|---------|
| **Personal** | Private garden, balcony garden, houseplants | Your own garden |
| **Organisation** | Community garden, club, business | "Green Oasis e.V.", cannabis cultivation association |

### Personal Tenant

When you register, the system automatically creates your **personal tenant**. You automatically hold the **Lead** role there plus both scopes (**Management** and **Technical**). All resources you create in Kamerplanter land in your personal tenant by default.

!!! info "Personal data stays private"
    Your personal tenant is completely isolated from all other tenants. No member of another tenant can see your private houseplants or balcony garden — even if you belong to the same community garden.

!!! warning "Your personal tenant ends with your account"
    If you invite someone into your personal tenant, it is deleted with your account — including everything the other members created in it. They receive an email as soon as you request the deletion. For a garden you want to run together for the long term, create a separate community garden instead. Details: [Data Retention](../guides/data-retention.md#what-happens-to-your-personal-garden).

!!! info "Member limit"
    Every tenant has a member limit. Your personal tenant starts at **1** — yourself. If you want to invite someone into your personal tenant, raise the limit first; otherwise the invited person is told on accepting that the tenant is full. A community garden starts at the maximum the platform operator sets (default: 50); it cannot go higher. <!-- Issue #2133 -->

---

## Switching Between Tenants

If you are a member of multiple tenants, you will see a **tenant selector** in the top left of the navigation bar.

1. Click the tenant name in the navigation bar
2. A dropdown opens showing all your tenants
3. Click the desired tenant — the view switches immediately

The currently active tenant is highlighted in the navigation bar. The URL contains the tenant slug: `/t/green-oasis/locations/...`

---

## Active Tenant: Catalog View and New Entries

If you are a member of a community garden, the actively selected tenant also affects the **plant catalog** — species, cultivars and botanical families.

- **The catalog view follows the active tenant.** With a community garden active, you see the global base catalog **plus** the species and cultivars that exact garden created itself. Species and cultivars belonging to a *different* one of your gardens stay hidden as long as that other garden is not active.
- **New entries belong to the active tenant.** If you create a new species or cultivar while a community garden is active, the new entry belongs to that garden — not to your personal garden. So switch the active tenant deliberately before creating a cultivar for the association.

!!! warning "Common misconception: union, not context switch"
    The active tenant does **not** show "everything I have ever created in any of my gardens". It shows exactly the view of the currently selected garden. If you are a member of three gardens, you see three different slices of the catalog depending on the active tenant — never all three combined at once. Use the tenant selector to see another garden's catalog entries.

Creating a new species or cultivar requires at least the Grower role in the active tenant; as a Viewer, you can only read the catalog. Details are available under [Roles, Tenants & Visibility](../reference/roles-and-permissions.md).

---

## What Stays the Same Across Your Gardens

Some settings belong to you, not to a garden. They apply in every tenant you are a member of and do **not** change with the tenant selector:

- your **dashboard layout** — which widgets sit where;
- your **notification settings** — channels, quiet hours, batching and escalation;
- which **modules** you show, your onboarding progress and your **favorites**.

What a widget shows, by contrast, always comes from the currently active garden: the same dashboard shows the community garden's plants and tasks there, and your own in your personal garden. A notification through Home Assistant only goes to destinations that are granted for the notification's garden.

---

## Creating a Community Garden

### Create a New Tenant

1. Click the tenant selector in the navigation bar
2. Choose **Create new garden**
3. Fill in the form:

    | Field | Description | Example |
    |-------|-------------|---------|
    | **Name** | Display name of the garden | Green Oasis e.V. |
    | **Slug** | URL-friendly short name (auto-generated) | green-oasis |
    | **Type** | Type of organisation | Organisation |
    | **Description** | Short description (optional) | Community garden in Westpark |

4. Click **Create**

You are automatically **Lead** of the new tenant and hold both scopes (**Management** and **Technical**).

---

## Inviting Members

With the **Management** scope you can invite members in three ways:

!!! note "When the tenant is full, the invitation stays open"
    Once your tenant has reached its member limit, nobody else can join — neither through an email invitation nor through an invitation link. The invitation does not expire because of it: as soon as a seat is free (somebody leaves the tenant) or you raise the limit, it can be accepted. Members who are already in always stay — even if you lower the limit below the current number of members. <!-- Issue #2133 -->

### Method 1: Email Invitation

1. Navigate to **Settings** > **Members** > **Invite**
2. Enter the member's email address
3. The invitation grants the **Viewer** role — you give the member another role after they join, under [Changing Roles](#changing-roles)
4. Click **Send Invitation**

The system sends an invitation email. After clicking the link in the email, the user is added to your tenant with the pre-selected role — whether they register fresh or already have an account.

!!! warning "The invitation is valid for the invited address only"
    An email invitation can only be accepted by the account whose email address is the invited one **and** has been confirmed. Forwarding the link does not hand the membership to anyone: another account — or the same account with a still unconfirmed address — gets `403`, the invitation stays open and nothing is created. When you are invited, confirm your account's address first and sign in with the account that carries it. An **invitation link** (method 2), by contrast, is meant to be shared and stays valid for any signed-in account. <!-- Issue #2115, REQ-024 AK-61 -->

### Method 2: Invitation Link

1. Navigate to **Settings** > **Members** > **Generate Invitation Link**
2. Optionally set:
    - Maximum number of uses (e.g. 20)
    - Expiry date (e.g. in 30 days)
    - Role new members will receive
3. Copy the link and share it (WhatsApp, notice board, email list)

!!! tip "Ideal for large groups"
    The invitation link is especially practical for community gardens: pin it at the garden gate or include it in the association newsletter. Anyone with the link can join until the limit is reached.

### Method 3: OIDC (OpenID Connect) Auto-Join

For associations and organisations with their own identity provider (Keycloak, etc.), the OIDC integration can be configured so that new users automatically join the tenant. This is set up by the platform administrator.

---

## Roles and Permissions

Each member has exactly one role per tenant: **Lead**, **Grower** or **Viewer**. The role determines what they may do with the garden's data. Independently of it, a member can hold scopes: **Management** (members, invitations, settings) and **Technical** (Home Assistant, sensors, import). There is no "Admin" role in a tenant any more.

### Role Comparison

| Task | Lead | Grower | Viewer |
|------|:----:|:------:|:------:|
| Read everything | Yes | Yes | Yes |
| Create/edit plants | Yes | Yes | No |
| Create/edit locations | Yes | Yes | No |
| Create tasks | Yes | Yes | No |
| Document harvests | Yes | Yes | No |
| Delete data | Yes | No | No |
| Choose a location's weather sources | Yes | No | No |

| Task | Who may do it? |
|------|----------------|
| Invite members | **Management** scope, regardless of role |
| Change roles | **Management** scope, regardless of role |
| Change tenant settings | **Management** scope, regardless of role |

The full permission overview — including platform roles, service accounts, and the question of who sees which data — is available under [Roles, Tenants & Visibility](../reference/roles-and-permissions.md).

!!! note "Planned community features are missing from this table"
    The bulletin board, watering rotation, and shared shopping list are not yet implemented (see [Community Features](#community-features) below) and therefore do not appear here as a permission.

### Changing Roles

1. Navigate to **Settings** > **Members**
2. Click the edit icon next to the desired member
3. Choose the new role
4. Confirm with **your own** credentials — the change takes effect immediately

!!! note "Changing a role and removing a member ask for your own confirmation"
    Whoever changes a member's role or removes a member enters **their own** current password for it — with no local password, they sign in again at their identity provider instead, or, only when they sign in exclusively through GitHub or Apple, have a code e-mailed. Reason: the role decides what someone may change and delete in the tenant, and removing a member locks that person out — the last lead too. Re-sending a role unchanged needs no confirmation. Deleting a plot attribution does not: it locks nobody out of the tenant.

!!! warning "You cannot raise your own role"
    Even with the management scope you cannot raise the role of your **own** membership — lowering it stays possible. In the technical `platform` tenant the lead role is the platform role; there, only someone who holds it hands it out, by role change as by invitation. In every other tenant the management scope may still appoint a lead. <!-- Issue #2078, REQ-024 AK-58 -->

---

## Attributing Plots

A garden is a shared working set: all growers tend all plants and tasks. A plot attribution therefore records **who looks after it** — it locks nobody out.

- **Attributed plots**: The member finds "their" plot faster; editing stays open to all growers.
- **Communal areas** such as compost or greenhouse need no attribution at all.
- **Viewers** read everything and change nothing — regardless of attributions.

The practical benefit: when someone drops out at short notice, another member steps in without someone with the Management scope having to change anything first.

!!! tip "Keeping something truly private"
    Separation always runs along the garden boundary, never inside a garden. Whatever concerns only you belongs in your personal garden — or in another garden, which you can create at any time.

!!! note "Partially available: Plot attribution"
    So far, attributions can only be created via the programming interface — there is no user interface for them yet. Details under [Roles, Tenants & Visibility](../reference/roles-and-permissions.md#location-assignments-inside-a-community-garden). <!-- REQ-049 §3.5 -->

---

## Community Features

!!! warning "Not yet implemented"
    The bulletin board, watering rotation, and shared shopping list are planned for community gardens but currently exist neither in the backend nor in the interface. The sections below describe the intended scope.

### Bulletin Board

The bulletin board will be a shared message area for all tenant members: members will be able to publish posts, and the lead will be able to pin and delete posts.

!!! example "Typical bulletin board posts (concept)"
    - "Slug alert! Please set out beer traps."
    - "Saturday 10am: Community compost turning."
    - "Too many courgettes — who wants some?"

### Watering Rotation

A rotation feature is planned for distributing watering duties among members: an interval (e.g. weekly) and the participating members will be configurable, and the system will remind the responsible member each week. Members will be able to swap duties among themselves without involving the lead.

### Shared Shopping List

A shared shopping list is planned: all growers will be able to add entries and tick them off, and the lead will be able to archive lists.

---

## Tenant Settings

With the **Management** scope, you can access all settings under **Settings** (gear icon).

### Key Settings

| Setting | Description |
|---------|-------------|
| **Name & Slug** | Display name and URL short name |
| **Master data assignment** | Which global plant species are visible |
| **Invitation settings** | Default role for new members |
| **OIDC configuration** | Auto-join via external identity provider |

!!! warning "Changing the slug breaks URLs"
    If you change the slug, all URLs within the tenant change. Bookmarks and shared links become invalid. Only change the slug if necessary.

---

## Leaving a Tenant

You can leave a tenant as long as you are not the only member with the **Management** scope:

1. Navigate to **Settings** > **Membership** > **Leave Tenant**
2. Confirm

!!! note "Tasks and reminders"
    When you leave a tenant — or someone with the Management scope removes you — you are no longer assigned to any task there: the tasks stay in the tenant, but without an assignee. The daily care reminders and the daily summary go to active members only; a summary holds the tasks of **one** tenant only (with several tenants you get one per tenant). <!-- Issue #2114, REQ-024 AK-62 -->

!!! warning "If you are the only member with Management"
    If you are the only member with the Management scope, you must either hand it to another member first, or delete the tenant — the latter additionally requires that you hold both the Lead role and the Management scope there. See [Roles, Tenants & Visibility](../reference/roles-and-permissions.md) for details. <!-- Issue #1791 -->

---

## Frequently Asked Questions

??? question "Can I share data between tenants?"
    No — resources always belong to exactly one tenant. Cross-tenant sharing is deliberately not possible to ensure data isolation. Global master data (plant species, pests) is however visible to all tenants.

??? question "How many tenants can I create?"
    There is no technical limit. You can create and join as many tenants as you like.

??? question "What happens to my data when I delete a tenant?"
    Only a member who holds both the Lead role and the Management scope in the affected tenant may delete it — Management alone is not enough (see [Roles, Tenants & Visibility](../reference/roles-and-permissions.md) for details) — and only from a signed-in session; a personal API key is not enough for this. As a safeguard, the system also asks you to re-enter the tenant's slug and, if the account has a local password, that password (in addition to the slug); an account without a local password that signs in through Google or a generic OIDC provider confirms instead with a fresh sign-in at that provider, an account signed in exclusively through GitHub and/or Apple with a one-time code mailed to it. After five wrong confirmations the system locks the confirmation for 15 minutes — repeated failures double the wait time up to 4 hours, and the error message states the remaining time; signing in itself is not affected. <!-- Issue #1791, #1813, #1814, #1816, #1815 -->

    The deletion is only **scheduled** at first: the tenant is closed for every member at once, and every member receives an email with the deletion date — until then they can save their own data through the data export. Until that date (90 days by default) a member with the Lead role and Management can cancel the deletion with their password (`POST /api/v1/tenants/{slug}/erasure/cancel`), and so can a platform admin in the admin area; the tenant is then active again, with every membership unchanged. <!-- Issue #2123 --> Only once the grace period has ended are all memberships deactivated. Then its contributed recognition vectors, its object storage (photos, attachments) and every domain record it holds are then deleted: sites, plants, planting runs, diary entries, tasks, tanks, sensors, feeding and watering logs, and every other location-bound record, then the tenant record itself. <!-- Issue #1769 -->

    One exception applies: harvest and treatment documentation (harvest batches, quality assessments, treatments, inspections) must be kept for several years under statutory law (CanG, German Plant Protection Act). These records are therefore retained but pseudonymized — members' names are removed from them and their account references replaced by a pseudonym.

    If not everything could be removed immediately, the deletion stays recorded and is retried automatically every day until it is complete. Your personal tenant and your memberships in other tenants are not affected by such a deletion.

??? question "Can the lead of a community garden see my personal houseplants?"
    No. Your personal tenant is completely isolated from all other tenants. Even if someone is lead or holds scopes in the community garden, they can never see data in your personal tenant.

---

## See Also

- [Roles, Tenants & Visibility](../reference/roles-and-permissions.md)
- [Getting Started — Onboarding](onboarding.md)
- [Account & Sign-In](account.md)
- [Locations & Substrates](locations-substrates.md)
