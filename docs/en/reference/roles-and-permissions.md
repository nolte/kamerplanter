# Roles, Tenants & Visibility

This page is the central place for every question about roles: which ones exist, how they interact with the tenant concept, why you can hold several roles at once, and who ends up seeing which data.

It answers three questions:

1. **Which roles exist** — and at which level do they apply?
2. **How do role and tenant relate** — and what happens when you take part in several gardens?
3. **Who sees what** — in particular: do your houseplants stay private while you are also active in an allotment association?

---

## The Three Levels at a Glance

In Kamerplanter, permissions come from three independent levels. They are frequently confused, but they must be considered separately:

| Level | What it controls | Where it applies | Values |
|-------|------------------|------------------|--------|
| **Tenant role** | What you may do inside *one* garden | Separately per tenant | Admin, Grower, Viewer |
| **Platform role** | Whether you may administer the instance (global master data, tenant overview) | Once for the entire installation | Platform administrator |
| **Account type** | Whether a human or a machine is behind the account | Per account | User account, service account |

The decisive property: the **tenant role belongs to the tenant, not to you**. You do not have a "Kamerplanter role" — you have one role per garden. Everything else on this page follows from that.

!!! info "What is a tenant?"
    A **tenant** is a self-contained container for data — your private garden, a community garden, a commercial operation. Every plant, location, task and harvest belongs to exactly one tenant. For a full introduction see [Tenants & Gardens](../user-guide/tenants.md).

---

## Tenant Roles: Who May Do What in a Garden

Inside a tenant, every member holds **exactly one** of three roles. They form a ranking: Admin includes everything a Grower may do; Grower includes everything a Viewer may do.

| Role | Short description | Typical use |
|------|-------------------|-------------|
| **Admin** | Full access inside the garden, including member and settings management | Association board, owner of a private garden |
| **Grower** | May plant, document and work through tasks — but not administer the garden | Active association member with their own plot |
| **Viewer** | May read everything, change nothing | Interested relatives, association archive, display screen |

### Role Comparison

<!-- Quelle: src/backend/app/core/permissions.py, src/backend/app/common/auth.py -->

| Task | Admin | Grower | Viewer |
|------|:-----:|:------:|:------:|
| Read all data in the garden | Yes | Yes | Yes |
| Create, edit and remove plants | Yes | Yes | No |
| Create and edit sites, areas and slots | Yes | Yes | No |
| Create planting runs and advance their phases | Yes | Yes | No |
| Create and complete tasks | Yes | Yes | No |
| Document harvests and post-harvest data | Yes | Yes | No |
| Log watering, feeding and treatments | Yes | Yes | No |
| Manage tanks and nutrient solutions | Yes | Yes | No |
| Create the garden's own fertilizers and nutrient plans | Yes | Yes | No |
| Confirm care reminders | Yes | Yes | No |
| Invite members, change roles, remove members | Yes | No | No |
| Change garden settings (name, slug, master-data assignment) | Yes | No | No |
| Manage location assignments | Yes | No | No |
| Delete the garden | Yes | No | No |
| View the member list (name and role) | Yes | Yes | Yes |
| Leave the garden yourself | Yes* | Yes | Yes |

*As the only admin you cannot leave the garden without first promoting another member to admin — otherwise the garden would be left without administration.

### Who May Manage Members?

Member management is deliberately reserved for admins. An admin can also only grant roles that do not exceed their own rank — so there is no way to gain more permissions than you already hold via member management.

!!! note "Partially available: Community features"
    The bulletin board, watering rotation and shared shopping list are planned for community gardens but not yet implemented. Once available they will get their own permissions in this table — until then they deliberately do not appear here. <!-- REQ-024 §1a.3 -->

---

## One Person, Several Roles at Once

A real user usually holds **several roles at once** — one per garden they are a member of. That is not an edge case but the norm: right after registration you have your personal garden, where you are automatically admin. Every further membership adds its own independent role.

The important points:

- **One role per garden, but any number of gardens.** There is no technical limit on the number of your memberships.
- **The roles are independent of each other.** Being admin in one garden grants you no additional permission whatsoever in another garden.
- **Only the garden you are currently working in counts.** Kamerplanter checks your role in exactly that garden for every action — not your "highest" role somewhere.
- **Your role can change at any time.** An association admin can demote you from grower to viewer; this takes effect immediately and exclusively in that garden.

### Example: Apartment and Allotment Association

The typical case this model was built for:

