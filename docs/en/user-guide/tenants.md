# Tenants & Gardens

Kamerplanter is a multi-tenant platform: your data is organised in **tenants** — isolated containers that correspond to exactly one organisational form. You can be a member of multiple tenants at the same time, for example your private balcony garden and the community garden of your association.

---

## What Is a Tenant?

A tenant is the central isolation container for all resources: plants, locations, tasks, harvests and care data always belong to exactly one tenant. Other tenants cannot see this data.

| Tenant type | Use case | Example |
|-------------|---------|---------|
| **Personal** | Private garden, balcony garden, houseplants | Your own garden |
| **Organisation** | Community garden, club, business | "Green Oasis e.V.", cannabis cultivation association |

### Personal Tenant

When you register, the system automatically creates your **personal tenant**. You are automatically the admin there. All resources you create in Kamerplanter land in your personal tenant by default.

!!! info "Personal data stays private"
    Your personal tenant is completely isolated from all other tenants. No member of another tenant can see your private houseplants or balcony garden — even if you belong to the same community garden.

---

## Switching Between Tenants

If you are a member of multiple tenants, you will see a **tenant selector** in the top left of the navigation bar.

1. Click the tenant name in the navigation bar
2. A dropdown opens showing all your tenants
3. Click the desired tenant — the view switches immediately

The currently active tenant is highlighted in the navigation bar. The URL contains the tenant slug: `/t/green-oasis/locations/...`

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

You are automatically the admin of the new tenant.

---

## Inviting Members

As an admin you can invite members in three ways:

### Method 1: Email Invitation

1. Navigate to **Settings** > **Members** > **Invite**
2. Enter the member's email address
3. Choose the role (Admin, Grower, Viewer)
4. Click **Send Invitation**

The system sends an invitation email. After clicking the link in the email, the user is added to your tenant with the pre-selected role — whether they register fresh or already have an account.

### Method 2: Invitation Link

1. Navigate to **Settings** > **Members** > **Generate Invitation Link**
2. Optionally set:
    - Maximum number of uses (e.g. 20)
    - Expiry date (e.g. in 30 days)
    - Role new members will receive
3. Copy the link and share it (WhatsApp, notice board, email list)

!!! tip "Ideal for large groups"
    The invitation link is especially practical for community gardens: pin it at the garden gate or include it in the association newsletter. Anyone with the link can join until the limit is reached.

### Method 3: OIDC Auto-Join

For associations and organisations with their own identity provider (Keycloak, etc.), the OIDC integration can be configured so that new users automatically join the tenant. This is set up by the platform administrator.

---

## Roles and Permissions

Each member has exactly one role per tenant. The role determines what they are allowed to do:

### Role Comparison

| Task | Admin | Grower | Viewer |
|------|:-----:|:------:|:------:|
| Read everything | Yes | Yes | Yes |
| Create/edit plants | Yes | Yes | No |
| Create/edit locations | Yes | No* | No |
| Create tasks | Yes | Yes | No |
| Document harvests | Yes | Yes | No |
| Invite members | Yes | No | No |
| Change roles | Yes | No | No |
| Change tenant settings | Yes | No | No |
| Pin bulletin board posts | Yes | No | No |
| Manage shopping list | Yes | Yes | No |
| Create watering rotation | Yes | No | No |

*Growers can edit locations assigned to them.

### Changing Roles

1. Navigate to **Settings** > **Members**
2. Click the edit icon next to the desired member
3. Choose the new role
4. Confirm — the change takes effect immediately

---

## Location-Based Write Access

In a community garden, not every member should be able to edit every plot. The **assignment system** controls who can edit which locations:

### Assigning a Location to a Member

1. Navigate to **Locations** > desired location
2. Click **Edit Assignment**
3. Select the member from the dropdown
4. Click **Save**

**Rules for location assignments:**

- **Assigned locations**: Only the assigned grower and admins may edit
- **Unassigned locations**: All growers in the tenant may edit (communal areas)
- **Viewers**: Always read everything, regardless of assignments
- **Admins**: Can always edit everything

!!! example "Typical community garden"
    The community garden has 20 plots (each assigned to one person), a compost area and a greenhouse (both unassigned, so editable by all growers).

---

## Community Features

### Bulletin Board

The bulletin board is a shared message area for all tenant members.

1. Navigate to **Community** > **Bulletin Board**
2. Click **New Post**
3. Write your message and click **Publish**

Admins can pin posts so they appear at the top, and can delete posts.

!!! example "Typical bulletin board posts"
    - "Slug alert! Please set out beer traps."
    - "Saturday 10am: Community compost turning."
    - "Too many courgettes — who wants some?"

### Watering Rotation

For distributing watering duties among members:

1. Navigate to **Community** > **Watering Rotation**
2. Click **Create New Rotation**
3. Set the interval (e.g. weekly) and add the members
4. The system reminds the responsible member each week

Members can swap duties among themselves — without involving the admin.

### Shared Shopping List

1. Navigate to **Community** > **Shopping List**
2. All growers can add entries and tick them off
3. Admins can archive lists

---

## Tenant Settings

As an admin, you can access all settings under **Settings** (gear icon).

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

You can leave a tenant as long as you are not the only admin:

1. Navigate to **Settings** > **Membership** > **Leave Tenant**
2. Confirm

!!! warning "If you are the only admin"
    If you are the only admin, you must either promote another member to admin first, or delete the tenant.

---

## Frequently Asked Questions

??? question "Can I share data between tenants?"
    No — resources always belong to exactly one tenant. Cross-tenant sharing is deliberately not possible to ensure data isolation. Global master data (plant species, pests) is however visible to all tenants.

??? question "How many tenants can I create?"
    There is no technical limit. You can create and join as many tenants as you like.

??? question "What happens to my data when I delete a tenant?"
    All resources of the tenant are deleted. Your personal tenant and your memberships in other tenants are not affected.

??? question "Can tenant admins see my personal houseplants?"
    No. Your personal tenant is completely isolated from all other tenants. Even if an admin has more rights in the community garden, they can never see data in your personal tenant.

---

## See Also

- [Getting Started — Onboarding](onboarding.md)
- [User Accounts & Authentication](../api/authentication.md)
- [Locations & Substrates](locations-substrates.md)