| Garden | Type | Your role | What it contains |
|--------|------|-----------|------------------|
| "My Home" | Personal | **Admin** | Monstera in the living room, basil on the windowsill, balcony boxes |
| "Grüne Aue Allotment Association" | Organization | **Grower** | Your plot 14, plus communal areas such as greenhouse and compost |
| "School Garden Club" | Organization | **Viewer** | You only watch, you document nothing |

One and the same person is admin, grower and viewer at the same time here — with no conflict, because each role only applies inside its own garden. In the association you cannot invite members (that would require the admin role there), in the school garden you cannot document anything — at home you may do everything.

### How to Switch Between Your Gardens

As soon as you are a member of more than one garden, a selector showing the current garden's name appears in the navigation bar. Clicking it lists all your gardens; the selection switches the entire application — dashboard, plant list, tasks, calendar, harvests. So you always see exactly one garden at a time, never a mix of several.

The step-by-step instructions are in [Tenants & Gardens](../user-guide/tenants.md#switching-between-tenants).

---

## Who Gets to See Which Elements?

Visibility falls into four categories. Every element in Kamerplanter belongs to exactly one of them.

### What Belongs to Exactly One Garden

This data is bound to a garden. Anyone who is a member of the garden sees it **in full** — regardless of role, because all three roles may read. Anyone who is not a member does not see it at all.

<!-- Quelle: tenant_key-Filter in src/backend/app/data_access/arango/ -->

- Plants and plant photos
- Sites, areas and slots
- Planting runs and succession plans
- Tasks and work planning
- Harvests and post-harvest data
- Watering log, feedings, plant-protection treatments and inspections
- Tanks and tank measurements
- The garden's sensors and actuators
- The garden's own fertilizers and nutrient plans
- Care profiles and overwintering profiles
- Dashboard metrics and calendar

Concretely this means: in a community garden **all members see all plots** — including those not assigned to them. Location assignment governs editing, not reading. A community garden is deliberately transparent: who turned the compost, or when plot 7 was last watered, should be traceable for everyone.

### What Belongs to You Personally — Across All Gardens

This data belongs to your account, not to a garden. It follows you into every garden, and no garden admin can view or change it:

<!-- Quelle: src/backend/app/domain/models/user_preference.py, notification_repository.py -->

- Your account: email address, display name, password, linked login providers
- Your sessions and signed-in devices
- Language and time zone
- Your experience level and the selection of visible modules
- Your personal dashboard arrangement
- Your notifications and notification channels
- Your privacy requests (data access, erasure)

So your experience level applies to you as a person — it is not a per-garden setting. Notifications are personal too: other members cannot see what was delivered to you.

### What All Gardens See Together

The master-data catalog is deliberately not split by garden but global. Every garden can **read** it, but only the platform administrator can change it:

<!-- Quelle: tenant_key == "" Sentinel, src/backend/app/data_access/arango/collections.py -->

- Plant species, cultivars and botanical families
- Pests, diseases and treatment products
- Global fertilizers and nutrient-plan templates
- Substrate types and workflow templates
- Climate zones and agroclimatic reference data

If you create your own cultivar or your own fertilizer inside your garden, it initially stays your garden's record. Only the platform administrator can promote such an entry into the global catalog, where it then becomes visible to everyone.

### What Is Never Visible Across Garden Boundaries

There is **no** way in Kamerplanter to share data between gardens or to look into another garden. This is an architectural decision, not a setting:

- No admin of a community garden sees data from your personal garden.
- No member of a garden sees which other gardens you belong to.
- There is no sharing feature that would let you "share" a single plant into another garden.

The platform administrator is the only exception — see [Platform Roles](#platform-roles-the-operator-level).

---

## Separating Private Care from Association Work

Because separating private plants from association work is the most common source of questions, here it is again in detail using the concrete case.

### Your Houseplants Stay Private

Registration automatically creates your **personal garden**, in which you are admin. Everything you create without deliberately switching to another garden first ends up there: the monstera, the basil, the balcony boxes. This garden is completely isolated from all others — including gardens where you are admin yourself.

An association admin sees **none** of it: not the plants, not the watering history, not the photos, not the tasks. In the association's member list they only see your display name and your role in the association.

### The Association Plot Stays With the Association

The reverse holds as well: your plot 14 belongs to the association's garden, not to you. If you leave the association, you lose access to that data — it stays with the association. Your private houseplants are unaffected. And if the association deletes its garden, your personal garden and all other memberships remain untouched.

### What This Means for Tasks and Reminders

| Element | Where it originates | Who sees it |
|---------|--------------------|-------------|
| Watering task for the monstera | Personal garden | Only you |
| Watering task for plot 14 | Association garden | All association members |
| Care reminder "water the basil" | Personal garden | Only you |
| Notification about a due association task | Association garden, delivered to you | Only you (everyone sees the task itself) |
| Your experience level "Intermediate" | Your account | Only you, applies in all gardens |

The everyday consequence: your dashboard and task list always show only the **currently selected** garden. There is no merged view across all gardens — if you want to check both your houseplants and the association plot in the morning, you switch gardens once. Notifications, by contrast, reach you regardless of which garden is currently open.

---

## Location Assignments Inside a Community Garden

A garden is a **shared working set**: all growers tend all plants and tasks of that garden. There is no partitioning of data among individual members inside a garden — whoever is a grower there may edit every plot.

An assignment is therefore an **agreement, not a barrier**:

- **Location assignment** — records who looks after a plot. It drives sorting, filtering and the "my plot" view, but does not restrict editing.
- **Task assignment** — records who takes a task on. The task is highlighted for that person; any grower may complete it — for instance when the assigned person drops out at short notice.
- **Viewers** — read everything, change nothing, regardless of assignments.

!!! tip "If you really want to keep something to yourself"
    Then it belongs in a garden of its own. The separation always runs along the garden boundary, never inside a garden. That is exactly what your personal garden is for — and you can create further gardens at any time, for example one just for you and your partner.

!!! example "Typical community garden"
    20 plots, each attributed to one member, plus a compost area and a greenhouse. Every member sees their own plot at a glance — but can step in when someone is on holiday, without an admin having to change anything.

---

## Platform Roles: The Operator Level

Besides the roles inside gardens there is a level above them: administering the installation itself. It is bound to an admin membership in a special, technical tenant that cannot be entered like a garden.

<!-- Quelle: src/backend/app/common/auth.py -->

| Role | What it may do |
|------|----------------|
| **Platform administrator** | Maintain the global master-data catalog; decide which global species a garden sees; overview of all gardens and user accounts; configure login providers; enable image recognition; promote a garden's own species and cultivars into the global catalog; suspend or reactivate gardens and accounts |

The platform administrator is therefore the only role that can look across garden boundaries — but only at **administrative data**: they see that a garden exists, what it is called and who is a member. This does not automatically grant read access to another garden's plants and harvests; for that, an admin of that garden would have to add them as a regular member.

The role is independent of the garden roles: a platform administrator is still not a member of your private garden. Conversely, being admin in a community garden makes nobody a platform administrator.

What the platform area offers in detail is described under [Platform Admin](../user-guide/admin.md).

!!! warning "Not yet implemented"
    A read-only role for the platform area is planned — intended for monitoring and audits, without write access to global data. It will make it possible to view the administration area without being able to change anything. Currently only the full platform administrator exists. <!-- REQ-024 §1a.4 Platform-Viewer -->

---

## Accounts for Machines

Besides accounts for humans there are **service accounts** for connecting other systems — for example Home Assistant, an analytics dashboard or an AI assistant.

<!-- Quelle: src/backend/app/domain/models/user.py, src/backend/app/mcp_server/auth.py -->

Technically a service account is an ordinary account with two peculiarities: it has no password and cannot sign in through the interface — it authenticates exclusively via a key. And it receives **the same roles as a human**: a service account with the grower role in your garden may do exactly what a human grower may do there, and no more.

From this follows the practical rule for setup: give a service account the lowest role that is sufficient for its job. A display dashboard needs **Viewer**. An automation service that logs watering needs **Grower**. A service account only needs **Admin** if it is supposed to create locations or manage members — which is rarely the case.

For AI assistants connected via the tool interface the same ranking applies: a viewer account may only query, a grower account may additionally document, and setup-style interventions such as creating locations remain reserved for admin accounts.

Setup is described under [Service Accounts](../api/service-accounts.md).

---

## Roles in Light Mode

Kamerplanter can be run without sign-in — as a local single-person installation. In this operating mode the entire role model collapses into a single case:

<!-- Quelle: src/backend/app/common/auth.py is_platform_admin -->

- There is exactly one account, and it is signed in automatically.
- That account is admin in its garden **and** platform administrator.
- There is no member management, no invitations and no role selection — there is nobody to assign a role to.

Everything described on this page only becomes relevant once the installation runs with sign-in. Switching is possible: on migration, the first registered account becomes admin of the existing garden and platform administrator. Details under [Light Mode](../user-guide/light-mode.md).

---

## For Technical Users / Self-Hosters

### Where Roles Are Checked Technically

The role is resolved from the membership on every access to a tenant-scoped path: the garden's slug is part of the path, and the membership of the signed-in account is looked up from it. If it is missing or inactive, the request ends with `403`. Endpoints then use a minimum-role dependency to check whether the resolved role is sufficient.

Isolation between gardens happens one layer deeper, in the database queries: every tenant-scoped query filters on the garden's key. Global catalog data is marked with an empty tenant key and additionally admitted in queries — which is why it is readable everywhere.

The interface hides write actions for the viewer role; it reads the role of the active garden and derives from it whether edit buttons appear.

### Limits of the Current Enforcement

Three limitations matter for operations, because the specification is ahead of the implementation here:

- **The viewer role is not yet a reliable boundary.** A substantial share of writing endpoints currently only checks membership in the garden, not the minimum role. Anyone addressing the interface directly can therefore create and change data as a viewer, even though the interface does not offer it. So assign the viewer role as an organizational arrangement, not as a security boundary against a member you do not trust. The ranking is fully enforced for actuators, propagation, aquaponics, post-harvest, inventory and member management, among others.
- **Notifications currently reach only one person.** The target state delivers every due task to all growers of the garden. What is implemented is a single recipient — whoever created or last edited the task, falling back to the assigned person. When a care task is generated automatically and nobody is assigned, **nobody** is notified at present.
- **Some side paths around the plant sit outside the garden check.** The plant endpoints proper verify garden ownership on every access. Three older paths, however, are bound only to being signed in, not to a garden: a plant's growth phases, its care reminders, and an older dashboard summary. Anyone who knows the key of another garden's plant can read and change phase and care data through them. Likewise, writing access to the global master-data catalog (species, lifecycles, phase profiles) is not yet restricted to the platform role.

The first two points only affect the gradation **inside** a garden. The third affects the separation **between** gardens: for the core resources — plant list, locations, tasks, harvests, photos — it is enforced in all queries; for the side paths named above it is not yet. So for now, run an instance with several mutually unknown parties only with trustworthy accounts.

### Location Assignments via the API

Assignments are managed under the path `/api/v1/t/{garden-slug}/assignments`; all writing calls there are reserved for the admin role. An assignment links a membership to a location and carries a flag for the intended edit permission plus a free-text note field. The corresponding calls already exist in the frontend as interface functions but are not yet wired to any page.

---

## Frequently Asked Questions

??? question "Can I be admin in one garden and only viewer in another?"
    Yes, and that is the norm. Roles always apply to a single garden only. Your role in one garden has no effect whatsoever on another.

??? question "Do the association members see my houseplants?"
    No. Your houseplants live in your personal garden, which is completely separate from all other gardens. In the member list, association members only see your display name and your role in the association.

??? question "Do other association members see my plot in the association?"
    Yes. Inside a garden all members may read everything — including other people's plots. Location assignment is meant to govern *editing*, not reading. If you want to keep something truly private, it belongs in your personal garden.

??? question "Can an association admin change my role without asking me?"
    Yes, inside their garden. They can demote you to viewer there or remove you entirely. They have no access to your personal garden or your other memberships.

??? question "What happens to my data if I leave the association?"
    Whatever you documented in the association's garden stays there — the data belongs to the garden, not to you. You only lose access. Your personal garden is unaffected.

??? question "Is there a view across all my gardens?"
    No. You always see exactly one garden. Notifications are the exception: they reach you regardless of which garden is currently open.

??? question "How do I get permissions for the platform area?"
    Through an admin membership in the technical platform tenant — granted by an existing platform administrator. On your own installation, the first registered account receives this role automatically.

??? question "Does Home Assistant need an admin account?"
    No. A service account with the grower role is enough to read and document; admin would only be needed to create locations.

---

## See Also

- [Tenants & Gardens](../user-guide/tenants.md) — creating gardens, inviting members, switching gardens
- [Account & Sign-In](../user-guide/account.md) — registration, login providers, sessions
- [Platform Admin](../user-guide/admin.md) — the administration area in detail
- [Light Mode](../user-guide/light-mode.md) — running without sign-in
- [Service Accounts](../api/service-accounts.md) — setting up accounts for machines
- [Privacy (GDPR)](../user-guide/privacy.md) — your rights regarding your data
- [Database Schema](database-schema.md) — collections and edges behind tenants and memberships
